import os
import torch
import numpy as np
import torch.nn as nn
from loguru import logger
import pytorch_lightning as pl
from typing import Any, Dict, Mapping, Tuple
from yacs.config import CfgNode
from torch.optim.lr_scheduler import ReduceLROnPlateau

from .backbones import create_backbone
from .losses import  Keypoint2DLoss
from .heads.smpl_head_keypoints import build_keypoints_head
from .utils.train_utils import (
    trans_points2d_parallel, denormalize_images
)
from .utils.pylogger import get_pylogger
from .constants import  VITPOSE_BACKBONE
log = get_pylogger(__name__)


class DenseKP(pl.LightningModule):

    def __init__(self, cfg: CfgNode, init_renderer: bool = True):
        super().__init__()

        self.save_hyperparameters(logger=False, ignore=['init_renderer'])
        self.cfg = cfg

        # Backbone feature extractor
        self.backbone = create_backbone()
        self.backbone.load_state_dict(torch.load(VITPOSE_BACKBONE, map_location='cpu')['state_dict'])

        self.keypoint_2d_loss = Keypoint2DLoss(loss_type='l1')
        self.head = build_keypoints_head()
        self.validation_step_output = []        
        self.automatic_optimization = False
        self.criterion_keypoints = nn.MSELoss(reduction='none')

    def visualize(self, input_batch, output):
        images = input_batch['img']
        img = denormalize_images(images)[0]
        save_dir = os.path.join('.', 'output_images2')
        os.makedirs(save_dir, exist_ok=True)
        from matplotlib import pyplot as plt

        img = img.detach().cpu().numpy().transpose(1,2,0)*255
        img = np.clip(img, 0, 255).astype(np.uint8)
        fig = plt.figure(dpi=300)
        ax = fig.add_subplot(111)
        ax.imshow(img)

        pred_vertices = output['pred_keypoints'][0].detach().cpu().numpy()
        pred_vertices = (pred_vertices+0.5)*self.cfg.MODEL.IMAGE_SIZE
 
        confidences = pred_vertices[:, 2]
        ax.scatter(pred_vertices[:, 0], pred_vertices[:, 1], s=1.0)# s=0.5)
        save_filename = os.path.join(save_dir, f'result_{self.current_epoch:04d}')
        plt.savefig(save_filename)
        
        
    def get_parameters(self):
        all_params = list(self.head.parameters())
        all_params += list(self.backbone.parameters())
        return all_params

    def configure_optimizers(self):

        return torch.optim.AdamW(
                self.get_parameters(),
                lr=self.cfg.TRAIN.LR,
                weight_decay=self.cfg.TRAIN.WEIGHT_DECAY)


    def forward_step(self, batch: Dict, train: bool = False) -> Dict:

        x = batch['img']
        batch_size = x.shape[0]
        conditioning_feats = self.backbone(x[:,:,:,32:-32])
        output = self.head(conditioning_feats)
        # self.visualize(batch, output)
        return output


    def compute_loss(self, batch: Dict, output: Dict, train: bool = True) -> torch.Tensor:
        
        pred_keypoints = output['pred_keypoints']
        gt_keypoints_2d_cropped = batch['proj_verts_cropped']
        batch_size = output['pred_keypoints'].shape[0]
        device = output['pred_keypoints'].device
        dtype = output['pred_keypoints'].dtype

        num_landmarks = gt_keypoints_2d_cropped.shape[1]

        if not self.cfg.MODEL.with_var:
            kpts_diffs = gt_keypoints_2d_cropped[:,:,:2] - pred_keypoints[:, :, :2]  # shape: (B, K, 2)
            kpts_sq_diffs = torch.sum(torch.square(kpts_diffs), axis=-1)  # shape: (B, K)
            kpts_loss = torch.mean(kpts_sq_diffs)
            sigmas_loss = 0.
        else:
            #https://microsoft.github.io/DenseLandmarks/ for confidence
            kpts_diffs = gt_keypoints_2d_cropped[:,:,:2] - pred_keypoints[:, :, :2]  # shape: (B, K, 2)
            kpts_sq_diffs = 1000 * torch.sum(torch.square(kpts_diffs), axis=-1)  # shape: (B, K)
            eps = 1e-6
            pred_log_sigmas = pred_keypoints[:, :, -1].view(batch_size, num_landmarks)
            #clip sigmas
            pred_log_sigmas = torch.clip(pred_log_sigmas, min=np.log(eps), max=None)
            pred_sigmas = torch.exp(pred_log_sigmas)
            pred_sigmas_square = torch.square(pred_sigmas)
            keypoint_2_sigma_sq = 2.0 * pred_sigmas_square
            kpts_loss = torch.mean(kpts_sq_diffs * (1.0 / keypoint_2_sigma_sq))
            sigmas_loss = torch.mean(torch.log(pred_sigmas_square))
      
        loss_dict = {
            'loss/loss_keypoints': kpts_loss,
            'loss/loss_confidence': sigmas_loss,
        }

        loss = sum(loss for loss in loss_dict.values())
        loss = loss*60.
        loss_dict['loss/total_loss'] = loss

        return loss, loss_dict

    
    def forward(self, batch: Dict) -> Dict:
        return self.forward_step(batch, train=False)


    def training_step(self, joint_batch: Dict, batch_idx: int) -> Dict:

        batch = joint_batch['img']
        optimizer = self.optimizers(use_pl_optimizer=True)
  
        batch_size = batch['img'].shape[0]
        output = self.forward_step(batch, train=True)
        pred_smpl_params = output['pred_keypoints']
       
        loss, loss_dict = self.compute_loss(batch, output, train=True)


        optimizer.zero_grad()
        self.manual_backward(loss)
        optimizer.step()
 
        self.log('train/loss', loss, on_step=True, on_epoch=True, prog_bar=True, logger=False,sync_dist=True)
        return output

   

    def validation_step(self, batch: Dict, batch_idx: int, dataloader_idx=0) -> Dict:

        batch_size = batch['img'].shape[0]
        output = self.forward_step(batch, train=False)
        pred_keypoints = output['pred_keypoints']

        gt_keypoints_2d = batch['proj_verts']
        # plt.savefig('temp.png')
        gt_keypoints_2d_cropped = gt_keypoints_2d.clone()
        gt_keypoints_2d_cropped[:,:,:2] = trans_points2d_parallel(gt_keypoints_2d[:,:,:2], batch['_trans'])
        gt_keypoints_2d_cropped[:,:,:2] = gt_keypoints_2d_cropped[:,:,:2]/ self.cfg.MODEL.IMAGE_SIZE - 0.5
        loss_dict = {}

        proj_verts_loss = torch.sqrt(((pred_keypoints[:, :, :-1] - gt_keypoints_2d_cropped[:, :, :-1]) ** 2).sum(dim=-1))
        proj_verts_loss = (proj_verts_loss.mean(-1))

        if dataloader_idx==0:
            self.log('val_loss',proj_verts_loss.mean(), logger=True, sync_dist=True)    
        self.validation_step_output.append({'val_loss': proj_verts_loss,  'dataloader_idx': dataloader_idx})
    

    def on_validation_epoch_end(self, dataloader_idx=0):
        outputs = self.validation_step_output
        if outputs and isinstance(outputs[0], list):
            outputs = [item for sublist in outputs for item in sublist]

        dataloader_outputs = [x for x in outputs if x.get('dataloader_idx') == 0]
        if dataloader_outputs:  # Ensure there are outputs for this dataloader
            avg_val_loss = torch.stack([x['val_loss'] for x in dataloader_outputs]).mean()
          
            logger.info('kp2d: '+str(dataloader_idx)+str(avg_val_loss))
         
        if dataloader_idx==0:
            self.log('val_loss',avg_val_loss, logger=True, sync_dist=True)

    def test_step(self, batch: Dict, batch_idx: int, dataloader_idx=0) -> Dict:
        return self.validation_step(batch, batch_idx, dataloader_idx)

    def on_test_epoch_end(self):
        return self.on_validation_epoch_end()
   