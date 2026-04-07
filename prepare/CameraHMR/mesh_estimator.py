import cv2
import os
import json
import torch
import smplx
import trimesh
import numpy as np
from tqdm import tqdm
from glob import glob
from copy import deepcopy
from torchvision.transforms import Normalize
from detectron2.config import LazyConfig

from core.utils.utils_detectron2 import DefaultPredictor_Lazy
from core.camerahmr_model import CameraHMR
from core.constants import CHECKPOINT_PATH, CAM_MODEL_CKPT, SMPL_MODEL_PATH, DETECTRON_CKPT, DETECTRON_CFG
from core.datasets.dataset import Dataset
from core.utils.renderer_pyrd import Renderer
from core.utils import recursive_to
from core.utils.geometry import batch_rot2aa
from core.cam_model.fl_net import FLNet
from core.constants import IMAGE_SIZE, IMAGE_MEAN, IMAGE_STD, NUM_BETAS

def resize_image(img, target_size):
    height, width = img.shape[:2]
    aspect_ratio = width / height

    # Calculate the new size while maintaining the aspect ratio
    if aspect_ratio > 1:
        new_width = target_size
        new_height = int(target_size / aspect_ratio)
    else:
        new_width = int(target_size * aspect_ratio)
        new_height = target_size

    # Resize the image using OpenCV
    resized_img = cv2.resize(img, (new_width, new_height), interpolation=cv2.INTER_AREA)

    # Create a new blank image with the target size
    final_img = np.ones((target_size, target_size, 3), dtype=np.uint8) * 255

    # Paste the resized image onto the blank image, centering it
    start_x = (target_size - new_width) // 2
    start_y = (target_size - new_height) // 2
    final_img[start_y:start_y + new_height, start_x:start_x + new_width] = resized_img

    return aspect_ratio, final_img

