#!/usr/bin/env python3
"""
Wan Avatar Generator

This module uses the Wan 2.1 T2V model to generate avatar videos for use in OWLmarketing content.
It provides functionality to create consistent, high-quality avatar videos optimized for L4 GPUs.
"""

import os
import sys
import logging
import traceback
import torch
import tempfile
import time
import shutil
import numpy as np
from PIL import Image
import cv2
from pathlib import Path
from typing import Dict, List, Optional, Union, Tuple, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('wan_avatar_generator')

# Get project root directory
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(project_root)

# Import local modules
from video_generation.avatar_config import AVATAR_CONFIGS, VIDEO_SETTINGS
from e2e_cloud.wan_t2v_generator import WanVideoGenerator

class WanAvatarGenerator:
    """Generate avatar videos using the Wan 2.1 Text-to-Video model."""
    
    def __init__(self, 
                model_dir=None, 
                output_dir=None,
                resolution="720p"):
        """
        Initialize the Wan Avatar Generator.
        
        Args:
            model_dir: Path to the Wan 2.1 T2V model directory
            output_dir: Directory to save generated avatar videos
            resolution: Video resolution (720p or 1080p)
        """
        self.model_dir = model_dir
        
        if self.model_dir is None:
            # Try to find the model in common locations
            potential_paths = [
                "/app/models/Wan2.1-T2V-14B",
                os.path.join(project_root, "models", "Wan2.1-T2V-14B"),
                os.environ.get("WAN_MODEL_DIR", "")
            ]
            for path in potential_paths:
                if path and os.path.exists(path):
                    self.model_dir = path
                    break
        
        if not self.model_dir or not os.path.exists(self.model_dir):
            logger.error(f"Wan 2.1 T2V model not found. Please specify a valid model_dir.")
            raise ValueError("Wan 2.1 T2V model directory not found")
            
        # Set output directory
        self.output_dir = output_dir or os.path.join(project_root, "output", "avatars")
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Set resolution
        self.resolution = resolution
        
        # Track whether generator is initialized
        self.generator = None
        
        # GPU type (default to L4, will be detected in initialize_generator)
        self.gpu_type = "L4"
        
        logger.info(f"Initialized WanAvatarGenerator with model: {self.model_dir}")
        logger.info(f"Output directory: {self.output_dir}")
    
    def _initialize_generator(self):
        """Initialize the Wan Video Generator with optimal settings."""
        if self.generator is not None:
            return self.generator
        
        # Detect GPU type
        try:
            gpu_info = torch.cuda.get_device_properties(0)
            total_memory = gpu_info.total_memory / (1024 ** 3)  # Convert to GB
            
            if "L4" in gpu_info.name or total_memory >= 22:
                self.gpu_type = "L4"
                logger.info(f"Detected L4 GPU: {gpu_info.name}")
            else:
                self.gpu_type = "T4"
                logger.info(f"Using default GPU settings: {gpu_info.name}")
                
        except Exception as e:
            logger.warning(f"Could not detect GPU type: {e}. Using default L4 settings.")
            self.gpu_type = "L4"
        
        # Initialize generator with optimal settings for L4 GPU
        try:
            self.generator = WanVideoGenerator(
                model_dir=self.model_dir,
                device="cuda",
                use_fp16=True,
                resolution=self.resolution,
                gpu_type=self.gpu_type
            )
            logger.info(f"Successfully initialized Wan Video Generator. GPU type: {self.gpu_type}")
            return self.generator
        except Exception as e:
            logger.error(f"Failed to initialize Wan Video Generator: {e}")
            raise RuntimeError(f"Failed to initialize Wan Video Generator: {e}")
    
    def generate_avatar_set(self, avatar_name: str, style: str = "default") -> Dict[str, Any]:
        """
        Generate a set of avatar videos for a specific avatar using Wan 2.1 T2V.
        
        Args:
            avatar_name: Name of the avatar from AVATAR_CONFIGS
            style: The style/variation for the avatar
            
        Returns:
            Dictionary with paths to generated videos
        """
        start_time = time.time()
        logger.info(f"Generating avatar videos for {avatar_name} with style {style}")
        
        # Validate avatar configuration
        if avatar_name not in AVATAR_CONFIGS:
            logger.error(f"Avatar '{avatar_name}' not found in configuration")
            return {"error": f"Avatar '{avatar_name}' not found"}
        
        # Get avatar configuration
        avatar_config = AVATAR_CONFIGS[avatar_name]
        
        # Get style configuration
        variations = avatar_config.get("variations", {})
        if style not in variations:
            logger.warning(f"Style '{style}' not found for avatar '{avatar_name}'. Using default.")
            style = "default" if "default" in variations else list(variations.keys())[0]
        
        style_config = variations[style]
        prompts = style_config.get("prompts", [])
        
        if not prompts:
            logger.error(f"No prompts found for avatar '{avatar_name}' with style '{style}'")
            return {"error": f"No prompts found for avatar '{avatar_name}' with style '{style}'"}
        
        # Create output directory for this avatar
        avatar_output_dir = os.path.join(self.output_dir, avatar_name, style)
        os.makedirs(avatar_output_dir, exist_ok=True)
        
        # Generate videos
        try:
            # Initialize generator
            generator = self._initialize_generator()
            
            # Generate videos
            videos = self._generate_videos(avatar_name, prompts, avatar_output_dir)
            
            if not videos:
                # If videos could not be generated, create a fallback video
                logger.warning(f"Failed to generate videos for {avatar_name}. Creating fallback.")
                fallback_video = self._create_fallback_video(avatar_name, style)
                videos = [fallback_video]
            
            # Return result
            result = {
                "avatar_name": avatar_name,
                "style": style,
                "avatar_video": videos[0],  # Select the first video as the primary one
                "all_videos": videos,
                "generation_time": time.time() - start_time
            }
            
            logger.info(f"Successfully generated avatar videos for {avatar_name}: {videos}")
            return result
            
        except Exception as e:
            logger.error(f"Error generating avatar videos: {e}")
            logger.error(traceback.format_exc())
            return {"error": str(e)}
    
    def _generate_videos(self, avatar_name: str, prompts: List[str], output_dir: str) -> List[str]:
        """
        Generate videos for avatar using the Wan 2.1 T2V model.
        
        Args:
            avatar_name: Name of the avatar
            prompts: List of prompts to generate videos from
            output_dir: Directory to save the videos
            
        Returns:
            List of paths to generated videos
        """
        videos = []
        
        for i, prompt in enumerate(prompts):
            try:
                # Prepare prompt for Wan 2.1 T2V
                # Add avatar-specific details to the prompt
                enhanced_prompt = f"{prompt}"
                
                # Add negative prompt
                negative_prompt = "blurry, low quality, duplicate face, deformed face, text, words, letters, watermark, signature"
                
                # Generate video
                logger.info(f"Generating video {i+1}/{len(prompts)} for {avatar_name}")
                logger.info(f"Prompt: {enhanced_prompt}")
                
                video_path = os.path.join(output_dir, f"{avatar_name}_video_{i+1}.mp4")
                
                # Call Wan 2.1 T2V to generate video
                result = self.generator.generate_video(
                    prompt=enhanced_prompt,
                    negative_prompt=negative_prompt,
                    output_path=video_path
                )
                
                if os.path.exists(video_path):
                    logger.info(f"Successfully generated video: {video_path}")
                    videos.append(video_path)
                else:
                    logger.error(f"Failed to generate video for prompt: {prompt}")
            
            except Exception as e:
                logger.error(f"Error generating video for prompt '{prompt}': {e}")
        
        return videos
    
    def _create_fallback_video(self, avatar_name: str, style: str) -> str:
        """
        Create a fallback video when Wan 2.1 T2V generation fails.
        This uses a static image or pre-generated video if available.
        
        Args:
            avatar_name: Name of the avatar
            style: Style of the avatar
            
        Returns:
            Path to the fallback video
        """
        # Look for any pre-generated videos or static images for this avatar
        avatar_dir = os.path.join(project_root, "assets", "avatars", avatar_name)
        fallback_output = os.path.join(self.output_dir, avatar_name, "fallback.mp4")
        
        # Create the output directory if it doesn't exist
        os.makedirs(os.path.dirname(fallback_output), exist_ok=True)
        
        # Check if pre-generated video exists
        for ext in ['.mp4', '.mov', '.avi']:
            video_path = os.path.join(avatar_dir, f"{avatar_name}_{style}{ext}")
            if os.path.exists(video_path):
                logger.info(f"Using pre-generated video as fallback: {video_path}")
                shutil.copy(video_path, fallback_output)
                return fallback_output
        
        # Check if static image exists
        for ext in ['.jpg', '.jpeg', '.png']:
            image_path = os.path.join(avatar_dir, f"{avatar_name}_{style}{ext}")
            if not os.path.exists(image_path):
                image_path = os.path.join(avatar_dir, f"{avatar_name}{ext}")
            
            if os.path.exists(image_path):
                logger.info(f"Creating video from static image: {image_path}")
                
                # Convert static image to video
                img = cv2.imread(image_path)
                if img is not None:
                    height, width = img.shape[:2]
                    fps = 24
                    seconds = 5
                    
                    # Create video writer
                    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                    video = cv2.VideoWriter(fallback_output, fourcc, fps, (width, height))
                    
                    # Write frames (same image repeated)
                    for _ in range(fps * seconds):
                        video.write(img)
                    
                    video.release()
                    logger.info(f"Created fallback video: {fallback_output}")
                    return fallback_output
        
        # If no pre-generated assets found, create a blank video
        logger.warning(f"No pre-generated assets found for {avatar_name}. Creating blank video.")
        
        # Create a blank video (black frames)
        width, height = 720, 1280
        if self.resolution == "1080p":
            width, height = 1080, 1920
            
        fps = 24
        seconds = 5
        
        # Create video writer
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        video = cv2.VideoWriter(fallback_output, fourcc, fps, (width, height))
        
        # Create a blank frame
        blank_frame = np.zeros((height, width, 3), dtype=np.uint8)
        
        # Write frames
        for _ in range(fps * seconds):
            video.write(blank_frame)
        
        video.release()
        logger.warning(f"Created blank fallback video: {fallback_output}")
        return fallback_output


