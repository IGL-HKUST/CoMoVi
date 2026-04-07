import torch
from collections import OrderedDict

def denormalize_images(images):
    images = images * torch.tensor([0.229, 0.224, 0.225], device=images.device).reshape(1, 3, 1, 1)
    images = images + torch.tensor([0.485, 0.456, 0.406], device=images.device).reshape(1, 3, 1, 1)
    return images
    
def trans_points2d_parallel(keypoints_2d, trans):
    # Augment keypoints with ones to apply affine transformation
    ones = torch.ones((*keypoints_2d.shape[:2], 1), dtype=torch.float64, device=keypoints_2d.device)
    keypoints_augmented = torch.cat([keypoints_2d, ones], dim=-1)
    
    # Apply transformation using batch matrix multiplication
    transformed_keypoints = torch.einsum('bij,bkj->bki', trans, keypoints_augmented)
    return transformed_keypoints[..., :2]


def strip_prefix_if_present(state_dict, prefix):
    keys = sorted(state_dict.keys())
    if not any(key.startswith(prefix) for key in keys):
        return state_dict
    stripped_state_dict = OrderedDict()
    for key, value in state_dict.items():
        stripped_state_dict[key.replace(prefix + '.', '')] = value
    return stripped_state_dict


def load_valid(model, pretrained_file, skip_list=None):

    pretrained_dict = torch.load(pretrained_file)['state_dict']
    pretrained_dict = strip_prefix_if_present(pretrained_dict, prefix='model')

    model_dict = model.state_dict()
    # 1. filter out unnecessary keys
    pretrained_dict1 = {k: v for k, v in pretrained_dict.items() if k in model_dict}
    # 2. overwrite entries in the existing state dict
    model_dict.update(pretrained_dict)
    model.load_state_dict(model_dict)


def perspective_projection(points, rotation, translation, cam_intrinsics):

    K = cam_intrinsics
    points = torch.einsum('bij,bkj->bki', rotation, points)
    points = points + translation.unsqueeze(1)
    projected_points = points / points[:, :, -1].unsqueeze(-1)
    projected_points = torch.einsum('bij,bkj->bki', K, projected_points.float())
    return projected_points[:, :, :-1]


def convert_to_full_img_cam(
        pare_cam, bbox_height, bbox_center,
        img_w, img_h, focal_length):

    s, tx, ty = pare_cam[:, 0], pare_cam[:, 1], pare_cam[:, 2]
    tz = 2. * focal_length / (bbox_height * s)

    cx = 2. * (bbox_center[:, 0] - (img_w / 2.)) / (s * bbox_height)
    cy = 2. * (bbox_center[:, 1] - (img_h / 2.)) / (s * bbox_height)

    cam_t = torch.stack([tx + cx, ty + cy, tz], dim=-1)
    return cam_t