class HumanMeshEstimator:
    def __init__(self, smpl_model_path=SMPL_MODEL_PATH, threshold=0.25, device=torch.device('cuda')):
        self.device = device
        self.model = self.init_model()
        self.detector = self.init_detector(threshold)
        self.cam_model = self.init_cam_model()
        self.smpl_model = smplx.SMPLLayer(model_path=smpl_model_path, num_betas=NUM_BETAS).to(self.device)
        self.normalize_img = Normalize(mean=IMAGE_MEAN, std=IMAGE_STD)

    def init_cam_model(self):
        model = FLNet()
        checkpoint = torch.load(CAM_MODEL_CKPT)['state_dict']
        model.load_state_dict(checkpoint)
        model.eval()
        return model

    def init_model(self):
        model = CameraHMR.load_from_checkpoint(CHECKPOINT_PATH, map_location='cpu', strict=False)
        model = model.to(self.device)
        model.eval()
        return model
    
    def init_detector(self, threshold):

        detectron2_cfg = LazyConfig.load(str(DETECTRON_CFG))
        detectron2_cfg.train.init_checkpoint = DETECTRON_CKPT
        for i in range(3):
            detectron2_cfg.model.roi_heads.box_predictors[i].test_score_thresh = threshold
        detector = DefaultPredictor_Lazy(detectron2_cfg)
        return detector

    
    def convert_to_full_img_cam(self, pare_cam, bbox_height, bbox_center, img_w, img_h, focal_length):
        s, tx, ty = pare_cam[:, 0], pare_cam[:, 1], pare_cam[:, 2]
        tz = 2. * focal_length / (bbox_height * s)
        cx = 2. * (bbox_center[:, 0] - (img_w / 2.)) / (s * bbox_height)
        cy = 2. * (bbox_center[:, 1] - (img_h / 2.)) / (s * bbox_height)
        cam_t = torch.stack([tx + cx, ty + cy, tz], dim=-1)
        return cam_t

    def get_output_mesh(self, params, pred_cam, batch):
        smpl_output = self.smpl_model(**{k: v.float() for k, v in params.items()})
        pred_keypoints_3d = smpl_output.joints
        pred_vertices = smpl_output.vertices
        img_h, img_w = batch['img_size'][0]
        cam_trans = self.convert_to_full_img_cam(
            pare_cam=pred_cam,
            bbox_height=batch['box_size'],
            bbox_center=batch['box_center'],
            img_w=img_w,
            img_h=img_h,
            focal_length=batch['cam_int'][:, 0, 0]
        )
        return pred_vertices, pred_keypoints_3d, cam_trans

    def get_cam_intrinsics(self, img):
        img_h, img_w, c = img.shape
        aspect_ratio, img_full_resized = resize_image(img, IMAGE_SIZE)
        img_full_resized = np.transpose(img_full_resized.astype('float32'),
                            (2, 0, 1))/255.0
        img_full_resized = self.normalize_img(torch.from_numpy(img_full_resized).float())

        estimated_fov, _ = self.cam_model(img_full_resized.unsqueeze(0))
        vfov = estimated_fov[0, 1]
        fl_h = (img_h / (2 * torch.tan(vfov / 2))).item()
        # fl_h = (img_w * img_w + img_h * img_h) ** 0.5
        cam_int = np.array([[fl_h, 0, img_w/2], [0, fl_h, img_h / 2], [0, 0, 1]]).astype(np.float32)
        return cam_int


    def remove_pelvis_rotation(self, smpl):
        """We don't trust the body orientation coming out of bedlam_cliff, so we're just going to zero it out."""
        smpl.body_pose[0][0][:] = np.zeros(3)

    def process_image(
        self,
        img_path,
        output_smpl_folder,
        output_overlay_folder
    ):
        img_cv2 = cv2.imread(str(img_path), cv2.IMREAD_COLOR)
        
        fname, img_ext = os.path.splitext(os.path.basename(img_path))
        overlay_fname = os.path.join(output_overlay_folder, f'{os.path.basename(fname)}{img_ext}')

        # Detect humans in the image
        det_out = self.detector(img_cv2)
        det_instances = det_out['instances']
        valid_idx = (det_instances.pred_classes == 0) & (det_instances.scores > 0.5)
        boxes = det_instances.pred_boxes.tensor[valid_idx].cpu().numpy()
        if boxes.shape[0] == 0:
            return
        bbox_scale = (boxes[:, 2:4] - boxes[:, 0:2]) / 200.0 
        bbox_center = (boxes[:, 2:4] + boxes[:, 0:2]) / 2.0
        bbox_length = boxes[:, 2:4] - boxes[:, 0:2]
        bbox_area = bbox_length[:, 0] * bbox_length[:, 1]
        valid_indices = np.argsort(bbox_area)[-1]   # only use the actor with max box area

        # Get Camera intrinsics using HumanFoV Model
        cam_int = self.get_cam_intrinsics(img_cv2)
        dataset = Dataset(
            img_cv2,
            bbox_center[valid_indices:valid_indices+1],
            bbox_scale[valid_indices:valid_indices+1],
            cam_int,
            False,
            img_path
        )
        dataloader = torch.utils.data.DataLoader(dataset, batch_size=1, shuffle=False)

        for batch in dataloader:
            batch = recursive_to(batch, self.device)
            img_h, img_w = batch['img_size'][0]
            with torch.no_grad():
                out_smpl_params, out_cam, focal_length_ = self.model(batch)
            output_vertices, output_joints, output_cam_trans = self.get_output_mesh(out_smpl_params, out_cam, batch)

            # Render overlay
            render_check = np.random.choice([0, 1], p=[0.8, 0.2])
            if False:
                focal_length = (focal_length_[0], focal_length_[0])
                pred_vertices_array = (output_vertices + output_cam_trans.unsqueeze(1)).detach().cpu().numpy()
                renderer = Renderer(focal_length=focal_length[0], img_w=img_w, img_h=img_h, faces=self.smpl_model.faces, same_mesh_color=True)
                front_view = renderer.render_front_view(pred_vertices_array, bg_img_rgb=img_cv2.copy())
                final_img = front_view
                # Write overlay
                cv2.imwrite(overlay_fname, final_img)
                renderer.delete()

            # process smpl vertices           
            output_vertices = [item.cpu().numpy() for item in output_vertices]

            # process camera t
            output_cam_trans = [item.cpu().numpy() for item in output_cam_trans]
            
            # process smpl parameters
            for k, _ in out_smpl_params.items():
                out_smpl_params[k] = out_smpl_params[k].cpu().numpy()
            
            # save frame-wise smpl and camera estimation result
            frame_result = {
                "verts": output_vertices,
                "cam_t": output_cam_trans,
                "render_res": np.array([img_w.item(), img_h.item()]),
                "smpls": out_smpl_params,
                "scaled_focal_length": np.array(focal_length_.cpu().numpy()[0])
            }
            np.save(
                os.path.join(output_smpl_folder, f"{fname}.npy"),
                frame_result
            )


    def run_on_images(
        self,
        image_folder,
        out_smpl_folder,
        output_overlay_dir
    ):
        os.makedirs(out_smpl_folder, exist_ok=True)
        os.makedirs(output_overlay_dir, exist_ok=True)

        image_extensions = ['*.jpg', '*.jpeg', '*.png', '*.gif', '*.bmp', '*.tiff', '*.webp']
        images_list = [image for ext in image_extensions for image in glob(os.path.join(image_folder, ext))]
        images_list = sorted(images_list, key=lambda x: int(x.split('/')[-1].split('.')[0]))
        max_frames = min(len(images_list) // 150, 2) * 150

        for ind, img_path in tqdm(enumerate(images_list), desc=f"processing {image_folder}"):
            if ind >= max_frames:
                return
            
            self.process_image(
                img_path,
                out_smpl_folder,
                output_overlay_dir
            )
