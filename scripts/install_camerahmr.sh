#!/bin/bash
set -e

PROJECT_ROOT=$(cd "$(dirname "$0")/.." && pwd)
CAMERAHMR_DIR="${PROJECT_ROOT}/prepare/CameraHMR"

# Installation
echo "==> Installing CameraHMR..."
cd ${CAMERAHMR_DIR}
pip install -r requirements.txt
if [ -d "detectron2" ]; then
    echo "detectron2 already exists, removing and re-cloning..."
    rm -rf detectron2
fi
git clone https://github.com/facebookresearch/detectron2.git
cd detectron2 && pip install --no-build-isolation -e . && cd ..
bash scripts/fetch_demo_data.sh
cd ${PROJECT_ROOT}