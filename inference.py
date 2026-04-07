import os
import sys
import argparse
import cv2

import torch
from diffusers import FlowMatchEulerDiscreteScheduler
from safetensors.torch import load_file
from omegaconf import OmegaConf

current_file_path = os.path.abspath(__file__)
project_roots = [os.path.dirname(current_file_path), os.path.dirname(os.path.dirname(current_file_path)), os.path.dirname(os.path.dirname(os.path.dirname(current_file_path)))]
for project_root in project_roots:
    sys.path.insert(0, project_root) if project_root not in sys.path else None

from comovi.dist import set_multi_gpus_devices, shard_model
from comovi.models import (
    AutoencoderKLWan3_8,
    AutoencoderKLWan,
    WanT5EncoderModel,
    AutoTokenizer,
    Wan2_2Transformer3DModel,
    ComoviTransformer3DModel
)
from comovi.models.cache_utils import get_teacache_coefficients
from comovi.pipeline import ComoviPipeline
from comovi.utils.fp8_optimization import (
    convert_model_weight_to_float8,
    replace_parameters_by_name,
    convert_weight_dtype_wrapper
)
from comovi.utils.lora_utils import merge_lora, unmerge_lora
from comovi.utils.utils import (
    filter_kwargs,
    get_image_to_video_latent,
    get_smpl_init_pose,
    save_videos_grid
)
from comovi.utils.fm_solvers import FlowDPMSolverMultistepScheduler
from comovi.utils.fm_solvers_unipc import FlowUniPCMultistepScheduler

os.environ["TOKENIZERS_PARALLELISM"] = "false"

