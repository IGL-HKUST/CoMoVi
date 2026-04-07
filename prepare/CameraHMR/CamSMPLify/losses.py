import torch
from constants import NUM_JOINTS, NUM_SURFACE_POINTS
IMG_RES = 768

def get_transform(center, scale, res):
    """
    Generate transformation matrix.
    """
    h = 200 * scale
    t = torch.zeros(3, 3, device=center.device)  # Ensure device consistency
    t[0, 0] = res[1] / h
    t[1, 1] = res[0] / h
    t[0, 2] = res[1] * (-center[0].float() / h + 0.5)
    t[1, 2] = res[0] * (-center[1].float() / h + 0.5)
    t[2, 2] = 1
    return t

def transform(pts, center, scale, res):
    """
    Transform pixel locations to a different reference.
    """
    t = get_transform(center, scale, res)
    ones_column = torch.ones(pts.shape[0], 1, device=pts.device)
    pts_homogeneous = torch.cat((pts, ones_column), dim=1)  # Convert to homogeneous coordinates
    new_pts = torch.matmul(t, pts_homogeneous.t()).t()
    new_pts = new_pts[:, :2] / new_pts[:, 2].unsqueeze(1)  # Normalize homogeneous coordinates
    return new_pts + 1

def j2d_processing(kp, center, scale):
    """
    Process 2D keypoints for normalization.
    """
    return transform(kp + 1, center, scale, [IMG_RES, IMG_RES])

def perspective_projection(points, translation, cam_intrinsics):
    """
    Apply perspective projection using camera intrinsics.
    """
    points_translated = points + translation.unsqueeze(0)
    projected_points = points_translated / points_translated[:, -1].unsqueeze(-1)  # Normalize
    return torch.einsum('ij,kj->ki', cam_intrinsics, projected_points.float())[:, :-1]

def gmof(x, sigma):
    """
    Geman-McClure robust error function.
    """
    x_squared = x**2
    sigma_squared = sigma**2
    return (sigma_squared * x_squared) / (sigma_squared + x_squared)

def body_fitting_loss_dense(
    init_pose, init_global_orient, init_betas,
    body_pose, global_orient, betas,
    model_joints, joints_init,
    verts_init, model_verts,
    verts_sampled, camera_t,
    camera_center, camera_scale,
    cam_int, joints_2d,
    joints_conf, dense_kp,
    sigma=100, 
    pose_prior_weight=0,
    beta_prior_weight=0,
    densekp_weight=0.0005,
    kp_weight=0.005,
    imgname=None, 
    verbose=False
):
    """
    Loss function for body fitting.
    """
    # Compute projected joints in full image space
    joints_2d_full_image = perspective_projection(model_joints[0], camera_t, cam_int)
    projected_joints = j2d_processing(joints_2d_full_image, camera_center, camera_scale)
    
    # Compute dense keypoints projection
    dense_kp_full_image = perspective_projection(verts_sampled[0], camera_t, cam_int)
    projected_dense_kp = j2d_processing(dense_kp_full_image, camera_center, camera_scale)
    # Compute reprojection loss
    reprojection_error = gmof(projected_joints[:NUM_JOINTS] - joints_2d[:NUM_JOINTS], sigma)
    reprojection_loss = kp_weight * (joints_conf[:NUM_JOINTS] * reprojection_error.sum(dim=-1)).sum(dim=-1)
    
    # Compute dense reprojection loss
    dense_reprojection_error = gmof(projected_dense_kp - dense_kp[:NUM_SURFACE_POINTS, :2], sigma)
    dense_loss = densekp_weight * dense_reprojection_error.sum(dim=[-1, -2])
    
    # Compute initialization losses
    # joints_init_loss = 10 * pose_prior_weight * ((model_joints[0, :NUM_JOINTS, :] - joints_init[0, :NUM_JOINTS, :])**2).sum(dim=[-1, -2])
    verts_init_loss = pose_prior_weight * ((model_verts - verts_init)**2).sum(dim=[-1, -2])
    
    # Compute pose and beta losses
    pose_loss = 10 * ((body_pose[0] - init_pose[0])**2).sum(dim=[-1, -2])
    beta_loss = beta_prior_weight * ((init_betas - betas)**2).sum(dim=-1)
    
    # Total loss computation
    total_loss = (
        reprojection_loss + beta_loss + 
        pose_loss + verts_init_loss + dense_loss
    )
    
    # Dictionary of losses
    loss_dict = {
        'reprojection': reprojection_loss,
        # 'joints_loss': joints_init_loss,
        'verts': verts_init_loss,
        'dense': dense_loss,
        'pose_prior': pose_loss,
        'shape_prior': beta_loss
    }
    
    if verbose:
        for k, v in loss_dict.items():
            print(f"{k}: {v}")
    
    return total_loss, loss_dict
