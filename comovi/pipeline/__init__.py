# from .pipeline_wan import WanPipeline
from .pipeline_wan2_2 import Wan2_2Pipeline
from .pipeline_wan2_2_ti2v import Wan2_2TI2VPipeline
from .pipeline_comovi import ComoviPipeline

Wan2_2FunPipeline = Wan2_2Pipeline

import importlib.util

if importlib.util.find_spec("paifuser") is not None:
    # --------------------------------------------------------------- #
    #   Sparse Attention
    # --------------------------------------------------------------- #
    from paifuser.ops import sparse_reset

    # Wan2.2
    Wan2_2FunPipeline.__call__ = sparse_reset(Wan2_2FunPipeline.__call__)
    Wan2_2Pipeline.__call__ = sparse_reset(Wan2_2Pipeline.__call__)
    Wan2_2TI2VPipeline.__call__ = sparse_reset(Wan2_2TI2VPipeline.__call__)