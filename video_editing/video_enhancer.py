#!/usr/bin/env python3
"""
Video Enhancer - Applies production-level enhancements to generated videos.

This module adds professional quality to the generated videos by:
1. Adding background music
2. Generating and adding captions
3. Applying color grading
4. Adding visual effects (transitions, overlays)
5. Optimizing output for social media platforms
"""

import os
import sys
import json
import logging
import subprocess
import tempfile
import random
from pathlib import Path
import shutil
from datetime import datetime
import math
import traceback
from typing import Dict, List, Optional, Tuple, Union

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('video_enhancer')

# Get project root directory
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

# Import local modules
sys.path.append(project_root)
from video_editing.hooks_templates import HOOK_TEMPLATES

class VideoEnhancer:
    """Apply production-level enhancements to generated videos."""
    
    def __init__(self, 
                output_dir=None, 
                music_dir=None, 
                font_dir=None,
                effects_dir=None):
        """Initialize the video enhancer.
        
        Args:
            output_dir: Directory for enhanced videos
            music_dir: Directory containing music tracks
            font_dir: Directory containing fonts
            effects_dir: Directory containing visual effects
        """
        # Set directories
        self.output_dir = output_dir or os.path.join(project_root, "output", "enhanced_videos")
        self.music_dir = music_dir or os.path.join(project_root, "assets", "audio", "music")
        self.font_dir = font_dir or os.path.join(project_root, "assets", "fonts")
        self.effects_dir = effects_dir or os.path.join(project_root, "assets", "effects")
        
        # Create directories if they don't exist
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.music_dir, exist_ok=True)
        os.makedirs(self.font_dir, exist_ok=True)
        os.makedirs(self.effects_dir, exist_ok=True)
        
        # Set high-quality video settings
        self.quality_settings = {
            "bitrate": "8M",
            "codec": "libx264",
            "preset": "slow",  # Options: ultrafast, superfast, veryfast, faster, fast, medium, slow, slower, veryslow
            "crf": 18,  # Lower is higher quality (18-28 is a good range)
            "pixel_format": "yuv420p"  # Compatible with most players
        }
        
        # Tracks for social media platforms
        self.platform_settings = {
            "tiktok": {
                "resolution": (1080, 1920),
                "aspect_ratio": "9:16",
                "max_duration": 60,
                "bitrate": "6M",
                "audio_bitrate": "192k"
            },
            "instagram": {
                "resolution": (1080, 1920),
                "aspect_ratio": "9:16",
                "max_duration": 60,
                "bitrate": "6M",
                "audio_bitrate": "192k"
            },
            "youtube": {
                "resolution": (1920, 1080),
                "aspect_ratio": "16:9",
                "max_duration": 600,
                "bitrate": "10M",
                "audio_bitrate": "256k"
            }
        }
        
        # Color grading presets
        self.color_presets = {
            "vibrant": "eq=saturation=1.3:contrast=1.1:brightness=0.05",
            "cinematic": "curves=master='0/0 0.25/0.15 0.5/0.5 0.75/0.85 1/1':red='0/0 0.5/0.5 1/1':green='0/0 0.5/0.5 1/1':blue='0/0 0.5/0.5 1/1'",
            "warm": "colorbalance=rs=0.1:gs=0.01:bs=-0.1:rm=0.05:gm=0.01:bm=-0.05:rh=0.05:gh=0.01:bh=-0.05",
            "cool": "colorbalance=rs=-0.05:gs=0.01:bs=0.1:rm=-0.025:gm=0.01:bm=0.05:rh=-0.025:gh=0.01:bh=0.05",
            "high_contrast": "eq=contrast=1.2:saturation=1.1:brightness=0.02"
        }
        
        # Check for ffmpeg installation
        try:
            subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
            logger.info("FFmpeg is installed and available")
        except (subprocess.SubprocessError, FileNotFoundError):
            logger.error("FFmpeg is not installed or not in PATH - video enhancement will fail")
        
        logger.info(f"Initialized VideoEnhancer with output directory: {self.output_dir}")
    
    def enhance_video(self, 
                     input_video, 
                     output_path=None, 
                     add_music=True, 
                     add_captions=True, 
                     color_grade=True,
                     platform="tiktok"):
        """
        Enhance a video with production-level quality.
        
        Args:
            input_video: Path to input video
            output_path: Path for enhanced output video (if None, will generate one)
            add_music: Whether to add background music
            add_captions: Whether to add captions
            color_grade: Whether to apply color grading
            platform: Target platform ("tiktok", "instagram", "youtube")
            
        Returns:
            Path to enhanced video or None if enhancement failed
        """
        try:
            # Validate input video
            if not os.path.exists(input_video):
                logger.error(f"Input video not found: {input_video}")
                return None
            
            # Generate output path if not provided
            if output_path is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"enhanced_{os.path.basename(input_video)}"
                if '.' not in filename:
                    filename += '.mp4'
                output_path = os.path.join(self.output_dir, filename)
            
            # Ensure output directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            logger.info(f"Enhancing video: {input_video} -> {output_path}")
            
            # Create temporary directory for processing
            temp_dir = tempfile.mkdtemp()
            
            try:
                # Extract video info
                video_info = self._get_video_info(input_video)
                logger.info(f"Video info: {video_info}")
                
                # Get platform settings
                platform_config = self.platform_settings.get(platform.lower(), self.platform_settings["tiktok"])
                
                # Perform enhancements in sequence
                current_video = input_video
                
                # 1. Resize and optimize for target platform
                optimized_video = os.path.join(temp_dir, "optimized.mp4")
                current_video = self._optimize_for_platform(current_video, optimized_video, platform_config)
                
                # 2. Apply color grading if requested
                if color_grade:
                    color_graded_video = os.path.join(temp_dir, "color_graded.mp4")
                    current_video = self._apply_color_grading(current_video, color_graded_video)
                
                # 3. Add captions if requested
                if add_captions:
                    # First extract captions/script if available
                    captions = self._extract_captions_from_video(input_video)
                    
                    # Only add captions if we successfully extracted them
                    if captions:
                        captioned_video = os.path.join(temp_dir, "captioned.mp4")
                        current_video = self._add_captions(current_video, captioned_video, captions)
                
                # 4. Add music if requested
                if add_music:
                    music_video = os.path.join(temp_dir, "with_music.mp4")
                    current_video = self._add_background_music(current_video, music_video, video_info["duration"])
                
                # 5. Add final effects and branding
                final_video = os.path.join(temp_dir, "final.mp4")
                current_video = self._add_final_effects(current_video, final_video)
                
                # 6. Final optimization for target platform
                self._final_export(current_video, output_path, platform_config)
                
                logger.info(f"Video enhancement complete: {output_path}")
                return output_path
                
            finally:
                # Clean up temporary directory
                shutil.rmtree(temp_dir)
                
        except Exception as e:
            logger.error(f"Error enhancing video: {e}")
            logger.error(traceback.format_exc())
            return None
    
    def _get_video_info(self, video_path):
        """Extract video information using ffprobe."""
        try:
            # Get duration
            duration_cmd = [
                "ffprobe", "-v", "error", "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1", video_path
            ]
            duration_result = subprocess.run(duration_cmd, capture_output=True, text=True, check=True)
            duration = float(duration_result.stdout.strip())
            
            # Get resolution
            res_cmd = [
                "ffprobe", "-v", "error", "-select_streams", "v:0",
                "-show_entries", "stream=width,height",
                "-of", "json", video_path
            ]
            res_result = subprocess.run(res_cmd, capture_output=True, text=True, check=True)
            res_data = json.loads(res_result.stdout)
            
            if "streams" in res_data and res_data["streams"]:
                width = res_data["streams"][0].get("width", 1080)
                height = res_data["streams"][0].get("height", 1920)
            else:
                # Default to vertical video if can't detect
                width, height = 1080, 1920
            
            # Get frame rate
            fps_cmd = [
                "ffprobe", "-v", "error", "-select_streams", "v:0",
                "-show_entries", "stream=r_frame_rate",
                "-of", "default=noprint_wrappers=1:nokey=1", video_path
            ]
            fps_result = subprocess.run(fps_cmd, capture_output=True, text=True, check=True)
            fps_str = fps_result.stdout.strip()
            
            # Parse frame rate (format could be "30/1" or "30000/1001")
            if "/" in fps_str:
                num, den = map(int, fps_str.split("/"))
                fps = num / den
            else:
                fps = float(fps_str)
            
            # Get audio info
            audio_cmd = [
                "ffprobe", "-v", "error", "-select_streams", "a:0",
                "-show_entries", "stream=codec_name,channels,sample_rate",
                "-of", "json", video_path
            ]
            audio_result = subprocess.run(audio_cmd, capture_output=True, text=True)
            
            has_audio = False
            audio_channels = 0
            if audio_result.returncode == 0:
                audio_data = json.loads(audio_result.stdout)
                if "streams" in audio_data and audio_data["streams"]:
                    has_audio = True
                    audio_channels = audio_data["streams"][0].get("channels", 0)
            
            return {
                "duration": duration,
                "width": width,
                "height": height,
                "fps": fps,
                "has_audio": has_audio,
                "audio_channels": audio_channels,
                "aspect_ratio": f"{width}:{height}"
            }
        except Exception as e:
            logger.error(f"Error getting video info: {e}")
            # Return default values
            return {
                "duration": 10.0,
                "width": 1080,
                "height": 1920,
                "fps": 30.0,
                "has_audio": False,
                "audio_channels": 0,
                "aspect_ratio": "9:16"
            }
    
    def _optimize_for_platform(self, input_video, output_path, platform_config):
        """Resize and optimize video for target platform."""
        try:
            # Get target resolution
            target_resolution = platform_config["resolution"]
            target_width, target_height = target_resolution
            
            # Get video info
            video_info = self._get_video_info(input_video)
            original_width, original_height = video_info["width"], video_info["height"]
            
            # Determine scaling
            if original_width / original_height > target_width / target_height:
                # Original is wider than target, scale by height
                scale_filter = f"scale=-1:{target_height}"
            else:
                # Original is taller than target, scale by width
                scale_filter = f"scale={target_width}:-1"
            
            # Build ffmpeg command
            cmd = [
                "ffmpeg", "-y",
                "-i", input_video,
                "-vf", f"{scale_filter},crop={target_width}:{target_height}:(in_w-{target_width})/2:(in_h-{target_height})/2",
                "-c:v", "libx264",
                "-preset", "medium",
                "-crf", "23",
                "-pix_fmt", "yuv420p",
                "-c:a", "aac",
                "-b:a", platform_config["audio_bitrate"],
                output_path
            ]
            
            # Execute the command
            subprocess.run(cmd, check=True)
            logger.info(f"Optimized video for {platform_config['aspect_ratio']} aspect ratio")
            
            return output_path
        except Exception as e:
            logger.error(f"Error optimizing for platform: {e}")
            # Return the original video as fallback
            shutil.copy2(input_video, output_path)
            return output_path
    
    def _apply_color_grading(self, input_video, output_path):
        """Apply color grading to the video."""
        try:
            # Select a color preset
            preset_name = random.choice(list(self.color_presets.keys()))
            color_filter = self.color_presets[preset_name]
            
            # Add unsharp mask for clarity
            combined_filter = f"{color_filter},unsharp=3:3:1.5:3:3:0.5"
            
            # Build ffmpeg command
            cmd = [
                "ffmpeg", "-y",
                "-i", input_video,
                "-vf", combined_filter,
                "-c:v", self.quality_settings["codec"],
                "-preset", self.quality_settings["preset"],
                "-crf", str(self.quality_settings["crf"]),
                "-c:a", "copy",
                output_path
            ]
            
            # Execute the command
            subprocess.run(cmd, check=True)
            logger.info(f"Applied color grading with preset: {preset_name}")
            
            return output_path
        except Exception as e:
            logger.error(f"Error applying color grading: {e}")
            # Return the original video as fallback
            shutil.copy2(input_video, output_path)
            return output_path
    
    def _extract_captions_from_video(self, video_path):
        """Extract captions from video file or associated script."""
        try:
            # Check for a script file with the same name
            video_name = os.path.splitext(os.path.basename(video_path))[0]
            script_path = os.path.join(os.path.dirname(video_path), f"{video_name}.json")
            
            captions = []
            
            # Try to load from script file
            if os.path.exists(script_path):
                logger.info(f"Found script file: {script_path}")
                with open(script_path, 'r') as f:
                    script_data = json.load(f)
                
                # Extract captions from script
                if "scenes" in script_data:
                    for scene in script_data["scenes"]:
                        if "text" in scene and scene["text"]:
                            captions.append({
                                "text": scene["text"],
                                "duration": scene.get("duration", 3.0)
                            })
            
            # If no captions found from script, use a default caption
            if not captions:
                # Extract app name from video path or use default
                app_name = "Optimal AI"
                if "app_demo" in video_path or "optimal" in video_path.lower():
                    app_name = "Optimal AI"
                
                # Create default caption
                captions = [
                    {
                        "text": f"Tracking calories with {app_name} is simple!",
                        "duration": 3.0
                    },
                    {
                        "text": "Just scan your food and get instant results",
                        "duration": 3.0
                    }
                ]
            
            logger.info(f"Extracted {len(captions)} captions")
            return captions
        except Exception as e:
            logger.error(f"Error extracting captions: {e}")
            return None
    
    def _add_captions(self, input_video, output_path, captions):
        """Add captions to the video."""
        try:
            if not captions:
                logger.warning("No captions to add, returning original video")
                shutil.copy2(input_video, output_path)
                return output_path
            
            # Get video info
            video_info = self._get_video_info(input_video)
            duration = video_info["duration"]
            
            # Calculate caption timing
            caption_count = len(captions)
            if caption_count == 1:
                # Single caption for whole video
                segment_duration = duration
                captions[0]["start"] = 0
                captions[0]["end"] = duration
            else:
                # Distribute captions evenly across video
                segment_duration = duration / caption_count
                for i, caption in enumerate(captions):
                    caption["start"] = i * segment_duration
                    caption["end"] = (i + 1) * segment_duration
            
            # Create drawtext filter for each caption
            filter_complex = []
            
            for i, caption in enumerate(captions):
                # Escape single quotes in text
                text = caption["text"].replace("'", "\\'")
                
                # Format text with newlines for long captions
                words = text.split()
                if len(words) > 7:
                    midpoint = len(words) // 2
                    formatted_text = " ".join(words[:midpoint]) + "\\n" + " ".join(words[midpoint:])
                else:
                    formatted_text = text
                
                # Font settings
                font_file = self._get_system_font()
                font_size = 48
                
                # Position settings - centered at bottom with margin
                x_position = "(w-text_w)/2"
                y_position = "h-text_h-120"  # Margin from bottom
                
                # Text appearance
                border_width = 3
                
                # Fade in/out duration (10% of caption duration or max 0.5s)
                fade_duration = min(0.5, (caption["end"] - caption["start"]) * 0.1)
                
                # Alpha expression for fade in/out
                alpha_expr = (
                    f"if(between(t,{caption['start']},{caption['start'] + fade_duration}),"
                    f"(t-{caption['start']})/{fade_duration},"
                    f"if(between(t,{caption['end'] - fade_duration},{caption['end']}),"
                    f"({caption['end']}-t)/{fade_duration},1))"
                )
                
                # Full drawtext filter
                drawtext_filter = (
                    f"drawtext=text='{formatted_text}':"
                    f"fontfile='{font_file}':"
                    f"fontsize={font_size}:"
                    f"fontcolor=white:"
                    f"bordercolor=black:"
                    f"borderw={border_width}:"
                    f"x={x_position}:"
                    f"y={y_position}:"
                    f"enable='between(t,{caption['start']},{caption['end']})':"
                    f"alpha={alpha_expr}"
                )
                
                filter_complex.append(drawtext_filter)
            
            # Combine all filters
            full_filter = ','.join(filter_complex)
            
            # Build ffmpeg command
            cmd = [
                "ffmpeg", "-y",
                "-i", input_video,
                "-vf", full_filter,
                "-c:v", self.quality_settings["codec"],
                "-preset", self.quality_settings["preset"],
                "-crf", str(self.quality_settings["crf"]),
                "-c:a", "copy",
                output_path
            ]
            
            # Execute the command
            subprocess.run(cmd, check=True)
            logger.info(f"Added {len(captions)} captions to video")
            
            return output_path
        except Exception as e:
            logger.error(f"Error adding captions: {e}")
            # Return the original video as fallback
            shutil.copy2(input_video, output_path)
            return output_path
    
    def _get_system_font(self):
        """Get a suitable font for captions."""
        try:
            # Check for fonts in our font directory
            for font_name in ['Arial.ttf', 'Roboto-Regular.ttf', 'OpenSans-Regular.ttf']:
                font_path = os.path.join(self.font_dir, font_name)
                if os.path.exists(font_path):
                    return font_path
            
            # Try system fonts
            system_fonts = {
                'darwin': [  # macOS
                    '/System/Library/Fonts/Helvetica.ttc',
                    '/Library/Fonts/Arial.ttf',
                    '/System/Library/Fonts/SFNSText.ttf'
                ],
                'win32': [  # Windows
                    'C:\\Windows\\Fonts\\arial.ttf',
                    'C:\\Windows\\Fonts\\calibri.ttf'
                ],
                'linux': [  # Linux
                    '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
                    '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf'
                ]
            }
            
            # Get fonts for current platform
            platform_fonts = system_fonts.get(sys.platform, [])
            
            # Try each font
            for font_path in platform_fonts:
                if os.path.exists(font_path):
                    return font_path
            
            logger.warning("No suitable font found, caption rendering may fail")
            return ""
        except Exception as e:
            logger.error(f"Error finding system font: {e}")
            return ""
    
    def _add_background_music(self, input_video, output_path, duration):
        """Add background music to the video."""
        try:
            # Check if we have music files
            music_files = [os.path.join(self.music_dir, f) for f in os.listdir(self.music_dir)
                          if f.endswith(('.mp3', '.wav', '.aac', '.m4a'))]
            
            if not music_files:
                logger.warning("No music files found, returning original video")
                shutil.copy2(input_video, output_path)
                return output_path
            
            # Get video info
            video_info = self._get_video_info(input_video)
            
            # Select a random music file
            music_file = random.choice(music_files)
            logger.info(f"Selected music: {os.path.basename(music_file)}")
            
            # Configure fading
            fade_out_start = max(0, duration - 1.5)
            fade_out_duration = min(1.5, duration)
            
            # Build the filter based on whether the original has audio
            if video_info["has_audio"]:
                # Mix original audio with music
                filter_complex = (
                    f"[1:a]afade=t=in:st=0:d=1,afade=t=out:st={fade_out_start}:d={fade_out_duration},"
                    f"volume=0.2[music];"
                    f"[0:a][music]amix=inputs=2:duration=shortest[a]"
                )
                
                # Build ffmpeg command with audio mixing
                cmd = [
                    "ffmpeg", "-y",
                    "-i", input_video,
                    "-i", music_file,
                    "-filter_complex", filter_complex,
                    "-map", "0:v",
                    "-map", "[a]",
                    "-c:v", "copy",
                    "-c:a", "aac",
                    "-b:a", "192k",
                    output_path
                ]
            else:
                # Just use the music file as audio
                cmd = [
                    "ffmpeg", "-y",
                    "-i", input_video,
                    "-i", music_file,
                    "-map", "0:v",
                    "-map", "1:a",
                    "-c:v", "copy",
                    "-c:a", "aac",
                    "-b:a", "192k",
                    "-af", f"afade=t=in:st=0:d=1,afade=t=out:st={fade_out_start}:d={fade_out_duration},volume=0.3",
                    "-shortest",
                    output_path
                ]
            
            # Execute the command
            subprocess.run(cmd, check=True)
            logger.info(f"Added background music to video")
            
            return output_path
        except Exception as e:
            logger.error(f"Error adding background music: {e}")
            # Return the original video as fallback
            shutil.copy2(input_video, output_path)
            return output_path
    
    def _add_final_effects(self, input_video, output_path):
        """Add final effects and branding to the video."""
        try:
            # Check for logo file
            logo_path = os.path.join(project_root, "assets", "app_ui", "brand", "logo.png")
            
            if not os.path.exists(logo_path):
                # No logo, just return the original
                logger.warning("No logo file found, skipping branding")
                shutil.copy2(input_video, output_path)
                return output_path
            
            # Get video info
            video_info = self._get_video_info(input_video)
            
            # Calculate logo position (top right with margin)
            logo_filter = (
                f"movie={logo_path},scale=120:-1[logo];"
                f"[0:v][logo]overlay=main_w-overlay_w-20:20:enable='between(t,0,{video_info['duration']})'[v]"
            )
            
            # Build ffmpeg command
            cmd = [
                "ffmpeg", "-y",
                "-i", input_video,
                "-filter_complex", logo_filter,
                "-map", "[v]",
                "-map", "0:a",
                "-c:v", self.quality_settings["codec"],
                "-preset", self.quality_settings["preset"],
                "-crf", str(self.quality_settings["crf"]),
                "-c:a", "copy",
                output_path
            ]
            
            # Execute the command
            subprocess.run(cmd, check=True)
            logger.info(f"Added branding and effects to video")
            
            return output_path
        except Exception as e:
            logger.error(f"Error adding final effects: {e}")
            # Return the original video as fallback
            shutil.copy2(input_video, output_path)
            return output_path
    
    def _final_export(self, input_video, output_path, platform_config):
        """Perform final export optimized for target platform."""
        try:
            # Final optimization with platform-specific settings
            cmd = [
                "ffmpeg", "-y",
                "-i", input_video,
                "-c:v", self.quality_settings["codec"],
                "-preset", self.quality_settings["preset"],
                "-crf", str(self.quality_settings["crf"]),
                "-b:v", platform_config["bitrate"],
                "-maxrate", platform_config["bitrate"],
                "-bufsize", str(int(platform_config["bitrate"].replace("M", "")) * 2) + "M",
                "-pix_fmt", self.quality_settings["pixel_format"],
                "-c:a", "aac",
                "-b:a", platform_config["audio_bitrate"],
                "-movflags", "+faststart",  # Optimize for web streaming
                output_path
            ]
            
            # Execute the command
            subprocess.run(cmd, check=True)
            logger.info(f"Exported final video optimized for {platform_config['aspect_ratio']}")
            
            return output_path
        except Exception as e:
            logger.error(f"Error in final export: {e}")
            # Return the input as fallback
            shutil.copy2(input_video, output_path)
            return output_path


