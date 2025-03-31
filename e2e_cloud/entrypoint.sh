#!/bin/bash

# Print NVIDIA GPU information
echo "NVIDIA GPU Information:"
nvidia-smi

# Copy the code to the working directory if mounted via volume
if [ -d "/workspace/code" ]; then
    cp -r /workspace/code/* /app/
    echo "Code copied from /workspace/code to /app"
fi

# Download Wan 2.1 model if not already downloaded
MODEL_DIR="/app/models/Wan2.1-T2V-14B"
if [ ! -d "$MODEL_DIR" ] || [ -z "$(ls -A $MODEL_DIR)" ]; then
    echo "Downloading Wan 2.1 T2V-14B model..."
    # Using huggingface-cli for more reliable download
    if command -v huggingface-cli &> /dev/null; then
        huggingface-cli download Wan-AI/Wan2.1-T2V-14B --local-dir $MODEL_DIR
    else
        pip install -q "huggingface_hub[cli]"
        huggingface-cli download Wan-AI/Wan2.1-T2V-14B --local-dir $MODEL_DIR
    fi
    echo "Wan 2.1 model downloaded to $MODEL_DIR"
else
    echo "Wan 2.1 model already exists at $MODEL_DIR"
fi

# Set up avatar-specific output directories
mkdir -p /app/output/videos/by_avatar
mkdir -p /app/output/raw
mkdir -p /app/output/processed

# Configure CUDA for optimal performance on L4 GPU
echo "Detecting and configuring environment for optimal GPU performance..."
export CUDA_VISIBLE_DEVICES=0

# Auto-detect GPU type
GPU_TYPE="T4"
GPU_INFO=$(nvidia-smi --query-gpu=name,memory.total --format=csv,noheader)
echo "Detected GPU: $GPU_INFO"

if [[ $GPU_INFO == *"L4"* ]] || [[ $GPU_INFO == *"24"*"MiB"* ]]; then
    echo "Confirmed NVIDIA L4 GPU, applying optimal settings"
    GPU_TYPE="L4"
    # L4 has 24GB VRAM, so we can use higher memory settings
    export PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:256
    # Higher batch size for L4 GPU
    export BATCH_SIZE_OVERRIDE=5
    # Default to 720p resolution for L4
    RESOLUTION="720p"
else
    echo "Using T4-compatible settings"
    GPU_TYPE="T4"
    # Conservative memory settings for T4
    export PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:128
    # Standard batch size for T4
    export BATCH_SIZE_OVERRIDE=3
    # Default to 480p resolution for T4
    RESOLUTION="480p"
fi

# Run the generation script by default if present
if [ -f "/app/run_generation.py" ]; then
    echo "Starting video generation with Wan 2.1 model on $GPU_TYPE GPU..."
    # Pass GPU-specific parameters to the generation script
    python3 /app/run_generation.py --model_dir $MODEL_DIR --gpu-type $GPU_TYPE --resolution $RESOLUTION --max-batch $BATCH_SIZE_OVERRIDE
elif [ $# -gt 0 ]; then
    # Execute the command if provided
    echo "Executing command: $@"
    exec "$@"
else
    # Start a shell by default
    echo "No specific command provided. Starting bash shell..."
    exec /bin/bash
fi