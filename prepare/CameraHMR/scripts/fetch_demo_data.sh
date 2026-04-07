#!/bin/bash
urle () { [[ "${1}" ]] || return 1; local LANG=C i x; for (( i = 0; i < ${#1}; i++ )); do x="${1:i:1}"; [[ "${x}" == [a-zA-Z0-9.~-] ]] && echo -n "${x}" || printf '%%%02X' "'${x}"; done; echo; }




# CameraHMR
echo -e "\nYou need to register at https://camerahmr.is.tue.mpg.de/"
read -p "Username (CameraHMR):" username
read -p "Password (CameraHMR):" password
username=$(urle $username)
password=$(urle $password)

mkdir -p data/models/SMPL
wget --post-data "username=$username&password=$password" 'https://download.is.tue.mpg.de/download.php?domain=camerahmr&sfile=SMPL_NEUTRAL.pkl' -O './data/models/SMPL/SMPL_NEUTRAL.pkl' --no-check-certificate --continue

mkdir -p data/pretrained-models
wget --post-data "username=$username&password=$password" 'https://download.is.tue.mpg.de/download.php?domain=camerahmr&sfile=cam_model_cleaned.ckpt' -O './data/pretrained-models/cam_model_cleaned.ckpt' --no-check-certificate --continue
wget --post-data "username=$username&password=$password" 'https://download.is.tue.mpg.de/download.php?domain=camerahmr&sfile=camerahmr_checkpoint_cleaned.ckpt' -O './data/pretrained-models/camerahmr_checkpoint_cleaned.ckpt' --no-check-certificate --continue
wget --post-data "username=$username&password=$password" 'https://download.is.tue.mpg.de/download.php?domain=camerahmr&sfile=model_final_f05665.pkl' -O './data/pretrained-models/model_final_f05665.pkl' --no-check-certificate --continue
wget --post-data "username=$username&password=$password" 'https://download.is.tue.mpg.de/download.php?domain=camerahmr&sfile=smpl_mean_params.npz' -O './data/smpl_mean_params.npz' --no-check-certificate --continue
