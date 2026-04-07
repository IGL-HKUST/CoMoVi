# Modified from https://github.com/Wan-Video/Wan2.1/blob/main/wan/modules/model.py
# Copyright 2024-2025 The Alibaba Wan Team Authors. All rights reserved.

import glob
import json
import math
import os
import types
from typing import Any, Dict, Optional, Union

import numpy as np
import torch
import torch.cuda.amp as amp
import torch.nn as nn
from torch import nn
from safetensors.torch import load_file

from diffusers.configuration_utils import ConfigMixin, register_to_config
from diffusers.loaders.single_file_model import FromOriginalModelMixin
from diffusers.models.modeling_utils import ModelMixin
from diffusers.utils import is_torch_version

from ..dist import (
    get_sequence_parallel_rank,
    get_sequence_parallel_world_size,
    get_sp_group,
    usp_attn_forward
)
from ..utils import cfg_skip
from .attention_utils import attention
from .cache_utils import TeaCache
from .wan_camera_adapter import SimpleAdapter


def sinusoidal_embedding_1d(dim, position):
    # preprocess
    assert dim % 2 == 0
    half = dim // 2
    position = position.type(torch.float64)

    # calculation
    sinusoid = torch.outer(
        position, torch.pow(10000, -torch.arange(half).to(position).div(half)))
    x = torch.cat([torch.cos(sinusoid), torch.sin(sinusoid)], dim=1)
    return x


@amp.autocast(enabled=False)
def rope_params(max_seq_len, dim, theta=10000):
    assert dim % 2 == 0
    freqs = torch.outer(
        torch.arange(max_seq_len),
        1.0 / torch.pow(theta,
                        torch.arange(0, dim, 2).to(torch.float64).div(dim)))
    freqs = torch.polar(torch.ones_like(freqs), freqs)
    return freqs


# modified from https://github.com/thu-ml/RIFLEx/blob/main/riflex_utils.py
@amp.autocast(enabled=False)
def get_1d_rotary_pos_embed_riflex(
    pos: Union[np.ndarray, int],
    dim: int,
    theta: float = 10000.0,
    use_real=False,
    k: Optional[int] = None,
    L_test: Optional[int] = None,
    L_test_scale: Optional[int] = None,
):
    """
    RIFLEx: Precompute the frequency tensor for complex exponentials (cis) with given dimensions.

    This function calculates a frequency tensor with complex exponentials using the given dimension 'dim' and the end
    index 'end'. The 'theta' parameter scales the frequencies. The returned tensor contains complex values in complex64
    data type.

    Args:
        dim (`int`): Dimension of the frequency tensor.
        pos (`np.ndarray` or `int`): Position indices for the frequency tensor. [S] or scalar
        theta (`float`, *optional*, defaults to 10000.0):
            Scaling factor for frequency computation. Defaults to 10000.0.
        use_real (`bool`, *optional*):
            If True, return real part and imaginary part separately. Otherwise, return complex numbers.
        k (`int`, *optional*, defaults to None): the index for the intrinsic frequency in RoPE
        L_test (`int`, *optional*, defaults to None): the number of frames for inference
    Returns:
        `torch.Tensor`: Precomputed frequency tensor with complex exponentials. [S, D/2]
    """
    assert dim % 2 == 0

    if isinstance(pos, int):
        pos = torch.arange(pos)
    if isinstance(pos, np.ndarray):
        pos = torch.from_numpy(pos)  # type: ignore  # [S]

    freqs = 1.0 / torch.pow(theta,
        torch.arange(0, dim, 2).to(torch.float64).div(dim))

    # === Riflex modification start ===
    # Reduce the intrinsic frequency to stay within a single period after extrapolation (see Eq. (8)).
    # Empirical observations show that a few videos may exhibit repetition in the tail frames.
    # To be conservative, we multiply by 0.9 to keep the extrapolated length below 90% of a single period.
    if k is not None:
        freqs[k-1] = 0.9 * 2 * torch.pi / L_test
    # === Riflex modification end ===
    if L_test_scale is not None:
        freqs[k-1] = freqs[k-1] / L_test_scale

    freqs = torch.outer(pos, freqs)  # type: ignore   # [S, D/2]
    if use_real:
        freqs_cos = freqs.cos().repeat_interleave(2, dim=1).float()  # [S, D]
        freqs_sin = freqs.sin().repeat_interleave(2, dim=1).float()  # [S, D]
        return freqs_cos, freqs_sin
    else:
        # lumina
        freqs_cis = torch.polar(torch.ones_like(freqs), freqs)  # complex64     # [S, D/2]
        return freqs_cis


# Similar to diffusers.pipelines.hunyuandit.pipeline_hunyuandit.get_resize_crop_region_for_grid
def get_resize_crop_region_for_grid(src, tgt_width, tgt_height):
    tw = tgt_width
    th = tgt_height
    h, w = src
    r = h / w
    if r > (th / tw):
        resize_height = th
        resize_width = int(round(th / h * w))
    else:
        resize_width = tw
        resize_height = int(round(tw / w * h))

    crop_top = int(round((th - resize_height) / 2.0))
    crop_left = int(round((tw - resize_width) / 2.0))

    return (crop_top, crop_left), (crop_top + resize_height, crop_left + resize_width)


