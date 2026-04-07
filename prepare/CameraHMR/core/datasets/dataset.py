from typing import Dict

import cv2
import numpy as np
import torch
from torchvision.transforms import Normalize
from ..constants import IMAGE_SIZE, IMAGE_MEAN, IMAGE_STD
from .utils import (convert_cvimg_to_tensor,
                    expand_to_aspect_ratio,
                    generate_image_patch_cv2)

DEFAULT_MEAN = 255. * np.array([0.485, 0.456, 0.406])
DEFAULT_STD = 255. * np.array([0.229, 0.224, 0.225])

    
class Dataset(torch.utils.data.Dataset):

    def __init__(self,
                 img_cv2: np.array,
                 bbox_center: np.array,
                 bbox_scale: np.array,
                 cam_int: np.array = None,
                 train: bool = False,
                 img_path = None,
                 **kwargs):
        super().__init__()
        self.img_cv2 = img_cv2
        self.img_path = img_path
        # self.boxes = boxes

        assert train == False, "ViTDetDataset is only for inference"
        self.train = train
        self.img_size = IMAGE_SIZE
        if cam_int is not None:
            self.cam_int = cam_int
        else:
            self.cam_int = np.array([]) # DenseKP model doesn't need cam_int
        self.mean = 255. * np.array(IMAGE_MEAN)
        self.std = 255. * np.array(IMAGE_STD)
        self.normalize_img = Normalize(mean=IMAGE_MEAN,
                                    std=IMAGE_STD)
        self.center = bbox_center
        self.scale = bbox_scale
        self.personid = np.arange(len(self.center), dtype=np.int32)


    def __len__(self) -> int:
        return len(self.personid)

    def __getitem__(self, idx: int):

        center = self.center[idx]
        center_x = center[0]
        center_y = center[1]

        scale = self.scale[idx]
        BBOX_SHAPE = None
        bbox_size = expand_to_aspect_ratio(scale*200, target_aspect_ratio=BBOX_SHAPE).max()

        patch_width = patch_height = self.img_size
        cvimg = self.img_cv2

        img_patch_cv, trans = generate_image_patch_cv2(cvimg,
                                                    center_x, center_y,
                                                    bbox_size, bbox_size,
                                                    patch_width, patch_height,
                                                    False, 1.0, 0,
                                                    border_mode=cv2.BORDER_CONSTANT)


        img_patch = convert_cvimg_to_tensor( img_patch_cv[:, :, ::-1])
        # apply normalization
        # img_patch = self.normalize_img(torch.tensor(img_patch))
        for n_c in range(min(self.img_cv2.shape[2], 3)):
            img_patch[n_c, :, :] = (img_patch[n_c, :, :] - self.mean[n_c]) / self.std[n_c]

        item = {
            'img': img_patch,
            'personid': int(self.personid[idx]),
        }
        item['imgname'] = str(self.img_path)
        item['box_center'] = self.center[idx]
        item['box_size'] =  bbox_size
        item['img_size'] = 1.0 * np.array([cvimg.shape[0], cvimg.shape[1]])
        item['cam_int'] = self.cam_int
        return item
