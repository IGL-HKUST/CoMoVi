import os
from typing import Dict
from yacs.config import CfgNode as CN
curr_dir = os.path.abspath(os.path.dirname(__file__))
base_dir = os.path.join(curr_dir, '../../')
DATASET_FOLDERS = {
    
    '3dpw-test-cam-smpl': os.path.join(base_dir, 'data/test-images/3DPW'),
    'coco-val-smpl': os.path.join(base_dir, 'data/test-images/COCO2017/images/'),
    'emdb-smpl': os.path.join(base_dir, 'data/test-images/EMDB'),
    'spec-test-smpl': os.path.join(base_dir, 'data/test-images/spec-syn'),
    'rich-smplx': os.path.join(base_dir, 'data/test-images/RICH'),
    'coco-val-smpl': os.path.join(base_dir, 'data/test-images/COCO2017/images'),

    'insta-1': os.path.join(base_dir, 'data/training-images/insta/images/'),
    'insta-2': os.path.join(base_dir, 'data/training-images/insta/images'),
    'aic': os.path.join(base_dir, 'data/training-images/aic/images'),
    'mpii-train':  os.path.join(base_dir, 'data/training-images/MPII-pose'),
    'coco-train':  os.path.join(base_dir, 'data/training-images/COCO'),

    'agora-body-bbox44': os.path.join(base_dir, 'data/training-images/images'),
    'zoom-suburbd-bbox44': os.path.join(base_dir, 'data/training-images/20221010_3-10_500_batch01hand_zoom_suburb_d_6fps/png'),
    'closeup-suburba-bbox44': os.path.join(base_dir, 'data/training-images/20221011_1_250_batch01hand_closeup_suburb_a_6fps/png'),
    'closeup-suburbb-bbox44': os.path.join(base_dir, 'data/training-images/20221011_1_250_batch01hand_closeup_suburb_b_6fps/png'),
    'closeup-suburbc-bbox44': os.path.join(base_dir, 'data/training-images/20221011_1_250_batch01hand_closeup_suburb_c_6fps/png'),
    'closeup-suburbd-bbox44': os.path.join(base_dir, 'data/training-images/20221011_1_250_batch01hand_closeup_suburb_d_6fps/png'),
    'closeup-gym-bbox44': os.path.join(base_dir, 'data/training-images/20221012_1_500_batch01hand_closeup_highSchoolGym_6fps/png'),
    'zoom-gym-bbox44': os.path.join(base_dir, 'data/training-images/20221012_3-10_500_batch01hand_zoom_highSchoolGym_6fps/png'),
    'static-gym-bbox44': os.path.join(base_dir, 'data/training-images/20221013_3-10_500_batch01hand_static_highSchoolGym_6fps/png'),
    'static-office-bbox44': os.path.join(base_dir, 'data/training-images/20221013_3_250_batch01hand_static_bigOffice_6fps/png'),
    'orbit-office-bbox44': os.path.join(base_dir, 'data/training-images/20221013_3_250_batch01hand_orbit_bigOffice_6fps/png'),
    'orbit-archviz-15-bbox44': os.path.join(base_dir, 'data/training-images/20221014_3_250_batch01hand_orbit_archVizUI3_time15_6fps/png'),
    'orbit-archviz-19-bbox44': os.path.join(base_dir, 'data/training-images/20221015_3_250_batch01hand_orbit_archVizUI3_time19_6fps/png'),
    'orbit-archviz-12-bbox44': os.path.join(base_dir, 'data/training-images/20221015_3_250_batch01hand_orbit_archVizUI3_time12_6fps/png'),
    'orbit-archviz-10-bbox44': os.path.join(base_dir, 'data/training-images/20221015_3_250_batch01hand_orbit_archVizUI3_time10_6fps/png'),
    'static-hdri-bbox44': os.path.join(base_dir, 'data/training-images/20221010_3_1000_batch01hand_6fps/png'),
    'static-hdri-zoomed-bbox44': os.path.join(base_dir, 'data/training-images/20221017_3_1000_batch01hand_6fps/png'),
    'staticzoomed-suburba-frameocc-bbox44': os.path.join(base_dir, 'data/training-images/20221017_1_250_batch01hand_closeup_suburb_a_6fps/png'),
    'zoom-suburbb-frameocc-bbox44': os.path.join(base_dir, 'data/training-images/20221018_1_250_batch01hand_zoom_suburb_b_6fps/png'),
    'static-hdri-frameocc-bbox44': os.path.join(base_dir, 'data/training-images/20221018_3-8_250_batch01hand_6fps/png'),
    'orbit-archviz-objocc-bbox44': os.path.join(base_dir, 'data/training-images/20221018_3_250_batch01hand_orbit_archVizUI3_time15_6fps/png'),
    'pitchup-stadium-bbox44': os.path.join(base_dir, 'data/training-images/20221018_3-8_250_batch01hand_pitchUp52_stadium_6fps/png'),
    'pitchdown-stadium-bbox44': os.path.join(base_dir, 'data/training-images/20221018_3-8_250_batch01hand_pitchDown52_stadium_6fps/png'),
    'static-hdri-bmi-bbox44': os.path.join(base_dir, 'data/training-images/20221019_3_250_highbmihand_6fps/png'),
    'closeup-suburbb-bmi-bbox44': os.path.join(base_dir, 'data/training-images/20221019_1_250_highbmihand_closeup_suburb_b_6fps/png'),
    'closeup-suburbc-bmi-bbox44': os.path.join(base_dir, 'data/training-images/20221019_1_250_highbmihand_closeup_suburb_c_6fps/png'),
    'static-stadium-bmi-bbox44': os.path.join(base_dir, 'data/training-images/20221019_3-8_250_highbmihand_static_stadium_6fps/png'),
    'orbit-stadium-bmi-bbox44': os.path.join(base_dir, 'data/training-images/20221019_3-8_250_highbmihand_orbit_stadium_6fps/png'),
    'static-suburbd-bmi-bbox44': os.path.join(base_dir, 'data/training-images/20221019_3-8_1000_highbmihand_static_suburb_d_6fps/png'),
    'zoom-gym-bmi-bbox44': os.path.join(base_dir, 'data/training-images/20221020-3-8_250_highbmihand_zoom_highSchoolGym_a_6fps/png'),
    'static-office-hair-bbox44': os.path.join(base_dir, 'data/training-images/20221022_3_250_batch01handhair_static_bigOffice_30fps/png'),
    'zoom-suburbd-hair-bbox44': os.path.join(base_dir, 'data/training-images/20221024_10_100_batch01handhair_zoom_suburb_d_30fps/png'),
    'static-gym-hair-bbox44': os.path.join(base_dir, 'data/training-images/20221024_3-10_100_batch01handhair_static_highSchoolGym_30fps/png'),

}

