#!/usr/bin/env python3
# /Users/vanshshah/Desktop/OWLmarketing/video_generation/generate_video.py

import os
import sys
import time
import logging
import random
import cv2
import numpy as np
import subprocess
import tempfile
import traceback
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from video_generation.avatar_config import AVATAR_CONFIGS, VIDEO_SETTINGS
from video_editing.hooks_templates import HOOK_TEMPLATES
from video_editing.video_analyzer import VideoAnalyzer
from video_generation.context_ui_integrator import get_context_ui_integrator
import json
import torch
from diffusers import StableDiffusionPipeline
from typing import List, Dict, Optional, Tuple
import textwrap
from datetime import datetime
import math
import shutil

# Configure enhanced logging
logging.basicConfig(level=logging.INFO, 
                   format='[%(asctime)s] %(levelname)s: %(message)s',
                   handlers=[
                       logging.FileHandler("video_generation.log"),
                       logging.StreamHandler()
                   ])
logger = logging.getLogger(__name__)

class VideoGenerator:
    def __init__(self, 
                 avatars_dir="data/generated_avatars", 
                 output_dir="data/generated_videos",
                 training_videos_dir="data/training_videos",
                 cache_dir="data/video_cache",
                 pose_model="movenet",
                 model_path="stabilityai/stable-diffusion-xl-base-1.0"):
        """
        Initialize the video generator.
        
        Args:
            avatars_dir (str): Directory containing generated avatars
            output_dir (str): Directory to save generated videos
            training_videos_dir (str): Directory containing training videos
            cache_dir (str): Directory to cache processed videos
            pose_model (str): Model to use for pose estimation
            model_path (str): Path to the Stable Diffusion model
        """
        # Setup logger instance for this class
        self.logger = logging.getLogger(__name__)
        
        # Set paths
        self.avatars_dir = Path(avatars_dir)
        self.output_dir = Path(output_dir)
        self.training_dir = Path(training_videos_dir)
        self.cache_dir = Path(cache_dir)
        
        # Create directories if they don't exist
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Set pose model
        self.pose_model = pose_model
        self.model_path = model_path
        
        # Load video analysis cache
        self.video_analyzer = VideoAnalyzer(
            training_videos_dir=str(self.training_dir), 
                pose_model=pose_model
            )
        self.logger.info(f"Initializing VideoGenerator with model path: {model_path}")
        
        # Analyze training videos to learn patterns
        self.style_patterns = self.video_analyzer.analyze_training_set()
        self.logger.info(f"Analyzed training set, found {len(self.style_patterns.get('duration', []))} style patterns")
        
        # Load video analysis cache
        self.video_cache = self._load_video_cache()
        self.logger.info(f"Loaded {len(self.video_cache)} entries from video analysis cache")
            
        # Initialize SDK and context-aware UI integrator
        self.context_ui_integrator = get_context_ui_integrator()
        self.logger.info("Initialized Context-Aware UI Integrator")
            
        # Set quality settings based on VIDEO_SETTINGS
        self.quality_settings = {
            "codec": "libx264",
            "preset": "slow",  # Can be ultrafast, superfast, veryfast, faster, fast, medium, slow, slower, veryslow
            "crf": 18,  # Lower is better quality, 18-28 is a good range
            "bitrate": "8M",
            "pixel_format": "yuv420p"
        }
        
        # Track generated videos
        self.generated_videos = []
            
        # Initialize the SD pipeline for potential use in transitions or effects
        # Defer to avoid loading if not necessary
        self.sd_pipeline = None
        
        self.logger.info("VideoGenerator initialization complete")
    
    def _initialize_sd_pipeline(self):
        """Initialize Stable Diffusion pipeline with optimizations for high-end GPUs like RTX 4090."""
        try:
            # Skip if already initialized
            if self.sd_pipeline is not None:
                return self.sd_pipeline
                
            # Import necessary modules
            import torch
            from diffusers import StableDiffusionPipeline
            
            self.logger.info(f"Initializing Stable Diffusion pipeline from {self.model_path}")
            
            if torch.cuda.is_available():
                # Get GPU information for logging
                gpu_name = torch.cuda.get_device_name(0)
                gpu_memory = torch.cuda.get_device_properties(0).total_memory / (1024 ** 3)  # Convert to GB
                self.logger.info(f"GPU detected: {gpu_name} with {gpu_memory:.2f}GB memory")
                
                # Load with optimizations for powerful GPUs like RTX 4090
                self.sd_pipeline = StableDiffusionPipeline.from_pretrained(
                    self.model_path,
                    torch_dtype=torch.float16,  # Use half precision for better performance
                    use_safetensors=True,
                    variant="fp16"  # Use FP16 variant if available
                )
                
                # Move to GPU
                self.sd_pipeline = self.sd_pipeline.to("cuda")
                
                # Apply memory optimizations
                self.sd_pipeline.enable_vae_slicing()  # Reduces VRAM usage during generation
                
                # Enable attention slicing for memory efficiency
                self.sd_pipeline.enable_attention_slicing(slice_size="auto")
                
                # For RTX 4090 and similar high-end GPUs, enable xformers for even better performance
                try:
                    import xformers
                    self.sd_pipeline.enable_xformers_memory_efficient_attention()
                    self.logger.info("Using xformers memory efficient attention for maximum performance")
                except ImportError:
                    self.logger.info("xformers package not found, using standard attention mechanism")
                    
                # For newer versions of diffusers that support torch compile
                if hasattr(torch, 'compile') and hasattr(self.sd_pipeline, 'unet'):
                    try:
                        self.sd_pipeline.unet = torch.compile(
                            self.sd_pipeline.unet, 
                            mode="reduce-overhead", 
                            fullgraph=True
                        )
                        self.logger.info("Using torch.compile for even faster inference")
                    except Exception as e:
                        self.logger.warning(f"Could not use torch.compile: {e}")
                
                # Set up optimized VAE forward method if needed
                if hasattr(self.sd_pipeline, 'vae'):
                    original_forward = self.sd_pipeline.vae.forward
                    self.sd_pipeline.vae.forward = self._accelerated_vae_forward(original_forward)
                
                self.logger.info("Stable Diffusion pipeline initialized with RTX 4090 optimizations")
            else:
                # CPU fallback with basic settings
                self.sd_pipeline = StableDiffusionPipeline.from_pretrained(
                    self.model_path,
                    use_safetensors=True
                )
                self.logger.info("Using CPU for generation (this will be slow for video tasks)")
            
            return self.sd_pipeline
            
        except Exception as e:
            self.logger.error(f"Error initializing Stable Diffusion pipeline: {e}")
            self.logger.error(traceback.format_exc())
            return None
    
    def _load_video_cache(self) -> Dict:
        """Load the video analysis cache from disk."""
        try:
            cache_file = self.cache_dir / "video_analysis_cache.json"
            if cache_file.exists():
                logger.debug(f"Loading video cache from: {cache_file}")
                with open(cache_file, 'r') as f:
                    cache_data = json.load(f)
                logger.debug(f"Loaded {len(cache_data)} cache entries")
                return cache_data
            logger.debug("No cache file found, returning empty cache")
            return {}
        except Exception as e:
            logger.error(f"Error loading video cache: {e}")
            logger.debug(traceback.format_exc())
            return {}
    
    def _save_video_cache(self):
        """Save the video analysis cache to disk."""
        try:
            cache_file = self.cache_dir / "video_analysis_cache.json"
            logger.debug(f"Saving video cache to: {cache_file} with {len(self.video_cache)} entries")
            with open(cache_file, 'w') as f:
                json.dump(self.video_cache, f)
            logger.debug(f"Video cache saved successfully")
        except Exception as e:
            logger.error(f"Error saving video cache: {e}")
            logger.debug(traceback.format_exc())
    
    def _find_matching_clips(self, style_patterns: Dict, duration: float) -> List[Dict]:
        """Find video clips that match the desired style patterns."""
        logger.info(f"Finding clips matching style patterns for duration: {duration:.2f}s")
        matching_clips = []
        
        try:
            # Check if training video directory exists
            if not self.training_dir.exists():
                logger.warning(f"Training videos directory {self.training_dir} does not exist")
                return []
        
            # Search through all training video directories
            for influencer_dir in self.training_dir.iterdir():
                if not influencer_dir.is_dir():
                    continue
                    
                logger.debug(f"Searching for videos in: {influencer_dir}")
                video_count = 0
                
                for video_file in influencer_dir.glob("*.mp4"):
                    video_path = str(video_file)
                    video_count += 1
                    
                    try:
                        # Check cache first
                        if video_path in self.video_cache:
                            logger.debug(f"Using cached analysis for: {video_path}")
                            analysis = self.video_cache[video_path]
                        else:
                            # Analyze video if not in cache
                            logger.info(f"Analyzing new video: {video_path}")
                            analysis = self.video_analyzer.analyze_video(video_path)
                            self.video_cache[video_path] = analysis
                            self._save_video_cache()
                        
                        # Check if video matches style patterns
                        if self._matches_style_patterns(analysis, style_patterns):
                            logger.debug(f"Video matches style patterns: {video_path}")
                            # Find suitable segments in the video
                            segments = self._find_suitable_segments(analysis, duration)
                            for segment in segments:
                                matching_clips.append({
                                    'path': video_path,
                                    'start_time': segment['start'],
                                    'duration': segment['duration']
                                })
                                logger.debug(f"Added matching segment: start={segment['start']:.2f}s, duration={segment['duration']:.2f}s")
                    except Exception as e:
                        logger.error(f"Error processing video {video_path}: {e}")
                        logger.debug(traceback.format_exc())
                        continue  # Skip this video but continue with others
                
                logger.debug(f"Processed {video_count} videos in {influencer_dir}")
            
            logger.info(f"Found {len(matching_clips)} matching clips")
            return matching_clips
        except Exception as e:
            logger.error(f"Error finding matching clips: {e}")
            logger.debug(traceback.format_exc())
            return []
    
    def _matches_style_patterns(self, analysis: Dict, target_patterns: Dict) -> bool:
        """Check if a video's analysis matches the target style patterns."""
        try:
            # Get video properties from analysis
            video_brightness = np.mean(analysis.get('brightness', []))
            video_contrast = np.mean(analysis.get('contrast', []))
            
            # Get target properties
            target_energy = target_patterns.get('energy_level', 0.5)
            target_emotion = target_patterns.get('emotion', 'neutral')
            
            # Calculate energy level based on brightness and contrast
            energy_level = (video_brightness / 255.0 + video_contrast / 255.0) / 2
            
            # Match energy level within a threshold
            energy_match = abs(energy_level - target_energy) < 0.2
            
            # For now, we'll consider all emotions as matching
            # In a real implementation, you would use emotion detection
            emotion_match = True
            
            logger.debug(f"Style match assessment: energy_level={energy_level:.2f} (target={target_energy:.2f}), match={energy_match}")
        
            return energy_match and emotion_match
        except Exception as e:
            logger.error(f"Error matching style patterns: {e}")
            logger.debug(traceback.format_exc())
            return False  # Default to not matching in case of error
    
    def _find_suitable_segments(self, analysis: Dict, target_duration: float) -> List[Dict]:
        """Find segments in a video that match the target duration."""
        try:
            video_duration = analysis.get('duration', 0)
            if video_duration < target_duration:
                logger.debug(f"Video too short: {video_duration:.2f}s < {target_duration:.2f}s")
                return []
            
            # Find segments with good transitions
            segments = []
            transitions = analysis.get('transitions', {})
            
            # If we have transition information, use it to find good cut points
            if transitions:
                logger.debug(f"Using transition information to find segments")
                # For now, we'll just take the first segment
                # In a real implementation, you would analyze transition points
                segments.append({
                    'start': 0,
                    'duration': min(target_duration, video_duration)
                })
                logger.debug(f"Added segment: start=0, duration={min(target_duration, video_duration):.2f}s")
            else:
                logger.debug(f"No transition information available, using video start")
                # If no transition information, just take the first part
                segments.append({
                    'start': 0,
                    'duration': min(target_duration, video_duration)
                })
                logger.debug(f"Added segment: start=0, duration={min(target_duration, video_duration):.2f}s")
            
            return segments
        except Exception as e:
            logger.error(f"Error finding suitable segments: {e}")
            logger.debug(traceback.format_exc())
            return []  # Return empty list in case of error
    
    def generate_complete_video(self, avatar_video, app_demo, script, output_path=None):
        """
        Generate a complete video by combining avatar and app demo videos.
        
        Args:
            avatar_video (str): Path to the avatar video file
            app_demo (str): Path to the app demo video file
            script (dict): Script details for context
            output_path (str, optional): Custom path for the output video
            
        Returns:
            str: Path to the generated video
        """
        try:
            # Create output directory if it doesn't exist
            if output_path is None:
                output_dir = os.path.join(os.path.dirname(avatar_video), "videos")
                os.makedirs(output_dir, exist_ok=True)
                
                timestamp = int(time.time())
                output_path = os.path.join(output_dir, f"video_{timestamp}.mp4")
            
            # Create temporary directory for processing
            with tempfile.TemporaryDirectory() as temp_dir:
                # Get target duration
                avatar_duration = self._get_video_duration(avatar_video)
                app_demo_duration = self._get_video_duration(app_demo)
                target_duration = max(avatar_duration, app_demo_duration)
                
                self.logger.info(f"Avatar video duration: {avatar_duration:.2f}s")
                self.logger.info(f"App demo video duration: {app_demo_duration:.2f}s")
                
                # Prepare videos for combination
                avatar_prepared = os.path.join(temp_dir, "avatar_prepared.mp4")
                self._prepare_avatar_video(avatar_video, avatar_prepared, target_duration)
                
                # Prepare app demo video
                demo_prepared = os.path.join(temp_dir, "demo_prepared.mp4")
                prepared_demo = self._prepare_app_demo_video(app_demo, target_duration)
                
                # Create side-by-side video
                self._create_side_by_side_video(avatar_prepared, prepared_demo, output_path)
                
                # Apply final enhancements
                try:
                    self._enhance_final_video(output_path, script)
                except Exception as e:
                    self.logger.error(f"Error enhancing final video: {e}")
                
                # Verify output file exists
                if not os.path.exists(output_path):
                    self.logger.error(f"Output file {output_path} was not created")
                    return None
                
                self.logger.info(f"Successfully generated video: {output_path}")
                return output_path
                
        except Exception as e:
            self.logger.error(f"Error generating complete video: {e}")
            return None
    
    def _get_video_duration(self, video_path):
        """
        Get the duration of a video.
        
        Args:
            video_path (str): Path to the video file
            
        Returns:
            float: Duration in seconds
        """
        try:
            if not os.path.exists(video_path):
                self.logger.error(f"Video file not found: {video_path}")
                return 0.0
                
            cmd = [
                'ffprobe', 
                '-v', 'error', 
                '-show_entries', 
                'format=duration', 
                '-of', 
                'default=noprint_wrappers=1:nokey=1', 
                video_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                self.logger.error(f"Error getting video duration: {result.stderr}")
                # Try an alternative approach
                return self._get_duration_fallback(video_path)
                
            duration = float(result.stdout.strip())
            return duration
            
        except Exception as e:
            self.logger.error(f"Error getting video duration: {e}")
            return self._get_duration_fallback(video_path)
            
    def _get_duration_fallback(self, video_path):
        """Fallback method to get video duration using OpenCV."""
        try:
            import cv2
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                return 5.0  # Default duration
                
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            
            if fps <= 0 or frame_count <= 0:
                return 5.0  # Default duration
                
            duration = frame_count / fps
            cap.release()
            
            return duration
        except Exception as e:
            self.logger.error(f"Error in duration fallback: {e}")
            return 5.0  # Default duration
    
    def _prepare_avatar_video(self, avatar_video, output_path, target_duration):
        """Prepare the avatar video for integration."""
        try:
            avatar_duration = self._get_video_duration(avatar_video)
            
            if avatar_duration >= target_duration:
                # Trim the avatar video if it's longer than needed
                cmd = [
                    "ffmpeg", "-y", "-i", avatar_video,
                    "-t", str(target_duration),
                    "-c:v", "libx264", "-c:a", "aac",
                    output_path
                ]
            else:
                # Loop the avatar video to reach target duration
                loop_count = math.ceil(target_duration / avatar_duration)
                
                # Create a concat file
                concat_file = os.path.join(os.path.dirname(output_path), "concat.txt")
                with open(concat_file, "w") as f:
                    for _ in range(loop_count):
                        f.write(f"file '{avatar_video}'\n")
                
                # Use ffmpeg concat demuxer
                cmd = [
                    "ffmpeg", "-y", "-f", "concat", "-safe", "0",
                    "-i", concat_file,
                    "-t", str(target_duration),
                    "-c:v", "libx264", "-c:a", "aac",
                    output_path
                ]
            
            # Execute ffmpeg command
            subprocess.run(cmd, check=True)
            self.logger.info(f"Prepared avatar video: {output_path}")
            
            # Delete concat file if it exists
            if os.path.exists(concat_file):
                os.unlink(concat_file)
                
            return output_path
        except Exception as e:
            self.logger.error(f"Error preparing avatar video: {e}")
            # Copy the original as fallback
            shutil.copy2(avatar_video, output_path)
            return output_path
    
    def _prepare_app_demo_video(self, video_path, target_duration):
        """Prepare app demo video for integration."""
        try:
            # Check if the input video has an audio stream
            has_audio = False
            probe_cmd = [
                'ffprobe', 
                '-v', 'error', 
                '-select_streams', 'a', 
                '-show_entries', 'stream=codec_type', 
                '-of', 'default=noprint_wrappers=1:nokey=1', 
                video_path
            ]
            try:
                result = subprocess.run(probe_cmd, capture_output=True, text=True)
                has_audio = result.stdout.strip() == 'audio'
            except Exception as e:
                logging.warning(f"Error checking for audio stream: {e}")
            
            # Get video duration
            duration = self._get_video_duration(video_path)
            
            # Calculate speed factor
            speed_factor = duration / target_duration if duration > 0 else 1.0
            
            # If speed factor is approximately 1.0, no need to adjust
            if 0.95 <= speed_factor <= 1.05:
                return video_path
            
            # Create temp directory for processing
            with tempfile.TemporaryDirectory() as temp_dir:
                output_path = os.path.join(temp_dir, "demo_prepared.mp4")
                
                # Construct FFmpeg command based on whether audio is present
                if has_audio:
                    # With audio
                    filter_complex = f'[0:v]setpts={speed_factor}*PTS[v];[0:a]atempo={1/speed_factor}[a]'
                    cmd = [
                        'ffmpeg', '-y',
                        '-i', video_path,
                        '-filter_complex', filter_complex,
                        '-map', '[v]', '-map', '[a]',
                        '-c:v', 'libx264', '-c:a', 'aac',
                        output_path
                    ]
                else:
                    # Without audio
                    filter_complex = f'[0:v]setpts={speed_factor}*PTS[v]'
                    cmd = [
                        'ffmpeg', '-y',
                        '-i', video_path,
                        '-filter_complex', filter_complex,
                        '-map', '[v]',
                        '-c:v', 'libx264',
                        output_path
                    ]
                
                # Run FFmpeg command
                subprocess.run(cmd, check=True)
                
                # Copy the output file to a persistent location
                persistent_output = os.path.join(os.path.dirname(video_path), "demo_prepared.mp4")
                shutil.copy2(output_path, persistent_output)
                
                return persistent_output
                
        except Exception as e:
            logging.error(f"Error preparing app demo video: {e}")
            return video_path
    
    def _create_side_by_side_video(self, avatar_video, demo_video, output_path):
        """Create a side-by-side video with avatar and app demo."""
        try:
            # Check if avatar video has audio
            avatar_has_audio = False
            probe_cmd = [
                'ffprobe', 
                '-v', 'error', 
                '-select_streams', 'a', 
                '-show_entries', 'stream=codec_type', 
                '-of', 'default=noprint_wrappers=1:nokey=1', 
                avatar_video
            ]
            try:
                result = subprocess.run(probe_cmd, capture_output=True, text=True)
                avatar_has_audio = result.stdout.strip() == 'audio'
            except Exception as e:
                logging.warning(f"Error checking for audio stream: {e}")

            # Get durations
            avatar_duration = self._get_video_duration(avatar_video)
            demo_duration = self._get_video_duration(demo_video)
            
            # Use the longer of the two videos
            max_duration = max(avatar_duration, demo_duration)
            
            with tempfile.TemporaryDirectory() as temp_dir:
                # Create the filter complex for side-by-side layout
                filter_complex = '[0:v]scale=540:960[left];[1:v]scale=540:960[right];[left][right]hstack=inputs=2[v]'
                
                # Create FFmpeg command
                cmd = [
                    'ffmpeg', '-y',
                    '-i', avatar_video,
                    '-i', demo_video,
                    '-filter_complex', filter_complex,
                    '-map', '[v]'
                ]
                
                # Add audio mapping only if avatar has audio
                if avatar_has_audio:
                    cmd.extend(['-map', '0:a'])
                
                # Add duration and encoding parameters
                cmd.extend([
                    '-t', str(max_duration),
                    '-c:v', 'libx264',
                    '-preset', 'slow',
                    '-crf', '18',
                    '-b:v', '8M',
                    '-pix_fmt', 'yuv420p'
                ])
                
                # Add audio codec only if we have audio
                if avatar_has_audio:
                    cmd.extend(['-c:a', 'aac', '-b:a', '192k'])
                
                # Add output path
                cmd.append(output_path)
                
                # Execute FFmpeg command
                subprocess.run(cmd, check=True)
                
            return output_path
        except Exception as e:
            self.logger.error(f"Error creating side-by-side video: {e}")
            return None
    
    def _create_pip_video(self, main_video, pip_video, output_path):
        """Create a picture-in-picture video with main video and PIP overlay."""
        try:
            # Get video durations
            main_duration = self._get_video_duration(main_video)
            pip_duration = self._get_video_duration(pip_video)
            
            # Use the longer duration
            target_duration = max(main_duration, pip_duration)
            
            # Execute ffmpeg command to create PIP video
            cmd = [
                "ffmpeg", "-y",
                "-i", main_video,
                "-i", pip_video,
                "-filter_complex",
                "[0:v]scale=1080:1920[main];[1:v]scale=360:640,format=yuva420p,boxblur=10[pip];[main][pip]overlay=main_w-overlay_w-20:main_h-overlay_h-20[v]",
                "-map", "[v]",
                "-map", "0:a",
                "-t", str(target_duration),
                "-c:v", self.quality_settings["codec"],
                "-preset", self.quality_settings["preset"],
                "-crf", str(self.quality_settings["crf"]),
                "-b:v", self.quality_settings["bitrate"],
                "-pix_fmt", self.quality_settings["pixel_format"],
                "-c:a", "aac",
                "-b:a", "192k",
                output_path
            ]
            
            # Execute ffmpeg command
            subprocess.run(cmd, check=True)
            self.logger.info(f"Created picture-in-picture video: {output_path}")
            return output_path
        except Exception as e:
            self.logger.error(f"Error creating picture-in-picture video: {e}")
            return None
    
    def _create_sequential_video(self, intro_video, main_video, output_path):
        """Create a sequential video with intro followed by main video."""
        try:
            # Create a temporary concat file
            temp_dir = os.path.dirname(output_path)
            concat_file = os.path.join(temp_dir, "concat_seq.txt")
            
            # Write to concat file
            with open(concat_file, "w") as f:
                f.write(f"file '{intro_video}'\n")
                f.write(f"file '{main_video}'\n")
            
            # Execute ffmpeg command to concatenate videos
            cmd = [
                "ffmpeg", "-y",
                "-f", "concat",
                "-safe", "0",
                "-i", concat_file,
                "-c:v", self.quality_settings["codec"],
                "-preset", self.quality_settings["preset"],
                "-crf", str(self.quality_settings["crf"]),
                "-b:v", self.quality_settings["bitrate"],
                "-pix_fmt", self.quality_settings["pixel_format"],
                "-c:a", "aac",
                "-b:a", "192k",
                output_path
            ]
            
            # Execute ffmpeg command
            subprocess.run(cmd, check=True)
            self.logger.info(f"Created sequential video: {output_path}")
            
            # Delete concat file
            os.unlink(concat_file)
            
            return output_path
        except Exception as e:
            self.logger.error(f"Error creating sequential video: {e}")
            return None
    
    def _enhance_final_video(self, video_path, script):
        """Add final enhancements to the video."""
        try:
            # Define project root
            project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
            
            # Create enhanced output path
            output_dir = os.path.dirname(video_path)
            basename = os.path.basename(video_path)
            enhanced_path = os.path.join(output_dir, f"enhanced_{basename}")
            
            # Get video metadata
            duration = self._get_video_duration(video_path)
            
            # Get a random music file if available
            music_dir = os.path.join(project_root, "assets", "audio", "music")
            music_file = None
            
            if os.path.exists(music_dir):
                music_files = [os.path.join(music_dir, f) for f in os.listdir(music_dir) 
                              if f.endswith(('.mp3', '.wav'))]
                if music_files:
                    music_file = random.choice(music_files)
            
            # Execute ffmpeg command for enhancements
            if music_file and os.path.exists(music_file):
                # Add music and other enhancements
                cmd = [
                    "ffmpeg", "-y",
                    "-i", video_path,
                    "-i", music_file,
                    "-filter_complex",
                    f"[0:v]unsharp=3:3:1.5:3:3:0.5[v];[1:a]afade=t=out:st={duration-1.5}:d=1.5,aformat=sample_fmts=fltp:sample_rates=44100:channel_layouts=stereo,volume=0.3[a1];[0:a][a1]amix=inputs=2:duration=shortest[a]",
                    "-map", "[v]",
                    "-map", "[a]",
                    "-c:v", self.quality_settings["codec"],
                    "-preset", self.quality_settings["preset"],
                    "-crf", str(self.quality_settings["crf"]),
                    "-b:v", self.quality_settings["bitrate"],
                    "-pix_fmt", self.quality_settings["pixel_format"],
                    "-c:a", "aac",
                    "-b:a", "192k",
                    "-movflags", "+faststart",
                    enhanced_path
                ]
            else:
                # Just add visual enhancements
                cmd = [
                    "ffmpeg", "-y",
                    "-i", video_path,
                    "-vf", "unsharp=3:3:1.5:3:3:0.5",
                    "-c:v", self.quality_settings["codec"],
                    "-preset", self.quality_settings["preset"],
                    "-crf", str(self.quality_settings["crf"]),
                    "-b:v", self.quality_settings["bitrate"],
                    "-pix_fmt", self.quality_settings["pixel_format"],
                    "-c:a", "aac",
                    "-b:a", "192k",
                    "-movflags", "+faststart",
                    enhanced_path
                ]
            
            # Execute ffmpeg command
            self.logger.info(f"Enhancing final video with quality settings")
            subprocess.run(cmd, check=True)
            
            if os.path.exists(enhanced_path):
                self.logger.info(f"Video enhanced successfully: {enhanced_path}")
                return enhanced_path
            else:
                self.logger.warning(f"Enhanced video not created, returning original: {video_path}")
                return video_path
        except Exception as e:
            self.logger.error(f"Error enhancing final video: {e}")
            return video_path

    def _accelerated_vae_forward(self, original_forward):
        """Create a wrapper for VAE forward that improves CPU performance."""
        def optimized_forward(*args, **kwargs):
            try:
                # Process smaller chunks for better memory usage
                with torch.no_grad():
                    # Apply original forward in a memory-efficient way
                    result = original_forward(*args, **kwargs)
                return result
            except Exception as e:
                self.logger.error(f"Error in accelerated VAE forward: {e}")
                self.logger.debug(traceback.format_exc())
                # Re-raise to let caller handle
                raise
        return optimized_forward

    def _format_prompt_with_style(self, base_prompt):
        """Format a prompt with style and quality modifiers for better Stable Diffusion results."""
        try:
            quality_modifiers = [
                "high quality", "best quality", "detailed", "sharp focus", 
                "highly detailed", "professional photo", "cinematic lighting"
            ]
            
            # Add quality modifiers if they're not already in the prompt
            prompt_parts = [base_prompt]
            for modifier in quality_modifiers:
                if modifier.lower() not in base_prompt.lower():
                    prompt_parts.append(modifier)
                    
            final_prompt = ", ".join(prompt_parts)
            self.logger.debug(f"Formatted prompt: {final_prompt[:50]}...")
            return final_prompt
        except Exception as e:
            self.logger.error(f"Error formatting prompt: {e}")
            self.logger.debug(traceback.format_exc())
            # Return original prompt as fallback
            return base_prompt

def generate_video_from_script(script: Dict, output_path: str = "raw_video.mp4") -> str:
    """
    Generate video based on script.
    
    Args:
        script (Dict): Script with details like avatar, hook, food item, etc.
        output_path (str): Path for the output video file
        
    Returns:
        str: Path to the generated video
    """
    try:
        logger.info(f"Generating video from script: {script.get('hook', '')[:30]}...")
        
        # Initialize video generator
        video_generator = VideoGenerator()
        
        # Generate avatar video
        avatar_key = script.get("avatar", "sarah")
        avatar_style = script.get("variation", "demo")
        
        from video_generation.generate_avatar import generate_avatar_set
        avatar_result = generate_avatar_set(avatar_key, style=avatar_style)
        
        if not avatar_result or "error" in avatar_result:
            logger.error(f"Failed to generate avatar: {avatar_result.get('error', 'Unknown error')}")
            return None
            
        avatar_video = avatar_result["avatar_video"]
        
        # Generate app demo
        from video_generation.app_ui_manager import get_ui_manager
        ui_manager = get_ui_manager()
        
        food_item = {
            "name": script.get("food_item", "avocado toast"),
            "calories": script.get("calories", 350),
            "protein": script.get("protein", 10),
            "carbs": script.get("carbs", 30),
            "fat": script.get("fat", 15)
        }
        
        app_demo = ui_manager.create_feature_demo(
            script.get("feature", "food scanning"),
            os.path.join(os.path.dirname(output_path), "app_demo.mp4"),
            duration=5.0,
            food_item=food_item,
            script=script
        )
        
        # Generate full video
        final_video = video_generator.generate_complete_video(avatar_video, app_demo, script, output_path)
        
        return final_video
    
    except Exception as e:
        logger.error(f"Failed to generate video from script: {e}")
        logger.debug(traceback.format_exc())
        return None

def replace_humans_with_avatar(video_path: str, avatar_key: str, output_path: Optional[str] = None) -> str:
    """
    Replace human subjects in a video with an AI avatar.
    
    Args:
        video_path (str): Path to the input video
        avatar_key (str): Key of the avatar to use
        output_path (str, optional): Path for the output video
        
    Returns:
        str: Path to the generated video
    """
    try:
        logger.info(f"Replacing humans in video {video_path} with avatar {avatar_key}")
        
        # Validate inputs
        if not os.path.exists(video_path):
            error_msg = f"Input video does not exist: {video_path}"
            logger.error(error_msg)
            raise FileNotFoundError(error_msg)
            
        if avatar_key not in AVATAR_CONFIGS:
            error_msg = f"Invalid avatar key: {avatar_key}. Available avatars: {list(AVATAR_CONFIGS.keys())}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        # Set default output path if not provided
        if output_path is None:
            basename = os.path.basename(video_path)
            dirname = os.path.dirname(video_path)
            output_path = os.path.join(dirname, f"avatar_{avatar_key}_{basename}")
        
        # Initialize video analyzer
        analyzer = VideoAnalyzer()
        
        # Replace humans in video
        result = analyzer.replace_humans_in_video(
            video_path=video_path,
            avatar_key=avatar_key,
            avatar_config=AVATAR_CONFIGS[avatar_key],
            output_path=output_path
        )
        
        logger.info(f"Successfully replaced humans with avatar. Output: {result}")
        return result
    except Exception as e:
        logger.error(f"Failed to replace humans with avatar: {e}")
        logger.debug(traceback.format_exc())
        raise

if __name__ == "__main__":
    try:
        logger.info("Starting generate_video.py script")
        
        # Example script with avatar replacement
        test_script = {
                "avatar": "sarah",
            "variation": "demo",
            "hook": "Transform your diet with AI food tracking!",
            "feature": "food scanning",
            "food_item": "avocado toast",
            "calories": 350,
            "duration": 10
        }
        
        video_file = generate_video_from_script(test_script)
        logger.info(f"Video file created: {video_file}")
        
    except Exception as e:
        logger.critical(f"Critical error in main script: {e}")
        logger.debug(traceback.format_exc())
        sys.exit(1)