# Singleton pattern
_enhancer_instance = None

def get_video_enhancer(force_new=False):
    """Get the singleton VideoEnhancer instance."""
    global _enhancer_instance
    
    if _enhancer_instance is None or force_new:
        _enhancer_instance = VideoEnhancer()
        
    return _enhancer_instance


def enhance_video(input_video, output_path=None, add_music=True, add_captions=True, color_grade=True, platform="tiktok"):
    """
    Enhance a video with production-level quality.
    
    Args:
        input_video: Path to input video
        output_path: Path for enhanced output video (if None, will generate one)
        add_music: Whether to add background music
        add_captions: Whether to add captions
        color_grade: Whether to apply color grading
        platform: Target platform ("tiktok", "instagram", "youtube")
        
    Returns:
        Path to enhanced video or None if enhancement failed
    """
    enhancer = get_video_enhancer()
    return enhancer.enhance_video(
        input_video=input_video, 
        output_path=output_path,
        add_music=add_music,
        add_captions=add_captions,
        color_grade=color_grade,
        platform=platform
    )


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Enhance videos with production-level quality")
    parser.add_argument("input", help="Input video file")
    parser.add_argument("--output", "-o", help="Output video file (optional)")
    parser.add_argument("--no-music", dest="add_music", action="store_false", help="Skip adding background music")
    parser.add_argument("--no-captions", dest="add_captions", action="store_false", help="Skip adding captions")
    parser.add_argument("--no-color", dest="color_grade", action="store_false", help="Skip color grading")
    parser.add_argument("--platform", choices=["tiktok", "instagram", "youtube"], default="tiktok", help="Target platform")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.input):
        print(f"Error: Input file not found: {args.input}")
        sys.exit(1)
    
    enhanced_path = enhance_video(
        input_video=args.input,
        output_path=args.output,
        add_music=args.add_music,
        add_captions=args.add_captions,
        color_grade=args.color_grade,
        platform=args.platform
    )
    
    if enhanced_path:
        print(f"Enhanced video saved to: {enhanced_path}")
    else:
        print("Error enhancing video")
        sys.exit(1) 