DATASET_FILES = [
    {
        '3dpw-test-cam-smpl': os.path.join(base_dir, 'data/test-labels/3dpw_test.npz'),
        'emdb-smpl': os.path.join(base_dir, 'data/test-labels/emdb_test.npz'),
        'rich-smplx': os.path.join(base_dir, 'data/test-labels/rich_test.npz'),
        'spec-test-smpl': os.path.join(base_dir, 'data/test-labels/spec_test.npz'),
        'coco-val-smpl': os.path.join(base_dir, 'data/test-labels/coco_val.npz'),
    },
    {
        'aic': os.path.join(base_dir, 'data//training-labels/aic-release.npz'),
        'insta-1': os.path.join(base_dir, 'data//training-labels/insta1-release.npz'),
        'insta-2': os.path.join(base_dir, 'data//training-labels/insta2-release.npz'),
        'coco-train': os.path.join(base_dir, 'data/training-labels/coco-release.npz'),
        'mpii-train': os.path.join(base_dir, 'data/training-labels/mpii-release.npz'),

        'agora-body-bbox44': os.path.join(base_dir, 'data/training-labels/bedlam-labels/agora.npz'),
        'zoom-suburbd-bbox44': os.path.join(base_dir, 'data/training-labels/bedlam-labels/20221010_3-10_500_batch01hand_zoom_suburb_d_6fps.npz'),
        'closeup-suburba-bbox44': os.path.join(base_dir, 'data/training-labels/bedlam-labels/20221011_1_250_batch01hand_closeup_suburb_a_6fps.npz'),
        'closeup-suburbb-bbox44': os.path.join(base_dir, 'data/training-labels/bedlam-labels/20221011_1_250_batch01hand_closeup_suburb_b_6fps.npz'),
        'closeup-suburbc-bbox44': os.path.join(base_dir, 'data/training-labels/bedlam-labels/20221011_1_250_batch01hand_closeup_suburb_c_6fps.npz'),
        'closeup-suburbd-bbox44': os.path.join(base_dir, 'data/training-labels/bedlam-labels/20221011_1_250_batch01hand_closeup_suburb_d_6fps.npz'),
        'closeup-gym-bbox44': os.path.join(base_dir, 'data/training-labels/bedlam-labels/20221012_1_500_batch01hand_closeup_highSchoolGym_6fps.npz'),
        'zoom-gym-bbox44': os.path.join(base_dir, 'data/training-labels/bedlam-labels/20221012_3-10_500_batch01hand_zoom_highSchoolGym_6fps.npz'),
        'static-gym-bbox44': os.path.join(base_dir, 'data/training-labels/bedlam-labels/20221013_3-10_500_batch01hand_static_highSchoolGym_6fps.npz'),
        'static-office-bbox44': os.path.join(base_dir, 'data/training-labels/bedlam-labels/20221013_3_250_batch01hand_static_bigOffice_6fps.npz'),
        'orbit-office-bbox44': os.path.join(base_dir, 'data/training-labels/bedlam-labels/20221013_3_250_batch01hand_orbit_bigOffice_6fps.npz'),
        'orbit-archviz-15-bbox44': os.path.join(base_dir, 'data/training-labels/bedlam-labels/20221014_3_250_batch01hand_orbit_archVizUI3_time15_6fps.npz'),
        'orbit-archviz-19-bbox44': os.path.join(base_dir, 'data/training-labels/bedlam-labels/20221015_3_250_batch01hand_orbit_archVizUI3_time19_6fps.npz'),
        'orbit-archviz-12-bbox44': os.path.join(base_dir, 'data/training-labels/bedlam-labels/20221015_3_250_batch01hand_orbit_archVizUI3_time12_6fps.npz'),
        'orbit-archviz-10-bbox44': os.path.join(base_dir, 'data/training-labels/bedlam-labels/20221015_3_250_batch01hand_orbit_archVizUI3_time10_6fps.npz'),
        'static-hdri-bbox44': os.path.join(base_dir, 'data/training-labels/bedlam-labels/20221010_3_1000_batch01hand_6fps.npz'),
        'static-hdri-zoomed-bbox44': os.path.join(base_dir, 'data/training-labels/bedlam-labels/20221017_3_1000_batch01hand_6fps.npz'),
        'staticzoomed-suburba-frameocc-bbox44': os.path.join(base_dir, 'data/training-labels/bedlam-labels/20221017_1_250_batch01hand_closeup_suburb_a_6fps.npz'),
        'pitchup-stadium-bbox44': os.path.join(base_dir, 'data/training-labels/bedlam-labels/20221018_3-8_250_batch01hand_pitchUp52_stadium_6fps.npz'),
        'static-hdri-bmi-bbox44': os.path.join(base_dir, 'data/training-labels/bedlam-labels/20221019_3_250_highbmihand_6fps.npz'),
        'closeup-suburbb-bmi-bbox44': os.path.join(base_dir, 'data/training-labels/bedlam-labels/20221019_1_250_highbmihand_closeup_suburb_b_6fps.npz'),
        'closeup-suburbc-bmi-bbox44': os.path.join(base_dir, 'data/training-labels/bedlam-labels/20221019_1_250_highbmihand_closeup_suburb_c_6fps.npz'),
        'static-suburbd-bmi-bbox44': os.path.join(base_dir, 'data/training-labels/bedlam-labels/20221019_3-8_1000_highbmihand_static_suburb_d_6fps.npz'),
        'zoom-gym-bmi-bbox44': os.path.join(base_dir, 'data/training-labels/bedlam-labels/20221020_3-8_250_highbmihand_zoom_highSchoolGym_a_6fps.npz'),
        'pitchdown-stadium-bbox44': os.path.join(base_dir, 'data/training-labels/bedlam-labels/20221018_3-8_250_batch01hand_pitchDown52_stadium_6fps.npz'),
        'static-office-hair-bbox44': os.path.join(base_dir, 'data/training-labels/bedlam-labels/20221022_3_250_batch01handhair_static_bigOffice_30fps.npz'),
        'zoom-suburbd-hair-bbox44': os.path.join(base_dir, 'data/training-labels/bedlam-labels/20221024_10_100_batch01handhair_zoom_suburb_d_30fps.npz'),
        'static-gym-hair-bbox44': os.path.join(base_dir, 'data/training-labels/bedlam-labels/20221024_3-10_100_batch01handhair_static_highSchoolGym_30fps.npz'),
        'orbit-stadium-bmi-bbox44': os.path.join(base_dir, 'data/training-labels/bedlam-labels/20221019_3-8_250_highbmihand_orbit_stadium_6fps.npz'),

    }
]

