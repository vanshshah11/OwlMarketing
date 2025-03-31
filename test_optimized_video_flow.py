#!/usr/bin/env python3
"""
Test script for optimized video flow.

This script tests the optimized video generation flow with accurate UI representation
and concise timing for hook and demo segments.
"""

import os
import sys
import logging
import json
from pathlib import Path

# Add project root to path
project_root = os.path.abspath(os.path.dirname(__file__))
sys.path.append(project_root)

# Import project modules
from scripts.run_content_pipeline import ContentPipeline
from video_generation.avatar_config import AVATAR_CONFIGS
from video_editing.hooks_templates import HOOK_TEMPLATES

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(project_root, "logs", "test_video.log")),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('test_video')

def main():
    """Run a test of the optimized video generation flow."""
    # Create output directory
    output_dir = os.path.join(project_root, "output", "test_optimized")
    os.makedirs(output_dir, exist_ok=True)
    
    # Initialize pipeline
    pipeline = ContentPipeline(output_dir=output_dir)
    
    # Test parameters
    avatar_name = "sophia"  # Choose an avatar from AVATAR_CONFIGS
    food_item = {
        "name": "Protein Bar",
        "calories": 210,
        "protein": 20,
        "carbs": 25,
        "fat": 7
    }
    hook_text = "Wait...HOW did I not know about this before??"
    
    # Create script
    script = {
        "avatar": avatar_name,
        "hook": hook_text,
        "feature": "realtime_tracking",
        "food_item": food_item["name"],
        "calories": food_item["calories"],
        "protein": food_item["protein"],
        "carbs": food_item["carbs"],
        "fat": food_item["fat"],
        "duration": {
            "total": 12,
            "hook": 5,
            "demo": 6
        },
        "variation": "talking_head"  # Use talking_head for hook
    }
    
    # Save script
    script_path = os.path.join(output_dir, "test_script.json")
    with open(script_path, 'w') as f:
        json.dump(script, f, indent=2)
    
    logger.info(f"Created test script: {script_path}")
    
    # Generate video using pipeline
    result = pipeline.generate_single_video(script, avatar_name)
    
    if result:
        logger.info(f"Successfully generated test video: {result}")
        print(f"\nGenerated test video: {result}")
        
        # Open video if on appropriate system
        if sys.platform == "darwin":  # macOS
            os.system(f"open {result}")
        elif sys.platform == "win32":  # Windows
            os.system(f"start {result}")
        elif sys.platform == "linux":  # Linux
            os.system(f"xdg-open {result}")
    else:
        logger.error("Failed to generate test video")
        print("\nFailed to generate test video. Check the logs for details.")

if __name__ == "__main__":
    main() 