#!/bin/bash
set -e

# stage-1: full parameter fine-tuning
export MODEL_NAME="checkpoint/Wan2.2-TI2V-5B"
export DATASET_NAME="examples/training/processed_trainable_data"
export DATASET_META_NAME="config/data/example_training.json"
# NCCL_IB_DISABLE=1 and NCCL_P2P_DISABLE=1 are used in multi nodes without RDMA. 
# export NCCL_IB_DISABLE=1
# export NCCL_P2P_DISABLE=1
NCCL_DEBUG=INFO

GPU_NUM=$1
MACHINE_NUM=$2
LOCAL_RANK=$3
GPU_IDS=$4
MAIN_MACHINE_IP=$5

CUDA_VISIBLE_DEVICES=$GPU_IDS accelerate launch --zero_stage 3 --zero3_save_16bit_model true --zero3_init_flag true --use_deepspeed --deepspeed_config_file config/zero_stage3_config_cpu_offload.json --deepspeed_multinode_launcher standard --num_processes $GPU_NUM --num_machines $MACHINE_NUM --machine_rank $LOCAL_RANK --gpu_ids $GPU_IDS --main_process_ip $MAIN_MACHINE_IP train.py \
  --config_path="config/wan2.2/wan_civitai_5b.yaml" \
  --pretrained_model_name_or_path=$MODEL_NAME \
  --train_data_dir=$DATASET_NAME \
  --train_data_meta=$DATASET_META_NAME \
  --image_sample_size=1024 \
  --video_sample_size=256 \
  --token_sample_size=512 \
  --video_sample_stride=2 \
  --video_sample_n_frames=81 \
  --train_batch_size=1 \
  --video_repeat=1 \
  --gradient_accumulation_steps=4 \
  --dataloader_num_workers=4 \
  --num_train_epochs=10000 \
  --checkpointing_steps=100 \
  --checkpoints_total_limit=10 \
  --learning_rate=2e-05 \
  --lr_scheduler="constant_with_warmup" \
  --lr_warmup_steps=100 \
  --seed=42 \
  --output_dir="output_dir" \
  --gradient_checkpointing \
  --mixed_precision="bf16" \
  --adam_weight_decay=3e-2 \
  --adam_epsilon=1e-10 \
  --vae_mini_batch=1 \
  --max_grad_norm=0.5 \
  --random_hw_adapt \
  --training_with_video_token_length \
  --enable_bucket \
  --uniform_sampling \
  --low_vram \
  --boundary_type="full" \
  --train_mode="ti2v" \
  --motion_type="smpl" \
  --interaction="single_m2v" \
  --interleave=1 \
  --require_grad_modules "rgb" "motion" "zero" \
  --trainable_modules "motion" "zero" \
  --trainable_modules_low_learning_rate "rgb" \
  --allow_missisng_modules "zero" \
  --rgb_loss_weight=1 \
  --motion_loss_weight=1 \
  --tracker_project_name="example_experiment_stage2" \
  --resume_from_checkpoint "latest"