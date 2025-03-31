FROM nvidia/cuda:12.1.1-cudnn8-runtime-ubuntu22.04

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-dev \
    ffmpeg \
    git \
    wget \
    unzip \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgl1-mesa-glx \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create a working directory
WORKDIR /app

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip3 install --no-cache-dir -r requirements.txt
RUN pip3 install torch==2.1.0+cu121 torchvision==0.16.0+cu121 --extra-index-url https://download.pytorch.org/whl/cu121

# Install additional packages for L4 optimization
RUN pip3 install --no-cache-dir \
    xformers==0.0.23 \
    triton==2.1.0 \
    einops>=0.7.0

# Download the Wan 2.1 model (will be mounted via volume instead, to save container size)
RUN mkdir -p /app/models

# Set default env vars for GPU performance
# These will be overridden based on detected GPU type in entrypoint.sh
ENV CUDA_VISIBLE_DEVICES=0
ENV PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb=256
ENV CUDA_MODULE_LOADING=LAZY

# Create directories for output and content
RUN mkdir -p /app/output /app/logs /app/content

# Set environment variables for GPU
ENV NVIDIA_VISIBLE_DEVICES=all
ENV NVIDIA_DRIVER_CAPABILITIES=compute,utility
ENV TORCH_CUDNN_V8_API_ENABLED=1

# Create an entrypoint script
COPY entrypoint.sh /app/
RUN chmod +x /app/entrypoint.sh

ENTRYPOINT ["/app/entrypoint.sh"]