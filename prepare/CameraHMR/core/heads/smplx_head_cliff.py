import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
import einops

from ..utils.geometry import rot6d_to_rotmat
from ..components.pose_transformer import TransformerDecoder
from ..constants import TRANSFORMER_DECODER, SMPL_MEAN_PARAMS_FILE, NUM_BETAS, NUM_POSE_PARAMS

def build_smplx_head():
    return SMPLXTransformerDecoderHead()


class SMPLXTransformerDecoderHead(nn.Module):
    def __init__(self):
        super().__init__()
        self.joint_rep_dim = 6
        npose = self.joint_rep_dim * (NUM_POSE_PARAMS + 1)
        self.npose = npose
        transformer_args = dict(
            num_tokens=1,
            token_dim=3,
            # token_dim=(3 + npose + NUM_BETAS + 3),
            dim=1024,
        )
        transformer_args = (transformer_args | dict(TRANSFORMER_DECODER))
        self.transformer = TransformerDecoder(
            **transformer_args
        )
        dim=transformer_args['dim']
        self.decpose = nn.Linear(dim, npose)
        self.decshape = nn.Linear(dim, NUM_BETAS)
        self.deccam = nn.Linear(dim, 3)

        mean_params = np.load(SMPL_MEAN_PARAMS_FILE)
    
        init_body_pose = torch.eye(3).reshape(1,3,3).repeat(NUM_POSE_PARAMS + 1, 1, 1)[:,:,:2].flatten(1).reshape(1, -1)
        init_body_pose[:, :22*6] = torch.from_numpy(mean_params['pose'][:22*6]).float() # global_orient+body_pose from SMPL

        init_betas = torch.zeros((1, NUM_BETAS)).float()
        init_betas[:, :10] = torch.from_numpy(mean_params['shape'].astype('float32')).unsqueeze(0)

        init_cam = torch.from_numpy(mean_params['cam'].astype(np.float32)).unsqueeze(0)

        self.register_buffer('init_body_pose', init_body_pose)
        self.register_buffer('init_betas', init_betas)
        self.register_buffer('init_cam', init_cam)


    def forward(self, x, bbox_info, **kwargs):
        batch_size = x.shape[0]
        x = einops.rearrange(x, 'b c h w -> b (h w) c')

        init_body_pose = self.init_body_pose.expand(batch_size, -1)
        init_betas = self.init_betas.expand(batch_size, -1)
        init_cam = self.init_cam.expand(batch_size, -1)

        pred_body_pose = init_body_pose
        pred_betas = init_betas
        pred_cam = init_cam
        pred_body_pose_list = []
        pred_betas_list = []
        pred_cam_list = []

 
        # token = torch.cat([bbox_info, pred_body_pose, pred_betas, pred_cam], dim=1)[:,None,:]
        token = bbox_info[:,None,:]

        token_out = self.transformer(token, context=x)
        token_out = token_out.squeeze(1) # (B, C)
        pred_body_pose = self.decpose(token_out) + pred_body_pose
        pred_betas = self.decshape(token_out) + pred_betas
        pred_cam = self.deccam(token_out) + pred_cam
        pred_body_pose_list.append(pred_body_pose)
        pred_betas_list.append(pred_betas)
        pred_cam_list.append(pred_cam)

        joint_conversion_fn = rot6d_to_rotmat

        pred_smpl_params_list = {}

        pred_smpl_params_list['body_pose'] = torch.cat([joint_conversion_fn(pbp).view(batch_size, -1, 3, 3)[:, 1:, :, :] for pbp in pred_body_pose_list], dim=0)
        pred_smpl_params_list['betas'] = torch.cat(pred_betas_list, dim=0)
        pred_smpl_params_list['cam'] = torch.cat(pred_cam_list, dim=0)
        pred_body_pose = joint_conversion_fn(pred_body_pose).view(batch_size, NUM_POSE_PARAMS+1, 3, 3)

        pred_smpl_params = {'global_orient': pred_body_pose[:, [0]],
                            'body_pose': pred_body_pose[:, 1:22],
                            # 'left_hand_pose':pred_body_pose[:, 25:40],
                            # 'right_hand_pose':pred_body_pose[:, 40:55],
                            # 'jaw_pose':pred_body_pose[:, 22:23],
                            # 'leye_pose':pred_body_pose[:, 23:24],
                            # 'reye_pose':pred_body_pose[:, 24:25],
                            'betas': pred_betas}
        return pred_smpl_params, pred_cam, pred_smpl_params_list
