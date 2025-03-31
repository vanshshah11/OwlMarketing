#!/usr/bin/env python3
"""
E2E Cloud Data Preparation Script for OWLmarketing

This script prepares and packages the necessary files for uploading to E2E Cloud:
1. Generates video scripts from templates
2. Packages code, scripts, and configuration files
3. Creates a zip file ready for upload

Usage:
    python prepare_data.py --output-dir ./e2e_data --scripts 3
"""

import os
import sys
import json
import shutil
import logging
import argparse
import random
import zipfile
from datetime import datetime
from pathlib import Path

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(project_root)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(project_root, "logs", "prepare_data.log")),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('prepare_data')

def create_output_dirs(output_dir):
    """Create the necessary output directories."""
    dirs = [
        os.path.join(output_dir, "code"),
        os.path.join(output_dir, "scripts"),
        os.path.join(output_dir, "config"),
        # Add directories for organized output
        os.path.join(output_dir, "output", "videos", "by_avatar"),
        os.path.join(output_dir, "output", "avatars"),
        os.path.join(output_dir, "output", "ui_demos"),
    ]
    
    for d in dirs:
        os.makedirs(d, exist_ok=True)
        logger.info(f"Created directory: {d}")
    
    return True

def generate_scripts(output_dir, script_count=3, group_by_avatar=True):
    """Generate video scripts from templates."""
    try:
        # Import local modules
        from video_editing.hooks_templates import HOOK_TEMPLATES
        from video_generation.avatar_config import AVATAR_CONFIGS
        
        # Create scripts directory
        scripts_dir = os.path.join(output_dir, "scripts")
        os.makedirs(scripts_dir, exist_ok=True)
        
        # Load configuration
        config_file = os.path.join(project_root, "config", "pipeline_config.json")
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                config = json.load(f)
        else:
            # Default configuration
            config = {
                "food_items": [
                    {"name": "avocado toast", "calories": 350, "protein": 12, "carbs": 38, "fat": 18},
                    {"name": "chicken salad", "calories": 250, "protein": 25, "carbs": 10, "fat": 12},
                    {"name": "protein shake", "calories": 180, "protein": 30, "carbs": 15, "fat": 2},
                    {"name": "salmon bowl", "calories": 420, "protein": 28, "carbs": 30, "fat": 22},
                    {"name": "greek yogurt parfait", "calories": 280, "protein": 18, "carbs": 35, "fat": 8}
                ]
            }
        
        # Choose avatars - if group_by_avatar is True, distribute scripts evenly among avatars
        avatars = list(AVATAR_CONFIGS.keys())
        random.shuffle(avatars)
        
        if group_by_avatar:
            # Calculate how many scripts per avatar to generate (minimum 1 per avatar)
            scripts_per_avatar = max(1, script_count // len(avatars))
            remaining = script_count - (scripts_per_avatar * len(avatars))
            
            # Distribute scripts evenly among avatars
            avatar_assignments = {}
            for avatar in avatars:
                avatar_assignments[avatar] = scripts_per_avatar
            
            # Distribute any remaining scripts
            for i in range(remaining):
                avatar_assignments[avatars[i % len(avatars)]] += 1
            
            # Generate scripts by avatar for better GPU utilization
            scripts = []
            script_index = 1
            
            for avatar, count in avatar_assignments.items():
                if count <= 0:
                    continue
                
                avatar_config = AVATAR_CONFIGS[avatar]
                
                for i in range(count):
                    # Select a random food item
                    food_item = random.choice(config.get("food_items", [{"name": "avocado toast", "calories": 350}]))
                    
                    # Select a random hook template
                    hook = random.choice(HOOK_TEMPLATES)
                    
                    # Create script
                    script = {
                        "avatar": avatar,
                        "hook": hook,
                        "feature": "food scanning" if random.random() < 0.7 else "meal tracking",
                        "food_item": food_item["name"],
                        "calories": food_item["calories"],
                        "protein": food_item.get("protein", 0),
                        "carbs": food_item.get("carbs", 0),
                        "fat": food_item.get("fat", 0),
                        "duration": random.randint(5, 13),
                        "variation": random.choice(list(avatar_config["variations"].keys()))
                    }
                    
                    scripts.append(script)
                    
                    # Save script
                    script_file = os.path.join(scripts_dir, f"script_{script_index}.json")
                    with open(script_file, 'w') as f:
                        json.dump(script, f, indent=2)
                    
                    logger.info(f"Generated script {script_index} for avatar {avatar}")
                    script_index += 1
        else:
            # Original random assignment method
            avatars = avatars[:script_count]
            
            # Generate scripts
            scripts = []
            for i in range(script_count):
                avatar = avatars[i % len(avatars)]
                avatar_config = AVATAR_CONFIGS[avatar]
                
                # Select a random food item
                food_item = random.choice(config.get("food_items", [{"name": "avocado toast", "calories": 350}]))
                
                # Select a random hook template
                hook = random.choice(HOOK_TEMPLATES)
                
                # Create script
                script = {
                    "avatar": avatar,
                    "hook": hook,
                    "feature": "food scanning" if random.random() < 0.7 else "meal tracking",
                    "food_item": food_item["name"],
                    "calories": food_item["calories"],
                    "protein": food_item.get("protein", 0),
                    "carbs": food_item.get("carbs", 0),
                    "fat": food_item.get("fat", 0),
                    "duration": random.randint(5, 13),
                    "variation": random.choice(list(avatar_config["variations"].keys()))
                }
                
                scripts.append(script)
                
                # Save script
                script_file = os.path.join(scripts_dir, f"script_{i+1}.json")
                with open(script_file, 'w') as f:
                    json.dump(script, f, indent=2)
                
                logger.info(f"Generated script {i+1} for avatar {avatar}")
        
        logger.info(f"Generated {len(scripts)} scripts successfully")
        return scripts
    
    except Exception as e:
        logger.error(f"Error generating scripts: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return []

def copy_project_files(output_dir):
    """Copy necessary project files to the output directory."""
    try:
        # Define directories to copy
        dirs_to_copy = [
            "video_generation",
            "video_editing",
            "assets"
        ]
        
        # Define individual files to copy
        files_to_copy = [
            "requirements.txt",
            os.path.join("config", "pipeline_config.json")
        ]
        
        # Copy directories
        for dir_name in dirs_to_copy:
            src_dir = os.path.join(project_root, dir_name)
            dest_dir = os.path.join(output_dir, "code", dir_name)
            
            if os.path.exists(src_dir):
                shutil.copytree(src_dir, dest_dir, dirs_exist_ok=True)
                logger.info(f"Copied directory: {dir_name}")
            else:
                logger.warning(f"Directory not found: {dir_name}")
        
        # Copy individual files
        for file_path in files_to_copy:
            src_file = os.path.join(project_root, file_path)
            dest_file = os.path.join(output_dir, "code", file_path)
            
            if os.path.exists(src_file):
                os.makedirs(os.path.dirname(dest_file), exist_ok=True)
                shutil.copy2(src_file, dest_file)
                logger.info(f"Copied file: {file_path}")
            else:
                logger.warning(f"File not found: {file_path}")
        
        # Copy E2E Cloud specific files
        e2e_cloud_dir = os.path.join(project_root, "e2e_cloud")
        e2e_files = ["Dockerfile", "entrypoint.sh", "run_generation.py", "wan_t2v_generator.py"]
        
        for file_name in e2e_files:
            src_file = os.path.join(e2e_cloud_dir, file_name)
            dest_file = os.path.join(output_dir, file_name)
            
            if os.path.exists(src_file):
                shutil.copy2(src_file, dest_file)
                logger.info(f"Copied E2E Cloud file: {file_name}")
            else:
                logger.warning(f"E2E Cloud file not found: {file_name}")
        
        # Copy E2E requirements
        e2e_req_file = os.path.join(e2e_cloud_dir, "requirements.txt")
        if os.path.exists(e2e_req_file):
            shutil.copy2(e2e_req_file, os.path.join(output_dir, "requirements.txt"))
            logger.info("Copied E2E Cloud requirements.txt")
        
        return True
    
    except Exception as e:
        logger.error(f"Error copying project files: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def create_e2e_config(output_dir, config_data=None):
    """Create a configuration file for E2E Cloud."""
    try:
        if config_data is None:
            config_data = {
                "gpu_settings": {
                    "model": "T4",
                    "memory": "16GB",
                    "cuda_version": "11.8"
                },
                "generation_settings": {
                    "resolution": [832, 480],  # Optimized for Wan 2.1 480p
                    "fps": 24,
                    "quality": "medium"  # Use medium quality for T4
                },
                "wan_model": {
                    "model_name": "Wan2.1-T2V-14B",
                    "resolution": "480p",
                    "optimize_for_t4": True,
                    "use_fp16": True,
                    "sample_steps": 25,  # Reduced for T4 performance
                    "guidance_scale": 6.0  # Optimized for generation quality
                },
                "batch_processing": {
                    "max_batch_size": 3,  # Process 3 videos max per batch for T4
                    "clear_cache_between_batches": True
                }
            }
        
        config_file = os.path.join(output_dir, "config.json")
        with open(config_file, 'w') as f:
            json.dump(config_data, f, indent=2)
        
        logger.info(f"Created E2E Cloud configuration file: {config_file}")
        return True
    
    except Exception as e:
        logger.error(f"Error creating E2E config: {e}")
        return False

def create_model_download_script(output_dir):
    """Create a script to download the Wan 2.1 model if needed."""
    try:
        script_content = """#!/bin/bash
# Script to download Wan 2.1 T2V-14B model if needed

MODEL_DIR="/app/models/Wan2.1-T2V-14B"

if [ ! -d "$MODEL_DIR" ] || [ -z "$(ls -A $MODEL_DIR)" ]; then
    echo "Downloading Wan 2.1 T2V-14B model..."
    # Install huggingface-cli if not already installed
    pip install -q "huggingface_hub[cli]"
    # Download the model
    huggingface-cli download Wan-AI/Wan2.1-T2V-14B --local-dir $MODEL_DIR
    echo "Wan 2.1 model downloaded to $MODEL_DIR"
else
    echo "Wan 2.1 model already exists at $MODEL_DIR"
fi
"""
        
        script_file = os.path.join(output_dir, "download_model.sh")
        with open(script_file, 'w') as f:
            f.write(script_content)
        
        # Make the script executable
        os.chmod(script_file, 0o755)
        
        logger.info(f"Created model download script: {script_file}")
        return True
    
    except Exception as e:
        logger.error(f"Error creating model download script: {e}")
        return False

def create_zip_archive(output_dir):
    """Create a ZIP archive of the prepared data."""
    try:
        # Create timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        zip_filename = f"e2e_cloud_data_{timestamp}.zip"
        zip_filepath = os.path.join(os.path.dirname(output_dir), zip_filename)
        
        # Create ZIP file
        with zipfile.ZipFile(zip_filepath, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, _, files in os.walk(output_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, os.path.dirname(output_dir))
                    zipf.write(file_path, arcname)
        
        logger.info(f"Created ZIP archive: {zip_filepath}")
        return zip_filepath
    
    except Exception as e:
        logger.error(f"Error creating ZIP archive: {e}")
        return None

def main():
    parser = argparse.ArgumentParser(description="E2E Cloud Data Preparation for OWLmarketing")
    parser.add_argument("--output-dir", default="./e2e_data", help="Directory to store prepared data")
    parser.add_argument("--scripts", type=int, default=3, help="Number of scripts to generate")
    parser.add_argument("--create-zip", action="store_true", help="Create a ZIP archive of the prepared data")
    parser.add_argument("--group-by-avatar", action="store_true", help="Group scripts by avatar for better GPU utilization")
    
    args = parser.parse_args()
    
    # Set output directory
    output_dir = os.path.abspath(args.output_dir)
    os.makedirs(output_dir, exist_ok=True)
    
    logger.info(f"Preparing data for E2E Cloud in: {output_dir}")
    
    # Create output directories
    create_output_dirs(output_dir)
    
    # Generate scripts
    scripts = generate_scripts(output_dir, args.scripts, args.group_by_avatar)
    if not scripts:
        logger.error("Failed to generate scripts")
        return 1
    
    # Copy project files
    if not copy_project_files(output_dir):
        logger.error("Failed to copy project files")
        return 1
    
    # Create E2E configuration
    if not create_e2e_config(output_dir):
        logger.error("Failed to create E2E configuration")
        return 1
    
    # Create model download script
    if not create_model_download_script(output_dir):
        logger.error("Failed to create model download script")
        return 1
    
    # Create ZIP archive if requested
    if args.create_zip:
        zip_filepath = create_zip_archive(output_dir)
        if zip_filepath:
            logger.info("Data preparation and ZIP creation complete")
            print(f"\nPrepared data package: {zip_filepath}")
        else:
            logger.error("Failed to create ZIP archive")
            return 1
    else:
        logger.info("Data preparation complete")
        print(f"\nPrepared data directory: {output_dir}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())