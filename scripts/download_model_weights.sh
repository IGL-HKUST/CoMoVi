#!/bin/bash
set -e

# Default source
SOURCE="modelscope"

# Parse arguments
usage() {
    echo "Usage: $0 [--source modelscope|huggingface]"
    echo ""
    echo "Options:"
    echo "  --source    Download source: 'modelscope' (default) or 'huggingface'"
    exit 1
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --source)
            SOURCE="$2"
            shift 2
            ;;
        -h|--help)
            usage
            ;;
        *)
            echo "Unknown option: $1"
            usage
            ;;
    esac
done

# Validate source
if [[ "$SOURCE" != "modelscope" && "$SOURCE" != "huggingface" ]]; then
    echo "Error: --source must be 'modelscope' or 'huggingface', got '$SOURCE'"
    usage
fi

mkdir -p ./checkpoint/Wan2.2-TI2V-5B

if [[ "$SOURCE" == "modelscope" ]]; then
    echo "Downloading from ModelScope..."
    modelscope download --model Wan-AI/Wan2.2-TI2V-5B --local_dir ./checkpoint/Wan2.2-TI2V-5B/
elif [[ "$SOURCE" == "huggingface" ]]; then
    echo "Downloading from Hugging Face..."
    hf download Wan-AI/Wan2.2-TI2V-5B --local-dir ./checkpoint/Wan2.2-TI2V-5B/
fi

echo "Download complete. Weights saved to ./checkpoint/Wan2.2-TI2V-5B/"
