import os
import pickle
import cv2
import constants
import torch
import trimesh
import numpy as np
from pathlib import Path
from constants import SMPL_MODEL_DIR, DOWNSAMPLE_MAT, LOSS_CUT, LOW_THRESHOLD, HIGH_THRESHOLD
from losses import body_fitting_loss_dense
from utils.smpl_openpose import SMPL
from utils.image_utils import crop, read_img, transform
from utils.renderer_cam import render_image_group

IMG_RES = 768

def get_transform(center, scale, res):
    """Generate transformation matrix."""
    h = 200 * scale
    t = torch.zeros(3, 3, device=center.device)  # Ensure device consistency
    t[0, 0] = res[1] / h
    t[1, 1] = res[0]/ h
    t[0, 2] = res[1] * (-center[0].float() / h + .5)
    t[1, 2] = res[0] * (-center[1].float() / h + .5)
    t[2, 2] = 1
    return t

def transform(pts, center, scale, res):
    """Transform pixel locations to a different reference."""
    t = get_transform(center, scale, res)
    ones_column = torch.ones(pts.shape[0], 1, device=pts.device)
    pts = torch.cat((pts, ones_column), dim=1)  # Add column of ones for homogeneous coordinates
    new_pts = torch.matmul(t, pts.t()).t()
    new_pts = new_pts[:, :2] / new_pts[:, 2].unsqueeze(1)  # Normalize homogeneous coordinates
    return new_pts + 1

def j2d_processing(kp, center, scale):
    kp_transformed = transform(kp + 1, center, scale, [IMG_RES, IMG_RES])
    # convert to normalized coordinates
    # kp[:, :-1] = 2.0 * kp[:, :-1] / IMG_RES - 1.0
    return kp_transformed

def perspective_projection(points, translation, cam_intrinsics):

    K = cam_intrinsics
    points_translated = points + translation.unsqueeze(0)
    projected_points = points_translated / points_translated[:, -1].unsqueeze(-1)  
    projected_points = torch.einsum('ij,kj->ki', K, projected_points.float())
    return projected_points


