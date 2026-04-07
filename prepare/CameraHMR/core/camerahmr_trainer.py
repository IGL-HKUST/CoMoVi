import torch
import pickle
import smplx
import pytorch_lightning as pl
from typing import Dict
from yacs.config import CfgNode
from loguru import logger
import numpy as np

from .backbones import create_backbone
from .losses import (
    Keypoint3DLoss, Keypoint2DLoss, Keypoint2DLossScaled, 
    ParameterLoss, VerticesLoss, TranslationLoss
)
from .cam_model.fl_net import FLNet
from .smpl_wrapper import SMPL2 as SMPL, SMPLLayer
from .heads.smpl_head_cliff import build_smpl_head
from .utils.train_utils import (
    trans_points2d_parallel, load_valid, perspective_projection, 
    convert_to_full_img_cam
)
from .utils.eval_utils import pck_accuracy, reconstruction_error
from .utils.geometry import aa_to_rotmat
from .utils.pylogger import get_pylogger
from .utils.renderer_cam import render_image_group
from .constants import (
    NUM_JOINTS, H36M_TO_J14, CAM_MODEL_CKPT, DOWNSAMPLE_MAT, 
    REGRESSOR_H36M, VITPOSE_BACKBONE, SMPL_MODEL_DIR
)

log = get_pylogger(__name__)

