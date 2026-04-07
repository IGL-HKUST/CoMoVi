import cv2
import numpy as np
import os
from tqdm import tqdm
import argparse
import tempfile
import shutil

def process_video(
    input_path,
    output_path,
    target_frames=81,
    target_fps=16,
    target_width=480,
    target_height=352
):
    # Process image files
    if input_path.endswith(('.jpg', '.jpeg', '.png', '.bmp')):
        if not os.path.exists(input_path):
            return False
        
        img = cv2.imread(input_path)
        if img is None:
            print(f"Cannot open the given image: {input_path}")
            return False
        
        img = adjust_resolution(img, target_width, target_height)
        cv2.imwrite(output_path, img)
        return True

    # Process video files
    try:
        cap = cv2.VideoCapture(input_path)
    
        # Get original video properties
        original_fps = cap.get(cv2.CAP_PROP_FPS)
        original_fps = 30 if original_fps > 30 else original_fps
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        assert total_frames > 0 and total_frames % 150 == 0, f"error: All video data should have 150n frames, but {input_path} has {total_frames} frames."

        # Load all video frames
        all_frames = []
        for _ in tqdm(range(total_frames), desc=f"loading frames from {input_path}...", leave=False):
            ret, frame = cap.read()
            assert ret, f"error: Failed to read frame {_} from {input_path}"
            all_frames.append(adjust_resolution(frame, target_width, target_height))
    except Exception as e:
        print(f"error with {input_path}: {e}")
        return False
    finally:
        cap.release()

    # Uniformly sample 81 frames
    num_points = int((target_fps/original_fps)*total_frames)
    frame_indices = np.linspace(0, total_frames-1, num_points, dtype=np.int32)[:target_frames].tolist()
    assert target_frames - num_points <= 1, f"error: in 16 or 24 fps, {input_path} should be resampled to at least {target_frames-1} frames, but got {num_points} frames."
    if target_frames - num_points == 1:
        frame_indices.append(frame_indices[-1])
        print(f">>> additional frame is appended for {input_path}.")

    # Save the first frame
    if os.path.basename(output_path) == "rgb.mp4":
        first_frame_name = "first_frame.jpg"
    if os.path.basename(output_path) == "motion.mp4":
        first_frame_name = "motion_first_frame.jpg"
    cv2.imwrite(os.path.join(os.path.dirname(output_path), first_frame_name), all_frames[frame_indices[0]])

    # Create temp directory and save all frames in temp directory
    try:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        temp_dir = tempfile.mkdtemp()
        for i in tqdm(range(len(frame_indices)), desc=f"saving frames to temp directory: {os.path.basename(input_path)}", leave=False):
            idx = frame_indices[i]
            cv2.imwrite(os.path.join(temp_dir, f"{i:06d}.jpg"), all_frames[idx])
        
        ffmpeg_cmd = f"ffmpeg -framerate {target_fps} -i {os.path.join(temp_dir, '%06d.jpg')} -vf \"format=yuv420p,scale=iw:ih:flags=lanczos\" -c:v libx264 -preset veryslow -crf 18 -pix_fmt yuv420p -movflags +faststart -loglevel error -y {output_path}"
        os.system(ffmpeg_cmd)
    except Exception as e:
        print(f"error with {input_path}: {e}")
        return False
    finally:
        shutil.rmtree(temp_dir)

    return True

def adjust_resolution(frame, target_width, target_height):
    # Get raw resolution
    h, w = frame.shape[:2]
    target_aspect = target_width / target_height
    original_aspect = w / h

    if original_aspect < target_aspect:
        new_width = target_width
        new_height = int(target_width / original_aspect)
    else:
        new_height = target_height
        new_width = int(target_height * original_aspect)

    # Scale
    resized = cv2.resize(frame, (new_width, new_height))
    resized_center_x = new_width // 2
    resized_center_y = new_height // 2

    resized = resized[
        resized_center_y - min(new_height, target_height)//2 : resized_center_y + min(new_height, target_height)//2,
        resized_center_x - min(new_width, target_width)//2 : resized_center_x + min(new_width, target_width)//2
    ]
    new_height, new_width = resized.shape[:2]
    
    canvas = np.zeros((target_height, target_width, 3), dtype=np.uint8)
    canvas_center_x = target_width // 2
    canvas_center_y = target_height // 2
    canvas[canvas_center_y-new_height//2:canvas_center_y+new_height//2, canvas_center_x-new_width//2:canvas_center_x+new_width//2] = resized
    
    return canvas

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--root_dir", type=str, default="./examples/training")
    parser.add_argument("--target_fps", type=int, default=16) 
    parser.add_argument("--target_frames", type=int, default=81) 
    parser.add_argument("--target_width", type=int, default=1280)
    parser.add_argument("--target_height", type=int, default=704)
    args = parser.parse_args()
    assert args.target_frames > 0 and args.target_frames % 8 == 1, "Target frames must be greater than 0 and divisible by 8 with a remainder of 1."
    assert args.target_width % 16 == 0 and args.target_height % 16 == 0, "Target width and height must be divisible by 16."

    TARGET_FPS = args.target_fps
    TARGET_FRAMES = args.target_frames
    TARGET_WIDTH = args.target_width
    TARGET_HEIGHT = args.target_height
    print("preparing data in config:")
    print(f">>> fps: {TARGET_FPS}")
    print(f">>> frames: {TARGET_FRAMES}")
    print(f">>> width: {TARGET_WIDTH}")
    print(f">>> length: {TARGET_HEIGHT}")

    # make output directory
    output_dir = os.path.join(args.root_dir, "processed_trainable_data")

    # get file paths
    valid_extensions = ('.mp4', '.avi', '.mov', '.mkv')
    rgb_dir = os.path.join(args.root_dir, "rgb_videos")
    motion_dir = os.path.join(args.root_dir, "motion_2d_videos")
    rgb_files = [os.path.join(rgb_dir, f) for f in sorted(os.listdir(rgb_dir))]
    motion_files = [os.path.join(motion_dir, f) for f in sorted(os.listdir(motion_dir))]

    # process each video files
    for file in rgb_files:
        data_name = os.path.basename(file).split(".")[0]
        output_path = os.path.join(output_dir, data_name, "rgb.mp4")
        process_video(
            file, 
            output_path,
            target_frames=TARGET_FRAMES,
            target_fps=TARGET_FPS,
            target_width=TARGET_WIDTH,
            target_height=TARGET_HEIGHT
        )


    for file in motion_files:
        data_name = os.path.basename(file).split(".")[0]
        output_path = os.path.join(output_dir, data_name, "motion.mp4")
        process_video(
            file, 
            output_path,
            target_frames=TARGET_FRAMES,
            target_fps=TARGET_FPS,
            target_width=TARGET_WIDTH,
            target_height=TARGET_HEIGHT
        )