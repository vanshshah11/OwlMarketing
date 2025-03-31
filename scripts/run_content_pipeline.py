#!/usr/bin/env python3
"""
OWLmarketing Content Pipeline Runner

This script orchestrates the full content pipeline:
1. Script generation from templates
2. Video generation with dynamic UI
3. Post-processing and optimization
4. Scheduling for social media posting

Usage:
    python run_content_pipeline.py --output-dir ./output --avatar-name emma
"""

import os
import sys
import json
import logging
import argparse
import random
from datetime import datetime
from pathlib import Path
import traceback

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(project_root)

# Import local modules
from video_generation.app_ui_manager import get_ui_manager
from video_generation.wan_avatar_generator import generate_avatar_set
from video_generation.generate_video import VideoGenerator
from scheduling.post_scheduler import schedule_posts
from video_editing.hooks_templates import HOOK_TEMPLATES
from video_generation.avatar_config import AVATAR_CONFIGS, VIDEO_SETTINGS

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(project_root, "logs", "pipeline.log")),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('content_pipeline')

class ContentPipeline:
    """Main content generation pipeline orchestrator."""
    
    def __init__(self, output_dir=None, config_file=None, wan_model_dir=None, gpu_type="L4"):
        """Initialize the content pipeline."""
        # Set output directory
        if output_dir is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_dir = os.path.join(project_root, "output", f"run_{timestamp}")
        
        self.output_dir = os.path.abspath(output_dir)
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Create subdirectories
        self.videos_dir = os.path.join(self.output_dir, "videos")
        self.scripts_dir = os.path.join(self.output_dir, "scripts")
        self.logs_dir = os.path.join(self.output_dir, "logs")
        
        os.makedirs(self.videos_dir, exist_ok=True)
        os.makedirs(self.scripts_dir, exist_ok=True)
        os.makedirs(self.logs_dir, exist_ok=True)
        
        # Set configuration file
        if config_file is None:
            config_file = os.path.join(project_root, "config", "pipeline_config.json")
        
        self.config_file = config_file
        self.config = self._load_config()
        
        # Set Wan model directory
        self.wan_model_dir = wan_model_dir
        if self.wan_model_dir is None:
            # Try to find it in common locations
            potential_paths = [
                "/app/models/Wan2.1-T2V-14B",
                os.path.join(project_root, "models", "Wan2.1-T2V-14B"),
                os.environ.get("WAN_MODEL_DIR", "")
            ]
            for path in potential_paths:
                if path and os.path.exists(path):
                    self.wan_model_dir = path
                    break
        
        # Set GPU type
        self.gpu_type = gpu_type
        
        # Initialize components
        self.ui_manager = get_ui_manager()
        self.video_generator = VideoGenerator(output_dir=self.videos_dir)
        
        # Track generated content
        self.generated_scripts = []
        self.generated_videos = []
        
        logger.info(f"Initialized ContentPipeline with output directory: {self.output_dir}")
        logger.info(f"Using Wan 2.1 T2V model for avatar generation with GPU type: {self.gpu_type}")
    
    def _load_config(self):
        """Load configuration from JSON file."""
        try:
            with open(self.config_file, 'r') as f:
                config = json.load(f)
                logger.info(f"Loaded configuration from {self.config_file}")
                return config
        except Exception as e:
            logger.warning(f"Failed to load configuration file: {e}")
            logger.info("Using default configuration")
            
            # Create default configuration
            default_config = {
                "script_generation": {
                    "script_count": 3,
                    "max_duration": 60,
                    "target_audience": ["health-conscious adults", "fitness enthusiasts"]
                },
                "video_generation": {
                    "resolution": [1080, 1920],
                    "fps": 30,
                    "quality": "high",
                    "wan_settings": {
                        "resolution": "720p",  # Default to 720p for L4 GPU
                        "sample_steps": 30,
                        "guide_scale": 9.0,
                        "fps": 24
                    }
                },
                "scheduling": {
                    "platforms": ["tiktok", "instagram"],
                    "posting_frequency": "daily",
                    "optimal_times": ["12:00", "18:00"]
                },
                "food_items": [
                    {"name": "avocado toast", "calories": 350, "protein": 12, "carbs": 38, "fat": 18},
                    {"name": "chicken salad", "calories": 250, "protein": 25, "carbs": 10, "fat": 12},
                    {"name": "protein shake", "calories": 180, "protein": 30, "carbs": 15, "fat": 2},
                    {"name": "salmon bowl", "calories": 420, "protein": 28, "carbs": 30, "fat": 22},
                    {"name": "greek yogurt parfait", "calories": 280, "protein": 18, "carbs": 35, "fat": 8}
                ]
            }
            
            # Save default configuration
            try:
                os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
                with open(self.config_file, 'w') as f:
                    json.dump(default_config, f, indent=2)
                    logger.info(f"Created default configuration at {self.config_file}")
            except Exception as e:
                logger.error(f"Failed to save default configuration: {e}")
            
            return default_config
    
    def run_full_pipeline(self, avatar_name=None, script_count=None, video_count=None, schedule=True):
        """Run the complete content pipeline using templates."""
        try:
            logger.info("Starting content pipeline")
            
            # Validate that UI assets are available or can be generated
            if not self.ui_manager.assets_validated:
                logger.warning("UI assets not fully validated. Using dynamic generation.")
            
            # 1. Generate scripts from templates
            if script_count is None:
                script_count = self.config["script_generation"]["script_count"]
            
            # Select avatar
            if avatar_name and avatar_name in AVATAR_CONFIGS:
                avatar_config = AVATAR_CONFIGS[avatar_name]
                avatars = [avatar_name]
            else:
                # Choose random avatars
                avatars = list(AVATAR_CONFIGS.keys())
                random.shuffle(avatars)
                avatars = avatars[:script_count]
                
            logger.info(f"Using avatars: {avatars}")
            logger.info(f"Generating {script_count} scripts from templates")
            
            # Generate scripts from templates
            scripts = []
            for i in range(script_count):
                avatar = avatars[i % len(avatars)]
                avatar_config = AVATAR_CONFIGS[avatar]
                
                # Select a random food item
                food_item = random.choice(self.config.get("food_items", [{"name": "avocado toast", "calories": 350}]))
                
                # Select a random hook template
                hook = random.choice(HOOK_TEMPLATES)
                
                # Create script - Set concise durations
                script = {
                    "avatar": avatar,
                    "hook": hook,
                    "feature": "realtime_tracking",  # Always use realtime tracking
                    "food_item": food_item["name"],
                    "calories": food_item["calories"],
                    "protein": food_item.get("protein", 0),
                    "carbs": food_item.get("carbs", 0),
                    "fat": food_item.get("fat", 0),
                    "duration": {
                        "total": random.randint(10, 13),  # Total video duration
                        "hook": random.randint(4, 5),     # Hook segment duration
                        "demo": random.randint(5, 7)      # Demo segment duration
                    },
                    "variation": random.choice(list(avatar_config["variations"].keys()))
                }
                
                scripts.append(script)
                
                # Save script
                script_file = os.path.join(self.scripts_dir, f"script_{i+1}.json")
                with open(script_file, 'w') as f:
                    json.dump(script, f, indent=2)
                
                self.generated_scripts.append(script_file)
            
            logger.info(f"Generated {len(scripts)} scripts")
            
            # 2. Generate videos
            if video_count is None:
                video_count = min(len(scripts), 3)  # Default to 3 videos max
                
            # Select scripts to use for video generation
            selected_scripts = scripts[:video_count]
            
            logger.info(f"Generating {len(selected_scripts)} videos")
            
            for i, script in enumerate(selected_scripts):
                try:
                    avatar_name = script["avatar"]
                    
                    # Generate avatar using Wan 2.1 T2V
                    logger.info(f"Generating avatar video using Wan 2.1 T2V for {avatar_name}")
                    avatar_result = generate_avatar_set(
                        avatar_name,
                        style=script["variation"],
                        output_dir=os.path.join(self.output_dir, "avatars", avatar_name),
                        model_dir=self.wan_model_dir,
                        resolution=self.config["video_generation"]["wan_settings"].get("resolution", "720p"),
                        gpu_type=self.gpu_type
                    )
                    
                    if "error" in avatar_result:
                        logger.error(f"Error generating avatar: {avatar_result['error']}")
                        continue
                    
                    # Extract food item from script
                    food_item = {
                        "name": script["food_item"],
                        "calories": script["calories"],
                        "protein": script["protein"],
                        "carbs": script["carbs"],
                        "fat": script["fat"]
                    }
                    
                    # Generate UI demo specifically for real-time tracking
                    logger.info(f"Generating UI demo for real-time tracking of {food_item['name']}")
                    ui_demo_path = os.path.join(
                        self.output_dir, 
                        "ui_demos", 
                        f"{avatar_name}_{food_item['name'].replace(' ', '_').lower()}_demo.mp4"
                    )
                    os.makedirs(os.path.dirname(ui_demo_path), exist_ok=True)
                    
                    # Create concise UI demo (5-7 seconds)
                    ui_demo = self.ui_manager.create_feature_demo(
                        feature="realtime_tracking",
                        output_path=ui_demo_path,
                        food_item=food_item,
                        duration=script["duration"]["demo"]  # Use the specific demo duration from script
                    )
                    
                    if not ui_demo or not os.path.exists(ui_demo):
                        logger.error(f"Failed to generate UI demo for {avatar_name}")
                        continue
                    
                    # Split the avatar video to extract the hook segment
                    hook_duration = script["duration"]["hook"]
                    avatar_video = avatar_result["avatar_video"]
                    hook_segment_path = os.path.join(
                        self.output_dir, 
                        "segments", 
                        f"{avatar_name}_hook.mp4"
                    )
                    os.makedirs(os.path.dirname(hook_segment_path), exist_ok=True)
                    
                    # Extract the hook segment
                    logger.info(f"Extracting hook segment for {avatar_name} ({hook_duration}s)")
                    hook_segment = self.video_generator.extract_segment(
                        avatar_video,
                        hook_segment_path,
                        duration=hook_duration
                    )
                    
                    if not hook_segment or not os.path.exists(hook_segment):
                        logger.error(f"Failed to extract hook segment for {avatar_name}")
                        continue
                    
                    # Combine hook and demo segments
                    final_video_path = os.path.join(
                        self.videos_dir, 
                        f"{avatar_name}_{script['food_item'].replace(' ', '_').lower()}.mp4"
                    )
                    
                    logger.info(f"Combining hook and demo for {avatar_name}")
                    final_video = self.video_generator.combine_segments(
                        [hook_segment, ui_demo],
                        final_video_path,
                        transition="fade"
                    )
                    
                    if not final_video or not os.path.exists(final_video):
                        logger.error(f"Failed to create final video for {avatar_name}")
                        continue
                    
                    # Add hook text overlay
                    logger.info(f"Adding hook text overlay for {avatar_name}")
                    hook_text = script["hook"]
                    final_video_with_text = self.video_generator.add_text_overlay(
                        final_video,
                        final_video_path,
                        text=hook_text,
                        position="bottom",
                        start_time=1.0,
                        duration=hook_duration - 1.5
                    )
                    
                    # Track the generated video
                    self.generated_videos.append({
                        "path": final_video_with_text,
                        "avatar": avatar_name,
                        "script": script
                    })
                    
                    logger.info(f"Successfully generated video for {avatar_name}: {final_video_with_text}")
                    
                except Exception as e:
                    logger.error(f"Error generating video for {avatar_name}: {e}")
                    logger.error(traceback.format_exc())
            
            logger.info(f"Generated {len(self.generated_videos)} videos")
            
            # 3. Schedule posts if requested
            if schedule and self.generated_videos:
                logger.info("Scheduling posts disabled for current phase")
                
            return {
                "scripts": self.generated_scripts,
                "videos": self.generated_videos
            }
            
        except Exception as e:
            logger.error(f"Error in content pipeline: {e}")
            logger.error(traceback.format_exc())
            return {"error": str(e)}

    def generate_single_video(self, script, avatar_name=None):
        """Generate a single video from a script."""
        try:
            if isinstance(script, str):
                # Load script from file
                with open(script, 'r') as f:
                    script = json.load(f)
            
            # Use specified avatar or the one from the script
            avatar = avatar_name or script.get("avatar")
            if not avatar or avatar not in AVATAR_CONFIGS:
                avatar = random.choice(list(AVATAR_CONFIGS.keys()))
            
            script["avatar"] = avatar
            
            # Set variation if not already set
            if "variation" not in script:
                script["variation"] = random.choice(list(AVATAR_CONFIGS[avatar]["variations"].keys()))
            
            # Generate avatar video using Wan 2.1 T2V
            logger.info(f"Generating avatar video using Wan 2.1 T2V for {avatar}")
            avatar_result = generate_avatar_set(
                avatar,
                style=script["variation"],
                output_dir=os.path.join(self.output_dir, "avatars", avatar),
                model_dir=self.wan_model_dir,
                resolution=self.config["video_generation"]["wan_settings"].get("resolution", "720p"),
                gpu_type=self.gpu_type
            )
            
            if "error" in avatar_result:
                logger.error(f"Error generating avatar: {avatar_result['error']}")
                return None
            
            # Prepare food item
            food_item = {
                "name": script.get("food_item", "avocado toast"),
                "calories": script.get("calories", 350),
                "protein": script.get("protein", 12),
                "carbs": script.get("carbs", 38),
                "fat": script.get("fat", 18)
            }
            
            # Generate app UI demo
            app_demo = self.ui_manager.create_feature_demo(
                script.get("feature", "food scanning"),
                os.path.join(self.videos_dir, f"app_demo_{len(self.generated_videos)+1}.mp4"),
                duration=5.0,
                food_item=food_item,
                script=script
            )
            
            if not app_demo:
                logger.error("Failed to generate app demo")
                return None
            
            # Generate full video
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            video_path = self.video_generator.generate_complete_video(
                avatar_result["avatar_video"],
                app_demo,
                script,
                output_path=os.path.join(self.videos_dir, f"video_{timestamp}.mp4")
            )
            
            if video_path:
                logger.info(f"Generated video: {video_path}")
                self.generated_videos.append(video_path)
                
                # Enhance video quality (optional post-processing)
                self.enhance_video_quality(video_path)
                
                return video_path
            else:
                logger.error("Failed to generate video")
                return None
                
        except Exception as e:
            logger.error(f"Error generating single video: {str(e)}")
            logger.error(traceback.format_exc())
            return None
    
    def enhance_video_quality(self, video_path, output_path=None):
        """Enhance the quality of a generated video (apply filters, stabilization, etc.)."""
        # If no output path provided, modify in place
        if output_path is None:
            output_path = video_path
            
        try:
            # Apply quality enhancements
            # Note: Actual implementation would involve ffmpeg commands for:
            # - Color grading
            # - Denoise
            # - Stabilization (if needed)
            
            # For now, just log that we're enhancing
            logger.info(f"Enhancing video quality: {video_path}")
            
            return output_path
        except Exception as e:
            logger.error(f"Error enhancing video: {str(e)}")
            return video_path

