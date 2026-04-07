import os
import cv2
import torch
import trimesh
import pyrender
import numpy as np
from smplx import SMPL
from torchvision.utils import make_grid
from typing import List, Set, Dict, Tuple, Optional


os.environ['PYOPENGL_PLATFORM'] = 'egl'

def get_colors():
    colors = {
        'pink': np.array([197, 27, 125]),  # L lower leg
        'light_pink': np.array([233, 163, 201]),  # L upper leg
        'light_green': np.array([161, 215, 106]),  # L lower arm
        'green': np.array([77, 146, 33]),  # L upper arm
        'red': np.array([215, 48, 39]),  # head
        'light_red': np.array([252, 146, 114]),  # head
        'light_orange': np.array([252, 141, 89]),  # chest
        'purple': np.array([118, 42, 131]),  # R lower leg
        'light_purple': np.array([175, 141, 195]),  # R upper
        'light_blue': np.array([145, 191, 219]),  # R lower arm
        'blue': np.array([69, 117, 180]),  # R upper arm
        'gray': np.array([130, 130, 130]),  #
        'white': np.array([255, 255, 255]),  #
        'pinkish': np.array([204, 77, 77]),
    }
    return colors

def get_checkerboard_plane(plane_width=4, num_boxes=9, center=True):

    pw = plane_width/num_boxes
    white = [220, 220, 220, 255]
    black = [35, 35, 35, 255]

    meshes = []
    for i in range(num_boxes):
        for j in range(num_boxes):
            c = i * pw, j * pw
            ground = trimesh.primitives.Box(
                center=[0, 0, -0.0001],
                extents=[pw, pw, 0.0002]
            )

            if center:
                c = c[0]+(pw/2)-(plane_width/2), c[1]+(pw/2)-(plane_width/2)
            # trans = trimesh.transformations.scale_and_translate(scale=1, translate=[c[0], c[1], 0])
            ground.apply_translation([c[0], c[1], 0])
            # ground.apply_transform(trimesh.transformations.rotation_matrix(np.rad2deg(-120), direction=[1,0,0]))
            ground.visual.face_colors = black if ((i+j) % 2) == 0 else white
            meshes.append(ground)

    return meshes

def render_overlay_image(
        image: np.ndarray,
        camera_translation: np.ndarray,
        vertices: np.ndarray,
        camera_rotation: np.ndarray,
        focal_length: Tuple,
        camera_center: Tuple,
        mesh_color: str = 'purple',
        alpha: float = 1.0,
        faces: np.ndarray = None,
        sideview_angle: int = 0,
        mesh_filename: str = None,
        add_ground_plane: bool = True,
        correct_ori: bool = True,
) -> np.ndarray:

    mesh_color = get_colors()[mesh_color]

    material = pyrender.MetallicRoughnessMaterial(
        metallicFactor=0.2,
        alphaMode='OPAQUE',
        baseColorFactor=(mesh_color[0] / 255., mesh_color[1] / 255., mesh_color[2] / 255., alpha))

    camera_translation[0] *= -1.

    mesh = trimesh.Trimesh(vertices, faces, process=False)

    if correct_ori:
        rot = trimesh.transformations.rotation_matrix(
            np.radians(180), [1, 0, 0])
        mesh.apply_transform(rot)

    if sideview_angle > 0:
        rot = trimesh.transformations.rotation_matrix(
            np.radians(sideview_angle), [0, 1, 0])
        mesh.apply_transform(rot)

    if mesh_filename:
        mesh.export(mesh_filename)
        if not mesh_filename.endswith('_rot.obj'):
            np.save(mesh_filename.replace('.obj', '.npy'), camera_translation)

    mesh = pyrender.Mesh.from_trimesh(mesh, material=material)

    scene = pyrender.Scene(bg_color=[0.0, 0.0, 0.0, 0.0],
                           ambient_light=np.ones(3) * 0)

    scene.add(mesh, 'mesh')

    camera_pose = np.eye(4)
    if camera_rotation is not None:
        camera_pose[:3, :3] = camera_rotation
        camera_pose[:3, 3] =  camera_rotation @ camera_translation
    else:
        camera_pose[:3, 3] =  camera_translation

    camera = pyrender.IntrinsicsCamera(fx=focal_length[0], fy=focal_length[1],
                                       cx=camera_center[0], cy=camera_center[1])

    scene.add(camera, pose=camera_pose)

    # Create light source
    light = pyrender.DirectionalLight(color=[1.0, 1.0, 1.0], intensity=5.0)
    # for DirectionalLight, only rotation matters
    light_pose = trimesh.transformations.rotation_matrix(np.radians(-45), [1, 0, 0])
    scene.add(light, pose=light_pose)
    light_pose = trimesh.transformations.rotation_matrix(np.radians(45), [0, 1, 0])
    scene.add(light, pose=light_pose)


    renderer = pyrender.OffscreenRenderer(
        viewport_width=image.shape[1],
        viewport_height=image.shape[0],
        point_size=1.0
    )

    color, rend_depth = renderer.render(scene, flags=pyrender.RenderFlags.RGBA)
    color = color.astype(np.float32) / 255.0
    valid_mask = (rend_depth > 0)[:, :, None]
    visible_weight = 0.6
    output_img = (
        color[:, :, :3] * valid_mask * visible_weight
        + image * (1-valid_mask) +
        + (valid_mask) * image * (1-visible_weight)
    )
    # output_img = (color[:, :, :3] * valid_mask +
    #               (1 - valid_mask) * image)
    return output_img, color[:, :, :3]*valid_mask


