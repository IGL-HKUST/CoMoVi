
import os
import cv2
import torch
import copy
import smplx
import pickle
import numpy as np
from torch.utils.data import Dataset
from ..utils.pylogger import get_pylogger
from ..configs import DATASET_FOLDERS, DATASET_FILES
from .utils import expand_to_aspect_ratio, get_example, resize_image
from torchvision.transforms import Normalize
from ..constants import FLIP_KEYPOINT_PERMUTATION, NUM_JOINTS, NUM_BETAS, NUM_PARAMS_SMPL, NUM_PARAMS_SMPLX, SMPLX2SMPL, SMPLX_MODEL_DIR, SMPL_MODEL_DIR

log = get_pylogger(__name__)


class DatasetVal(Dataset):
    def __init__(self, cfg, dataset, is_train=False):
        super(DatasetVal, self).__init__()

        self.dataset = dataset
        self.is_train = is_train
        self.cfg = cfg
        self.IMG_SIZE = cfg.MODEL.IMAGE_SIZE
        self.BBOX_SHAPE = cfg.MODEL.get('BBOX_SHAPE', None)
        self.MEAN = 255. * np.array(cfg.MODEL.IMAGE_MEAN)
        self.STD = 255. * np.array(cfg.MODEL.IMAGE_STD)
        self.normalize_img = Normalize(mean=cfg.MODEL.IMAGE_MEAN,
                                    std=cfg.MODEL.IMAGE_STD)
        self.use_skimage_antialias = cfg.DATASETS.get('USE_SKIMAGE_ANTIALIAS', False)
        self.border_mode = {
            'constant': cv2.BORDER_CONSTANT,
            'replicate': cv2.BORDER_REPLICATE,
        }[cfg.DATASETS.get('BORDER_MODE', 'constant')]

        self.img_dir = DATASET_FOLDERS[dataset] 
        self.data = np.load(DATASET_FILES[is_train][dataset], allow_pickle=True)
        self.imgname = self.data['imgname']
        self.scale = self.data['scale']
        self.center = self.data['center']
        if ('coco' in self.dataset or 'lsp' in self.dataset):
            self.scale = self.scale/200

        if 'pose_cam' in self.data:
            if 'smplx' in self.dataset:
                self.pose = self.data['pose_cam'][:, :NUM_PARAMS_SMPLX*3].astype(np.float)
            else:
                self.pose = self.data['pose_cam'][:, :NUM_PARAMS_SMPL*3].astype(np.float)
        else:
            self.pose = np.zeros((len(self.imgname), 24*3), dtype=np.float32)

        if 'shape' in self.data:
            self.betas = self.data['shape'].astype(np.float)[:,:NUM_BETAS] 
        else:
            self.betas = np.zeros((len(self.imgname), 10), dtype=np.float32)

        if 'part' in self.data:
            self.keypoints = self.data['part']
        elif 'gtkps' in self.data:
            self.keypoints = self.data['gtkps'][:,:NUM_JOINTS]#Todo later: change it to a variable
        elif 'body_keypoints_2d' in self.data:
            self.keypoints = self.data['body_keypoints_2d']
        else:
            self.keypoints = np.zeros((len(self.imgname), NUM_JOINTS, 3))
        
        if self.keypoints.shape[2]<3:
            ones_array = np.ones((self.keypoints.shape[0],self.keypoints.shape[1],1))
            self.keypoints = np.concatenate((self.keypoints, ones_array), axis=2)

        if 'cam_int' in self.data:
            self.cam_int = self.data['cam_int']
        else:
            self.cam_int = np.zeros((len(self.imgname),3,3), dtype=np.float32)
        try:
            gender = self.data['gender']
            self.gender = np.array([0 if str(g) == 'm' or str(g)=='male'
                                    else 1 for g in gender]).astype(np.int32)
        except KeyError:
            self.gender = -1 * np.ones(len(self.imgname)).astype(np.int32)


        self.smpl_gt_male = smplx.SMPL(SMPL_MODEL_DIR,
                                gender='male')
        self.smpl_gt_female = smplx.SMPL(SMPL_MODEL_DIR,
                                    gender='female')
        self.smpl_gt_neutral = smplx.SMPL(SMPL_MODEL_DIR,
                                    gender='neutral')
        
        self.smplx_gt_male = smplx.SMPLX(SMPLX_MODEL_DIR,
                                gender='male')
        self.smplx_gt_female = smplx.SMPLX(SMPLX_MODEL_DIR,
                                    gender='female')
        self.smplx_gt_neutral = smplx.SMPLX(SMPLX_MODEL_DIR,
                                    gender='neutral')
        self.smplx2smpl = pickle.load(open(SMPLX2SMPL, 'rb'))
        self.smplx2smpl = torch.tensor(self.smplx2smpl['matrix'][None],
                                        dtype=torch.float32)

        self.length = self.scale.shape[0]
        log.info(f'Loaded {self.dataset} dataset, num samples {self.length}')

    def __getitem__(self, index):
        item = {}
        scale = self.scale[index].copy()
        center = self.center[index].copy()
        keypoints_2d = self.keypoints[index].copy()
        orig_keypoints_2d = self.keypoints[index].copy()
        center_x = center[0]
        center_y = center[1]
        bbox_size = expand_to_aspect_ratio(scale*200, target_aspect_ratio=self.BBOX_SHAPE).max()
        if bbox_size < 1:
            #Todo raise proper error
            breakpoint()

        augm_config = copy.deepcopy(self.cfg.DATASETS.CONFIG)
        imgname = os.path.join(self.img_dir, self.imgname[index])
        cv_img = cv2.imread(imgname, cv2.IMREAD_COLOR | cv2.IMREAD_IGNORE_ORIENTATION)
        cv_img = cv_img[:, :, ::-1]
        aspect_ratio, img_full_resized = resize_image(cv_img, 256)
        img_full_resized = np.transpose(img_full_resized.astype('float32'),
                        (2, 0, 1))/255.0
        item['img_full_resized'] = self.normalize_img(torch.from_numpy(img_full_resized).float())
        if 'smplx' in self.dataset:
            smpl_params = {'global_orient': self.pose[index][:3].astype(np.float32),
                        'body_pose': self.pose[index][3:66].astype(np.float32),
                        'betas': self.betas[index].astype(np.float32)
                        }
            item['smpl_params'] = smpl_params
        else:
            smpl_params = {'global_orient': self.pose[index][:3].astype(np.float32),
                        'body_pose': self.pose[index][3:].astype(np.float32),
                        'betas': self.betas[index].astype(np.float32)
                        }
            item['smpl_params'] = smpl_params

        img_patch_rgba = None
        img_patch_cv = None
        img_patch_rgba, \
        img_patch_cv,\
        keypoints_2d, \
        img_size, cx, cy, bbox_w, bbox_h, trans, scale_aug = get_example(imgname,
                                      center_x, center_y,
                                      bbox_size, bbox_size,
                                      keypoints_2d,
                                      FLIP_KEYPOINT_PERMUTATION,
                                      self.IMG_SIZE, self.IMG_SIZE,
                                      self.MEAN, self.STD, self.is_train, augm_config,
                                      is_bgr=True, return_trans=True,
                                      use_skimage_antialias=self.use_skimage_antialias,
                                      border_mode=self.border_mode,
                                      dataset=self.dataset
                                      )

        img_w = img_size[1]
        img_h = img_size[0]
        fl = 5000 # This will be updated in forward_step of camerahmr_trainer
        item['cam_int'] = np.array([[fl, 0, img_w/2.], [0, fl, img_h / 2.], [0, 0, 1]]).astype(np.float32)

        new_center = np.array([cx, cy])
        img_patch = img_patch_rgba[:3,:,:]
        item['img'] = img_patch
        item['img_disp'] = img_patch_cv
        item['keypoints_2d'] = keypoints_2d.astype(np.float32)
        item['orig_keypoints_2d'] = orig_keypoints_2d
        item['box_center'] = new_center
        item['box_size'] = bbox_w * scale_aug
        item['img_size'] = 1.0 * img_size.copy()
        item['_scale'] = scale
        item['_trans'] = trans
        item['imgname'] = imgname
        item['dataset'] = self.dataset
        item['gender'] = self.gender[index]
        if 'smplx' in self.dataset:
            if self.gender[index] == 1:
                model = self.smplx_gt_female
            elif self.gender[index] == 0:
                model = self.smplx_gt_male
            else:
                model = self.smplx_gt_neutral

            gt_smpl_out = model(
                        global_orient=torch.from_numpy(item['smpl_params']['global_orient']).unsqueeze(0),
                        body_pose=torch.from_numpy(item['smpl_params']['body_pose']).unsqueeze(0),
                        betas=torch.from_numpy(item['smpl_params']['betas']).unsqueeze(0))
            gt_vertices = gt_smpl_out.vertices.detach()
            gt_vertices = torch.matmul(self.smplx2smpl, gt_vertices)
            item['keypoints_3d'] = torch.matmul(self.smpl_gt_neutral.J_regressor, gt_vertices[0])
            item['vertices'] = gt_vertices[0].float()
        else:
            if self.gender[index] == 1:
                model = self.smpl_gt_female
            elif self.gender[index] == 0:
                model = self.smpl_gt_male
            else:
                model = self.smpl_gt_neutral
            gt_smpl_out = model(
                        global_orient=torch.from_numpy(item['smpl_params']['global_orient']).unsqueeze(0),
                        body_pose=torch.from_numpy(item['smpl_params']['body_pose']).unsqueeze(0),
                        betas=torch.from_numpy(item['smpl_params']['betas']).unsqueeze(0))
            
            gt_vertices = gt_smpl_out.vertices.detach()  
            item['keypoints_3d'] = torch.matmul(model.J_regressor, gt_vertices[0])
            item['vertices'] = gt_vertices[0].float()
        return item

    def __len__(self):
        return int(len(self.imgname))
        
       