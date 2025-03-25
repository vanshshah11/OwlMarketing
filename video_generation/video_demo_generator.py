#!/usr/bin/env python3
"""
Video Demo Generator - Creates dynamic app demo videos integrated with avatars.
This module integrates the UI Generator with video editing to produce authentic UGC-style app demos.
"""

import os
import sys
import json
import logging
import cv2
import numpy as np
from pathlib import Path
import subprocess
import tempfile
import random
import shutil
from typing import Dict, List, Tuple, Optional, Union
import time
from datetime import datetime

# Local imports
from .ui_generator import get_ui_generator, FoodItem

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('video_demo_generator')

# Get project root directory
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

class VideoDemoSequence:
    """Represents a video demo sequence with UI screens and transitions."""
    
    def __init__(self, name, food_item=None, duration=5.0):
        """Initialize the sequence."""
        self.name = name
        self.food_item = food_item
        self.duration = duration
        self.screens = []
        self.keyframes = []
        self.output_dir = None
        
    def add_screen(self, screen_type, variant, duration=1.0, transition_duration=0.5):
        """Add a screen to the sequence."""
        self.screens.append({
            'screen_type': screen_type,
            'variant': variant,
            'duration': duration,
            'transition_duration': transition_duration
        })
        
    def add_keyframe(self, time, action, params=None):
        """Add a keyframe for animation or interaction."""
        if params is None:
            params = {}
            
        self.keyframes.append({
            'time': time,
            'action': action,
            'params': params
        })
        
    def to_dict(self):
        """Convert to dictionary."""
        return {
            'name': self.name,
            'food_item': self.food_item.to_dict() if self.food_item else None,
            'duration': self.duration,
            'screens': self.screens,
            'keyframes': self.keyframes,
            'output_dir': self.output_dir
        }
        
    @classmethod
    def from_dict(cls, data):
        """Create from dictionary."""
        sequence = cls(
            data['name'],
            FoodItem.from_dict(data['food_item']) if data['food_item'] else None,
            data.get('duration', 5.0)
        )
        
        sequence.screens = data.get('screens', [])
        sequence.keyframes = data.get('keyframes', [])
        sequence.output_dir = data.get('output_dir')
        
        return sequence
        
    def get_preset_sequence(self, sequence_name=None):
        """Get a preset sequence definition."""
        if sequence_name is None:
            sequence_name = self.name
            
        # Scan to result sequence
        if sequence_name == 'scan_to_result':
            self.screens = [
                {
                    'screen_type': 'camera_interface',
                    'variant': 'scanning',
                    'duration': 1.5,
                    'transition_duration': 0.3
                },
                {
                    'screen_type': 'camera_interface',
                    'variant': 'processing',
                    'duration': 1.0,
                    'transition_duration': 0.5
                },
                {
                    'screen_type': 'results_screen',
                    'variant': 'result',
                    'duration': 2.5,
                    'transition_duration': 0.0
                }
            ]
            
            self.keyframes = [
                {
                    'time': 0.5,
                    'action': 'tap',
                    'params': {'target': 'capture_button'}
                },
                {
                    'time': 2.0,
                    'action': 'processing_animation',
                    'params': {'duration': 0.8}
                },
                {
                    'time': 3.0,
                    'action': 'reveal_nutrition',
                    'params': {'duration': 1.0}
                }
            ]
            
        # Browse food log sequence
        elif sequence_name == 'browse_food_log':
            self.screens = [
                {
                    'screen_type': 'food_log',
                    'variant': 'overview',
                    'duration': 1.5,
                    'transition_duration': 0.3
                },
                {
                    'screen_type': 'food_log',
                    'variant': 'detail',
                    'duration': 1.5,
                    'transition_duration': 0.5
                },
                {
                    'screen_type': 'results_screen',
                    'variant': 'result',
                    'duration': 2.0,
                    'transition_duration': 0.0
                }
            ]
            
            self.keyframes = [
                {
                    'time': 0.7,
                    'action': 'tap',
                    'params': {'target': 'log_item'}
                },
                {
                    'time': 2.5,
                    'action': 'scroll',
                    'params': {'direction': 'up', 'distance': 200}
                }
            ]
            
        # Result to log sequence
        elif sequence_name == 'result_to_log':
            self.screens = [
                {
                    'screen_type': 'results_screen',
                    'variant': 'result',
                    'duration': 1.5,
                    'transition_duration': 0.3
                },
                {
                    'screen_type': 'food_log',
                    'variant': 'adding',
                    'duration': 1.0,
                    'transition_duration': 0.3
                },
                {
                    'screen_type': 'food_log',
                    'variant': 'updated',
                    'duration': 2.5,
                    'transition_duration': 0.0
                }
            ]
            
            self.keyframes = [
                {
                    'time': 0.8,
                    'action': 'tap',
                    'params': {'target': 'add_to_log_button'}
                },
                {
                    'time': 2.0,
                    'action': 'confirmation_animation',
                    'params': {'duration': 0.5}
                }
            ]
            
        self.duration = sum(screen['duration'] for screen in self.screens)
        return self