def main():
    """Main entry point for the content pipeline."""
    parser = argparse.ArgumentParser(description="Run the OWLmarketing content pipeline")
    parser.add_argument("--output-dir", default=None, help="Output directory for generated content")
    parser.add_argument("--config", default=None, help="Path to configuration file")
    parser.add_argument("--avatar", default=None, help="Specific avatar to use")
    parser.add_argument("--scripts", type=int, default=None, help="Number of scripts to generate")
    parser.add_argument("--videos", type=int, default=None, help="Number of videos to generate")
    parser.add_argument("--no-schedule", action="store_true", help="Don't schedule posts")
    parser.add_argument("--wan-model-dir", default=None, help="Path to Wan 2.1 T2V model directory")
    parser.add_argument("--gpu-type", default="L4", choices=["L4", "T4"], help="GPU type to optimize for")
    
    args = parser.parse_args()
    
    # Initialize pipeline
    pipeline = ContentPipeline(
        output_dir=args.output_dir,
        config_file=args.config,
        wan_model_dir=args.wan_model_dir,
        gpu_type=args.gpu_type
    )
    
    # Run pipeline
    result = pipeline.run_full_pipeline(
        avatar_name=args.avatar,
        script_count=args.scripts,
        video_count=args.videos,
        schedule=not args.no_schedule
    )
    
    if "error" in result:
        print(f"\nError in content pipeline: {result['error']}")
    else:
        print(f"\nGenerated {len(result['videos'])} videos:")
        for i, video in enumerate(result['videos'], 1):
            print(f"{i}. {video}")
    
    return 0 if "error" not in result else 1

if __name__ == "__main__":
    sys.exit(main())