import os
import sys
import argparse
import tempfile
import shutil
import cv2

sys.path.insert(0, "prepare/CameraHMR")
from mesh_estimator import HumanMeshEstimator

def extract_images(video_path):
    temp_dir = tempfile.mkdtemp()
    try:
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise RuntimeError(f"Video cannot be opened: {video_path}")

        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        cap.release()
        
        cmd = f"ffmpeg -i {video_path} -qscale:v 2 -f image2 -v error -start_number 0 -threads 64 {temp_dir}/%06d.jpg"
        os.system(cmd)
    except Exception as e:
        shutil.rmtree(temp_dir)
        temp_dir = None
    
    return temp_dir
        

def get_all_file_list(args):
    mp4_files = []; count = 0
        
    for file in sorted(os.listdir(os.path.join(args.root_dir, "rgb_videos"))):
        if not file.endswith('.mp4'):
            continue
        
        if count % args.global_size == args.local_rank:
            mp4_files.append(os.path.join(args.root_dir, "rgb_videos", file))
        count += 1
    
    return mp4_files

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--root_dir", type=str, default="./examples/training")
    parser.add_argument("--threshold", type=float, default=0.25)
    parser.add_argument("--global_size", type=int, default=1)
    parser.add_argument("--local_rank", type=int, default=0)
    args = parser.parse_args()

    estimator = HumanMeshEstimator(threshold=args.threshold)

    image_folders = get_all_file_list(args)
    for i in range(len(image_folders)):
        image_folder = image_folders[i]
        output_smpl_dir = os.path.join(
            args.root_dir,
            "CameraHMR_smpl_results",
            os.path.basename(image_folder).replace(".mp4", "")
        )
        output_overlay_dir = os.path.join(
            args.root_dir,
            "CameraHMR_smpl_results_overlay",
            os.path.basename(image_folder).replace(".mp4", "")
        )

        # check already processed
        if os.path.exists(output_smpl_dir):
            continue
        
        # extract images from video
        temp_dir = extract_images(image_folder)
        if temp_dir is None:
            continue

        estimator.run_on_images(
            temp_dir,
            output_smpl_dir,
            output_overlay_dir
        )

        shutil.rmtree(temp_dir)