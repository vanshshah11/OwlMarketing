# E2E Cloud Setup for OWLmarketing with Wan 2.1 T2V Model

This directory contains the necessary files and instructions for using E2E Cloud with NVIDIA GPUs (T4 or L4) to accelerate the OWLmarketing video generation process using the Wan 2.1 Text-to-Video model. This setup provides high-quality video generation with organized output and optimized resource usage.

## Overview

The workflow is designed to:

1. Generate and prepare video generation scripts on your local machine
2. Package scripts, code, and configuration files for E2E Cloud
3. Process the scripts using Wan 2.1 T2V model on E2E Cloud's GPU (L4 preferred for higher quality)
4. Organize generated videos by avatar for easy management
5. Optimize resource usage to minimize cloud GPU costs

## Requirements

- E2E Cloud account with access to GPU instances (L4 recommended, T4 supported)
- Python 3.8+ on your local machine
- Basic knowledge of Docker and command-line operations

## Setup Instructions

### 1. E2E Cloud Account Setup

1. Sign up for an E2E Cloud account
2. Set up billing information
3. Familiarize yourself with the E2E Cloud dashboard and pricing
4. Ensure you have access to NVIDIA L4 GPU instances (recommended) or T4 instances

### 2. Local Environment Setup

Ensure you have the necessary packages installed on your local machine:

```bash
# From the project root directory
pip install -r requirements.txt
```

### 3. Preparing Data for E2E Cloud

Use the provided script to prepare your data, with scripts organized by avatar for better GPU utilization:

```bash
# Generate data package for E2E Cloud with scripts grouped by avatar
python e2e_cloud/prepare_data.py --output-dir ./e2e_data --scripts 6 --create-zip --group-by-avatar
```

This will:
- Generate 6 video scripts organized by avatar
- Prepare all necessary code files including Wan 2.1 integration
- Create a zip file ready for upload to E2E Cloud

### 4. Setting Up E2E Cloud Instance

1. Create a new instance on E2E Cloud:
   - Choose the NVIDIA L4 GPU option for best quality/performance (T4 is also supported)
   - Select an Ubuntu 20.04 image with CUDA 11.8+ support
   - Allocate at least 50GB disk space

2. Upload the prepared zip file to your E2E Cloud instance:
   ```bash
   # Using scp (replace with your instance's IP and credentials)
   scp ./e2e_cloud_data_TIMESTAMP.zip username@instance-ip:/home/username/
   ```

3. SSH into your instance and extract the files:
   ```bash
   ssh username@instance-ip
   unzip e2e_cloud_data_TIMESTAMP.zip -d e2e_data
   cd e2e_data
   ```

### 5. Building and Running the Docker Container

1. Download the Wan 2.1 model (if not already available):
   ```bash
   # Run the model download script
   ./download_model.sh
   ```

2. Build the Docker container:
   ```bash
   docker build -t owlmarketing:wan21 -f Dockerfile .
   ```

3. Run the container with GPU access:
   ```bash
   docker run --gpus all -v $(pwd):/workspace -v $(pwd)/output:/app/output -v $(pwd)/models:/app/models owlmarketing:wan21
   ```

   This command:
   - Mounts your current directory as `/workspace`
   - Mounts the output directory for saving generated videos
   - Mounts the models directory to avoid re-downloading the model

### 6. Monitoring Progress and Resource Usage

You can monitor the progress and resource usage:

```bash
# Check container ID
docker ps

# View logs in real-time
docker logs -f CONTAINER_ID

# Monitor GPU usage
nvidia-smi -l 5  # Updates every 5 seconds
```

The generation process is optimized to:
- Process videos in batches to maximize GPU utilization
- Clear GPU memory between batches to avoid CUDA out-of-memory errors
- Organize output videos by avatar

### 7. Accessing Organized Output

Once processing completes, the videos will be organized in the following structure:

```
output/
├── avatars/             # Raw avatar videos
│   ├── emma/
│   ├── sophia/
│   └── ...
├── ui_demos/            # UI demonstration videos
├── videos/              # Final combined videos
│   ├── by_avatar/       # Organized by avatar
│   │   ├── emma/
│   │   ├── sophia/
│   │   └── ...
└── generation_summary.json  # Summary of all generated videos
```

This organization makes it easy to manage videos for your social media posting schedule.

### 8. Downloading Generated Videos

Download the organized videos back to your local machine:

```bash
# From your local machine
mkdir -p ./generated_videos
scp -r username@instance-ip:/home/username/e2e_data/output ./generated_videos
```

## Cost Optimization for E2E Cloud

The E2E Cloud setup is optimized to minimize costs while maximizing quality:

1. **GPU Selection**: 
   - L4 GPU (24GB VRAM): Optimal for high-quality 720p/1080p generation
   - T4 GPU (16GB VRAM): Budget-friendly option for 480p/720p generation

2. **Batch Processing**: Videos are processed in optimal batch sizes based on GPU type:
   - L4: Up to 5 videos per batch
   - T4: Up to 3 videos per batch

3. **Resource Management**:
   - GPU memory is cleared between batches
   - FP16 precision is used when possible
   - Model parameters are automatically optimized for your GPU

### Recommended Workflow for Cost Efficiency:

1. Generate a larger batch of scripts (e.g., 10-20)
2. Process them in a single E2E Cloud session
3. Shut down the instance immediately after completion
4. Use the generated videos over a longer period

This approach maximizes GPU utilization while minimizing the hourly costs.

## Wan 2.1 T2V-14B Model

This setup uses the Wan 2.1 T2V-14B model, which provides several advantages:

- Higher video quality than previous models like SDXL
- Better motion consistency and temporal coherence
- Supports multiple resolutions:
  - 1080p (1920x1080) - L4 GPU only
  - 720p (1280x720) - Both L4 and T4
  - 480p (832x480) - Both L4 and T4, recommended for T4
- Produces more realistic avatar animations

The model is automatically downloaded during container startup if not already present.

## Performance Tuning

The configuration is automatically optimized based on your GPU type:

### L4 GPU Settings (24GB VRAM)
```json
{
  "wan_model": {
    "resolution": "720p",        // Can use up to 1080p
    "sample_steps": 30-35,       // Higher for better quality
    "guidance_scale": 9.0-9.5,   // Stronger guidance for better results
    "use_fp16": true             // Still beneficial on L4
  },
  "batch_processing": {
    "max_batch_size": 5          // Can process more videos at once
  }
}
```

### T4 GPU Settings (16GB VRAM)
```json
{
  "wan_model": {
    "resolution": "480p",        // Lower to save memory
    "sample_steps": 20-25,       // Reduce for faster generation
    "guidance_scale": 5.0-6.0,   // Lower for faster generation
    "use_fp16": true             // Essential for T4 memory optimization
  },
  "batch_processing": {
    "max_batch_size": 2-3        // Lower batch size for T4
  }
}
```

## Troubleshooting

- **Out of Memory Errors**: Reduce the `max_batch_size` in `config.json` or lower the resolution
- **Slow Generation**: Make sure the GPU is properly detected and CUDA is enabled
- **Download Issues**: If model download fails, manually download from Hugging Face and place in the `models` directory
- **Container Crashes**: Check logs with `docker logs CONTAINER_ID` to identify issues