class VideoDemoGenerator:
    """Generates dynamic app demo videos integrated with avatars."""
    
    def __init__(self, ui_generator=None):
        """Initialize the video demo generator with UI generator."""
        self.logger = logging.getLogger(__name__)
        self.ui_generator = ui_generator or self._init_ui_generator()
        self.config = self._load_config()
        
    def _init_ui_generator(self):
        """Initialize the UI generator if not provided."""
        from video_generation.ui_generator import UIGenerator
        return UIGenerator()
    
    def _load_config(self) -> Dict:
        """Load UI configuration from config file."""
        config_path = os.path.join('config', 'app_ui_config.json')
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
                self.logger.info(f"Loaded UI configuration from {config_path}")
                return config
        except (FileNotFoundError, json.JSONDecodeError) as e:
            self.logger.warning(f"Failed to load UI config: {e}")
            return {}
        
    def generate_demo_sequence(self, sequence_name: str, food_item: Dict = None, output_dir: str = None, output_video: str = None) -> Dict:
        """
        Generate a complete demo sequence based on a predefined sequence configuration.
        
        Args:
            sequence_name: Name of the sequence to generate
            food_item: Food item to use in the demo (or will use default)
            output_dir: Directory to save generated files
            output_video: Path to save the final video
            
        Returns:
            Dictionary with demo sequence information
        """
        # Create output directory if provided
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
            
        # Load sequence configuration from app UI config    
        config = self._load_config()
        if 'demo_sequences' not in config or sequence_name not in config['demo_sequences']:
            self.logger.warning(f"Sequence '{sequence_name}' not found in configuration")
            return {}
            
        sequence_config = config['demo_sequences'][sequence_name]
        
        # Create food item if not provided
        if food_item is None:
            # Use a default food item from config
            if 'common_food_items' in config and config['common_food_items']:
                food_item = random.choice(config['common_food_items'])
            else:
                food_item = {
                    "name": "Chicken Salad",
                    "calories": 350,
                    "protein": 30,
                    "carbs": 15,
                    "fat": 20
                }
        
        # Save food item metadata
        self.logger.info(f"Generating demo sequence '{sequence_name}' with food item: {food_item['name']}")
        if output_dir:
            food_item_path = os.path.join(output_dir, "food_item.json")
            with open(food_item_path, 'w') as f:
                json.dump(food_item, f, indent=2)
        
        # Generate UI screens for each step in the sequence
        screens = self._generate_ui_screens(sequence_config, food_item, output_dir)
        
        # Generate animations/transitions between screens
        animations = self._generate_animations(sequence_config, screens, output_dir)
        
        # Create the final video if requested
        if output_video and animations:
            self._create_final_video(animations, output_video)
        
        # Create and save sequence metadata
        sequence_meta = {
            "name": sequence_name,
            "description": sequence_config.get("description", ""),
            "screens": screens,
            "animations": animations,
            "total_duration": sum(screen.get("duration", 0) for screen in sequence_config.get("screens", [])),
            "food_item": food_item
        }
        
        if output_dir:
            meta_path = os.path.join(output_dir, "sequence_meta.json")
            with open(meta_path, 'w') as f:
                json.dump(sequence_meta, f, indent=2)
                
        return sequence_meta
        
    def _generate_ui_screens(self, sequence_config: Dict, food_item: Dict, output_dir: str) -> List[Dict]:
        """
        Generate the UI screens needed for the demo sequence.
        
        Args:
            sequence_config: Configuration for the sequence
            food_item: Food item to use in UI screens
            output_dir: Directory to save generated files
            
        Returns:
            List of dictionaries with screen information
        """
        screens = []
        
        # First check if we have existing assets that match what we need
        existing_assets = self._check_existing_assets(food_item)
        
        # Process each screen in the sequence
        for i, screen_config in enumerate(sequence_config.get("screens", [])):
            screen_type = screen_config.get("screen")
            variant = screen_config.get("variant", "default")
            duration = screen_config.get("duration", 1.0)
            
            # File naming
            screen_filename = f"{i+1:02d}_{screen_type}_{variant}.png"
            screen_path = os.path.join(output_dir, screen_filename) if output_dir else None
            
            # Check if we already have this asset
            use_existing = False
            if screen_type in existing_assets.get('screenshots', {}):
                existing_path = existing_assets['screenshots'][screen_type]
                if os.path.exists(existing_path):
                    self.logger.info(f"Using existing UI asset: {existing_path}")
                    if screen_path:
                        shutil.copy(existing_path, screen_path)
                    use_existing = True
            
            # Generate new screen if needed
            if not use_existing:
                self.logger.info(f"Generating UI screen: {screen_type} ({variant})")
                
                # Check for real app assets first
                real_asset_dir = os.path.join('assets', 'app_ui', 'screenshots')
                real_assets = []
                if os.path.exists(real_asset_dir):
                    for asset in os.listdir(real_asset_dir):
                        if asset.endswith('.png') or asset.endswith('.jpg'):
                            # Match screen type
                            if screen_type.lower() in asset.lower():
                                # Match food item if possible
                                if food_item and 'name' in food_item and food_item['name'].lower().replace(' ', '_') in asset.lower():
                                    real_assets.append(os.path.join(real_asset_dir, asset))
                                elif 'generated' not in asset.lower():
                                    # Include general assets but prioritize food-specific ones
                                    real_assets.append(os.path.join(real_asset_dir, asset))
                
                if real_assets:
                    # Prioritize food-specific assets
                    real_assets.sort(key=lambda x: 'generated' not in x.lower())
                    real_assets.sort(key=lambda x: food_item['name'].lower().replace(' ', '_') in x.lower() if food_item and 'name' in food_item else False, reverse=True)
                    
                    # Use the best real asset
                    self.logger.info(f"Using real app asset: {real_assets[0]}")
                    if screen_path:
                        shutil.copy(real_assets[0], screen_path)
                else:
                    # Generate using UI generator
                    self.ui_generator.generate_ui_screen(screen_type, food_item, screen_path)
            
            # Add screen to the list
            screen_info = {
                "type": screen_type,
                "variant": variant,
                "duration": duration,
                "path": screen_path,
                "food_item": food_item
            }
            screens.append(screen_info)
        
        return screens
    
    def _check_existing_assets(self, food_item: Dict) -> Dict:
        """Check if we have existing app UI assets for this food item."""
        assets = {}
        
        # Check in the screenshots directory
        screenshots_dir = os.path.join('assets', 'app_ui', 'screenshots')
        if os.path.exists(screenshots_dir):
            # Look for food-specific screenshots first
            if food_item and 'name' in food_item:
                food_name = food_item['name'].lower().replace(' ', '_')
                for filename in os.listdir(screenshots_dir):
                    if food_name in filename.lower():
                        # Extract the screen type from filename
                        for screen_type in ['home_screen', 'camera_interface', 'results_screen', 'food_log']:
                            if screen_type in filename:
                                assets[screen_type] = os.path.join(screenshots_dir, filename)
                                break
            
            # Look for general screenshots
            for screen_type in ['home_screen', 'camera_interface', 'results_screen', 'food_log']:
                if screen_type not in assets:
                    for filename in os.listdir(screenshots_dir):
                        if screen_type in filename and 'generated' not in filename:
                            assets[screen_type] = os.path.join(screenshots_dir, filename)
                            break
                            
        return assets
    
    def _generate_animations(self, sequence_config: Dict, screens: List[Dict], output_dir: str) -> List[Dict]:
        """Generate transition animations between screens."""
        animations = []
        
        # For now, we're just using static transitions between screens
        # This could be enhanced with actual animated transitions
        
        for i in range(len(screens) - 1):
            current_screen = screens[i]
            next_screen = screens[i+1]
            transition_type = current_screen.get('transition', 'none')
            
            if transition_type == 'none':
                # No animation needed
                continue
                
            # For now, we just log that we would create an animation
            self.logger.info(f"Would create {transition_type} animation from {current_screen['type']} to {next_screen['type']}")
            
            # In a real implementation, this would create the animation files
            animation = {
                'type': transition_type,
                'from_screen': current_screen['type'],
                'to_screen': next_screen['type'],
                'duration': 0.5  # Default transition duration
            }
            
            animations.append(animation)
            
        return animations
    
    def _create_final_video(self, animations: List[Dict], output_video: str):
        """Create the final video by combining screens and animations."""
        # This is a placeholder for the actual video creation logic
        # In a real implementation, this would use a video editing library
        
        self.logger.info(f"Would create final video at {output_video}")
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(output_video), exist_ok=True)
        
        # For now, just create an empty file as a placeholder
        with open(output_video, 'w') as f:
            f.write("Placeholder for generated video")
            
        self.logger.info(f"Created placeholder video file at {output_video}")
        
    def render_demo_video(self, sequence_data, output_path=None, fps=30, resolution=(1080, 1920)):
        """Render a video from the sequence data."""
        if output_path is None:
            output_path = os.path.join(
                sequence_data['output_dir'], 
                f"{os.path.basename(sequence_data['output_dir'])}.mp4"
            )
            
        # Prepare frames list for FFmpeg
        frames_list_path = os.path.join(sequence_data['output_dir'], "frames_list.txt")
        
        # Collect all frames
        all_frames = []
        
        # Add regular screens
        for screen in sequence_data['screens']:
            # Duration in frames
            frame_duration = int(screen['duration'] * fps)
            
            # Check if this screen has animation frames
            has_animations = False
            for anim in sequence_data['animations']:
                if anim['screen_index'] == screen['index']:
                    has_animations = True
                    break
                    
            if not has_animations:
                # Use static screen for the whole duration
                for _ in range(frame_duration):
                    all_frames.append(screen['path'])
                    
        # Add animation frames at their specific times
        for anim in sequence_data['animations']:
            frame_time = anim['time']
            frame_index = int(frame_time * fps)
            
            # Ensure index is within bounds
            if 0 <= frame_index < len(all_frames):
                all_frames[frame_index] = anim['path']
                
        # Write frames list
        with open(frames_list_path, 'w') as f:
            for i, frame_path in enumerate(all_frames):
                frame_duration = 1.0 / fps
                f.write(f"file '{frame_path}'\n")
                f.write(f"duration {frame_duration}\n")
                
            # Add last frame to avoid truncation
            f.write(f"file '{all_frames[-1]}'\n")
            
        # Use FFmpeg to create video
        try:
            width, height = resolution
            cmd = [
                'ffmpeg',
                '-y',  # Overwrite output file if it exists
                '-f', 'concat',
                '-safe', '0',
                '-i', frames_list_path,
                '-c:v', 'libx264',
                '-preset', 'medium',
                '-crf', '23',
                '-vf', f'scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2',
                '-pix_fmt', 'yuv420p',
                '-r', str(fps),
                '-movflags', '+faststart',  # Optimize for web streaming
                output_path
            ]
            
            # Set high-quality encoding parameters
            cmd.extend([
                "-c:v", self.quality_settings["codec"],
                "-preset", self.quality_settings["preset"],
                "-crf", str(self.quality_settings["crf"]),
                "-b:v", self.quality_settings["bitrate"],
                "-pix_fmt", self.quality_settings["pixel_format"],
                "-r", str(fps),
                "-movflags", "+faststart",  # Optimize for web streaming
                output_path
            ])
            
            logger.info(f"Rendering video: {' '.join(cmd)}")
            subprocess.run(cmd, check=True)
            
            logger.info(f"Video rendered successfully: {output_path}")
            return output_path
        except subprocess.CalledProcessError as e:
            logger.error(f"Error rendering video: {e}")
            return None
            
    def generate_complete_demo(self, food_name, sequence_name="scan_to_result", custom_duration=None):
        """Generate a complete demo video from start to finish."""
        try:
            # Create sequence
            sequence = VideoDemoSequence(sequence_name, food_name, custom_duration or 5.0)
            
            # Use preset sequence configuration
            sequence.get_preset_sequence(sequence_name)
            
            # Generate and render demo
            logger.info(f"Generating complete demo for {food_name} using sequence: {sequence_name}")
            sequence_data = self.generate_demo_sequence(sequence_name, food_name)
            
            if not sequence_data:
                logger.error("Failed to generate demo sequence")
                return None
            
            # Ensure output directory exists
            output_dir = os.path.join(self.output_dir, "videos")
            os.makedirs(output_dir, exist_ok=True)
            
            # Sanitize food name for filename
            safe_food_name = food_name.replace(" ", "_").lower()
            
            # Generate output filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"{sequence_name}_{safe_food_name}_{timestamp}.mp4"
            output_path = os.path.join(output_dir, output_filename)
            
            # Render the video
            self.render_demo_video(sequence_data, output_path)
            
            # Add music and enhance the video
            enhanced_path = self._enhance_video(output_path)
            
            return {
                "video_path": enhanced_path or output_path,
                "food_name": food_name,
                "sequence_name": sequence_name,
                "duration": sequence.duration
            }
        except Exception as e:
            logger.error(f"Error generating complete demo: {e}")
            return None
            
    def _enhance_video(self, video_path):
        """Enhance the video with music, color grading, and other post-processing."""
        try:
            # Create enhanced output path
            output_dir = os.path.dirname(video_path)
            filename = os.path.basename(video_path)
            enhanced_path = os.path.join(output_dir, f"enhanced_{filename}")
            
            # Get a random royalty-free music file if available
            music_dir = os.path.join(project_root, "assets", "audio", "music")
            music_file = None
            
            if os.path.exists(music_dir):
                music_files = [f for f in os.listdir(music_dir) if f.endswith(('.mp3', '.wav'))]
                if music_files:
                    music_file = os.path.join(music_dir, random.choice(music_files))
            
            # Get video duration
            ffprobe_cmd = [
                "ffprobe", "-v", "error", "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1", video_path
            ]
            
            try:
                result = subprocess.run(ffprobe_cmd, check=True, capture_output=True, text=True)
                duration = float(result.stdout.strip())
            except subprocess.CalledProcessError:
                logger.warning("Could not determine video duration, using default enhancement")
                duration = 5.0
            
            # Build ffmpeg command for enhancement
            ffmpeg_cmd = ["ffmpeg", "-y", "-i", video_path]
            
            # Add music if available
            if music_file:
                ffmpeg_cmd.extend([
                    "-i", music_file,
                    "-filter_complex",
                    f"[1:a]afade=t=out:st={duration-1.5}:d=1.5,aformat=sample_fmts=fltp:sample_rates=44100:channel_layouts=stereo,volume=0.3[a1];"
                    f"[0:a][a1]amix=inputs=2:duration=shortest[a]",
                    "-map", "0:v", "-map", "[a]"
                ])
            
            # Add color grading and visual enhancements
            ffmpeg_cmd.extend([
                "-vf", "unsharp=3:3:1.5:3:3:0.5",  # Sharpen
                "-c:v", self.quality_settings["codec"],
                "-preset", self.quality_settings["preset"],
                "-crf", str(self.quality_settings["crf"]),
                "-b:v", self.quality_settings["bitrate"],
                "-pix_fmt", self.quality_settings["pixel_format"],
                "-movflags", "+faststart",
                enhanced_path
            ])
            
            # Run the enhancement command
            logger.info(f"Enhancing video: {video_path}")
            subprocess.run(ffmpeg_cmd, check=True)
            
            if os.path.exists(enhanced_path):
                logger.info(f"Video enhanced: {enhanced_path}")
                return enhanced_path
            else:
                logger.warning("Enhanced video not created, returning original")
                return video_path
                
        except Exception as e:
            logger.error(f"Error enhancing video: {e}")
            return video_path  # Return original if enhancement fails