@amp.autocast(enabled=False)
@torch.compiler.disable()
def rope_apply(x, grid_sizes, freqs):
    n, c = x.size(2), x.size(3) // 2

    # split freqs
    freqs = freqs.split([c - 2 * (c // 3), c // 3, c // 3], dim=1)

    # loop over samples
    output = []
    for i, (f, h, w) in enumerate(grid_sizes.tolist()):
        seq_len = f * h * w

        # precompute multipliers
        x_i = torch.view_as_complex(x[i, :seq_len].to(torch.float32).reshape(
            seq_len, n, -1, 2))
        freqs_i = torch.cat([
            freqs[0][:f].view(f, 1, 1, -1).expand(f, h, w, -1),
            freqs[1][:h].view(1, h, 1, -1).expand(f, h, w, -1),
            freqs[2][:w].view(1, 1, w, -1).expand(f, h, w, -1)
        ],
                            dim=-1).reshape(seq_len, 1, -1)

        # apply rotary embedding
        x_i = torch.view_as_real(x_i * freqs_i).flatten(2)
        x_i = torch.cat([x_i, x[i, seq_len:]])

        # append to collection
        output.append(x_i)
    return torch.stack(output).to(x.dtype)


def rope_apply_qk(q, k, grid_sizes, freqs):
    q = rope_apply(q, grid_sizes, freqs)
    k = rope_apply(k, grid_sizes, freqs)
    return q, k


class WanRMSNorm(nn.Module):

    def __init__(self, dim, eps=1e-5):
        super().__init__()
        self.dim = dim
        self.eps = eps
        self.weight = nn.Parameter(torch.ones(dim))

    def forward(self, x):
        r"""
        Args:
            x(Tensor): Shape [B, L, C]
        """
        return self._norm(x) * self.weight

    def _norm(self, x):
        return x * torch.rsqrt(x.pow(2).mean(dim=-1, keepdim=True) + self.eps).to(x.dtype)


class WanLayerNorm(nn.LayerNorm):

    def __init__(self, dim, eps=1e-6, elementwise_affine=False):
        super().__init__(dim, elementwise_affine=elementwise_affine, eps=eps)

    def forward(self, x):
        r"""
        Args:
            x(Tensor): Shape [B, L, C]
        """
        return super().forward(x)


class WanSelfAttention(nn.Module):

    def __init__(self,
                 dim,
                 num_heads,
                 window_size=(-1, -1),
                 qk_norm=True,
                 eps=1e-6):
        assert dim % num_heads == 0
        super().__init__()
        self.dim = dim
        self.num_heads = num_heads
        self.head_dim = dim // num_heads
        self.window_size = window_size
        self.qk_norm = qk_norm
        self.eps = eps

        # layers
        self.q = nn.Linear(dim, dim)
        self.k = nn.Linear(dim, dim)
        self.v = nn.Linear(dim, dim)
        self.o = nn.Linear(dim, dim)
        self.norm_q = WanRMSNorm(dim, eps=eps) if qk_norm else nn.Identity()
        self.norm_k = WanRMSNorm(dim, eps=eps) if qk_norm else nn.Identity()

    def forward(self, x, seq_lens, grid_sizes, freqs, dtype=torch.bfloat16, t=0):
        r"""
        Args:
            x(Tensor): Shape [B, L, num_heads, C / num_heads]
            seq_lens(Tensor): Shape [B]
            grid_sizes(Tensor): Shape [B, 3], the second dimension contains (F, H, W)
            freqs(Tensor): Rope freqs, shape [1024, C / num_heads / 2]
        """
        b, s, n, d = *x.shape[:2], self.num_heads, self.head_dim

        # query, key, value function
        def qkv_fn(x):
            q = self.norm_q(self.q(x.to(dtype))).view(b, s, n, d)
            k = self.norm_k(self.k(x.to(dtype))).view(b, s, n, d)
            v = self.v(x.to(dtype)).view(b, s, n, d)
            return q, k, v

        q, k, v = qkv_fn(x)

        q, k = rope_apply_qk(q, k, grid_sizes, freqs)

        x = attention(
            q.to(dtype), 
            k.to(dtype), 
            v=v.to(dtype),
            k_lens=seq_lens,
            window_size=self.window_size)
        x = x.to(dtype)

        # output
        x = x.flatten(2)
        x = self.o(x)
        return x


class WanT2VCrossAttention(WanSelfAttention):

    def forward(self, x, context, context_lens, dtype=torch.bfloat16, t=0):
        r"""
        Args:
            x(Tensor): Shape [B, L1, C]
            context(Tensor): Shape [B, L2, C]
            context_lens(Tensor): Shape [B]
        """
        b, n, d = x.size(0), self.num_heads, self.head_dim

        # compute query, key, value
        q = self.norm_q(self.q(x.to(dtype))).view(b, -1, n, d)
        k = self.norm_k(self.k(context.to(dtype))).view(b, -1, n, d)
        v = self.v(context.to(dtype)).view(b, -1, n, d)

        # compute attention
        x = attention(
            q.to(dtype), 
            k.to(dtype), 
            v.to(dtype), 
            k_lens=context_lens
        )
        x = x.to(dtype)

        # output
        x = x.flatten(2)
        x = self.o(x)
        return x


class WanI2VCrossAttention(WanSelfAttention):

    def __init__(self,
                 dim,
                 num_heads,
                 window_size=(-1, -1),
                 qk_norm=True,
                 eps=1e-6):
        super().__init__(dim, num_heads, window_size, qk_norm, eps)

        self.k_img = nn.Linear(dim, dim)
        self.v_img = nn.Linear(dim, dim)
        # self.alpha = nn.Parameter(torch.zeros((1, )))
        self.norm_k_img = WanRMSNorm(dim, eps=eps) if qk_norm else nn.Identity()

    def forward(self, x, context, context_lens, dtype=torch.bfloat16, t=0):
        r"""
        Args:
            x(Tensor): Shape [B, L1, C]
            context(Tensor): Shape [B, L2, C]
            context_lens(Tensor): Shape [B]
        """
        context_img = context[:, :257]
        context = context[:, 257:]
        b, n, d = x.size(0), self.num_heads, self.head_dim

        # compute query, key, value
        q = self.norm_q(self.q(x.to(dtype))).view(b, -1, n, d)
        k = self.norm_k(self.k(context.to(dtype))).view(b, -1, n, d)
        v = self.v(context.to(dtype)).view(b, -1, n, d)
        k_img = self.norm_k_img(self.k_img(context_img.to(dtype))).view(b, -1, n, d)
        v_img = self.v_img(context_img.to(dtype)).view(b, -1, n, d)

        img_x = attention(
            q.to(dtype), 
            k_img.to(dtype), 
            v_img.to(dtype), 
            k_lens=None
        )
        img_x = img_x.to(dtype)
        # compute attention
        x = attention(
            q.to(dtype), 
            k.to(dtype), 
            v.to(dtype), 
            k_lens=context_lens
        )
        x = x.to(dtype)

        # output
        x = x.flatten(2)
        img_x = img_x.flatten(2)
        x = x + img_x
        x = self.o(x)
        return x


class WanCrossAttention(WanSelfAttention):
    def forward(self, x, context, context_lens, dtype=torch.bfloat16, t=0):
        r"""
        Args:
            x(Tensor): Shape [B, L1, C]
            context(Tensor): Shape [B, L2, C]
            context_lens(Tensor): Shape [B]
        """
        b, n, d = x.size(0), self.num_heads, self.head_dim
        # compute query, key, value
        q = self.norm_q(self.q(x.to(dtype))).view(b, -1, n, d)
        k = self.norm_k(self.k(context.to(dtype))).view(b, -1, n, d)
        v = self.v(context.to(dtype)).view(b, -1, n, d)
        # compute attention
        x = attention(q.to(dtype), k.to(dtype), v.to(dtype), k_lens=context_lens)
        # output
        x = x.flatten(2)
        x = self.o(x.to(dtype))
        return x

WAN_CROSSATTENTION_CLASSES = {
    't2v_cross_attn': WanT2VCrossAttention,
    'i2v_cross_attn': WanI2VCrossAttention,
    'cross_attn': WanCrossAttention,
}

class WanAttentionBlock(nn.Module):

    def __init__(self,
                 cross_attn_type,
                 dim,
                 ffn_dim,
                 num_heads,
                 window_size=(-1, -1),
                 qk_norm=True,
                 cross_attn_norm=False,
                 eps=1e-6):
        super().__init__()
        self.dim = dim
        self.ffn_dim = ffn_dim
        self.num_heads = num_heads
        self.window_size = window_size
        self.qk_norm = qk_norm
        self.cross_attn_norm = cross_attn_norm
        self.eps = eps

        # layers
        self.norm1 = WanLayerNorm(dim, eps)
        self.self_attn = WanSelfAttention(dim, num_heads, window_size, qk_norm,
                                          eps)
        self.norm3 = WanLayerNorm(
            dim, eps,
            elementwise_affine=True) if cross_attn_norm else nn.Identity()
        self.cross_attn = WAN_CROSSATTENTION_CLASSES[cross_attn_type](dim,
                                                                      num_heads,
                                                                      (-1, -1),
                                                                      qk_norm,
                                                                      eps)
        self.norm2 = WanLayerNorm(dim, eps)
        self.ffn = nn.Sequential(
            nn.Linear(dim, ffn_dim), nn.GELU(approximate='tanh'),
            nn.Linear(ffn_dim, dim))

        # modulation
        self.modulation = nn.Parameter(torch.randn(1, 6, dim) / dim**0.5)

    def forward(
        self,
        x,
        e,
        seq_lens,
        grid_sizes,
        freqs,
        context,
        context_lens,
        dtype=torch.bfloat16,
        t=0,
    ):
        r"""
        Args:
            x(Tensor): Shape [B, L, C]
            e(Tensor): Shape [B, 6, C]
            seq_lens(Tensor): Shape [B], length of each sequence in batch
            grid_sizes(Tensor): Shape [B, 3], the second dimension contains (F, H, W)
            freqs(Tensor): Rope freqs, shape [1024, C / num_heads / 2]
        """
        if e.dim() > 3:
            e = (self.modulation.unsqueeze(0) + e).chunk(6, dim=2)
            e = [e.squeeze(2) for e in e]
        else:        
            e = (self.modulation + e).chunk(6, dim=1)

        # self-attention
        temp_x = self.norm1(x) * (1 + e[1]) + e[0]
        temp_x = temp_x.to(dtype)

        y = self.self_attn(temp_x, seq_lens, grid_sizes, freqs, dtype, t=t)
        x = x + y * e[2]

        # cross-attention & ffn function
        def cross_attn_ffn(x, context, context_lens, e):
            # cross-attention
            x = x + self.cross_attn(self.norm3(x), context, context_lens, dtype, t=t)

            # ffn function
            temp_x = self.norm2(x) * (1 + e[4]) + e[3]
            temp_x = temp_x.to(dtype)
            
            y = self.ffn(temp_x)
            x = x + y * e[5]
            return x

        x = cross_attn_ffn(x, context, context_lens, e)
        return x

class Head(nn.Module):

    def __init__(self, dim, out_dim, patch_size, eps=1e-6):
        super().__init__()
        self.dim = dim
        self.out_dim = out_dim
        self.patch_size = patch_size
        self.eps = eps

        # layers
        out_dim = math.prod(patch_size) * out_dim
        self.norm = WanLayerNorm(dim, eps)
        self.head = nn.Linear(dim, out_dim)

        # modulation
        self.modulation = nn.Parameter(torch.randn(1, 2, dim) / dim**0.5)

    def forward(self, x, e):
        r"""
        Args:
            x(Tensor): Shape [B, L1, C]
            e(Tensor): Shape [B, C]
        """
        if e.dim() > 2:
            e = (self.modulation.unsqueeze(0) + e.unsqueeze(2)).chunk(2, dim=2)
            e = [e.squeeze(2) for e in e]
        else:
            e = (self.modulation + e.unsqueeze(1)).chunk(2, dim=1)
        
        x = (self.head(self.norm(x) * (1 + e[1]) + e[0]))
        return x

class MLPProj(nn.Module):

    def __init__(self, in_dim, out_dim):
        super().__init__()

        self.proj = nn.Sequential(
            nn.LayerNorm(in_dim), nn.Linear(in_dim, in_dim),
            nn.GELU(), nn.Linear(in_dim, out_dim),
            nn.LayerNorm(out_dim))

    def forward(self, image_embeds):
        clip_extra_context_tokens = self.proj(image_embeds)
        return clip_extra_context_tokens

class SmplSelfAttention(WanSelfAttention):
    def forward(self, pose_token, dtype=torch.bfloat16):
        r"""
        Args:
            pose_token(Tensor): Shape [B, (F-1)*4, C]
        """
        b, s, n, d = *pose_token.shape[:2], self.num_heads, self.head_dim

        # query, key, value function
        def qkv_fn(x):
            q = self.norm_q(self.q(x.to(dtype))).view(b, s, n, d)
            k = self.norm_k(self.k(x.to(dtype))).view(b, s, n, d)
            v = self.v(x.to(dtype)).view(b, s, n, d)
            return q, k, v

        q, k, v = qkv_fn(pose_token)

        x = attention(
            q.to(dtype), 
            k.to(dtype), 
            v=v.to(dtype)
        ).to(dtype)

        # output
        x = x.flatten(2)
        x = self.o(x)
        return x

class SmplCrossAttention(WanSelfAttention):
    def forward(self, pose_token, dit_token, dtype=torch.bfloat16, t=0):
        r"""
        Args:
            pose_token(Tensor): Shape [B, (F-1)*4, C]
            dit_token(Tensor): Shape [B, F*H*W, C]
        """
        b, f, n, d = dit_token.size(0), pose_token.size(1) // 4 + 1, self.num_heads, self.head_dim
        hw = dit_token.size(1) // f
        pose_token = pose_token.view(b*(f-1), 4, n*d)
        dit_token = dit_token.view(b, f, hw, n*d)[:, 1:].contiguous()
        dit_token = dit_token.view(b*(f-1), hw, n*d)

        # compute query, key, value
        q = self.norm_q(self.q(pose_token.to(dtype))).view(b*(f-1), 4, n, d)
        k = self.norm_k(self.k(dit_token.to(dtype))).view(b*(f-1), hw, n, d)
        v = self.v(dit_token.to(dtype)).view(b*(f-1), hw, n, d)
        
        # compute attention
        x = attention(q.to(dtype), k.to(dtype), v.to(dtype), k_lens=None)

        # output
        x = x.flatten(2)
        x = self.o(x.to(dtype))
        return x.view(b, (f-1)*4, n*d)

class SmplDecoderBlock(nn.Module):
    def __init__(self, transformer_dim, ffn_dim, num_heads=12):
        super().__init__()

        self.transformer_dim = transformer_dim
        self.ffn_dim = ffn_dim
        self.num_heads = num_heads

        self.norm1 = WanLayerNorm(transformer_dim)
        
        self.sa = SmplSelfAttention(transformer_dim, num_heads)
        self.norm2 = WanLayerNorm(transformer_dim)
        
        self.ca = SmplCrossAttention(transformer_dim, num_heads)
        self.norm3 = WanLayerNorm(transformer_dim)
        
        self.ffn = nn.Sequential(
            nn.Linear(transformer_dim, ffn_dim),
            nn.GELU(approximate='tanh'),
            nn.Linear(ffn_dim, transformer_dim)
        )
        self.norm4 = WanLayerNorm(transformer_dim)

    def forward(self, x_pose, fused_feature, dtype=torch.bfloat16):
        """
        Args:
            x_pose(Tensor): Shape [B, (F-1)*4, C]
            fused_feature(Tensor): Shape [B, F*H*W, C]
        """

        x_pose = x_pose + self.sa(self.norm2(x_pose), dtype=dtype)
        x_pose = x_pose + self.ca(self.norm3(x_pose), self.norm1(fused_feature), dtype=dtype)
        x_pose = x_pose + self.ffn(self.norm4(x_pose))
        
        return x_pose

class ComoviTransformer3DModel(ModelMixin, ConfigMixin, FromOriginalModelMixin):
    _supports_gradient_checkpointing = True

    @register_to_config
    def __init__(
        self,
        model_type='t2v',
        patch_size=(1, 2, 2),
        text_len=512,
        in_dim=16,
        dim=2048,
        ffn_dim=8192,
        freq_dim=256,
        text_dim=4096,
        out_dim=16,
        num_heads=16,
        num_layers=32,
        window_size=(-1, -1),
        qk_norm=True,
        cross_attn_norm=True,
        eps=1e-6,
        in_channels=16,
        hidden_size=2048,
        add_control_adapter=False,
        in_dim_control_adapter=24,
        downscale_factor_control_adapter=8,
        add_ref_conv=False,
        in_dim_ref_conv=16,
        cross_attn_type="cross_attn",
        interaction="dual",
        interleave=2,
        predict_smpl=False,
        smpl_predictor_layers=6,
        smpl_ffn_dim=4096
    ):
        r"""
        Initialize the diffusion model backbone.

        Args:
            model_type (`str`, *optional*, defaults to 't2v'):
                Model variant - 't2v' (text-to-video) or 'i2v' (image-to-video)
            patch_size (`tuple`, *optional*, defaults to (1, 2, 2)):
                3D patch dimensions for video embedding (t_patch, h_patch, w_patch)
            text_len (`int`, *optional*, defaults to 512):
                Fixed length for text embeddings
            in_dim (`int`, *optional*, defaults to 16):
                Input video channels (C_in)
            dim (`int`, *optional*, defaults to 2048):
                Hidden dimension of the transformer
            ffn_dim (`int`, *optional*, defaults to 8192):
                Intermediate dimension in feed-forward network
            freq_dim (`int`, *optional*, defaults to 256):
                Dimension for sinusoidal time embeddings
            text_dim (`int`, *optional*, defaults to 4096):
                Input dimension for text embeddings
            out_dim (`int`, *optional*, defaults to 16):
                Output video channels (C_out)
            num_heads (`int`, *optional*, defaults to 16):
                Number of attention heads
            num_layers (`int`, *optional*, defaults to 32):
                Number of transformer blocks
            window_size (`tuple`, *optional*, defaults to (-1, -1)):
                Window size for local attention (-1 indicates global attention)
            qk_norm (`bool`, *optional*, defaults to True):
                Enable query/key normalization
            cross_attn_norm (`bool`, *optional*, defaults to False):
                Enable cross-attention normalization
            eps (`float`, *optional*, defaults to 1e-6):
                Epsilon value for normalization layers
        """

        super().__init__()

        self.model_type = model_type

        self.patch_size = patch_size
        self.text_len = text_len
        self.in_dim = in_dim
        self.dim = dim
        self.ffn_dim = ffn_dim
        self.freq_dim = freq_dim
        self.text_dim = text_dim
        self.out_dim = out_dim
        self.num_heads = num_heads
        self.num_layers = num_layers
        self.window_size = window_size
        self.qk_norm = qk_norm
        self.cross_attn_norm = cross_attn_norm
        self.interaction = interaction
        self.interleave = interleave
        self.eps = eps
        assert self.num_layers % self.interleave == 0

        self.predict_smpl = predict_smpl
        if predict_smpl:
            self.num_joints = 24
            self.temporal_compression_ratio = 4
            self.pose_dim = self.num_joints * 6     # rotation 6d representation
            self.smpl_predictor_layers = smpl_predictor_layers
            self.smpl_ffn_dim = smpl_ffn_dim

        # patch embeddings
        self.rgb_patch_embedding = nn.Conv3d(
            in_dim, dim, kernel_size=patch_size, stride=patch_size)
        self.motion_patch_embedding = nn.Conv3d(
            in_dim, dim, kernel_size=patch_size, stride=patch_size)
        
        # text embedding
        self.text_embedding = nn.Sequential(
            nn.Linear(text_dim, dim),
            nn.GELU(approximate='tanh'),
            nn.Linear(dim, dim)
        )

        # time embedding
        self.time_embedding = nn.Sequential(
            nn.Linear(freq_dim, dim), nn.SiLU(), nn.Linear(dim, dim))
        self.time_projection = nn.Sequential(nn.SiLU(), nn.Linear(dim, dim * 6))

        # dit blocks
        if cross_attn_type is None:
            cross_attn_type = 't2v_cross_attn' if model_type == 't2v' else 'i2v_cross_attn'
        rgb_blocks = []; motion_blocks = []
        for i in range(num_layers):
            rgb_blocks.append(
                WanAttentionBlock(
                    cross_attn_type,
                    dim,
                    ffn_dim,
                    num_heads,
                    window_size,
                    qk_norm,
                    cross_attn_norm,
                    eps
                )
            )
            if i % self.interleave == 0:
                motion_blocks.append(
                    WanAttentionBlock(
                        cross_attn_type,
                        dim,
                        ffn_dim,
                        num_heads,
                        window_size,
                        qk_norm,
                        cross_attn_norm,
                        eps
                    )
                )
        self.rgb_blocks = nn.ModuleList(rgb_blocks)
        self.motion_blocks = nn.ModuleList(motion_blocks)

        # smpl predictors
        if predict_smpl:
            smpl_fusion_layers = []
            for i in range(len(motion_blocks)):
                smpl_fusion_layers.append(nn.Linear(dim, dim))
            self.smpl_fusion_layers = nn.ModuleList(smpl_fusion_layers)

            self.smpl_proj_in = nn.Linear(self.pose_dim, dim)
            self.smpl_pe = nn.Parameter(torch.randn(1, 80, dim))
            smpl_decoders = []
            for i in range(smpl_predictor_layers):
                smpl_decoders.append(SmplDecoderBlock(dim, smpl_ffn_dim))
            self.smpl_decoders = nn.ModuleList(smpl_decoders)
            self.smpl_proj_out = nn.Linear(dim, self.pose_dim)

        # interleaving zero linear layers
        if self.interaction != "none":
            zero_linear_blocks = []
            if self.interaction == "dual":
                for i in range(num_layers):
                    zero_linear_blocks.append(nn.Linear(dim, dim))
            else:
                for i in range(num_layers // self.interleave):
                    zero_linear_blocks.append(nn.Linear(dim, dim))
            self.zero_linear_blocks = nn.ModuleList(zero_linear_blocks)

        # head
        self.rgb_head = Head(dim, out_dim, patch_size, eps)
        self.motion_head = Head(dim, out_dim, patch_size, eps)

        # buffers (don't use register_buffer otherwise dtype will be changed in to())
        assert (dim % num_heads) == 0 and (dim // num_heads) % 2 == 0
        d = dim // num_heads
        self.d = d
        self.dim = dim
        self.freqs = torch.cat(
            [
                rope_params(1024, d - 4 * (d // 6)),
                rope_params(1024, 2 * (d // 6)),
                rope_params(1024, 2 * (d // 6))
            ],
            dim=1
        )

        if model_type == 'i2v':
            self.img_emb = MLPProj(1280, dim)
        
        if add_control_adapter:
            self.control_adapter = SimpleAdapter(in_dim_control_adapter, dim, kernel_size=patch_size[1:], stride=patch_size[1:], downscale_factor=downscale_factor_control_adapter)
        else:
            self.control_adapter = None

        if add_ref_conv:
            self.ref_conv = nn.Conv2d(in_dim_ref_conv, dim, kernel_size=patch_size[1:], stride=patch_size[1:])
        else:
            self.ref_conv = None

        self.teacache = None
        self.cfg_skip_ratio = None
        self.current_steps = 0
        self.num_inference_steps = None
        self.gradient_checkpointing = False
        self.sp_world_size = 1
        self.sp_world_rank = 0

    def _set_gradient_checkpointing(self, *args, **kwargs):
        if "value" in kwargs:
            self.gradient_checkpointing = kwargs["value"]
        elif "enable" in kwargs:
            self.gradient_checkpointing = kwargs["enable"]
        else:
            raise ValueError("Invalid set gradient checkpointing")

    def enable_teacache(
        self,
        coefficients,
        num_steps: int,
        rel_l1_thresh: float,
        num_skip_start_steps: int = 0,
        offload: bool = True,
    ):
        self.teacache = TeaCache(
            coefficients, num_steps, rel_l1_thresh=rel_l1_thresh, num_skip_start_steps=num_skip_start_steps, offload=offload
        )

    def share_teacache(
        self,
        transformer = None,
    ):
        self.teacache = transformer.teacache

    def disable_teacache(self):
        self.teacache = None

    def enable_cfg_skip(self, cfg_skip_ratio, num_steps):
        if cfg_skip_ratio != 0:
            self.cfg_skip_ratio = cfg_skip_ratio
            self.current_steps = 0
            self.num_inference_steps = num_steps
        else:
            self.cfg_skip_ratio = None
            self.current_steps = 0
            self.num_inference_steps = None

    def share_cfg_skip(
        self,
        transformer = None,
    ):
        self.cfg_skip_ratio = transformer.cfg_skip_ratio
        self.current_steps = transformer.current_steps
        self.num_inference_steps = transformer.num_inference_steps

    def disable_cfg_skip(self):
        self.cfg_skip_ratio = None
        self.current_steps = 0
        self.num_inference_steps = None

    def enable_riflex(
        self,
        k = 6,
        L_test = 66,
        L_test_scale = 4.886,
    ):
        device = self.freqs.device
        self.freqs = torch.cat(
            [
                get_1d_rotary_pos_embed_riflex(1024, self.d - 4 * (self.d // 6), use_real=False, k=k, L_test=L_test, L_test_scale=L_test_scale),
                rope_params(1024, 2 * (self.d // 6)),
                rope_params(1024, 2 * (self.d // 6))
            ],
            dim=1
        ).to(device)

    def disable_riflex(self):
        device = self.freqs.device
        self.freqs = torch.cat(
            [
                rope_params(1024, self.d - 4 * (self.d // 6)),
                rope_params(1024, 2 * (self.d // 6)),
                rope_params(1024, 2 * (self.d // 6))
            ],
            dim=1
        ).to(device)

    def enable_multi_gpus_inference(self,):
        self.sp_world_size = get_sequence_parallel_world_size()
        self.sp_world_rank = get_sequence_parallel_rank()
        self.all_gather = get_sp_group().all_gather

        # For normal model.
        for block in self.blocks:
            block.self_attn.forward = types.MethodType(
                usp_attn_forward, block.self_attn)

        # For vace model.
        if hasattr(self, 'vace_blocks'):
            for block in self.vace_blocks:
                block.self_attn.forward = types.MethodType(
                    usp_attn_forward, block.self_attn)

    @cfg_skip()
    def forward(
        self,
        x,
        t,
        context,
        seq_len,
        clip_fea=None,
        y=None,
        y_camera=None,
        full_ref=None,
        subject_ref=None,
        cond_flag=True,
        init_smpl_pose=None,
        layer_predict_smpl_idx=None
    ):
        r"""
        Forward pass through the diffusion model

        Args:
            x (List[Tensor]):
                List of input video tensors, each with shape [C_in, F, H, W]
            t (Tensor):
                Diffusion timesteps tensor of shape [B]
            context (List[Tensor]):
                List of text embeddings each with shape [L, C]
            seq_len (`int`):
                Maximum sequence length for positional encoding
            clip_fea (Tensor, *optional*):
                CLIP image features for image-to-video mode
            y (List[Tensor], *optional*):
                Conditional video inputs for image-to-video mode, same shape as x
            cond_flag (`bool`, *optional*, defaults to True):
                Flag to indicate whether to forward the condition input

        Returns:
            List[Tensor]:
                List of denoised video tensors with original input shapes [C_out, F, H / 8, W / 8]
        """
        rgb_latent, motion_latent = x

        # params
        device = self.rgb_patch_embedding.weight.device
        dtype = rgb_latent.dtype
        if self.freqs.device != device and torch.device(type="meta") != device:
            self.freqs = self.freqs.to(device)

        if y is not None:
            x = [torch.cat([u, v], dim=0) for u, v in zip(x, y)]

        # embeddings
        x_rgb = [self.rgb_patch_embedding(u.unsqueeze(0)) for u in rgb_latent]
        x_motion = [self.motion_patch_embedding(u.unsqueeze(0)) for u in motion_latent]

        # add control adapter
        if self.control_adapter is not None and y_camera is not None:
            y_camera = self.control_adapter(y_camera)
            x = [u + v for u, v in zip(x, y_camera)]

        grid_sizes = torch.stack(
            [torch.tensor(u.shape[2:], dtype=torch.long) for u in x_rgb])

        x_rgb = [u.flatten(2).transpose(1, 2) for u in x_rgb]
        x_motion = [u.flatten(2).transpose(1, 2) for u in x_motion]

        if self.ref_conv is not None and full_ref is not None:
            full_ref = self.ref_conv(full_ref).flatten(2).transpose(1, 2)
            grid_sizes = torch.stack([torch.tensor([u[0] + 1, u[1], u[2]]) for u in grid_sizes]).to(grid_sizes.device)
            seq_len += full_ref.size(1)
            x = [torch.concat([_full_ref.unsqueeze(0), u], dim=1) for _full_ref, u in zip(full_ref, x)]
            if t.dim() != 1 and t.size(1) < seq_len:
                pad_size = seq_len - t.size(1)
                last_elements = t[:, -1].unsqueeze(1)
                padding = last_elements.repeat(1, pad_size)
                t = torch.cat([padding, t], dim=1)

        if subject_ref is not None:
            subject_ref_frames = subject_ref.size(2)
            subject_ref = self.patch_embedding(subject_ref).flatten(2).transpose(1, 2)
            grid_sizes = torch.stack([torch.tensor([u[0] + subject_ref_frames, u[1], u[2]]) for u in grid_sizes]).to(grid_sizes.device)
            seq_len += subject_ref.size(1)
            x = [torch.concat([u, _subject_ref.unsqueeze(0)], dim=1) for _subject_ref, u in zip(subject_ref, x)]
            if t.dim() != 1 and t.size(1) < seq_len:
                pad_size = seq_len - t.size(1)
                last_elements = t[:, -1].unsqueeze(1)
                padding = last_elements.repeat(1, pad_size)
                t = torch.cat([t, padding], dim=1)
        
        seq_lens = torch.tensor([u.size(1) for u in x_rgb], dtype=torch.long)
        if self.sp_world_size > 1:
            seq_len = int(math.ceil(seq_len / self.sp_world_size)) * self.sp_world_size
        assert seq_lens.max() <= seq_len

        x_rgb = torch.cat([
            torch.cat([u, u.new_zeros(1, seq_len - u.size(1), u.size(2))],
                      dim=1) for u in x_rgb
        ])
        x_motion = torch.cat([
            torch.cat([u, u.new_zeros(1, seq_len - u.size(1), u.size(2))],
                      dim=1) for u in x_motion
        ])
        layer_smpl_pred = []

        # time embeddings
        with amp.autocast(dtype=torch.float32):
            if t.dim() != 1:
                if t.size(1) < seq_len:
                    pad_size = seq_len - t.size(1)
                    last_elements = t[:, -1].unsqueeze(1)
                    padding = last_elements.repeat(1, pad_size)
                    t = torch.cat([t, padding], dim=1)
                bt = t.size(0)
                ft = t.flatten()
                e = self.time_embedding(
                    sinusoidal_embedding_1d(self.freq_dim,
                                            ft).unflatten(0, (bt, seq_len)).float())
                e0 = self.time_projection(e).unflatten(2, (6, self.dim))
            else:
                e = self.time_embedding(
                    sinusoidal_embedding_1d(self.freq_dim, t).float())
                e0 = self.time_projection(e).unflatten(1, (6, self.dim))

        # context
        context_lens = None
        context = self.text_embedding(
            torch.stack([
                torch.cat(
                    [u, u.new_zeros(self.text_len - u.size(0), u.size(1))])
                for u in context
            ]))

        if clip_fea is not None:
            context_clip = self.img_emb(clip_fea)
            context = torch.concat([context_clip, context], dim=1)

        # Context Parallel
        if self.sp_world_size > 1:
            x_rgb = torch.chunk(x_rgb, self.sp_world_size, dim=1)[self.sp_world_rank]
            x_motion = torch.chunk(x_motion, self.sp_world_size, dim=1)[self.sp_world_rank]
            if t.dim() != 1:
                e0 = torch.chunk(e0, self.sp_world_size, dim=1)[self.sp_world_rank]
                e = torch.chunk(e, self.sp_world_size, dim=1)[self.sp_world_rank]
        
        # TeaCache
        if self.teacache is not None:
            if cond_flag:
                if t.dim() != 1:
                    modulated_inp = e0[:, -1, :]
                else:
                    modulated_inp = e0
                skip_flag = self.teacache.cnt < self.teacache.num_skip_start_steps
                if skip_flag:
                    self.should_calc = True
                    self.teacache.accumulated_rel_l1_distance = 0
                else:
                    if cond_flag:
                        rel_l1_distance = self.teacache.compute_rel_l1_distance(self.teacache.previous_modulated_input, modulated_inp)
                        self.teacache.accumulated_rel_l1_distance += self.teacache.rescale_func(rel_l1_distance)
                    if self.teacache.accumulated_rel_l1_distance < self.teacache.rel_l1_thresh:
                        self.should_calc = False
                    else:
                        self.should_calc = True
                        self.teacache.accumulated_rel_l1_distance = 0
                self.teacache.previous_modulated_input = modulated_inp
                self.teacache.should_calc = self.should_calc
            else:
                self.should_calc = self.teacache.should_calc
        
        # TeaCache
        if self.teacache is not None:
            if not self.should_calc:
                previous_residual = self.teacache.previous_residual_cond if cond_flag else self.teacache.previous_residual_uncond
                x = x + previous_residual.to(x.device)[-x.size()[0]:,]
            else:
                ori_x = x.clone().cpu() if self.teacache.offload else x.clone()

                for block in self.blocks:
                    if torch.is_grad_enabled() and self.gradient_checkpointing:

                        def create_custom_forward(module):
                            def custom_forward(*inputs):
                                return module(*inputs)

                            return custom_forward
                        ckpt_kwargs: Dict[str, Any] = {"use_reentrant": False} if is_torch_version(">=", "1.11.0") else {}
                        x = torch.utils.checkpoint.checkpoint(
                            create_custom_forward(block),
                            x,
                            e0,
                            seq_lens,
                            grid_sizes,
                            self.freqs,
                            context,
                            context_lens,
                            dtype,
                            t,
                            **ckpt_kwargs,
                        )
                    else:
                        # arguments
                        kwargs = dict(
                            e=e0,
                            seq_lens=seq_lens,
                            grid_sizes=grid_sizes,
                            freqs=self.freqs,
                            context=context,
                            context_lens=context_lens,
                            dtype=dtype,
                            t=t  
                        )
                        x = block(x, **kwargs)
                    
                if cond_flag:
                    self.teacache.previous_residual_cond = x.cpu() - ori_x if self.teacache.offload else x - ori_x
                else:
                    self.teacache.previous_residual_uncond = x.cpu() - ori_x if self.teacache.offload else x - ori_x
        else:
            for i in range(self.num_layers):
                rgb_block = self.rgb_blocks[i]
                motion_block = self.motion_blocks[i//self.interleave] if i % self.interleave == 0 else None
                smpl_fusion_layer = self.smpl_fusion_layers[i//self.interleave] if i % self.interleave == 0 and self.predict_smpl else None
                if torch.is_grad_enabled() and self.gradient_checkpointing:
                    def create_custom_forward(module):
                        def custom_forward(*inputs):
                            return module(*inputs)

                        return custom_forward
                    
                    ckpt_kwargs: Dict[str, Any] = {"use_reentrant": False} if is_torch_version(">=", "1.11.0") else {}
                    
                    if motion_block is not None:
                        if self.interaction == "dual":
                            x_motion = x_motion + torch.utils.checkpoint.checkpoint(create_custom_forward(self.zero_linear_blocks[i]), x_rgb, **ckpt_kwargs)
                        elif self.interaction == "single_v2m":
                            x_motion = x_motion + torch.utils.checkpoint.checkpoint(create_custom_forward(self.zero_linear_blocks[i//self.interleave]), x_rgb, **ckpt_kwargs)
                        x_motion = torch.utils.checkpoint.checkpoint(
                            create_custom_forward(motion_block),
                            x_motion,
                            e0,
                            seq_lens,
                            grid_sizes,
                            self.freqs,
                            context,
                            context_lens,
                            dtype,
                            t,
                            **ckpt_kwargs,
                        )
                        x_rgb = torch.utils.checkpoint.checkpoint(
                            create_custom_forward(rgb_block),
                            x_rgb,
                            e0,
                            seq_lens,
                            grid_sizes,
                            self.freqs,
                            context,
                            context_lens,
                            dtype,
                            t,
                            **ckpt_kwargs,
                        )
                        if self.predict_smpl and i in layer_predict_smpl_idx:
                            fused_feat = x_motion + torch.utils.checkpoint.checkpoint(create_custom_forward(smpl_fusion_layer), x_rgb, **ckpt_kwargs)
                            x_pose = self.smpl_pe + torch.utils.checkpoint.checkpoint(create_custom_forward(self.smpl_proj_in), init_smpl_pose, **ckpt_kwargs)
                            for smpl_i in range(self.smpl_predictor_layers):
                                x_pose = torch.utils.checkpoint.checkpoint(
                                    create_custom_forward(self.smpl_decoders[smpl_i]),
                                    x_pose,
                                    fused_feat,
                                    **ckpt_kwargs
                                )
                            x_pose = init_smpl_pose + torch.utils.checkpoint.checkpoint(create_custom_forward(self.smpl_proj_out), x_pose, **ckpt_kwargs)
                            layer_smpl_pred.append(x_pose)
                        if self.interaction == "dual":
                            x_rgb = x_rgb + torch.utils.checkpoint.checkpoint(create_custom_forward(self.zero_linear_blocks[i+1]), x_motion, **ckpt_kwargs)
                        elif self.interaction == "single_m2v":
                            x_rgb = x_rgb + torch.utils.checkpoint.checkpoint(create_custom_forward(self.zero_linear_blocks[i//self.interleave]), x_motion, **ckpt_kwargs)
                    else:
                        x_rgb = torch.utils.checkpoint.checkpoint(
                            create_custom_forward(rgb_block),
                            x_rgb,
                            e0,
                            seq_lens,
                            grid_sizes,
                            self.freqs,
                            context,
                            context_lens,
                            dtype,
                            t,
                            **ckpt_kwargs,
                        )
                else:
                    # arguments
                    kwargs = dict(
                        e=e0,
                        seq_lens=seq_lens,
                        grid_sizes=grid_sizes,
                        freqs=self.freqs,
                        context=context,
                        context_lens=context_lens,
                        dtype=dtype,
                        t=t  
                    )
                    # x = block(x, **kwargs)
                    if motion_block is not None:
                        if self.interaction == "dual":
                            x_motion = x_motion + self.zero_linear_blocks[i](x_rgb)
                        elif self.interaction == "single_v2m":
                            x_motion = x_motion + self.zero_linear_blocks[i//self.interleave](x_rgb)
                        x_motion = motion_block(x_motion, **kwargs)
                        x_rgb = rgb_block(x_rgb, **kwargs)
                        if self.predict_smpl and i == self.num_layers-1:
                            fused_feat = x_motion + smpl_fusion_layer(x_rgb)
                            x_pose = self.smpl_pe + self.smpl_proj_in(init_smpl_pose)
                            for smpl_i in range(self.smpl_predictor_layers):
                                x_pose = self.smpl_decoders[smpl_i](x_pose, fused_feat)
                            x_pose = init_smpl_pose + self.smpl_proj_out(x_pose)
                            layer_smpl_pred.append(x_pose)
                        if self.interaction == "dual":
                            x_rgb = x_rgb + self.zero_linear_blocks[i+1](x_motion)
                        elif self.interaction == "single_m2v":
                            x_rgb = x_rgb + self.zero_linear_blocks[i//self.interleave](x_motion)
                    else:
                        x_rgb = rgb_block(x_rgb, **kwargs)

        # head
        if torch.is_grad_enabled() and self.gradient_checkpointing:
            def create_custom_forward(module):
                def custom_forward(*inputs):
                    return module(*inputs)

                return custom_forward
            ckpt_kwargs: Dict[str, Any] = {"use_reentrant": False} if is_torch_version(">=", "1.11.0") else {}
            x_rgb = torch.utils.checkpoint.checkpoint(create_custom_forward(self.rgb_head), x_rgb, e, **ckpt_kwargs)
            x_motion = torch.utils.checkpoint.checkpoint(create_custom_forward(self.motion_head), x_motion, e, **ckpt_kwargs)
        else:
            x_rgb = self.rgb_head(x_rgb, e)
            x_motion = self.motion_head(x_motion, e)

        if self.sp_world_size > 1:
            x_rgb = self.all_gather(x_rgb, dim=1)
            x_motion = self.all_gather(x_motion, dim=1)

        if self.ref_conv is not None and full_ref is not None:
            full_ref_length = full_ref.size(1)
            x = x[:, full_ref_length:]
            grid_sizes = torch.stack([torch.tensor([u[0] - 1, u[1], u[2]]) for u in grid_sizes]).to(grid_sizes.device)

        if subject_ref is not None:
            subject_ref_length = subject_ref.size(1)
            x = x[:, :-subject_ref_length]
            grid_sizes = torch.stack([torch.tensor([u[0] - subject_ref_frames, u[1], u[2]]) for u in grid_sizes]).to(grid_sizes.device)

        # unpatchify
        x_rgb = self.unpatchify(x_rgb, grid_sizes)
        x_motion = self.unpatchify(x_motion, grid_sizes)
        x_rgb = torch.stack(x_rgb)
        x_motion = torch.stack(x_motion)

        out = torch.cat([x_rgb, x_motion], dim=1)
        out_smpl = torch.stack(layer_smpl_pred).transpose(0, 1) if self.predict_smpl else None

        if self.teacache is not None and cond_flag:
            self.teacache.cnt += 1
            if self.teacache.cnt == self.teacache.num_steps:
                self.teacache.reset()
        
        return out, out_smpl


    def unpatchify(self, x, grid_sizes):
        r"""
        Reconstruct video tensors from patch embeddings.

        Args:
            x (List[Tensor]):
                List of patchified features, each with shape [L, C_out * prod(patch_size)]
            grid_sizes (Tensor):
                Original spatial-temporal grid dimensions before patching,
                    shape [B, 3] (3 dimensions correspond to F_patches, H_patches, W_patches)

        Returns:
            List[Tensor]:
                Reconstructed video tensors with shape [C_out, F, H / 8, W / 8]
        """

        c = self.out_dim
        out = []
        for u, v in zip(x, grid_sizes.tolist()):
            u = u[:math.prod(v)].view(*v, *self.patch_size, c)
            u = torch.einsum('fhwpqrc->cfphqwr', u)
            u = u.reshape(c, *[i * j for i, j in zip(v, self.patch_size)])
            out.append(u)
        return out

    
    def init_weights(self):
        r"""
        Initialize model parameters using Xavier initialization.
        """

        # basic init
        for m in self.modules():
            if isinstance(m, nn.Linear):
                nn.init.xavier_uniform_(m.weight)
                if m.bias is not None:
                    nn.init.zeros_(m.bias)

        # init embeddings
        nn.init.xavier_uniform_(self.rgb_patch_embedding.weight.flatten(1))
        nn.init.xavier_uniform_(self.motion_patch_embedding.weight.flatten(1))
        for m in self.text_embedding.modules():
            if isinstance(m, nn.Linear):
                nn.init.normal_(m.weight, std=.02)
        for m in self.time_embedding.modules():
            if isinstance(m, nn.Linear):
                nn.init.normal_(m.weight, std=.02)

        # init output layer
        nn.init.zeros_(self.rgb_head.head.weight)
        nn.init.zeros_(self.motion_head.head.weight)

    
    @classmethod
    def from_pretrained(
        cls, pretrained_model_path, subfolder=None, transformer_additional_kwargs={},
        low_cpu_mem_usage=False, torch_dtype=torch.bfloat16, interaction="dual", interleave=2, predict_smpl=False
    ):
        if subfolder is not None:
            pretrained_model_path = os.path.join(pretrained_model_path, subfolder)
        print(f"loaded 3D transformer's pretrained weights from {pretrained_model_path} ...")

        config_file = os.path.join(pretrained_model_path, 'config.json')        
        if not os.path.isfile(config_file):
            raise RuntimeError(f"{config_file} does not exist")
        with open(config_file, "r") as f:
            config = json.load(f)

        from diffusers.utils import WEIGHTS_NAME
        model_file = os.path.join(pretrained_model_path, WEIGHTS_NAME)
        model_file_safetensors = model_file.replace(".bin", ".safetensors")

        if "dict_mapping" in transformer_additional_kwargs.keys():
            for key in transformer_additional_kwargs["dict_mapping"]:
                transformer_additional_kwargs[transformer_additional_kwargs["dict_mapping"][key]] = config[key]

        if low_cpu_mem_usage:
            try:
                import re

                from diffusers import __version__ as diffusers_version
                if diffusers_version >= "0.33.0":
                    from diffusers.models.model_loading_utils import \
                        load_model_dict_into_meta
                else:
                    from diffusers.models.modeling_utils import \
                        load_model_dict_into_meta
                from diffusers.utils import is_accelerate_available
                if is_accelerate_available():
                    import accelerate
                
                # Instantiate model with empty weights
                with accelerate.init_empty_weights():
                    model = cls.from_config(
                        config,
                        **transformer_additional_kwargs,
                        interaction=interaction,
                        interleave=interleave,
                        predict_smpl=predict_smpl
                    )

                param_device = "cpu"
                if os.path.exists(model_file):
                    state_dict = torch.load(model_file, map_location="cpu")
                elif os.path.exists(model_file_safetensors):
                    state_dict = load_file(model_file_safetensors)
                else:
                    model_files_safetensors = glob.glob(os.path.join(pretrained_model_path, "*.safetensors"))
                    state_dict = {}
                    for _model_file_safetensors in model_files_safetensors:
                        _state_dict = load_file(_model_file_safetensors)
                        for key in _state_dict:
                            state_dict[key] = _state_dict[key]

                if diffusers_version >= "0.33.0":
                    # Diffusers has refactored `load_model_dict_into_meta` since version 0.33.0 in this commit:
                    # https://github.com/huggingface/diffusers/commit/f5929e03060d56063ff34b25a8308833bec7c785.
                    load_model_dict_into_meta(
                        model,
                        state_dict,
                        dtype=torch_dtype,
                        model_name_or_path=pretrained_model_path,
                    )
                else:
                    model._convert_deprecated_attention_blocks(state_dict)
                    # move the params from meta device to cpu
                    missing_keys = set(model.state_dict().keys()) - set(state_dict.keys())
                    if len(missing_keys) > 0:
                        raise ValueError(
                            f"Cannot load {cls} from {pretrained_model_path} because the following keys are"
                            f" missing: \n {', '.join(missing_keys)}. \n Please make sure to pass"
                            " `low_cpu_mem_usage=False` and `device_map=None` if you want to randomly initialize"
                            " those weights or else make sure your checkpoint file is correct."
                        )

                    unexpected_keys = load_model_dict_into_meta(
                        model,
                        state_dict,
                        device=param_device,
                        dtype=torch_dtype,
                        model_name_or_path=pretrained_model_path,
                    )

                    if cls._keys_to_ignore_on_load_unexpected is not None:
                        for pat in cls._keys_to_ignore_on_load_unexpected:
                            unexpected_keys = [k for k in unexpected_keys if re.search(pat, k) is None]

                    if len(unexpected_keys) > 0:
                        print(
                            f"Some weights of the model checkpoint were not used when initializing {cls.__name__}: \n {[', '.join(unexpected_keys)]}"
                        )
                
                return model
            except Exception as e:
                print(
                    f"The low_cpu_mem_usage mode is not work because {e}. Use low_cpu_mem_usage=False instead."
                )
        
        model = cls.from_config(
            config,
            **transformer_additional_kwargs,
            interaction=interaction,
            interleave=interleave,
            predict_smpl=predict_smpl
        )
        if os.path.exists(model_file):
            state_dict = torch.load(model_file, map_location="cpu")
        elif os.path.exists(model_file_safetensors):
            from safetensors.torch import load_file, safe_open
            state_dict = load_file(model_file_safetensors)
        else:
            from safetensors.torch import load_file, safe_open
            model_files_safetensors = glob.glob(os.path.join(pretrained_model_path, "*.safetensors"))
            state_dict = {}
            for _model_file_safetensors in model_files_safetensors:
                _state_dict = load_file(_model_file_safetensors)
                for key in _state_dict:
                    state_dict[key] = _state_dict[key]

        tmp_state_dict = {} 
        for key in state_dict:
            if key.split('.')[0] == "blocks":
                new_key = ".".join(["rgb_blocks"] + key.split('.')[1:])
            elif key.split('.')[0] == "patch_embedding":
                new_key = ".".join(["rgb_patch_embedding"] + key.split('.')[1:])
            elif key.split('.')[0] == "head":
                new_key = ".".join(["rgb_head"] + key.split('.')[1:])
            else:
                new_key = key

            if new_key in model.state_dict().keys() and model.state_dict()[new_key].size() == state_dict[key].size():
                tmp_state_dict[new_key] = state_dict[key]
                if new_key.split('.')[0] == "rgb_blocks":
                    block_id = int(new_key.split('.')[1])
                    if block_id % interleave == 0:
                        motion_new_key = ".".join(["motion_blocks", str(block_id//interleave)] + new_key.split('.')[2:])
                        tmp_state_dict[motion_new_key] = state_dict[key]
                elif new_key.split('.')[0] == "rgb_patch_embedding":
                    motion_new_key = ".".join(["motion_patch_embedding"] + new_key.split('.')[1:])
                    tmp_state_dict[motion_new_key] = state_dict[key]
                elif new_key.split('.')[0] == "rgb_head":
                    motion_new_key = ".".join(["motion_head"] + new_key.split('.')[1:])
                    tmp_state_dict[motion_new_key] = state_dict[key]
            else:
                print(f"{key} -> {new_key}: size don't match, skip")
        
        # add smpl decoders params
        if predict_smpl:
            for i in range(len(model.smpl_fusion_layers)):
                nn.init.zeros_(model.smpl_fusion_layers[i].weight)
                nn.init.zeros_(model.smpl_fusion_layers[i].bias)
                tmp_state_dict[f"smpl_fusion_layers.{i}.weight"] = model.smpl_fusion_layers[i].weight
                tmp_state_dict[f"smpl_fusion_layers.{i}.bias"] = model.smpl_fusion_layers[i].bias

            nn.init.zeros_(model.smpl_proj_in.weight)
            nn.init.zeros_(model.smpl_proj_in.bias)
            tmp_state_dict[f"smpl_proj_in.weight"] = model.smpl_proj_in.weight
            tmp_state_dict[f"smpl_proj_in.bias"] = model.smpl_proj_in.bias

            tmp_state_dict[f"smpl_pe"] = model.smpl_pe

            for i in range(len(model.smpl_decoders)):
                for sd_m in model.smpl_decoders[i].modules():
                    if isinstance(sd_m, nn.Linear):
                        nn.init.zeros_(sd_m.weight)
                        nn.init.zeros_(sd_m.bias)
                    
                tmp_state_dict[f"smpl_decoders.{i}.sa.q.weight"]            = model.smpl_decoders[i].sa.q.weight
                tmp_state_dict[f"smpl_decoders.{i}.sa.q.bias"]              = model.smpl_decoders[i].sa.q.bias
                tmp_state_dict[f"smpl_decoders.{i}.sa.k.weight"]            = model.smpl_decoders[i].sa.k.weight
                tmp_state_dict[f"smpl_decoders.{i}.sa.k.bias"]              = model.smpl_decoders[i].sa.k.bias
                tmp_state_dict[f"smpl_decoders.{i}.sa.v.weight"]            = model.smpl_decoders[i].sa.v.weight
                tmp_state_dict[f"smpl_decoders.{i}.sa.v.bias"]              = model.smpl_decoders[i].sa.v.bias
                tmp_state_dict[f"smpl_decoders.{i}.sa.o.weight"]            = model.smpl_decoders[i].sa.o.weight
                tmp_state_dict[f"smpl_decoders.{i}.sa.o.bias"]              = model.smpl_decoders[i].sa.o.bias
                tmp_state_dict[f"smpl_decoders.{i}.sa.norm_q.weight"]       = model.smpl_decoders[i].sa.norm_q.weight
                tmp_state_dict[f"smpl_decoders.{i}.sa.norm_k.weight"]       = model.smpl_decoders[i].sa.norm_k.weight

                tmp_state_dict[f"smpl_decoders.{i}.ca.q.weight"]            = model.smpl_decoders[i].ca.q.weight
                tmp_state_dict[f"smpl_decoders.{i}.ca.q.bias"]              = model.smpl_decoders[i].ca.q.bias
                tmp_state_dict[f"smpl_decoders.{i}.ca.k.weight"]            = model.smpl_decoders[i].ca.k.weight
                tmp_state_dict[f"smpl_decoders.{i}.ca.k.bias"]              = model.smpl_decoders[i].ca.k.bias
                tmp_state_dict[f"smpl_decoders.{i}.ca.v.weight"]            = model.smpl_decoders[i].ca.v.weight
                tmp_state_dict[f"smpl_decoders.{i}.ca.v.bias"]              = model.smpl_decoders[i].ca.v.bias
                tmp_state_dict[f"smpl_decoders.{i}.ca.o.weight"]            = model.smpl_decoders[i].ca.o.weight
                tmp_state_dict[f"smpl_decoders.{i}.ca.o.bias"]              = model.smpl_decoders[i].ca.o.bias
                tmp_state_dict[f"smpl_decoders.{i}.ca.norm_q.weight"]       = model.smpl_decoders[i].ca.norm_q.weight
                tmp_state_dict[f"smpl_decoders.{i}.ca.norm_k.weight"]       = model.smpl_decoders[i].ca.norm_k.weight

                tmp_state_dict[f"smpl_decoders.{i}.ffn.0.weight"]           = model.smpl_decoders[i].ffn[0].weight
                tmp_state_dict[f"smpl_decoders.{i}.ffn.0.bias"]             = model.smpl_decoders[i].ffn[0].bias
                tmp_state_dict[f"smpl_decoders.{i}.ffn.2.weight"]           = model.smpl_decoders[i].ffn[2].weight
                tmp_state_dict[f"smpl_decoders.{i}.ffn.2.bias"]             = model.smpl_decoders[i].ffn[2].bias

            nn.init.zeros_(model.smpl_proj_out.weight)
            nn.init.zeros_(model.smpl_proj_out.bias)
            tmp_state_dict[f"smpl_proj_out.weight"] = model.smpl_proj_out.weight
            tmp_state_dict[f"smpl_proj_out.bias"] = model.smpl_proj_out.bias
        
        # add zero linear blocks params
        if interaction != "none":
            for i in range(len(model.zero_linear_blocks)):
                nn.init.zeros_(model.zero_linear_blocks[i].weight)
                nn.init.zeros_(model.zero_linear_blocks[i].bias)
                tmp_state_dict[f"zero_linear_blocks.{i}.weight"] = model.zero_linear_blocks[i].weight
                tmp_state_dict[f"zero_linear_blocks.{i}.bias"] = model.zero_linear_blocks[i].bias
                
        state_dict = tmp_state_dict

        m, u = model.load_state_dict(state_dict, strict=False)
        print(f"### missing keys: {len(m)}; \n### unexpected keys: {len(u)};")
        if len(m) > 0:
            print(f"### missing keys: {m}")
        if len(u) > 0:
            print(f"### unexpected keys: {u}")
        
        params = [p.numel() if "." in n else 0 for n, p in model.named_parameters()]
        print(f"### All Parameters: {sum(params) / 1e6} M")

        params = [p.numel() if "attn1." in n else 0 for n, p in model.named_parameters()]
        print(f"### attn1 Parameters: {sum(params) / 1e6} M")
        
        model = model.to(torch_dtype)
        return model