#!/usr/bin/env python3
"""
E2E Cloud Video Generation Script for OWLmarketing

This script is designed to run on E2E Cloud with NVIDIA GPUs (T4 or L4) to generate
avatar videos and UI demonstrations for the Optimal AI calorie tracking app.
It uses Wan 2.1 T2V-14B model for high-quality video generation.

Usage:
    python run_generation.py [--config CONFIG_FILE] [--output-dir OUTPUT_DIR] [--model_dir MODEL_DIR] [--gpu-type L4|T4] [--resolution 480p|720p]
"""

import os
import sys
import json
import logging
import argparse
import time
from pathlib import Path
import shutil
import random
from concurrent.futures import ThreadPoolExecutor, as_completed

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("e2e_generation.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('e2e_generation')

# Import the Wan 2.1 generator
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from wan_t2v_generator import WanVideoGenerator

def setup_environment():
    """Setup the environment and verify GPU availability."""
    try:
        import torch
        if torch.cuda.is_available():
            device_count = torch.cuda.device_count()
            device_name = torch.cuda.get_device_name(0)
            logger.info(f"CUDA available: {device_count} device(s). Using: {device_name}")
            torch.backends.cudnn.benchmark = True
            
            # Auto-detect GPU type
            gpu_type = "T4"
            vram_mb = torch.cuda.get_device_properties(0).total_memory / (1024 * 1024)
            
            if 'l4' in device_name.lower() or vram_mb > 20000:
                logger.info(f"Detected NVIDIA L4 GPU with {vram_mb:.0f}MB VRAM")
                gpu_type = "L4"
            elif 't4' in device_name.lower():
                logger.info(f"Detected NVIDIA T4 GPU with {vram_mb:.0f}MB VRAM")
                gpu_type = "T4"
                # Clear GPU memory for T4
                if hasattr(torch.cuda, 'empty_cache'):
                    torch.cuda.empty_cache()
            else:
                logger.info(f"Using default settings for GPU: {device_name}")
                
            return True, gpu_type
        else:
            logger.warning("CUDA not available. Running on CPU which may be slow for video generation.")
            return False, None
    except Exception as e:
        logger.error(f"Error checking CUDA: {e}")
        return False, None

def load_scripts(script_dir):
    """Load generation scripts from the scripts directory."""
    scripts = []
    if not os.path.exists(script_dir):
        logger.error(f"Script directory {script_dir} not found")
        return scripts
    
    for file in os.listdir(script_dir):
        if file.endswith('.json'):
            try:
                with open(os.path.join(script_dir, file), 'r') as f:
                    script = json.load(f)
                    scripts.append(script)
                    logger.info(f"Loaded script from {file}")
            except Exception as e:
                logger.error(f"Error loading script {file}: {e}")
    
    return scripts

def add_to_python_path(project_root):
    """Add project root to Python path."""
    if project_root not in sys.path:
        sys.path.append(project_root)
        logger.info(f"Added {project_root} to Python path")

def create_avatar_prompt(script):
    """Create a tailored prompt for avatar generation using Wan 2.1."""
    avatar_name = script.get("avatar", "emma")
    variation = script.get("variation", "casual")
    
    # Base prompts for different avatars
    avatar_prompts = {
        "emily": "A young woman with blonde hair in casual clothing looking at her smartphone",
        "sophia": "A woman with dark hair and glasses using a smartphone app",
        "olivia": "A woman with shoulder-length brown hair looking at her smartphone",
        "emma": "A woman with red hair in casual clothes using a mobile application",
        "ava": "A young woman with curly hair looking at a smartphone app",
        "isabella": "A woman with long black hair in professional attire looking at her phone",
        "mia": "A young athletic woman using a smartphone application",
        "charlotte": "A blonde woman in casual clothing using a mobile app",
        "amelia": "A woman with short brown hair using a calorie tracking app",
        "harper": "A woman with glasses and dark hair scanning food with a phone",
        "sarah": "A woman with auburn hair in casual attire using a smartphone"
    }
    
    # Get base prompt or use default
    base_prompt = avatar_prompts.get(avatar_name.lower(), 
                               f"A person looking at a smartphone, using a calorie tracking app")
    
    # Add food context
    food_item = script.get("food_item", "healthy meal")
    feature = script.get("feature", "food scanning")
    
    if feature == "food scanning":
        action = f"scanning {food_item} with their smartphone camera"
    else:
        action = f"tracking {food_item} in a calorie tracking app"
    
    # Enhance prompt with the specific action and style
    enhanced_prompt = f"{base_prompt}, {action}. The person is {variation}, focused, well-lit, detailed photograph"
    
    # Add technical quality markers
    final_prompt = f"{enhanced_prompt}, professional, high detail, 4K, natural lighting, soft shadows"
    
    return final_prompt

def generate_avatar_video_with_wan(script, output_dir, model_dir, resolution="720p", gpu_type="L4"):
    """Generate avatar video using Wan 2.1 model."""
    try:
        # Create avatar-specific output directory
        avatar_name = script.get("avatar", "emma")
        avatar_output_dir = os.path.join(output_dir, "avatars", avatar_name)
        os.makedirs(avatar_output_dir, exist_ok=True)
        
        # Create output path
        output_path = os.path.join(avatar_output_dir, f"{avatar_name}_video.mp4")
        
        # Create a prompt for the avatar video
        prompt = create_avatar_prompt(script)
        logger.info(f"Generated prompt for {avatar_name}: {prompt}")
        
        # Initialize Wan generator with proper GPU settings
        generator = WanVideoGenerator(
            model_dir=model_dir,
            resolution=resolution,
            optimize_for_gpu=True,
            gpu_type=gpu_type
        )
        
        # Generate the video
        video_path = generator.generate_video(
            prompt=prompt,
            output_path=output_path,
            duration=5,  # 5 seconds is a good length for avatar videos
            fps=24
        )
        
        # Clean up resources
        generator.cleanup()
        
        if video_path and os.path.exists(video_path):
            logger.info(f"Generated avatar video: {video_path}")
            return {"avatar": avatar_name, "avatar_video": video_path}
        else:
            logger.error(f"Failed to generate avatar video for {avatar_name}")
            return None
    
    except Exception as e:
        logger.error(f"Error generating avatar video: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return None

def run_video_generation(script, output_dir, project_root, model_dir, batch_id, resolution="720p", gpu_type="L4"):
    """Run video generation for a single script."""
    try:
        # Add project root to path if not already added
        add_to_python_path(project_root)
        
        # Import generation modules
        from video_generation.app_ui_manager import get_ui_manager
        from video_generation.generate_video import VideoGenerator
        
        # Extract avatar information
        avatar_name = script.get("avatar", "emma")
        
        # Generate avatar video using Wan 2.1
        logger.info(f"Generating avatar video for {avatar_name}")
        avatar_result = generate_avatar_video_with_wan(
            script, 
            output_dir, 
            model_dir,
            resolution=resolution,
            gpu_type=gpu_type
        )
        
        if not avatar_result or not os.path.exists(avatar_result.get("avatar_video", "")):
            logger.error(f"Failed to generate avatar for {avatar_name}")
            return None
        
        # Extract food item from script
        food_item = {
            "name": script.get("food_item", "avocado toast"),
            "calories": script.get("calories", 350),
            "protein": script.get("protein", 0),
            "carbs": script.get("carbs", 0),
            "fat": script.get("fat", 0)
        }
        
        # Generate app UI demo
        ui_manager = get_ui_manager()
        app_demo_path = os.path.join(output_dir, "ui_demos", f"app_demo_{avatar_name}_{batch_id}.mp4")
        os.makedirs(os.path.dirname(app_demo_path), exist_ok=True)
        
        logger.info(f"Generating UI demo for feature: {script.get('feature', 'food scanning')}")
        app_demo = ui_manager.create_feature_demo(
            script.get("feature", "food scanning"),
            app_demo_path,
            duration=5.0,
            food_item=food_item,
            script=script
        )
        
        if not app_demo or not os.path.exists(app_demo):
            logger.error(f"Failed to generate app demo for {avatar_name}")
            return None
        
        # Generate full video
        video_generator = VideoGenerator(output_dir=os.path.join(output_dir, "videos"))
        
        # Create avatar-specific output directory
        avatar_videos_dir = os.path.join(output_dir, "videos", "by_avatar", avatar_name)
        os.makedirs(avatar_videos_dir, exist_ok=True)
        
        output_path = os.path.join(avatar_videos_dir, f"video_{avatar_name}_{batch_id}.mp4")
        
        logger.info(f"Generating complete video for {avatar_name}")
        video_path = video_generator.generate_complete_video(
            avatar_result["avatar_video"],
            app_demo,
            script,
            output_path=output_path
        )
        
        if video_path and os.path.exists(video_path):
            logger.info(f"Successfully generated video: {video_path}")
            
            # Also copy to the main videos directory for compatibility
            main_video_dir = os.path.join(output_dir, "videos")
            main_video_path = os.path.join(main_video_dir, f"video_{avatar_name}_{batch_id}.mp4")
            shutil.copy2(video_path, main_video_path)
            
            return {
                "avatar": avatar_name,
                "video_path": video_path,
                "main_path": main_video_path,
                "app_demo_path": app_demo,
                "avatar_video_path": avatar_result["avatar_video"]
            }
        else:
            logger.error(f"Failed to generate complete video for {avatar_name}")
            return None
    
    except Exception as e:
        logger.error(f"Error in video generation: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return None

def group_scripts_by_avatar(scripts):
    """Group scripts by avatar for more efficient processing."""
    avatar_groups = {}
    
    for script in scripts:
        avatar = script.get("avatar", "emma")
        if avatar not in avatar_groups:
            avatar_groups[avatar] = []
        avatar_groups[avatar].append(script)
    
    # Sort each group by feature for better batching
    for avatar in avatar_groups:
        avatar_groups[avatar].sort(key=lambda s: s.get("feature", ""))
    
    return avatar_groups

def main():
    parser = argparse.ArgumentParser(description="E2E Cloud Video Generation for OWLmarketing")
    parser.add_argument("--config", default="/workspace/config.json", help="Path to configuration file")
    parser.add_argument("--output-dir", default="/app/output", help="Directory to store generated videos")
    parser.add_argument("--script-dir", default="/workspace/scripts", help="Directory containing generation scripts")
    parser.add_argument("--project-root", default="/app", help="Root directory of the project")
    parser.add_argument("--model_dir", default="/app/models/Wan2.1-T2V-14B", help="Directory containing the Wan 2.1 model")
    parser.add_argument("--max-batch", type=int, default=3, help="Maximum number of videos to generate in a batch")
    parser.add_argument("--process-all", action="store_true", help="Process all scripts even if some fail")
    parser.add_argument("--gpu-type", choices=["L4", "T4"], default=None, help="GPU type to optimize for (L4 or T4)")
    parser.add_argument("--resolution", choices=["480p", "720p"], default=None, help="Video resolution to generate")
    
    args = parser.parse_args()
    
    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Create organized output directories
    os.makedirs(os.path.join(args.output_dir, "videos", "by_avatar"), exist_ok=True)
    os.makedirs(os.path.join(args.output_dir, "avatars"), exist_ok=True)
    os.makedirs(os.path.join(args.output_dir, "ui_demos"), exist_ok=True)
    
    # Setup environment and check for GPU
    gpu_available, detected_gpu_type = setup_environment()
    if not gpu_available:
        logger.warning("No GPU detected. Generation will be extremely slow or may fail.")
        if not args.process_all:
            logger.error("Aborting due to lack of GPU. Use --process-all to force processing.")
            return 1
    
    # Determine GPU type to use (command line arg > detected > default)
    gpu_type = args.gpu_type or detected_gpu_type or "T4"
    logger.info(f"Using GPU type: {gpu_type}")
    
    # Determine default resolution based on GPU type
    default_resolution = "720p" if gpu_type == "L4" else "480p"
    resolution = args.resolution or default_resolution
    logger.info(f"Using resolution: {resolution}")
    
    # Load configuration
    config = {}
    if os.path.exists(args.config):
        try:
            with open(args.config, 'r') as f:
                config = json.load(f)
                logger.info(f"Loaded configuration from {args.config}")
                
                # Override from config if not specified in command line
                if args.gpu_type is None and "gpu_settings" in config and "model" in config["gpu_settings"]:
                    gpu_type = config["gpu_settings"]["model"]
                
                if args.resolution is None and "wan_model" in config and "resolution" in config["wan_model"]:
                    resolution = config["wan_model"]["resolution"]
        except Exception as e:
            logger.error(f"Error loading config: {e}")
    else:
        logger.warning(f"Config file {args.config} not found. Using default settings.")
    
    # Load generation scripts
    scripts = load_scripts(args.script_dir)
    if not scripts:
        logger.error("No scripts found. Cannot proceed with generation.")
        return 1
    
    # Group scripts by avatar for more efficient GPU usage
    avatar_groups = group_scripts_by_avatar(scripts)
    
    # Determine optimal batch size
    default_max_batch = 5 if gpu_type == "L4" else 3  # L4 can handle larger batches
    max_batch = min(args.max_batch or default_max_batch, len(scripts))
    logger.info(f"Using batch size of {max_batch} for processing on {gpu_type} GPU")
    
    # Process each script in organized batches
    successful_videos = []
    batch_id = int(time.time()) % 10000  # Use timestamp as batch ID
    
    # Process each avatar group
    for avatar, avatar_scripts in avatar_groups.items():
        logger.info(f"Processing {len(avatar_scripts)} scripts for avatar {avatar}")
        
        # Process scripts in appropriate batch sizes for the GPU
        for i in range(0, len(avatar_scripts), max_batch):
            batch = avatar_scripts[i:i+max_batch]
            logger.info(f"Processing batch of {len(batch)} videos for {avatar}")
            
            for j, script in enumerate(batch):
                script_id = i + j + 1
                logger.info(f"Processing script {script_id}/{len(avatar_scripts)} for {avatar}")
                
                # Generate video with appropriate GPU settings
                video_result = run_video_generation(
                    script, 
                    args.output_dir, 
                    args.project_root, 
                    args.model_dir,
                    f"{batch_id}_{script_id}",
                    resolution=resolution,
                    gpu_type=gpu_type
                )
                
                if video_result:
                    successful_videos.append(video_result)
                    logger.info(f"Successfully generated video {script_id} for {avatar}")
                else:
                    logger.error(f"Failed to generate video {script_id} for {avatar}")
            
            # Clear GPU memory between batches
            try:
                import torch
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
                    logger.info("Cleared GPU cache between batches")
            except:
                pass
            
            # Shorter delay for L4 which has better thermal management
            cooling_delay = 3 if gpu_type == "L4" else 5
            logger.info(f"Completed batch for {avatar}. Pausing briefly before next batch...")
            time.sleep(cooling_delay)
    
    # Summarize results
    logger.info(f"Video generation complete. Generated {len(successful_videos)}/{len(scripts)} videos successfully.")
    
    # Create a summary file with the organization by avatar
    summary = {"videos_by_avatar": {}}
    
    for result in successful_videos:
        avatar = result["avatar"]
        if avatar not in summary["videos_by_avatar"]:
            summary["videos_by_avatar"][avatar] = []
        
        summary["videos_by_avatar"][avatar].append({
            "video_path": result["video_path"],
            "main_path": result["main_path"],
            "app_demo_path": result["app_demo_path"],
            "avatar_video_path": result["avatar_video_path"]
        })
    
    # Write summary to file
    summary_file = os.path.join(args.output_dir, "generation_summary.json")
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)
    
    logger.info(f"Created summary file: {summary_file}")
    
    # Copy the log file to the output directory for reference
    try:
        shutil.copy2("e2e_generation.log", os.path.join(args.output_dir, "e2e_generation.log"))
    except Exception as e:
        logger.error(f"Error copying log file: {e}")
    
    # Print avatar-specific summary for easy reference
    logger.info("Summary by avatar:")
    for avatar, videos in summary["videos_by_avatar"].items():
        logger.info(f"  {avatar}: {len(videos)} videos")
    
    return 0 if successful_videos else 1

if __name__ == "__main__":
    start_time = time.time()
    exit_code = main()
    end_time = time.time()
    logger.info(f"Total execution time: {end_time - start_time:.2f} seconds")
    sys.exit(exit_code)