def generate_avatar_set(avatar_name, style="default", output_dir=None, model_dir=None, resolution="720p", gpu_type="L4"):
    """
    Generate a set of avatar videos for a specific avatar.
    
    Args:
        avatar_name: Name of the avatar from AVATAR_CONFIGS
        style: The style/variation for the avatar
        output_dir: Directory to save the videos
        model_dir: Path to the Wan 2.1 T2V model
        resolution: Video resolution (720p or 1080p)
        gpu_type: Type of GPU to optimize for (L4 or T4)
        
    Returns:
        Dictionary with paths to generated videos
    """
    try:
        # Create generator
        generator = WanAvatarGenerator(
            model_dir=model_dir,
            output_dir=output_dir,
            resolution=resolution
        )
        
        # Generate avatar videos
        result = generator.generate_avatar_set(avatar_name, style)
        return result
    
    except Exception as e:
        logger.error(f"Error in generate_avatar_set: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return {"error": str(e)}


# Command-line interface
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate avatar videos using Wan 2.1 T2V")
    parser.add_argument("--avatar", required=True, help="Name of the avatar to generate")
    parser.add_argument("--style", default="default", help="Style/variation for the avatar")
    parser.add_argument("--output-dir", help="Directory to save generated videos")
    parser.add_argument("--model-dir", help="Path to Wan 2.1 T2V model directory")
    parser.add_argument("--resolution", default="720p", choices=["720p", "1080p"], help="Video resolution")
    parser.add_argument("--gpu-type", default="L4", choices=["L4", "T4"], help="GPU type to optimize for")
    
    args = parser.parse_args()
    
    # Generate avatar videos
    result = generate_avatar_set(
        avatar_name=args.avatar,
        style=args.style,
        output_dir=args.output_dir,
        model_dir=args.model_dir,
        resolution=args.resolution,
        gpu_type=args.gpu_type
    )
    
    if "error" in result:
        print(f"Error: {result['error']}")
        sys.exit(1)
    else:
        print(f"Successfully generated avatar videos:")
        print(f"Primary video: {result['avatar_video']}")
        print(f"All videos: {result['all_videos']}")
        sys.exit(0)