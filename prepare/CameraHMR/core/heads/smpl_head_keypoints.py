import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
import einops

from ..constants import TRANSFORMER_DECODER, NUM_DENSEKP_SMPL
from ..components.pose_transformer import TransformerDecoder

def build_keypoints_head():
    return KeypointsHead()
    
class KeypointsHead(nn.Module):

    def __init__(self, ):
        super().__init__()
        
        transformer_args = dict(
            num_tokens=1,
            token_dim=1,
            dim=1024,
        )
        transformer_args = (transformer_args | dict(TRANSFORMER_DECODER))
        self.transformer = TransformerDecoder(
            **transformer_args
        )
        dim=transformer_args['dim']
        self.dec_kp = nn.Linear(dim, NUM_DENSEKP_SMPL*3)

    def forward(self, x, **kwargs):
        batch_size = x.shape[0]
        # vit pretrained backbone is channel-first. Change to token-first
        x = einops.rearrange(x, 'b c h w -> b (h w) c')
        token = torch.zeros(batch_size, 1, 1).to(x.device)

        # Pass through transformer
        token_out = self.transformer(token, context=x)
        token_out = token_out.squeeze(1) # (B, C)
        # Readout from token_out
        pred_keypoints = self.dec_kp(token_out) 

        pred_keypoints = pred_keypoints.view(batch_size, -1, 3)

        output = {
            'pred_keypoints': pred_keypoints
        }
        return output