def render_nonoverlay_image(
        image: np.ndarray,
        camera_translation: np.ndarray,
        vertices: np.ndarray,
        camera_rotation: np.ndarray,
        focal_length: Tuple,
        camera_center: Tuple,
        mesh_color: str = 'purple',
        alpha: float = 1.0,
        faces: np.ndarray = None,
        sideview_angle: int = 0,
        mesh_filename: str = None,
        add_ground_plane: bool = True,
        correct_ori: bool = True,
) -> np.ndarray:

    mesh_color = get_colors()[mesh_color]

    material = pyrender.MetallicRoughnessMaterial(
        metallicFactor=0.2,
        alphaMode='OPAQUE',
        baseColorFactor=(mesh_color[0] / 255., mesh_color[1] / 255., mesh_color[2] / 255., alpha))

    camera_translation[0] *= -1.

    mesh = trimesh.Trimesh(vertices, faces, process=False)

    if correct_ori:
        rot = trimesh.transformations.rotation_matrix(
            np.radians(180), [1, 0, 0])
        mesh.apply_transform(rot)

    if sideview_angle > 0:
        rot = trimesh.transformations.rotation_matrix(
            np.radians(sideview_angle), [0, 1, 0])
        mesh.apply_transform(rot)

    if mesh_filename:
        mesh.export(mesh_filename)
        if not mesh_filename.endswith('_rot.obj'):
            np.save(mesh_filename.replace('.obj', '.npy'), camera_translation)

    mesh = pyrender.Mesh.from_trimesh(mesh, material=material)

    scene = pyrender.Scene(bg_color=[1.0, 1.0, 1.0, 1.0],
                           ambient_light=np.ones(3) * 0)

    scene.add(mesh, 'mesh')


    camera_pose = np.eye(4)
    if camera_rotation is not None:
        camera_pose[:3, :3] = camera_rotation
        camera_pose[:3, 3] =  camera_rotation @ camera_translation
    else:
        camera_pose[:3, 3] =  camera_translation

    camera = pyrender.IntrinsicsCamera(fx=2000, fy=2000,
                                       cx=camera_center[0], cy=camera_center[1])

    scene.add(camera, pose=camera_pose)


    # Create light source
    light = pyrender.DirectionalLight(color=[1.0, 1.0, 1.0], intensity=5.0)
    # for DirectionalLight, only rotation matters
    light_pose = trimesh.transformations.rotation_matrix(np.radians(-45), [1, 0, 0])
    scene.add(light, pose=light_pose)
    light_pose = trimesh.transformations.rotation_matrix(np.radians(45), [0, 1, 0])
    scene.add(light, pose=light_pose)


    renderer = pyrender.OffscreenRenderer(
        viewport_width=768,
        viewport_height=768,
        point_size=1.0
    )

    color, rend_depth = renderer.render(scene, flags=pyrender.RenderFlags.RGBA)
    color = color.astype(np.float32) / 255.0
    valid_mask = (rend_depth > 0)[:, :, None]

    return color[:, :, :3]*valid_mask + (1-valid_mask)


def render_image_group(
        image: np.ndarray,
        camera_translation: torch.tensor,
        vertices: torch.tensor,
        camera_rotation: torch.tensor,
        focal_length: Tuple,
        camera_center: Tuple,
        mesh_color: str = 'blue',
        alpha: float = 1.0,
        faces: np.ndarray = None,
        mesh_filename: str = None,
        save_filename: str = None,
        keypoints_2d: np.ndarray = None,
        cam_params: np.ndarray = None,
        correct_ori: bool = True,
):
    to_numpy = lambda x: x.detach().cpu().numpy()

    if np.max(image) > 10:
        image = image / 255.

    # if keypoints_2d is not None:
    #     image = draw_skeleton(image, kp_2d=keypoints_2d, dataset='spin', unnormalize=False)


    camera_translation = to_numpy(camera_translation)
    if camera_rotation is not None:
        camera_rotation = to_numpy(camera_rotation)
    vertices = to_numpy(vertices)

    # input image to this step should be between [0,1]
    overlay_img, _ = render_overlay_image(
        image=image,
        camera_translation=camera_translation,
        vertices=vertices,
        camera_rotation=camera_rotation,
        focal_length=focal_length,
        camera_center=camera_center,
        # mesh_color=mesh_color,
        alpha=alpha,
        faces=faces,
        mesh_filename=mesh_filename,
        sideview_angle=0,
        add_ground_plane=False,
        correct_ori=correct_ori,
    )

    # input image to this step should be between [0,1]
    
    non_overlay_img = render_nonoverlay_image(
        image=image,
        camera_translation=np.array([0,0,6.]),
        vertices=vertices,
        camera_rotation=camera_rotation,
        focal_length=focal_length,
        camera_center=(768/2.,768/2.),
        # mesh_color=mesh_color,
        alpha=alpha,
        faces=faces,
        mesh_filename=mesh_filename,
        sideview_angle=90,
        add_ground_plane=False,
        correct_ori=correct_ori,
    )
    if save_filename is not None:
        images_save = overlay_img * 255
        images_save = np.clip(images_save, 0, 255).astype(np.uint8)
        cv2.imwrite(save_filename, images_save)

    return  overlay_img, non_overlay_img