class CameraHMR(pl.LightningModule):
    """
    Pytorch Lightning Module for Camera Human Mesh Recovery (CameraHMR).
    This module integrates backbone feature extraction, camera modeling, SMPL fitting, 
    and loss functions for training a 3D human mesh recovery pipeline.
    """

    def __init__(self, cfg: CfgNode):
        super().__init__()
        
        self.save_hyperparameters(logger=False, ignore=['init_renderer'])
        self.cfg = cfg

        # Backbone feature extractor
        self.backbone = create_backbone()
        self.backbone.load_state_dict(torch.load(VITPOSE_BACKBONE, map_location='cpu')['state_dict'])

        # Camera model
        self.cam_model = FLNet()
        load_valid(self.cam_model, CAM_MODEL_CKPT)

        # SMPL Head
        self.smpl_head = build_smpl_head()

        # Loss functions
        loss_type = cfg.TRAIN.LOSS_TYPE
        self.keypoint_3d_loss = Keypoint3DLoss(loss_type=loss_type)
        self.keypoint_2d_loss = Keypoint2DLoss(loss_type=loss_type)
        self.keypoint_2d_loss_scaled = Keypoint2DLossScaled(loss_type=loss_type)
        self.trans_loss = TranslationLoss(loss_type=loss_type)
        self.vertices_loss = VerticesLoss(loss_type=loss_type)
        self.smpl_parameter_loss = ParameterLoss()

        self.smpl = SMPL(SMPL_MODEL_DIR, gender='neutral')
        self.smpl_layer = SMPLLayer(SMPL_MODEL_DIR, gender='neutral')

        # Ground truth SMPL models
        self.smpl_gt = smplx.SMPL(SMPL_MODEL_DIR, gender='neutral').cuda()
        self.smpl_gt_male = smplx.SMPL(SMPL_MODEL_DIR, gender='male').cuda()
        self.smpl_gt_female = smplx.SMPL(SMPL_MODEL_DIR, gender='female').cuda()

        # Initialize ActNorm layers flag
        self.register_buffer('initialized', torch.tensor(False))

        # Disable automatic optimization for adversarial training
        self.automatic_optimization = False

        # Additional configurations
        self.J_regressor = torch.from_numpy(np.load(REGRESSOR_H36M))
        self.downsample_mat = pickle.load(open(DOWNSAMPLE_MAT, 'rb')).to_dense().cuda()

        # Store validation outputs
        self.validation_step_output = []

    def get_parameters(self):
        """Aggregate model parameters for optimization."""
        return list(self.smpl_head.parameters()) + list(self.backbone.parameters())

    def configure_optimizers(self):
        """Configure optimizers for training."""
        optimizer = torch.optim.AdamW(
            params=[
                {
                    'params': filter(lambda p: p.requires_grad, self.get_parameters()),
                    'lr': self.cfg.TRAIN.LR
                }
            ],
            weight_decay=self.cfg.TRAIN.WEIGHT_DECAY
        )
        return optimizer


    def forward_step(self, batch: Dict, train: bool = False) -> Dict:
        # Use RGB image as input
        x = batch['img']
        batch_size = x.shape[0]
        
        # Compute conditioning features using the backbone
        # if using ViT backbone, we need to use a different aspect ratio
        conditioning_feats = self.backbone(x[:,:,:,32:-32])

        cx, cy = batch['box_center'][:, 0], batch['box_center'][:, 1]
    
        b = batch['box_size']
        img_h = batch['img_size'][:,0]
        img_w = batch['img_size'][:,1]
        if train:
            cam_intrinsics = batch['cam_int']
            fl_h = cam_intrinsics[:,0,0]
            vfov = (2 * torch.arctan((img_h)/(2*batch['cam_int'][:,0,0])))
            hfov = (2 * torch.arctan((img_w)/(2*batch['cam_int'][:,0,0])))
        else:
           cam_intrinsics = batch['cam_int']
           fl_h = cam_intrinsics[:,0,0]
           cam, features = self.cam_model(batch['img_full_resized'])
           vfov = cam[:, 1]
           fl_h = (img_h / (2 * torch.tan(vfov / 2)))
           cam_intrinsics[:,0,0]=fl_h
           cam_intrinsics[:,1,1]=fl_h
 

        # Original
        bbox_info = torch.stack([cx - img_w / 2., cy - img_h / 2., b],
                                dim=-1)
        bbox_info[:, :2] = bbox_info[:, :2] / cam_intrinsics[:, 0, 0].unsqueeze(-1)   # [-1, 1]
        bbox_info[:, 2] = (bbox_info[:, 2] / cam_intrinsics[:, 0, 0])  # [-1, 1]

        bbox_info = bbox_info.cuda().float()
        pred_smpl_params, pred_cam, _, pred_kp = self.smpl_head(conditioning_feats, bbox_info=bbox_info)

        # Compute model vertices, joints and the projected joints
        pred_smpl_params['global_orient'] = pred_smpl_params['global_orient'].reshape(batch_size, -1, 3, 3)
        pred_smpl_params['body_pose'] = pred_smpl_params['body_pose'].reshape(batch_size, -1, 3, 3)
        pred_smpl_params['betas'] = pred_smpl_params['betas'].reshape(batch_size, -1)
        smpl_output = self.smpl_layer(**{k: v.float() for k,v in pred_smpl_params.items()}, pose2rot=False)
        if train:
            smpl_output_gt = self.smpl(**{k: v.float() for k,v in batch['smpl_params'].items()})
            batch['gt_vertices'] = smpl_output_gt.vertices
            ones = torch.ones((batch_size, NUM_JOINTS, 1),device=self.device)
            batch['keypoints_3d'] = torch.cat((smpl_output_gt.joints[:,:NUM_JOINTS], ones), dim=-1)

        pred_keypoints_3d = smpl_output.joints
        pred_vertices = smpl_output.vertices
        output = {}

        output['pred_keypoints_3d'] = pred_keypoints_3d.reshape(batch_size, -1, 3)
        output['pred_vertices'] = pred_vertices.reshape(batch_size, -1, 3)
        
        # Store useful regression outputs to the output dict
        output['pred_cam'] = pred_cam
        output['pred_smpl_params'] = {k: v.clone() for k,v in pred_smpl_params.items()}

        # Compute camera translation
        device = pred_smpl_params['body_pose'].device
        dtype = pred_smpl_params['body_pose'].dtype

        cam_t = convert_to_full_img_cam(
            pare_cam=output['pred_cam'],
            bbox_height=batch['box_size'],
            bbox_center=batch['box_center'],
            img_w=img_w,
            img_h=img_h,
            focal_length=batch['cam_int'][:, 0, 0],
        )

      
        output['pred_cam_t'] = cam_t
        
        joints2d = perspective_projection(
            output['pred_keypoints_3d'],
            rotation=torch.eye(3, device=device).unsqueeze(0).expand(batch_size, -1, -1),
            translation=cam_t,
            cam_intrinsics=batch['cam_int'],
        )
        if self.cfg.LOSS_WEIGHTS['VERTS2D'] or self.cfg.LOSS_WEIGHTS['VERTS2D_CROP'] or self.cfg.LOSS_WEIGHTS['VERTS_2D_NORM']:
            pred_verts_subsampled = self.downsample_mat.matmul(output['pred_vertices'])

            pred_verts2d = perspective_projection(
                pred_verts_subsampled,
                rotation=torch.eye(3, device=device).unsqueeze(0).expand(batch_size, -1, -1),
                translation=cam_t,
                cam_intrinsics=batch['cam_int'],
            )
            output['pred_verts2d'] = pred_verts2d


        output['pred_keypoints_2d'] = joints2d.reshape(batch_size, -1, 2)
        import numpy as np

     
        return output, fl_h

    def perspective_projection_vis(self, input_batch, output, max_save_img=1):
        import os
        import cv2


        translation = input_batch['translation'].detach()[:,:3]
        vertices = input_batch['gt_vertices'].detach()
        for i in range(len(input_batch['imgname'])):
            cy, cx = input_batch['img_size'][i] // 2
            img_h, img_w = cy*2, cx*2
            imgname = input_batch['imgname'][i]
            save_filename = os.path.join('.', f'{self.global_step:08d}_{i:02d}_{os.path.basename(imgname)}')
            # focal_length_ = (img_w * img_w + img_h * img_h) ** 0.5  # Assumed fl
    
            focal_length_ = input_batch['cam_int'][i, 0, 0]
            focal_length = (focal_length_, focal_length_)

            rendered_img = render_image_group(
                image=cv2.imread(imgname),
                camera_translation=translation[i],
                vertices=vertices[i],
                focal_length=focal_length,
                camera_center=(cx, cy),
                camera_rotation=None,
                save_filename=save_filename,
                faces=self.smpl_gt.faces,
            )
            if i >= (max_save_img - 1):
                break

    def compute_loss(self, batch: Dict, output: Dict, train: bool = True) -> torch.Tensor:

        pred_smpl_params = output['pred_smpl_params']
        pred_keypoints_2d = output['pred_keypoints_2d']
        pred_keypoints_3d = output['pred_keypoints_3d']

        batch_size = pred_smpl_params['body_pose'].shape[0]
        device = pred_smpl_params['body_pose'].device
        dtype = pred_smpl_params['body_pose'].dtype

        # Get annotations
        gt_keypoints_3d = batch['keypoints_3d']
        gt_smpl_params = batch['smpl_params']


        img_size = batch['img_size'].rot90().T.unsqueeze(1)

        loss_keypoints_3d = self.keypoint_3d_loss(pred_keypoints_3d, gt_keypoints_3d, pelvis_id=25+14)
        loss_vertices = self.vertices_loss(output['pred_vertices'], batch['gt_vertices'])

        # Compute loss on SMPL parameters
        loss_smpl_params = {}
        for k, pred in pred_smpl_params.items():
            gt = gt_smpl_params[k].view(batch_size, -1)
            if 'beta' not in k:
                gt = aa_to_rotmat(gt.reshape(-1, 3)).view(batch_size, -1, 3, 3)
            loss_smpl_params[k] = self.smpl_parameter_loss(pred.reshape(batch_size, -1), gt.reshape(batch_size, -1))

        loss = self.cfg.LOSS_WEIGHTS['KEYPOINTS_3D'] * loss_keypoints_3d +\
                sum([loss_smpl_params[k] * self.cfg.LOSS_WEIGHTS[k.upper()] for k in loss_smpl_params])+\
                self.cfg.LOSS_WEIGHTS['VERTICES'] * loss_vertices


        if self.cfg.LOSS_WEIGHTS['VERTS2D_CROP']:
            gt_verts2d = batch['proj_verts']
            pred_verts2d = output['pred_verts2d']
            pred_verts2d_cropped = trans_points2d_parallel(pred_verts2d, batch['_trans'])
            pred_verts2d_cropped = pred_verts2d_cropped/ self.cfg.MODEL.IMAGE_SIZE - 0.5
            gt_verts_2d_cropped = gt_verts2d.clone()
            gt_verts_2d_cropped[:,:,:2] = trans_points2d_parallel(gt_verts2d[:,:,:2], batch['_trans'])
            gt_verts_2d_cropped[:,:,:2] = gt_verts_2d_cropped[:,:,:2]/ self.cfg.MODEL.IMAGE_SIZE - 0.5

            loss_proj_vertices_cropped = self.keypoint_2d_loss(pred_verts2d_cropped, gt_verts_2d_cropped)
            loss += self.cfg.LOSS_WEIGHTS['VERTS2D_CROP'] * loss_proj_vertices_cropped

        if self.cfg.LOSS_WEIGHTS['VERTS2D']:
            gt_verts2d = batch['proj_verts'].clone()
            pred_verts2d = output['pred_verts2d'].clone()
            pred_verts2d[:, :, :2] = 2 * (pred_verts2d[:, :, :2] / img_size) - 1
            gt_verts2d[:, :, :2] = 2 * (gt_verts2d[:, :, :2] / img_size) - 1
            loss_proj_vertices = self.keypoint_2d_loss(pred_verts2d, gt_verts2d)
            loss += self.cfg.LOSS_WEIGHTS['VERTS2D'] * loss_proj_vertices

        if self.cfg.LOSS_WEIGHTS['VERTS_2D_NORM']:
     
            gt_verts2d = batch['proj_verts'].clone()
            pred_verts2d = output['pred_verts2d'].clone()
            
            pred_verts2d[:, :, :2] =  (pred_verts2d[:, :, :2] - pred_verts2d[:, [0], :2])/batch['box_size'].unsqueeze(-1).unsqueeze(-1)
            gt_verts2d[:, :, :2] =  (gt_verts2d[:, :, :2] - gt_verts2d[:, [0], :2])/batch['box_size'].unsqueeze(-1).unsqueeze(-1)
            loss_proj_vertices_norm = self.keypoint_2d_loss(pred_verts2d, gt_verts2d)
            loss += self.cfg.LOSS_WEIGHTS['VERTS_2D_NORM'] * loss_proj_vertices_norm 

        if self.cfg.LOSS_WEIGHTS['KEYPOINTS_2D_CROP']:

            gt_keypoints_2d = batch['keypoints_2d'].clone()
            pred_keypoints_2d_cropped = trans_points2d_parallel(pred_keypoints_2d, batch['_trans'])
            pred_keypoints_2d_cropped = pred_keypoints_2d_cropped/ self.cfg.MODEL.IMAGE_SIZE - 0.5

            loss_keypoints_2d_cropped = self.keypoint_2d_loss(pred_keypoints_2d_cropped, gt_keypoints_2d)
            loss += self.cfg.LOSS_WEIGHTS['KEYPOINTS_2D_CROP'] * loss_keypoints_2d_cropped

        if self.cfg.LOSS_WEIGHTS['KEYPOINTS_2D']:
            pred_keypoints_2d_clone = pred_keypoints_2d.clone()
            pred_keypoints_2d_clone[:, :, :2] = 2 * (pred_keypoints_2d_clone[:, :, :2] / img_size) - 1
            gt_keypoints_2d = batch['orig_keypoints_2d']
            gt_keypoints_2d[:, :, :2] = 2 * (gt_keypoints_2d[:, :, :2] / img_size) - 1
            loss_keypoints_2d = self.keypoint_2d_loss_scaled(pred_keypoints_2d_clone, gt_keypoints_2d, batch['box_size'], img_size)
            loss += self.cfg.LOSS_WEIGHTS['KEYPOINTS_2D'] * loss_keypoints_2d 

        if self.cfg.LOSS_WEIGHTS['KEYPOINTS_2D_NORM']:
            # This loss would neek full kp loss or crop kp loss to anchor the root joint
            pred_keypoints_2d_clone = pred_keypoints_2d.clone()
            pred_keypoints_2d_clone[:, :, :2] =  (pred_keypoints_2d_clone[:, :, :2] - pred_keypoints_2d_clone[:, [0], :2])/batch['box_size'].unsqueeze(-1).unsqueeze(-1)
            gt_keypoints_2d = batch['orig_keypoints_2d'].clone()
            gt_keypoints_2d[:, :, :2] =  (gt_keypoints_2d[:, :, :2] - gt_keypoints_2d[:, [0], :2])/batch['box_size'].unsqueeze(-1).unsqueeze(-1)
            loss_keypoints_2d_norm = self.keypoint_2d_loss(pred_keypoints_2d_clone, gt_keypoints_2d)
            loss += self.cfg.LOSS_WEIGHTS['KEYPOINTS_2D_NORM'] * loss_keypoints_2d_norm

        if self.cfg.LOSS_WEIGHTS['TRANS_LOSS']:

            gt_trans = batch['translation'][:,:3]
            pred_trans = output['pred_cam_t']
            loss_trans = self.trans_loss(pred_trans, gt_trans)
            loss += self.cfg.LOSS_WEIGHTS['TRANS_LOSS'] * loss_trans

        losses = dict(loss=loss.detach(),
                      loss_keypoints_3d=loss_keypoints_3d.detach(),
                      loss_vertices=loss_vertices.detach(),
                      loss_kp2d_cropped=loss_keypoints_2d_cropped.detach())
        for k, v in loss_smpl_params.items():
            losses['loss_' + k] = v.detach()

        output['losses'] = losses

        return loss


    def forward(self, batch: Dict) -> Dict:
        return self.forward_step(batch, train=False)


    def training_step(self, joint_batch: Dict, batch_idx: int) -> Dict:

        batch = joint_batch['img']
        # mocap_batch = joint_batch['mocap']
        optimizer = self.optimizers(use_pl_optimizer=True)
        # if self.cfg.LOSS_WEIGHTS.ADVERSARIAL > 0:
        batch_size = batch['img'].shape[0]

        output,_ = self.forward_step(batch, train=True)
        pred_smpl_params = output['pred_smpl_params']

        loss = self.compute_loss(batch, output, train=True)
        # Error if Nan
        if torch.isnan(loss):
            print(batch['imgname'])
            for k,v in output['losses'].items():
                print(k,v)

        optimizer.zero_grad()
        self.manual_backward(loss)
        # Clip gradient
        if self.cfg.TRAIN.get('GRAD_CLIP_VAL', 0) > 0:
            gn = torch.nn.utils.clip_grad_norm_(self.get_parameters(), self.cfg.TRAIN.GRAD_CLIP_VAL, error_if_nonfinite=True)
            self.log('train/grad_norm', gn, on_step=True, on_epoch=True, prog_bar=True, logger=True,sync_dist=True)
        optimizer.step()
 
        self.log('train/loss', output['losses']['loss'], on_step=True, on_epoch=True, prog_bar=True, logger=False,sync_dist=True)
        return output

   

    def validation_step(self, batch: Dict, batch_idx: int, dataloader_idx=0) -> Dict:

        batch_size = batch['img'].shape[0]
        output,_ = self.forward_step(batch, train=False)
        dataset_names = batch['dataset']

        joint_mapper_h36m = H36M_TO_J14
        J_regressor_batch_smpl = self.J_regressor[None, :].expand(batch['img'].shape[0], -1, -1).float().cuda()


        if '3dpw' in dataset_names[0]:
            # For 3dpw vertices are generated in dataset.py because gender is needed
            gt_cam_vertices = batch['vertices']
            # Get 14 predicted joints from the mesh
            gt_keypoints_3d = torch.matmul(J_regressor_batch_smpl, gt_cam_vertices)
            gt_pelvis = gt_keypoints_3d[:, [0], :].clone()
            gt_keypoints_3d = gt_keypoints_3d[:, joint_mapper_h36m, :]
            gt_keypoints_3d = gt_keypoints_3d - gt_pelvis
            gt_cam_vertices = gt_cam_vertices - gt_pelvis
            # Convert predicted vertices to SMPL Fromat
            # Get 14 predicted joints from the mesh
            pred_cam_vertices = output['pred_vertices']

            pred_keypoints_3d = torch.matmul(J_regressor_batch_smpl, pred_cam_vertices)
            pred_pelvis = pred_keypoints_3d[:, [0], :].clone()
            pred_keypoints_3d = pred_keypoints_3d[:, joint_mapper_h36m, :]
            pred_keypoints_3d = pred_keypoints_3d - pred_pelvis
            pred_cam_vertices = pred_cam_vertices - pred_pelvis
            r_error, _ = reconstruction_error(
                pred_keypoints_3d.float().cpu().numpy(),
                gt_keypoints_3d.float().cpu().numpy(),
                reduction=None
            )
         
        elif 'emdb' in dataset_names[0]:
            gt_cam_vertices = batch['vertices']
            gt_keypoints_3d = torch.matmul(self.smpl.J_regressor, gt_cam_vertices)
            gt_pelvis = (gt_keypoints_3d[:, [1], :] + gt_keypoints_3d[:, [2], :]) / 2.0
            gt_keypoints_3d = gt_keypoints_3d - gt_pelvis
            gt_cam_vertices = gt_cam_vertices - gt_pelvis
            pred_cam_vertices = output['pred_vertices']

            pred_keypoints_3d = torch.matmul(self.smpl.J_regressor, pred_cam_vertices)
            pred_pelvis = (pred_keypoints_3d[:, [1], :] + pred_keypoints_3d[:, [2], :]) / 2.0
            pred_keypoints_3d = pred_keypoints_3d - pred_pelvis
            pred_cam_vertices = pred_cam_vertices - pred_pelvis
            # Reconstuction_error (PA-MPJPE)
            r_error, _ = reconstruction_error(
                pred_keypoints_3d.float().cpu().numpy(),
                gt_keypoints_3d.float().cpu().numpy(),
                reduction=None
            )

        elif 'rich' in dataset_names[0]:
            gt_cam_vertices = batch['vertices']
            gt_keypoints_3d = torch.matmul(self.smpl.J_regressor, gt_cam_vertices)
            gt_pelvis = (gt_keypoints_3d[:, [1], :] + gt_keypoints_3d[:, [2], :]) / 2.0
            gt_keypoints_3d = gt_keypoints_3d - gt_pelvis
            gt_cam_vertices = gt_cam_vertices - gt_pelvis
            pred_cam_vertices = output['pred_vertices']
            pred_keypoints_3d = torch.matmul(self.smpl.J_regressor, pred_cam_vertices)
            pred_pelvis = (pred_keypoints_3d[:, [1], :] + pred_keypoints_3d[:, [2], :]) / 2.0
            pred_keypoints_3d = pred_keypoints_3d - pred_pelvis
            pred_cam_vertices = pred_cam_vertices - pred_pelvis    
            r_error, _ = reconstruction_error(
                pred_keypoints_3d.float().cpu().numpy(),
                gt_keypoints_3d.float().cpu().numpy(),
                reduction=None
            )

        else:
            smpl_output_gt = self.smpl_gt(**{k: v.float() for k,v in batch['smpl_params'].items()})
            male_indices = (batch['gender'] == 0)  # Assuming 0 represents males
            female_indices = ~male_indices
            male_batch = {k: v[male_indices] for k, v in batch['smpl_params'].items()}
            female_batch = {k: v[female_indices] for k, v in batch['smpl_params'].items()}

            # Create an empty tensor with the same shape as the original batch
            output_shape = (batch['gender'].shape[0], 6890, 3)  # Assuming the output shape is the same for both models
            smpl_output_gt = torch.empty(output_shape, dtype=self.smpl_gt().vertices.dtype, device=batch['gender'].device)

        # Apply the smpl_gt_male and smpl_gt_female models
            if male_indices.any():
                smpl_output_gt[male_indices] = self.smpl_gt_male(**male_batch).vertices
            if female_indices.any():
                smpl_output_gt[female_indices] = self.smpl_gt_female(**female_batch).vertices

            gt_cam_vertices =smpl_output_gt
            pred_cam_vertices = output['pred_vertices']

            gt_keypoints_3d = torch.matmul(J_regressor_batch_smpl, gt_cam_vertices)
            pred_keypoints_3d = torch.matmul(J_regressor_batch_smpl, pred_cam_vertices)
            gt_pelvis = (gt_keypoints_3d[:, [1], :] + gt_keypoints_3d[:, [2], :]) / 2.0
            pred_pelvis = (pred_keypoints_3d[:, [1], :] + pred_keypoints_3d[:, [2], :]) / 2.0

            pred_keypoints_3d = pred_keypoints_3d - pred_pelvis
            pred_cam_vertices = pred_cam_vertices - pred_pelvis
            gt_keypoints_3d = gt_keypoints_3d - gt_pelvis
            gt_cam_vertices = gt_cam_vertices - gt_pelvis
            r_error, _ = reconstruction_error(
                pred_keypoints_3d.float().cpu().numpy(),
                gt_keypoints_3d.float().cpu().numpy(),
                reduction=None
            )
 
        img_h = batch['img_size'][:,0]
        img_w = batch['img_size'][:,1]
        device = output['pred_cam'].device
        cam_t = convert_to_full_img_cam(
            pare_cam=output['pred_cam'],
            bbox_height=batch['box_size'],
            bbox_center=batch['box_center'],
            img_w=img_w,
            img_h=img_h,
            focal_length=batch['cam_int'][:, 0, 0],
        )

        joints2d = perspective_projection(
            output['pred_keypoints_3d'],
            rotation=torch.eye(3, device=device).unsqueeze(0).expand(batch_size, -1, -1),
            translation=cam_t,
            cam_intrinsics=batch['cam_int'],
        )

        if batch['keypoints_2d'].shape[1]>=17:
            pred_kp = trans_points2d_parallel(joints2d, batch['_trans'])
            pred_kp = pred_kp / self.cfg.MODEL.IMAGE_SIZE - 0.5
            gt_kp = batch['keypoints_2d']
            mask = gt_kp[:,:,2]>0
            zeros_to_insert = torch.zeros((gt_kp.shape[0], 1, 3)).cuda()
            if '3dpw' in dataset_names[0]:
                gt_kp = torch.cat((gt_kp[:, :9, :], zeros_to_insert, gt_kp[:, 9:, :]), dim=1)    
                pck1, avgpck1, _ = (pck_accuracy(pred_kp[:,:18,:2],gt_kp[:,:18,:2],mask[:,:18],0.05))
                pck2, avgpck2, _ = (pck_accuracy(pred_kp[:,:18,:2],gt_kp[:,:18,:2],mask[:,:18],0.1))
            else: 
                pck1, avgpck1, _ = (pck_accuracy(pred_kp[:,:18,:2],gt_kp[:,:18,:2],mask[:,:18],0.05))
                pck2, avgpck2, _ = (pck_accuracy(pred_kp[:,:18,:2],gt_kp[:,:18,:2],mask[:,:18],0.1))

        else:
            pck1 = torch.zeros(joints2d.shape)
            pck2 = torch.zeros(joints2d.shape)

        # Absolute error (MPJPE)
        error = torch.sqrt(((pred_keypoints_3d - gt_keypoints_3d) ** 2).sum(dim=-1))
        error_verts = torch.sqrt(((pred_cam_vertices - gt_cam_vertices) ** 2).sum(dim=-1))

        # error_trans = torch.sqrt(((cam_t.unsqueeze(1) - batch['cam_trans']) ** 2).sum(dim=-1))
        # val_mrpe = error_trans.mean(-1)
        val_mpjpe = error.mean(-1)*1000
        val_pve = error_verts.mean(-1)*1000
        val_pampjpe = torch.tensor(r_error.mean(-1))*1000

        avgpck_005 = pck1
        avgpck_01 = pck2
        if 'coco' in dataset_names[0]:
            self.log('avgpck_0.05',avgpck_005.mean(), logger=True, sync_dist=True)
            self.log('avgpck_0.1',avgpck_01.mean(), logger=True, sync_dist=True)
        else:
            self.log('val_pve',val_pve.mean(), logger=True, sync_dist=True)
            # self.log('val_trans',val_mrpe.mean(), logger=True, sync_dist=True)
            self.log('val_mpjpe',val_mpjpe.mean(), logger=True, sync_dist=True)
            self.log('val_pampjpe',val_pampjpe.mean(), logger=True, sync_dist=True)

        self.validation_step_output.append({'val_loss': val_pve ,'val_loss_mpjpe': val_mpjpe, 'val_loss_pampjpe':val_pampjpe,  'avgpck_0.05':avgpck_005, 'avgpck_0.1':avgpck_01, 'dataloader_idx': dataloader_idx})

    def on_validation_epoch_end(self, dataloader_idx=0):
        # Flatten outputs if it's a list of lists
        outputs = self.validation_step_output
        if outputs and isinstance(outputs[0], list):
            outputs = [item for sublist in outputs for item in sublist]
        val_dataset = self.cfg.DATASETS.VAL_DATASETS.split('_')
        # Proceed with the assumption outputs is a list of dictionaries
        for dataloader_idx in range(len(val_dataset)):
            dataloader_outputs = [x for x in outputs if x.get('dataloader_idx') == dataloader_idx]
            if dataloader_outputs:  # Ensure there are outputs for this dataloader
                avg_val_loss = torch.stack([x['val_loss'] for x in dataloader_outputs]).mean()
                avg_mpjpe_loss = torch.stack([x['val_loss_mpjpe'] for x in dataloader_outputs]).mean()
                avg_pampjpe_loss = torch.stack([x['val_loss_pampjpe'] for x in dataloader_outputs]).mean()

                avg_pck_005_loss = torch.stack([x['avgpck_0.05'] for x in dataloader_outputs]).mean()
                avg_pck_01_loss = torch.stack([x['avgpck_0.1'] for x in dataloader_outputs]).mean()

                # avg_mrpe_loss = torch.stack([x['val_trans'] for x in dataloader_outputs]).mean()*1000
                logger.info('PA-MPJPE: '+str(dataloader_idx)+str(avg_pampjpe_loss))
                logger.info('MPJPE: '+str(dataloader_idx)+str(avg_mpjpe_loss))
                logger.info('PVE: '+str(dataloader_idx)+ str(avg_val_loss))
                logger.info('avgpck_0.05: '+str(dataloader_idx)+str(avg_pck_005_loss))
                logger.info('avgpck_0.1: '+str(dataloader_idx)+str(avg_pck_01_loss))
            if dataloader_idx==0:
                self.log('val_loss',avg_val_loss, logger=True, sync_dist=True)


    def test_step(self, batch: Dict, batch_idx: int, dataloader_idx=0) -> Dict:
        return self.validation_step(batch, batch_idx, dataloader_idx)

    def on_test_epoch_end(self):
        return self.on_validation_epoch_end()