def to_lower(x: Dict) -> Dict:
    return {k.lower(): v for k, v in x.items()}

_C = CN(new_allowed=True)

_C.GENERAL = CN(new_allowed=True)
_C.GENERAL.RESUME = True
_C.GENERAL.TIME_TO_RUN = 3300
_C.GENERAL.VAL_STEPS = 100
_C.GENERAL.LOG_STEPS = 100
_C.GENERAL.CHECKPOINT_STEPS = 20000
_C.GENERAL.CHECKPOINT_DIR = "checkpoints"
_C.GENERAL.SUMMARY_DIR = "tensorboard"
_C.GENERAL.NUM_GPUS = 1
_C.GENERAL.NUM_WORKERS = 4
_C.GENERAL.MIXED_PRECISION = True
_C.GENERAL.ALLOW_CUDA = True
_C.GENERAL.PIN_MEMORY = False
_C.GENERAL.DISTRIBUTED = False
_C.GENERAL.LOCAL_RANK = 0
_C.GENERAL.USE_SYNCBN = False
_C.GENERAL.WORLD_SIZE = 1

_C.TRAIN = CN(new_allowed=True)
_C.TRAIN.NUM_EPOCHS = 100
_C.TRAIN.BATCH_SIZE = 32
_C.TRAIN.SHUFFLE = True
_C.TRAIN.WARMUP = False
_C.TRAIN.NORMALIZE_PER_IMAGE = False
_C.TRAIN.CLIP_GRAD = False
_C.TRAIN.CLIP_GRAD_VALUE = 1.0
_C.LOSS_WEIGHTS = CN(new_allowed=True)

