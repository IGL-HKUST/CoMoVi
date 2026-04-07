import torch
import pytorch_lightning as pl
from .backbones import create_backbone
from .heads.smpl_head_cliff import build_smpl_head
from .constants import NUM_POSE_PARAMS

class CameraHMR(pl.LightningModule):

    def __init__(self):

        super().__init__()
        self.backbone = create_backbone()
        self.smpl_head = build_smpl_head()

    def forward(self, batch):
        x = batch['img']
        batch_size = x.shape[0]
        conditioning_feats = self.backbone(x[:, :, :, 32:-32])

        # Extract box centers, size, image dimensions, and camera intrinsics
        cx, cy = batch['box_center'][:, 0], batch['box_center'][:, 1]
        b = batch['box_size']
        img_h, img_w = batch['img_size'][:, 0], batch['img_size'][:, 1]
        cam_intrinsics = batch['cam_int']
        fl_h = cam_intrinsics[:, 0, 0]

        bbox_info = torch.stack([cx - img_w / 2., cy - img_h / 2., b], dim=-1)
        bbox_info[:, :2] /= cam_intrinsics[:, 0, 0].unsqueeze(-1)
        bbox_info[:, 2] /= cam_intrinsics[:, 0, 0]
        bbox_info = bbox_info.float()

        # Get SMPL parameters and camera prediction from the SMPLX head
        pred_smpl_params, pred_cam, _, _ = self.smpl_head(conditioning_feats, bbox_info=bbox_info)

        # Reshape SMPL parameter outputs
        pred_smpl_params['global_orient'] = pred_smpl_params['global_orient'].view(batch_size, -1, 3, 3)
        pred_smpl_params['body_pose'] = pred_smpl_params['body_pose'].view(batch_size, -1, 3, 3)[:, :NUM_POSE_PARAMS]  # Only use first 21 joints for now
        pred_smpl_params['betas'] = pred_smpl_params['betas'].view(batch_size, -1)


        return pred_smpl_params, pred_cam, fl_h