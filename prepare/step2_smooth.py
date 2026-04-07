import os
import sys
import argparse
import torch
import numpy as np
from glob import glob
from tqdm import tqdm

sys.path.insert(0, "prepare/CameraHMR")
from mesh_estimator import HumanMeshEstimator


def get_all_file_list(args):
    npy_dirs = []; count = 0
        
    for file in tqdm(sorted(os.listdir(os.path.join(args.root_dir, "CameraHMR_smpl_results"))), leave=False):
        file_path = os.path.join(args.root_dir, "CameraHMR_smpl_results", file)
        if not os.path.isdir(file_path):
            continue
        
        if count % args.global_size == args.local_rank:
            npy_dirs.append(file_path)
        count += 1

    return npy_dirs

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--root_dir", type=str, default="./examples/training")
    parser.add_argument("--global_size", type=int, default=1)
    parser.add_argument("--local_rank", type=int, default=0)
    args = parser.parse_args()

    estimator = HumanMeshEstimator(device=torch.device('cpu'))

    sequence_folders = get_all_file_list(args)
    for i in range(len(sequence_folders)):
        sequence_folder = sequence_folders[i]

        target_path = sequence_folder.replace('CameraHMR_smpl_results', 'CameraHMR_smpl_results_smoothed')
        if os.path.exists(target_path):
            continue

        cmd = f"blender --background --python prepare/CameraHMR/scripts/smooth_smpls.py --smpls_group_path {sequence_folder} --smoothed_result_path {os.path.join(sequence_folder, 'smpls_smoothed_group.npz')}"
        os.system(cmd)

        if not os.path.exists(os.path.join(sequence_folder, 'smpls_smoothed_group.npz')):
            continue
        else:
            os.makedirs(target_path, exist_ok=False)
        smpl_result_smoothed = np.load(
            os.path.join(sequence_folder, 'smpls_smoothed_group.npz'),
            allow_pickle=True
        )
        smpl_result_smoothed = {name: smpl_result_smoothed[name] for name in smpl_result_smoothed.files}
        
        smpl_result = {
            "smpl": [],
            "camera": [],
            "render_res": [],
            "scaled_focal_length": []
        }
        smpl_result_fns = sorted(glob(os.path.join(sequence_folder, '*.npy')), key=lambda x: int(x.split('/')[-1].split('.')[0]))
        for frame in smpl_result_fns:
            frame_result = np.load(frame, allow_pickle=True).item()
            smpl_result["camera"].append(frame_result["cam_t"][0])
            smpl_result["render_res"].append(frame_result["render_res"])
            smpl_result["scaled_focal_length"].append(frame_result["scaled_focal_length"])
        
        smpl_result_smoothed["camera"] = smpl_result["camera"]
        smpl_result_smoothed["render_res"] = smpl_result["render_res"]
        smpl_result_smoothed["scaled_focal_length"] = smpl_result["scaled_focal_length"]
        for i in range(len(smpl_result_smoothed["smpl"])):
            frame_result_smoothed = {
                "verts": [None],
                "cam_t": [np.array(smpl_result_smoothed["camera"][i], dtype=np.float32)],
                "render_res": smpl_result_smoothed["render_res"][i],
                "smpls": smpl_result_smoothed["smpl"][i],
                "scaled_focal_length": smpl_result_smoothed["scaled_focal_length"][i]
            }
            smpl_output_smoothed = estimator.smpl_model(**{k: torch.from_numpy(v).float() for k, v in frame_result_smoothed["smpls"].items()})
            frame_result_smoothed["verts"][0] = smpl_output_smoothed.vertices.view(-1, 3).cpu().numpy()
            fname, _ = os.path.splitext(os.path.basename(smpl_result_fns[i]))
            np.save(
                os.path.join(target_path, f"{fname}.npy"),
                frame_result_smoothed
            )