_C.DATASETS = CN(new_allowed=True)

_C.MODEL = CN(new_allowed=True)
_C.MODEL.IMAGE_SIZE = 224

_C.EXTRA = CN(new_allowed=True)
_C.EXTRA.FOCAL_LENGTH = 5000

_C.DATASETS.CONFIG = CN(new_allowed=True)
_C.DATASETS.CONFIG.SCALE_FACTOR = 0.3
_C.DATASETS.CONFIG.ROT_FACTOR = 30
_C.DATASETS.CONFIG.TRANS_FACTOR = 0.02
_C.DATASETS.CONFIG.COLOR_SCALE = 0.2
_C.DATASETS.CONFIG.ROT_AUG_RATE = 0.6
_C.DATASETS.CONFIG.TRANS_AUG_RATE = 0.5
_C.DATASETS.CONFIG.DO_FLIP = True
_C.DATASETS.CONFIG.FLIP_AUG_RATE = 0.5
_C.DATASETS.CONFIG.EXTREME_CROP_AUG_RATE = 0.10
_C.DATASETS.CONFIG.USE_ALB = True
_C.DATASETS.CONFIG.ALB_PROB = 0.3

def default_config() -> CN:
    return _C.clone()

def dataset_config() -> CN:
    cfg = CN(new_allowed=True)
    cfg.freeze()
    return cfg


