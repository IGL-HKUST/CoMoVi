import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
import einops

from ..utils.geometry import rot6d_to_rotmat, aa_to_rotmat
from ..components.pose_transformer import TransformerDecoder
from ..constants import TRANSFORMER_DECODER, SMPL_MEAN_PARAMS_FILE, NUM_BETAS, NUM_POSE_PARAMS

def build_smpl_head():
    return SMPLTransformerDecoderHead()


class SMPLTransformerDecoderHead(nn.Module):

    def __init__(self):
        super().__init__()
        self.joint_rep_dim = 6
        npose = self.joint_rep_dim * (NUM_POSE_PARAMS + 1)
        self.npose = npose
        transformer_args = dict(
            num_tokens=1,
            token_dim=(3 + npose + NUM_BETAS + 3),
            dim=1024,
        )
        transformer_args = (transformer_args | dict(TRANSFORMER_DECODER))
        self.transformer = TransformerDecoder(
            **transformer_args
        )
        dim=transformer_args['dim']
        self.decpose = nn.Linear(dim, npose)
        self.decshape = nn.Linear(dim, 10)
        self.deccam = nn.Linear(dim, 3)
        self.deckp = nn.Linear(dim, 88)

        mean_params = np.load(SMPL_MEAN_PARAMS_FILE)
        init_body_pose = torch.from_numpy(mean_params['pose'].astype(np.float32)).unsqueeze(0)
        init_betas = torch.from_numpy(mean_params['shape'].astype('float32')).unsqueeze(0)
        init_cam = torch.from_numpy(mean_params['cam'].astype(np.float32)).unsqueeze(0)
        self.register_buffer('init_body_pose', init_body_pose)
        self.register_buffer('init_betas', init_betas)
        self.register_buffer('init_cam', init_cam)

    def forward(self, x, bbox_info, **kwargs):
        batch_size = x.shape[0]
        # vit pretrained backbone is channel-first. Change to token-first
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
        token = torch.cat([bbox_info, pred_body_pose, pred_betas, pred_cam], dim=1)[:,None,:]

        # Pass through transformer
        token_out = self.transformer(token, context=x)
        token_out = token_out.squeeze(1) # (B, C)
        # Readout from token_out
        pred_body_pose = self.decpose(token_out) + pred_body_pose
        pred_betas = self.decshape(token_out) + pred_betas
        pred_cam = self.deccam(token_out) + pred_cam
        pred_kp = self.deckp(token_out)
        pred_body_pose_list.append(pred_body_pose)
        pred_betas_list.append(pred_betas)
        pred_cam_list.append(pred_cam)

        joint_conversion_fn = rot6d_to_rotmat

        pred_smpl_params_list = {}

        pred_smpl_params_list['body_pose'] = torch.cat([joint_conversion_fn(pbp).view(batch_size, -1, 3, 3)[:, 1:, :, :] for pbp in pred_body_pose_list], dim=0)
        pred_smpl_params_list['betas'] = torch.cat(pred_betas_list, dim=0)
        pred_smpl_params_list['cam'] = torch.cat(pred_cam_list, dim=0)
        pred_body_pose = joint_conversion_fn(pred_body_pose).view(batch_size, 24, 3, 3)

        pred_smpl_params = {'global_orient': pred_body_pose[:, [0]],
                            'body_pose': pred_body_pose[:, 1:],
                            'betas': pred_betas}
        return pred_smpl_params, pred_cam, pred_smpl_params_list, pred_kp