# Get singleton instance
_demo_generator_instance = None

def get_demo_generator(force_new=False):
    """Get the singleton demo generator instance."""
    global _demo_generator_instance
    
    if _demo_generator_instance is None or force_new:
        _demo_generator_instance = VideoDemoGenerator()
        
    return _demo_generator_instance


if __name__ == "__main__":
    import argparse
    
    # Set up argument parser
    parser = argparse.ArgumentParser(description="Generate a demo video")
    parser.add_argument("--sequence", type=str, default="quick_scan_pizza", 
                        help="Sequence name from config")
    parser.add_argument("--output", type=str, default="output/demos",
                       help="Output directory")
    parser.add_argument("--food", type=str, help="Food item name (optional)")
    
    args = parser.parse_args()
    
    # Initialize generator
    generator = VideoDemoGenerator()
    
    # Get food item
    food_item = None
    
    # If food argument is provided, use it
    if args.food:
        # Find the matching food item in config
        for item in generator.config.get('common_food_items', []):
            if item['name'].lower() == args.food.lower():
                food_item = item
                break
    # Otherwise parse food name from sequence (e.g., quick_scan_pizza -> Pizza)
    elif '_' in args.sequence:
        food_name = args.sequence.split('_')[-1].capitalize()
        # Find the matching food item in config
        for item in generator.config.get('common_food_items', []):
            if item['name'].lower() == food_name.lower():
                food_item = item
                break
    
    # Generate the sequence
    result = generator.generate_demo_sequence(
        sequence_name=args.sequence,
        output_dir=args.output,
        food_item=food_item
    )
    
    print(f"Generated demo sequence: {args.sequence}")
    
    # Check if result is a VideoDemoSequence object or a dict
    if hasattr(result, 'output_path'):
        output_path = result.output_path
        duration = result.duration
    else:
        # It's a dict (for backward compatibility)
        output_path = result.get('output_video', os.path.join(args.output, 'demo.mp4'))
        duration = result.get('total_duration', 0)
    
    print(f"Output video: {output_path}")
    if food_item:
        print(f"Food item: {food_item['name']}")
    print(f"Total duration: {duration} seconds")  