class SMPLify:
    """Implementation of single-stage SMPLify."""

    def __init__(self, step_size=1e-3, batch_size=1, num_iters=5000, focal_length=5000,
                 device=torch.device('cuda'), vis=False, verbose=False, save_path=None):
        self.device = device or torch.device("cpu")
        self.focal_length = focal_length
        self.step_size = step_size
        self.num_iters = num_iters
        self.threshold = 20
        self.verbose = verbose
        # Load SMPL model
        self.smpl = SMPL(SMPL_MODEL_DIR).to(self.device)
        self.vis = vis
        self.save_path = save_path
        self.downsample_mat = pickle.load(open(DOWNSAMPLE_MAT, 'rb')).to_dense().cuda()

            
    def visualize_result(self, image_full, smpl_output, focal_length, bbox_center, bbox_scale, camera_translation, cam_int):
        vertices3d = smpl_output.vertices
        img_h, img_w, _ = image_full.shape

        render_img, non_overlay_img = render_image_group(
            image=image_full,
            camera_translation=camera_translation.detach(),
            vertices=vertices3d[0].detach(),
            focal_length=(focal_length, focal_length),
            camera_center=(img_w / 2., img_h / 2.),
            camera_rotation=None,
            save_filename=None,
            faces=self.smpl.faces,
        )
        render_img = crop(render_img, bbox_center, bbox_scale, [IMG_RES, IMG_RES])
        render_img = np.clip(render_img * 255, 0, 255).astype(np.uint8)

        non_overlay_img = np.clip(non_overlay_img * 255, 0, 255).astype(np.uint8)
        
        combined_img = np.concatenate([render_img, non_overlay_img], axis=1)

        # Display instructions in the console
        print("[INFO] Press any key to continue fitting")

        cv2.imshow("Visualization", combined_img)
        pressed_key = cv2.waitKey()


    def __call__(self, args, init_pose, init_betas, cam_t, bbox_center, bbox_scale, cam_int, imgname, joints_2d_=None,
                 dense_kp=None, ind=-1):
        body_pose = torch.tensor(init_pose[:, 3:], device=self.device, dtype=torch.float32, requires_grad=True)
        init_pose_ = torch.tensor(init_pose[:, 3:], device=self.device, dtype=torch.float32)

        global_orient = torch.tensor(init_pose[:, :3], device=self.device, dtype=torch.float32, requires_grad=True)
        init_global_orient_ = torch.tensor(init_pose[:, :3], device=self.device, dtype=torch.float32)
        betas = torch.tensor(init_betas, device=self.device, dtype=torch.float32, requires_grad=True)
        init_betas_ = torch.tensor(init_betas, device=self.device, dtype=torch.float32)

        bbox_center = torch.tensor(bbox_center, device=self.device, dtype=torch.float32)
        bbox_scale = torch.tensor(bbox_scale, device=self.device, dtype=torch.float32)
        camera_translation = torch.tensor(cam_t, device=self.device, dtype=torch.float32, requires_grad=True)
        cam_int = torch.tensor(cam_int, device=self.device, dtype=torch.float32, requires_grad=False)
        focal_length = cam_int[0, 0]

        smpl_output = self.smpl(global_orient=global_orient, body_pose=body_pose, betas=betas)
        model_joints_init = smpl_output.joints.detach()
        model_verts_init = smpl_output.vertices.detach()

        dense_kp = torch.tensor(dense_kp, device=self.device, dtype=torch.float32)
        dense_kp = (dense_kp + 0.5) * IMG_RES

        if joints_2d_ is None or len(joints_2d_) == 0:
            joints_2d_full_image_orig = perspective_projection(model_joints_init[0], camera_translation.detach(), cam_int)
            joints_2d = j2d_processing(joints_2d_full_image_orig[:, :-1], bbox_center, bbox_scale)
            joints_conf = joints_2d_full_image_orig[:, -1]
        else:
            joints_2d_ = torch.tensor(joints_2d_, device=self.device, dtype=torch.float32)
            joints_2d = j2d_processing(joints_2d_[:, :-1], bbox_center, bbox_scale)
            joints_conf = torch.tensor(joints_2d_[:, -1] > 0.7, device=self.device, dtype=torch.float32)
            joints_conf[constants.JOINT_IDS['OP RHip']] = 0
            joints_conf[constants.JOINT_IDS['OP LHip']] = 0
            joints_conf[constants.JOINT_IDS['OP Neck']] = 0

            if joints_conf.sum() < 8:
                print('SUM', joints_conf.sum())
                return 0

        vertices3d = smpl_output.vertices

        if self.vis:
            draw_add = torch.zeros((joints_2d.shape[0],1))
            image_full = read_img(imgname)
            image_full = image_full[:, :, ::-1]
            img_h, img_w, _ = image_full.shape
            return_val = self.visualize_result(image_full, smpl_output, focal_length, bbox_center, bbox_scale, camera_translation, cam_int)

        def run_optimization(optimizer, num_iters, pose_prior_weight, beta_prior_weight):
            nonlocal prev_loss
            for i in range(num_iters):
                smpl_output = self.smpl(global_orient=global_orient, body_pose=body_pose, betas=betas)
                model_joints, model_verts = smpl_output.joints, smpl_output.vertices
                model_verts_sampled = self.downsample_mat.matmul(model_verts)

                loss, _ = body_fitting_loss_dense( 
                    init_pose_, init_global_orient_, init_betas_, body_pose, global_orient, betas,
                    model_joints, model_joints_init, model_verts_init, model_verts, model_verts_sampled,
                    camera_translation, bbox_center, bbox_scale, cam_int, joints_2d, joints_conf, dense_kp,
                    imgname=imgname, verbose=self.verbose,
                    pose_prior_weight=pose_prior_weight,
                    beta_prior_weight=beta_prior_weight
                )
                
                if prev_loss == float('inf'):
                    # Note that these threshold are manually chosen after going through many samples. 
                    # If the losses changed the threshold has to be adjusted accordingly.
                    if loss.item()>args.loss_cut:
                        self.threshold = args.high_threshold
                    else:
                        self.threshold = args.low_threshold
                optimizer.zero_grad()
                loss.backward()
                optimizer.step()

                if i % args.vis_int == 0 and self.vis:
                    return_val = self.visualize_result(image_full, smpl_output, focal_length, bbox_center, bbox_scale, camera_translation, cam_int)
          
            return loss
        
        # Phase 1 Optimization

        prev_loss = float('inf')
        camera_translation.requires_grad = True
        betas.requires_grad = True
        
        body_optimizer = torch.optim.Adam([camera_translation, betas], lr=self.step_size, betas=(0.9, 0.999))
        pose_prior_weight, beta_prior_weight = 0.0, 0.0

        loss = run_optimization(body_optimizer, 300, pose_prior_weight, beta_prior_weight)
       
        smpl_output = self.smpl(global_orient=global_orient, body_pose=body_pose, betas=betas)
        model_joints_init, model_verts_init = smpl_output.joints.detach(), smpl_output.vertices.detach()

        # Phase 2 Optimization
        global_orient.requires_grad = True
        camera_translation.requires_grad = True
        betas.requires_grad = True
        
        body_optimizer = torch.optim.Adam([global_orient, camera_translation, betas], lr=self.step_size, betas=(0.9, 0.999))
        pose_prior_weight, beta_prior_weight = 0.0, 0.01

        loss = run_optimization(body_optimizer, 300, pose_prior_weight, beta_prior_weight)
       
        smpl_output = self.smpl(global_orient=global_orient, body_pose=body_pose, betas=betas)
        model_joints_init, model_verts_init = smpl_output.joints.detach(), smpl_output.vertices.detach()
         

        # Phase 3 Optimization
        init_global_orient_ = global_orient.detach().clone()
        init_betas_ = betas.detach().clone()
        body_pose.requires_grad = True
        body_optimizer = torch.optim.Adam([body_pose, global_orient, camera_translation, betas], lr=self.step_size, betas=(0.9, 0.999))
        pose_prior_weight, beta_prior_weight = 1.0, 10.0
        
        loss = run_optimization(body_optimizer, 500, pose_prior_weight, beta_prior_weight)
        
        print('Final loss {:.4f}, Threshold cut {:.4f}'.format(loss.item(), self.threshold))
        
        return {
            'pose': body_pose,
            'global_orient': global_orient,
            'camera_translation': camera_translation,
            'betas': betas
        } if loss.item() < self.threshold else {}