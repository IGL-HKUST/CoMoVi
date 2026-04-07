import numpy as np
import torch
import cv2
import os
from tqdm import tqdm
import argparse
import json
import tempfile
import shutil

from pytorch3d.structures import Meshes
from pytorch3d.renderer import TexturesVertex
from pytorch3d.utils import cameras_from_opencv_projection
from pytorch3d.renderer import (
    RasterizationSettings,
    MeshRenderer,
    MeshRasterizer,
    HardPhongShader,
    Materials
)

device = torch.device("cuda:0") if torch.cuda.is_available() else torch.device("cpu")
smpl_info = np.load("prepare/CameraHMR/smpl_mesh_info.npy", allow_pickle=True).item()
smpl_faces = torch.from_numpy(smpl_info["faces"].astype(np.int32)).int()

with open("prepare/CameraHMR//smpl_vert_segmentation.json", "r") as f:
    smpl_vert_segmentation = json.load(f)
parts = list(smpl_vert_segmentation.keys())
vertex_to_part = {}
for i in range(len(parts)):
    for id in smpl_vert_segmentation[parts[i]]:
        vertex_to_part[id] = i

# encoding sign(normal_z)
# e.g. -1: right_hand with normal_z < 0; 1: right_hand with normal_z > 0
semantic_colors = torch.from_numpy(np.linspace(1, 2*len(parts), 2*len(parts)) / (2*len(parts))).float().to(device)

# materials
materials = Materials(
    device=device,
    ambient_color=((1, 1, 1),),
    diffuse_color=((1, 1, 1),),
    specular_color=((1, 1, 1),),
    shininess=0,
)


def ffmpeg(args, temp_dir, video_name):
    source_video_path = os.path.join(args.root_dir, "rgb_videos", video_name+".mp4")
    cap = cv2.VideoCapture(source_video_path)
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    cap.release()
    
    output_file = os.path.join(args.root_dir, f"motion_2d_videos/{video_name}.mp4")
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    cmd = f"ffmpeg -framerate {fps} -i {temp_dir}/%06d.jpg -vf \"format=yuv420p,scale=iw:ih:flags=lanczos\" -c:v libx264 -preset veryslow -crf 18 -pix_fmt yuv420p -movflags +faststart {output_file}"
    os.system(cmd)


def make_renderer(smpl_data):
    # construct camera
    focal = smpl_data["scaled_focal_length"]
    img_size = [x.item() for x in smpl_data["render_res"].astype(np.int32)]
    if "center" in smpl_data.keys():
        cx, cy = smpl_data["center"]
    else:
        cx, cy = img_size[0]//2, img_size[1]//2

    if isinstance(focal, float):
        focal_x = focal
        focal_y = focal
    elif isinstance(focal, np.ndarray):
        if focal.size == 1:
            focal_x = focal.item()
            focal_y = focal.item()
        else:
            focal_x, focal_y = focal

    K = torch.eye(3).view(1, 3, 3)
    K[0, 0, 0] = focal_x; K[0, 1, 1] = focal_y
    K[0, 0, 2] = cx; K[0, 1, 2] = cy
    cameras = cameras_from_opencv_projection(
        torch.eye(3).view(1, 3, 3).to(device),
        torch.zeros(1, 3).to(device),
        K.to(device),
        torch.tensor([img_size[1], img_size[0]]).unsqueeze(0)
    )

    # define rasterization setting
    raster_settings = RasterizationSettings(
        image_size=[img_size[1], img_size[0]],
        blur_radius=0.0,
        faces_per_pixel=10,
        max_faces_per_bin=100000
    )

    # define shader
    bp = None
    shader = HardPhongShader(
        device=device,
        cameras=cameras,
        materials=materials,
        blend_params=bp
    )

    # create renderer
    renderer = MeshRenderer(
        rasterizer=MeshRasterizer(cameras=cameras, raster_settings=raster_settings),
        shader=shader
    )

    return renderer

def render_single_frame(npy_path):
    smpl_data = np.load(npy_path, allow_pickle=True).item()
    
    # load mesh
    smpl_verts = torch.from_numpy(smpl_data["verts"][0]).float()
    smpl_verts += torch.from_numpy(smpl_data["cam_t"][0]).float().view(1, 3)
    smpl_mesh = Meshes(
        verts=[smpl_verts.to(device)],
        faces=[smpl_faces.to(device)],
        # textures=verts_texture
    )
    mesh_normal = smpl_mesh.verts_normals_list()[0]
    
    # calculate semantic color
    semantic_channel_color = torch.zeros(mesh_normal.shape[0], 1).to(device)
    z_semantic_channel_color = torch.zeros(mesh_normal.shape[0], 1).to(device)
    for vid in range(semantic_channel_color.shape[0]):
        semantic_channel_color[vid] = semantic_colors[2*vertex_to_part[vid]+1]
        
        if torch.sign(mesh_normal[vid][2]) < 0:
            z_semantic_channel_color[vid] = semantic_colors[2*vertex_to_part[vid]]
        else:
            z_semantic_channel_color[vid] = semantic_colors[2*vertex_to_part[vid]+1]
            
    # calculate normal color
    normal_channel_color = mesh_normal / 2 + 0.5

    # merge normal and semantic color
    vc_xy_z_semantic = torch.cat([normal_channel_color[:, :2], z_semantic_channel_color], dim=-1)

    # color mesh
    smpl_mesh = Meshes(
        verts=[smpl_verts.to(device)],
        faces=[smpl_faces.to(device)],
        textures=TexturesVertex(verts_features=[vc_xy_z_semantic.to(device)])
    )

    # create renderer
    renderer = make_renderer(smpl_data)

    # render
    rendered_img = renderer(smpl_mesh)

    return 255 * rendered_img[0, :, :, :-1].detach().cpu().numpy()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--root_dir", type=str, default="./examples/training")
    args = parser.parse_args()
    
    data_dir = os.path.join(args.root_dir, "CameraHMR_smpl_results_smoothed")
    sequence_folders = sorted(os.listdir(data_dir))
    for i in range(len(sequence_folders)):
        if os.path.exists(
            os.path.join(args.root_dir, f"motion_2d_videos/{sequence_folders[i]}.mp4")
        ):
            continue

        # motion npy files
        sequence_dir = os.path.join(data_dir, sequence_folders[i])
        npy_files = [os.path.join(sequence_dir, x) for x in sorted(os.listdir(sequence_dir)) if x.endswith('.npy')]
        
        # temp image saving dir
        temp_dir = tempfile.mkdtemp()
        for smpl_path in tqdm(npy_files):
            rendered_img = render_single_frame(smpl_path)

            # 5. save results
            cv2.imwrite(
                os.path.join(temp_dir, f"{os.path.basename(smpl_path).replace('.npy', '.jpg')}"),
                rendered_img
            )
        
        ffmpeg(args, temp_dir, os.path.basename(sequence_dir))
        shutil.rmtree(temp_dir)