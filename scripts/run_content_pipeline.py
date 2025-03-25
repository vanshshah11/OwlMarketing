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
from video_generation.generate_avatar import generate_avatar_set
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
    
    def __init__(self, output_dir=None, config_file=None):
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
        
        # Initialize components
        self.ui_manager = get_ui_manager()
        self.video_generator = VideoGenerator(output_dir=self.videos_dir)
        
        # Track generated content
        self.generated_scripts = []
        self.generated_videos = []
        
        logger.info(f"Initialized ContentPipeline with output directory: {self.output_dir}")
    
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
                    "quality": "high"
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
                script_file = os.path.join(self.scripts_dir, f"script_{i+1}.json")
                with open(script_file, 'w') as f:
                    json.dump(script, f, indent=2)
                
                self.generated_scripts.append(script_file)
            
            logger.info(f"Generated {len(scripts)} scripts")
            
            # 2. Generate videos
            if video_count is None:
                video_count = min(len(scripts), 3)  # Default to 3 videos max
            
            logger.info(f"Generating {video_count} videos")
            
            selected_scripts = scripts[:video_count]
            for i, script in enumerate(selected_scripts):
                try:
                    avatar_name = script["avatar"]
                    
                    # Generate avatar
                    avatar_result = generate_avatar_set(
                        avatar_name,
                        style=script["variation"],
                        output_dir=os.path.join(self.output_dir, "avatars", avatar_name)
                    )
                    
                    # Extract food item from script
                    food_item = {
                        "name": script["food_item"],
                        "calories": script["calories"],
                        "protein": script.get("protein", 0),
                        "carbs": script.get("carbs", 0),
                        "fat": script.get("fat", 0)
                    }
                    
                    # Generate app UI demo
                    app_demo = self.ui_manager.create_feature_demo(
                        script["feature"],
                        os.path.join(self.videos_dir, f"app_demo_{i+1}.mp4"),
                        duration=5.0,
                        food_item=food_item,
                        script=script
                    )
                    
                    if not app_demo:
                        logger.error(f"Failed to generate app demo for script {i+1}")
                        continue
                    
                    # Generate full video
                    video_path = self.video_generator.generate_complete_video(
                        avatar_result["avatar_video"],
                        app_demo,
                        script,
                        output_path=os.path.join(self.videos_dir, f"video_{i+1}.mp4")
                    )
                    
                    if video_path:
                        logger.info(f"Generated video: {video_path}")
                        self.generated_videos.append(video_path)
                    else:
                        logger.error(f"Failed to generate video for script {i+1}")
                    
                except Exception as e:
                    logger.error(f"Error generating video {i+1}: {e}")
                    logger.error(traceback.format_exc())
            
            # 3. Schedule posts if requested
            if schedule and self.generated_videos:
                logger.info("Scheduling posts for social media")
                schedule_result = schedule_posts(
                    self.generated_videos,
                    platforms=self.config["scheduling"]["platforms"],
                    frequency=self.config["scheduling"]["posting_frequency"],
                    optimal_times=self.config["scheduling"]["optimal_times"]
                )
                
                logger.info(f"Scheduled {len(schedule_result['scheduled_posts'])} posts")
            
            # Summary
            logger.info("Content pipeline completed")
            logger.info(f"Generated {len(self.generated_scripts)} scripts")
            logger.info(f"Generated {len(self.generated_videos)} videos")
            
            return {
                "scripts": self.generated_scripts,
                "videos": self.generated_videos,
                "output_dir": self.output_dir
            }
            
        except Exception as e:
            logger.error(f"Error in content pipeline: {e}")
            logger.error(traceback.format_exc())
            return {
                "error": str(e),
                "scripts": self.generated_scripts,
                "videos": self.generated_videos,
                "output_dir": self.output_dir
            }
    
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
            
            # Generate avatar
            avatar_result = generate_avatar_set(
                avatar,
                style=script["variation"],
                output_dir=os.path.join(self.output_dir, "avatars", avatar)
            )
            
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
                return video_path
            else:
                logger.error("Failed to generate video")
                return None
                
        except Exception as e:
            logger.error(f"Error generating video: {e}")
            logger.error(traceback.format_exc())
            return None
    
    def enhance_video_quality(self, video_path, output_path=None):
        """Enhance video quality for production-level output."""
        try:
            from video_editing.video_enhancer import enhance_video
            
            if output_path is None:
                dirname = os.path.dirname(video_path)
                basename = os.path.basename(video_path)
                output_path = os.path.join(dirname, f"enhanced_{basename}")
            
            # Enhance video
            enhanced_path = enhance_video(
                video_path, 
                output_path,
                add_captions=True,
                add_music=True,
                color_grade=True
            )
            
            if enhanced_path:
                logger.info(f"Enhanced video: {enhanced_path}")
                return enhanced_path
            else:
                logger.error("Failed to enhance video")
                return video_path
                
        except Exception as e:
            logger.error(f"Error enhancing video: {e}")
            return video_path


def main():
    """Main entry point."""
    # Create argument parser
    parser = argparse.ArgumentParser(description="Run the OWLmarketing content pipeline")
    
    parser.add_argument("--output-dir", type=str, default=None,
                       help="Output directory for generated content")
    
    parser.add_argument("--config", type=str, default=None,
                       help="Path to pipeline configuration file")
    
    parser.add_argument("--avatar-name", type=str, default=None,
                       help="Name of the avatar to use (e.g., emily, sophia)")
    
    parser.add_argument("--script-count", type=int, default=None,
                       help="Number of scripts to generate")
    
    parser.add_argument("--video-count", type=int, default=None,
                       help="Number of videos to generate")
    
    parser.add_argument("--no-schedule", action="store_true",
                       help="Skip scheduling the generated content")
    
    parser.add_argument("--script-file", type=str, default=None,
                       help="Generate a single video from a script file")
    
    parser.add_argument("--enhance-video", type=str, default=None,
                       help="Enhance an existing video file")
    
    # Parse arguments
    args = parser.parse_args()
    
    # Create logs directory if it doesn't exist
    logs_dir = os.path.join(project_root, "logs")
    os.makedirs(logs_dir, exist_ok=True)
    
    # Initialize pipeline
    pipeline = ContentPipeline(
        output_dir=args.output_dir,
        config_file=args.config
    )
    
    # Handle different modes
    if args.enhance_video:
        # Enhance a single video
        if not os.path.exists(args.enhance_video):
            logger.error(f"Video file not found: {args.enhance_video}")
            return 1
        
        enhanced_path = pipeline.enhance_video_quality(args.enhance_video)
        print(f"Enhanced video: {enhanced_path}")
        return 0
    
    if args.script_file:
        # Generate a single video from a script file
        if not os.path.exists(args.script_file):
            logger.error(f"Script file not found: {args.script_file}")
            return 1
        
        video_path = pipeline.generate_single_video(args.script_file, args.avatar_name)
        if video_path:
            print(f"Generated video: {video_path}")
            return 0
        else:
            logger.error("Failed to generate video")
            return 1
    
    # Run full pipeline with templates
    result = pipeline.run_full_pipeline(
        avatar_name=args.avatar_name,
        script_count=args.script_count,
        video_count=args.video_count,
        schedule=not args.no_schedule
    )
    
    # Print summary
    print("\nPipeline completed")
    print(f"Generated {len(result['scripts'])} scripts")
    print(f"Generated {len(result['videos'])} videos")
    print(f"Output directory: {result['output_dir']}")
    
    if 'error' in result:
        print(f"Error: {result['error']}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main()) 