def prepare(img_path, threshold=0.25):
    sys.path.insert(0, "prepare/CameraHMR")
    from mesh_estimator import HumanMeshEstimator
    from prepare.step3_render_2d_morep import render_single_frame

    img_dir = os.path.dirname(img_path)
    npy_path = os.path.join(img_dir, "first_frame.npy")
    estimator = HumanMeshEstimator(threshold=threshold)
    estimator.process_image(img_path, img_dir, img_dir)
    motion_2d = render_single_frame(npy_path)
    cv2.imwrite(os.path.join(img_dir, "motion_first_frame.jpg"), motion_2d)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--arch", type=str, default="Wan2.2-TI2V-5B")
    parser.add_argument("--fps", type=int, default=16)
    parser.add_argument("--frames", type=int, default=81)
    parser.add_argument("--height", type=int, default=480)
    parser.add_argument("--width", type=int, default=832)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--motion_type", type=str, default="smpl", choices=["smpl", "dwpose"])
    parser.add_argument("--interaction", type=str, default="dual", choices=["dual", "single_m2v", "single_v2m", "none"])
    parser.add_argument("--interleave", type=int, default=1)
    parser.add_argument("--predict_smpl", action="store_true", help="predict smpl or not")
    parser.add_argument("--use_pretrained_model", action="store_true", help="use pretrained model")
    parser.add_argument("--dtype", type=str, choices=["float16", "bfloat16"], default="bfloat16")
    parser.add_argument("--save_mode", type=str, default="merge", choices=["merge", "separate"])
    parser.add_argument("--quality", type=int, default=5)
    args = parser.parse_args()

    # Input & Output
    inference_data_dir      = "examples/inference/"
    rgb_image_start         = os.path.join(inference_data_dir, "first_frame.jpg")
    prepare(rgb_image_start)
    
    motion_image_start      = os.path.join(inference_data_dir, "motion_first_frame.jpg")
    init_pose_npz_file      = os.path.join(inference_data_dir, "first_frame.npy")
    prompt                  = "A woman in blue yoga attire transitions from the Upward-Facing Dog pose to the Downward-Facing Dog pose on a grey yoga mat."
    negative_prompt         = "色调艳丽，过曝，静态，细节模糊不清，字幕，风格，作品，画作，画面，静止，整体发灰，最差质量，低质量，JPEG压缩残留，丑陋的，残缺的，多余的手指，画得不好的手部，画得不好的脸部，畸形的，毁容的，形态畸形的肢体，手指融合，静止不动的画面，杂乱的背景，三条腿，背景人很多，倒着走"

    # model configuration
    config_path             = "config/wan2.2/wan_civitai_5b.yaml"
    model_name              = "checkpoint/Wan2.2-TI2V-5B"
    transformer_path        = "checkpoint/CoMoVi/diffusion_pytorch_model.safetensors"
    transformer_high_path   = None
    vae_path                = None
    lora_path               = None
    lora_high_path          = None
    config                  = OmegaConf.load(config_path)
    boundary                = config['transformer_additional_kwargs'].get('boundary', 0.875)

    # GPU configuration
    GPU_memory_mode         = "sequential_cpu_offload"
    ulysses_degree          = 1
    ring_degree             = 1
    fsdp_dit                = False
    fsdp_text_encoder       = False
    compile_dit             = False
    device                  = set_multi_gpus_devices(ulysses_degree, ring_degree)

    # denoising configuration
    weight_dtype            = torch.bfloat16 if args.dtype == "bfloat16" else torch.float16
    guidance_scale          = 6.0
    seed                    = 42
    num_inference_steps     = 50
    lora_weight             = 0.55
    lora_high_weight        = 0.55
    cfg_skip_ratio          = 0

    # video configuration
    sample_size             = [args.height, args.width]
    video_length            = args.frames
    fps                     = args.fps

    # Riflex configuration
    enable_riflex           = False
    riflex_k                = 6

    # sampler configuration
    sampler_name            = "Flow_Unipc"
    shift                   = 5

    # TeaCache configuration (never used)
    enable_teacache         = False
    teacache_threshold      = 0.10
    num_skip_start_steps    = 5
    teacache_offload        = False

    # Get video diffusion transformer
    transformer = ComoviTransformer3DModel.from_pretrained(
        os.path.join(model_name, config['transformer_additional_kwargs'].get('transformer_low_noise_model_subpath', 'transformer')),
        transformer_additional_kwargs=OmegaConf.to_container(config['transformer_additional_kwargs']),
        low_cpu_mem_usage=False,
        torch_dtype=weight_dtype,
        interaction=args.interaction,
        interleave=args.interleave,
        predict_smpl=args.predict_smpl
    )
    if config['transformer_additional_kwargs'].get('transformer_combination_type', 'single') == "moe":
        transformer_2 = Wan2_2Transformer3DModel.from_pretrained(
            os.path.join(model_name, config['transformer_additional_kwargs'].get('transformer_high_noise_model_subpath', 'transformer')),
            transformer_additional_kwargs=OmegaConf.to_container(config['transformer_additional_kwargs']),
            low_cpu_mem_usage=True,
            torch_dtype=weight_dtype,
        )
    else:
        transformer_2 = None

    if transformer_path is not None:
        if transformer_path.endswith("safetensors"):
            state_dict = load_file(transformer_path)
        else:
            state_dict = torch.load(transformer_path, map_location="cpu", weights_only=True)
        state_dict = state_dict["state_dict"] if "state_dict" in state_dict else state_dict

        m, u = transformer.load_state_dict(state_dict, strict=False)
        print(f"missing keys: {len(m)}, unexpected keys: {len(u)}")
    transformer = transformer.eval()

    if transformer_2 is not None:
        if transformer_high_path is not None:
            print(f"From checkpoint: {transformer_high_path}")
            if transformer_high_path.endswith("safetensors"):
                state_dict = load_file(transformer_high_path)
            else:
                state_dict = torch.load(transformer_high_path, map_location="cpu", weights_only=True)
            state_dict = state_dict["state_dict"] if "state_dict" in state_dict else state_dict

            m, u = transformer_2.load_state_dict(state_dict, strict=False)
            print(f"missing keys: {len(m)}, unexpected keys: {len(u)}")

    # Get video vae
    Chosen_AutoencoderKL = {
        "AutoencoderKLWan": AutoencoderKLWan,
        "AutoencoderKLWan3_8": AutoencoderKLWan3_8
    }[config['vae_kwargs'].get('vae_type', 'AutoencoderKLWan')]
    vae = Chosen_AutoencoderKL.from_pretrained(
        os.path.join(model_name, config['vae_kwargs'].get('vae_subpath', 'vae')),
        additional_kwargs=OmegaConf.to_container(config['vae_kwargs']),
    ).to(weight_dtype)

    if vae_path is not None:
        print(f"From checkpoint: {vae_path}")
        if vae_path.endswith("safetensors"):
            from safetensors.torch import load_file, safe_open
            state_dict = load_file(vae_path)
        else:
            state_dict = torch.load(vae_path, map_location="cpu", weights_only=True)
        state_dict = state_dict["state_dict"] if "state_dict" in state_dict else state_dict

        m, u = vae.load_state_dict(state_dict, strict=False)
        print(f"missing keys: {len(m)}, unexpected keys: {len(u)}")
    vae = vae.eval()

    # Get tokenizer
    tokenizer = AutoTokenizer.from_pretrained(
        os.path.join(model_name, config['text_encoder_kwargs'].get('tokenizer_subpath', 'tokenizer')),
    )

    # Get text encoder
    text_encoder = WanT5EncoderModel.from_pretrained(
        os.path.join(model_name, config['text_encoder_kwargs'].get('text_encoder_subpath', 'text_encoder')),
        additional_kwargs=OmegaConf.to_container(config['text_encoder_kwargs']),
        low_cpu_mem_usage=True,
        torch_dtype=weight_dtype,
    )
    text_encoder = text_encoder.eval()

    # Get noise scheduler
    Chosen_Scheduler = scheduler_dict = {
        "Flow": FlowMatchEulerDiscreteScheduler,
        "Flow_Unipc": FlowUniPCMultistepScheduler,
        "Flow_DPM++": FlowDPMSolverMultistepScheduler,
    }[sampler_name]
    if sampler_name == "Flow_Unipc" or sampler_name == "Flow_DPM++":
        config['scheduler_kwargs']['shift'] = 1
    scheduler = Chosen_Scheduler(
        **filter_kwargs(Chosen_Scheduler, OmegaConf.to_container(config['scheduler_kwargs']))
    )

    # Get Pipeline
    pipeline = ComoviPipeline(
        transformer=transformer,
        transformer_2=transformer_2,
        vae=vae,
        tokenizer=tokenizer,
        text_encoder=text_encoder,
        scheduler=scheduler,
    )
    if ulysses_degree > 1 or ring_degree > 1:
        from functools import partial
        transformer.enable_multi_gpus_inference()
        if transformer_2 is not None:
            transformer_2.enable_multi_gpus_inference()
        if fsdp_dit:
            shard_fn = partial(shard_model, device_id=device, param_dtype=weight_dtype)
            pipeline.transformer = shard_fn(pipeline.transformer)
            if transformer_2 is not None:
                pipeline.transformer_2 = shard_fn(pipeline.transformer_2)
            print("Add FSDP DIT")
        if fsdp_text_encoder:
            shard_fn = partial(shard_model, device_id=device, param_dtype=weight_dtype)
            pipeline.text_encoder = shard_fn(pipeline.text_encoder)
            print("Add FSDP TEXT ENCODER")

    if compile_dit:
        for i in range(len(pipeline.transformer.blocks)):
            pipeline.transformer.blocks[i] = torch.compile(pipeline.transformer.blocks[i])
        if transformer_2 is not None:
            for i in range(len(pipeline.transformer_2.blocks)):
                pipeline.transformer_2.blocks[i] = torch.compile(pipeline.transformer_2.blocks[i])
        print("Add Compile")

    if GPU_memory_mode == "sequential_cpu_offload":
        replace_parameters_by_name(transformer, ["modulation",], device=device)
        transformer.freqs = transformer.freqs.to(device=device)
        if transformer_2 is not None:
            replace_parameters_by_name(transformer_2, ["modulation",], device=device)
            transformer_2.freqs = transformer_2.freqs.to(device=device)
        pipeline.enable_sequential_cpu_offload(device=device)
    elif GPU_memory_mode == "model_cpu_offload_and_qfloat8":
        convert_model_weight_to_float8(transformer, exclude_module_name=["modulation",], device=device)
        convert_weight_dtype_wrapper(transformer, weight_dtype)
        if transformer_2 is not None:
            convert_model_weight_to_float8(transformer_2, exclude_module_name=["modulation",], device=device)
            convert_weight_dtype_wrapper(transformer_2, weight_dtype)
        pipeline.enable_model_cpu_offload(device=device)
    elif GPU_memory_mode == "model_cpu_offload":
        pipeline.enable_model_cpu_offload(device=device)
    elif GPU_memory_mode == "model_full_load_and_qfloat8":
        convert_model_weight_to_float8(transformer, exclude_module_name=["modulation",], device=device)
        convert_weight_dtype_wrapper(transformer, weight_dtype)
        if transformer_2 is not None:
            convert_model_weight_to_float8(transformer_2, exclude_module_name=["modulation",], device=device)
            convert_weight_dtype_wrapper(transformer_2, weight_dtype)
        pipeline.to(device=device)
    else:
        pipeline.to(device=device)

    # Teacache config
    coefficients = get_teacache_coefficients(model_name) if enable_teacache else None
    if coefficients is not None:
        print(f"Enable TeaCache with threshold {teacache_threshold} and skip the first {num_skip_start_steps} steps.")
        pipeline.transformer.enable_teacache(
            coefficients, num_inference_steps, teacache_threshold, num_skip_start_steps=num_skip_start_steps, offload=teacache_offload
        )
        if transformer_2 is not None:
            pipeline.transformer_2.share_teacache(transformer=pipeline.transformer)

    if cfg_skip_ratio is not None:
        print(f"Enable cfg_skip_ratio {cfg_skip_ratio}.")
        pipeline.transformer.enable_cfg_skip(cfg_skip_ratio, num_inference_steps)
        if transformer_2 is not None:
            pipeline.transformer_2.share_cfg_skip(transformer=pipeline.transformer)

    generator = torch.Generator(device=device).manual_seed(seed)

    if lora_path is not None:
        pipeline = merge_lora(pipeline, lora_path, lora_weight, device=device, dtype=weight_dtype)
        if transformer_2 is not None:
            pipeline = merge_lora(pipeline, lora_high_path, lora_high_weight, device=device, dtype=weight_dtype, sub_transformer_name="transformer_2")


    # Run inference
    with torch.no_grad():
        video_length = int((video_length - 1) // vae.config.temporal_compression_ratio * vae.config.temporal_compression_ratio) + 1 if video_length != 1 else 1
        latent_frames = (video_length - 1) // vae.config.temporal_compression_ratio + 1

        if enable_riflex:
            pipeline.transformer.enable_riflex(k = riflex_k, L_test = latent_frames)
            if transformer_2 is not None:
                pipeline.transformer_2.enable_riflex(k = riflex_k, L_test = latent_frames)

        rgb_input_video, video_mask, _ = get_image_to_video_latent(
            rgb_image_start,
            None,
            video_length=video_length,
            sample_size=sample_size
        )
        motion_input_video, _, _ = get_image_to_video_latent(
            motion_image_start,
            None,
            video_length=video_length,
            sample_size=sample_size
        )
        if args.predict_smpl:
            init_pose, init_shape = get_smpl_init_pose(init_pose_npz_file)
        else:
            init_pose, init_shape = None, None

        sample, smpl_pred = pipeline(
            prompt, 
            num_frames          = video_length,
            negative_prompt     = negative_prompt,
            height              = sample_size[0],
            width               = sample_size[1],
            generator           = generator,
            guidance_scale      = guidance_scale,
            num_inference_steps = num_inference_steps,
            boundary            = boundary,

            video               = [rgb_input_video, motion_input_video],
            mask_video          = video_mask,
            shift               = shift,
            predict_smpl        = args.predict_smpl,
            init_smpl           = init_pose
        )
        sample = [x.videos for x in sample]

    if lora_path is not None:
        pipeline = unmerge_lora(pipeline, lora_path, lora_weight, device=device, dtype=weight_dtype)
        if transformer_2 is not None:
            pipeline = unmerge_lora(pipeline, lora_high_path, lora_high_weight, device=device, dtype=weight_dtype, sub_transformer_name="transformer_2")

    # Save generated videos
    # Default quality of video saving is 5, evaluation uses 10 for all methods
    if args.save_mode == "merge":
        save_videos_grid(sample, os.path.join(inference_data_dir, "example_output.mp4"), fps=fps, quality=args.quality)
    elif args.save_mode == "separate":
        save_videos_grid([sample[0]], os.path.join(inference_data_dir, "example_output_rgb.mp4"), fps=fps, quality=args.quality)
        save_videos_grid([sample[1]], os.path.join(inference_data_dir, "example_output_motion.mp4"), fps=fps, quality=args.quality)