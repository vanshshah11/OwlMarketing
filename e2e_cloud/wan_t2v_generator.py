#!/usr/bin/env python3
"""
Wan 2.1 T2V Generator for OWLmarketing

This module integrates the Wan 2.1 Text-to-Video model with the OWLmarketing pipeline,
providing high-quality video generation with optimized performance for L4 GPUs.
"""

import os
import shutil
import sys
import torch
import logging
import numpy as np
from PIL import Image
from typing import Optional, List, Dict, Any, Tuple
import time
import tempfile
from pathlib import Path
import cv2
import subprocess
from tqdm import tqdm

# Configure logging
logger = logging.getLogger("wan_generator")

class WanVideoGenerator:
    """Wrapper for the Wan 2.1 Text-to-Video model."""
    
    def __init__(
        self, 
        model_dir: str, 
        device: str = "cuda", 
        use_fp16: bool = True,
        resolution: str = "720p",  # Default to 720p for L4
        optimize_for_gpu: bool = True,
        gpu_type: str = "L4"  # Default to L4 optimization
    ):
        """
        Initialize the Wan 2.1 Text-to-Video generator.
        
        Args:
            model_dir: Path to the Wan 2.1 T2V model directory
            device: Device to use for generation (cuda or cpu)
            use_fp16: Whether to use FP16 precision for faster generation
            resolution: Video resolution to generate (480p, 720p, or 1080p)
            optimize_for_gpu: Whether to optimize settings for GPU
            gpu_type: Type of GPU (L4 or T4)
        """
        self.model_dir = model_dir
        self.device = device
        self.use_fp16 = use_fp16
        self.resolution = resolution
        self.optimize_for_gpu = optimize_for_gpu
        self.gpu_type = gpu_type
        self.model = None
        self.initialized = False
        
        # Initialize session_dir for temporary files
        self.session_dir = tempfile.mkdtemp(prefix="wan_generator_")
        logger.info(f"Created temporary directory: {self.session_dir}")
        
        # Set resolution parameters
        if resolution == "480p":
            self.width, self.height = 832, 480
        elif resolution == "720p":
            self.width, self.height = 1280, 720
        elif resolution == "1080p":
            if self.gpu_type == "L4":
                self.width, self.height = 1920, 1080
                logger.info("Using 1080p resolution with L4 GPU")
            else:
                logger.warning("1080p resolution may be too demanding for T4 GPU, using 720p instead")
                self.width, self.height = 1280, 720
                self.resolution = "720p"
        else:
            logger.warning(f"Unknown resolution {resolution}, defaulting to 720p")
            self.width, self.height = 1280, 720
        
        # Optimize settings based on GPU type
        if gpu_type == "L4":
            # L4 has 24GB VRAM, can handle more intensive settings
            self.sample_steps = 30  # Standard quality with L4
            self.sample_shift = 15  # Standard setting for quality
            self.guide_scale = 9.0  # Higher guidance for better quality
            self.model_chunk_size = 2  # Optimize for better memory usage on L4
            logger.info("Optimizing for NVIDIA L4 GPU with 24GB VRAM")
        else:
            # Fallback to T4 settings
            self.sample_steps = 25  # Reduced from default 30
            self.sample_shift = 10  # Optimized for T4
            self.guide_scale = 6.0  # Optimized for T4 generation quality
            self.model_chunk_size = 3  # More chunks for T4 to conserve memory
            logger.info("Using T4-compatible settings")
    
    def initialize(self) -> bool:
        """Initialize the Wan 2.1 model."""
        try:
            import sys
            sys.path.append(self.model_dir)
            
            # Import needed modules from the model
            from diffusers import DiffusionPipeline, DPMSolverMultistepScheduler
            from transformers import T5EncoderModel
            
            # Check GPU type and apply optimizations
            if self.optimize_for_gpu and torch.cuda.is_available():
                gpu_name = torch.cuda.get_device_name(0).lower()
                vram_mb = torch.cuda.get_device_properties(0).total_memory / (1024 * 1024)
                logger.info(f"Detected GPU: {gpu_name} with {vram_mb:.0f}MB VRAM")
                
                # Clear GPU memory
                torch.cuda.empty_cache()
                
                # L4-specific optimizations
                if 'l4' in gpu_name or vram_mb > 20000:
                    logger.info("Confirmed NVIDIA L4 GPU, applying optimal settings")
                    self.gpu_type = "L4"
                    # L4 settings optimized for performance
                    torch.cuda.set_per_process_memory_fraction(0.95)
                    
                    # Set L4-specific parameters if needed
                    if self.resolution == "720p" and "l4" in gpu_name:
                        # Boost quality settings for L4
                        self.sample_steps = 35  # Higher quality for L4
                        self.guide_scale = 9.5  # Stronger guidance for L4
                elif 't4' in gpu_name:
                    logger.info("Detected T4 GPU, applying conservative memory settings")
                    self.gpu_type = "T4"
                    torch.cuda.set_per_process_memory_fraction(0.9)
            
            logger.info(f"Loading T2V model from {self.model_dir}")
            
            # Set up model with optimizations for detected GPU
            dtype = torch.float16 if self.use_fp16 else torch.float32
            
            # Load the pipeline with memory optimizations
            self.model = DiffusionPipeline.from_pretrained(
                self.model_dir,
                torch_dtype=dtype,
                variant="fp16" if self.use_fp16 else None,
            )
            
            # Use a faster scheduler if available
            if hasattr(self.model, 'scheduler') and self.gpu_type == "L4":
                try:
                    # Use DPMSolverMultistepScheduler for faster sampling on L4
                    self.model.scheduler = DPMSolverMultistepScheduler.from_config(
                        self.model.scheduler.config,
                        algorithm_type="dpmsolver++",
                        use_karras_sigmas=True
                    )
                    logger.info("Using optimized DPMSolver++ scheduler for L4 GPU")
                except Exception as e:
                    logger.warning(f"Could not set optimized scheduler: {e}")
            
            # Move to device
            self.model = self.model.to(self.device)
            
            # Apply memory optimizations based on GPU type
            if self.optimize_for_gpu:
                if self.gpu_type == "T4":
                    # Full offload for T4
                    self.model.enable_model_cpu_offload()
                    if hasattr(self.model, 'enable_xformers_memory_efficient_attention'):
                        self.model.enable_xformers_memory_efficient_attention()
                else:
                    # L4 can handle more components on GPU for faster processing
                    # Only offload text encoder and VAE for better performance on L4
                    if hasattr(self.model, 'enable_sequential_cpu_offload'):
                        self.model.enable_sequential_cpu_offload()
                    else:
                        # Fallback to standard offload if sequential not available
                        self.model.enable_model_cpu_offload()
                    
                    # Still use memory efficient attention for L4
                    if hasattr(self.model, 'enable_xformers_memory_efficient_attention'):
                        self.model.enable_xformers_memory_efficient_attention()
                        
                    # Additional L4 optimizations for speed
                    if self.gpu_type == "L4":
                        if hasattr(self.model, 'enable_attention_slicing'):
                            # Use smaller slices for L4 since it has more VRAM
                            self.model.enable_attention_slicing(slice_size="auto")
                            logger.info("Enabled dynamic attention slicing for L4 GPU")
            
            self.initialized = True
            logger.info(f"Wan 2.1 T2V model initialized successfully with {self.gpu_type} settings")
            return True
            
        except Exception as e:
            logger.error(f"Error initializing Wan 2.1 model: {e}")
            import traceback
            logger.error(traceback.format_exc())
            self.initialized = False
            return False
    
    def generate_video(
        self, 
        prompt: str, 
        output_path: str,
        negative_prompt: str = "",
        duration: int = 5,
        fps: int = 24,
        use_prompt_extend: bool = False,
    ) -> Optional[str]:
        """
        Generate a video using the Wan 2.1 T2V model.
        
        Args:
            prompt: Text prompt describing the video
            output_path: Path to save the generated video
            negative_prompt: Text to avoid in the video
            duration: Duration of the video in seconds
            fps: Frames per second
            use_prompt_extend: Whether to use prompt extension for better quality
            
        Returns:
            Path to the generated video if successful, None otherwise
        """
        if not self.initialized:
            if not self.initialize():
                logger.error("Failed to initialize Wan 2.1 model")
                return None
        
        try:
            logger.info(f"Generating video for prompt: {prompt}")
            
            # Calculate frames based on duration and fps
            num_frames = duration * fps
            
            # Prepare settings based on GPU type
            sample_steps = self.sample_steps
            guide_scale = self.guide_scale
            
            # For shorter videos, we can use more steps on L4 for higher quality
            if self.gpu_type == "L4" and duration <= 5:
                sample_steps = 40  # Higher quality for short videos on L4
            
            # Start the generation
            logger.info(f"Starting Wan 2.1 video generation with {num_frames} frames at {self.width}x{self.height}")
            logger.info(f"Using {sample_steps} sample steps and guidance scale {guide_scale}")
            
            # Ensure output directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Generate video with the model
            start_time = time.time()
            
            # Set seed for reproducibility if needed
            # torch.manual_seed(42)
            
            with torch.inference_mode():
                # Call the model's generation method
                output = self.model(
                    prompt=prompt,
                    negative_prompt=negative_prompt,
                    width=self.width,
                    height=self.height,
                    num_frames=num_frames,
                    num_inference_steps=sample_steps,
                    guidance_scale=guide_scale,
                )
                
                # Process and save the video
                video_frames = output.frames[0]
                
                # Save as MP4
                if video_frames is not None:
                    try:
                        # Convert to numpy array if not already
                        if isinstance(video_frames, torch.Tensor):
                            video_frames = video_frames.cpu().numpy()
                        
                        # Normalize and convert to uint8 if needed
                        if video_frames.max() <= 1.0:
                            video_frames = (video_frames * 255).astype(np.uint8)
                        
                        # Create temporary directory for frames
                        temp_frame_dir = os.path.join(self.session_dir, "frames")
                        os.makedirs(temp_frame_dir, exist_ok=True)
                        
                        # Save individual frames
                        frame_paths = []
                        for i, frame in enumerate(video_frames):
                            frame_path = os.path.join(temp_frame_dir, f"frame_{i:04d}.png")
                            Image.fromarray(frame).save(frame_path)
                            frame_paths.append(frame_path)
                        
                        # Use ffmpeg to create video with the correct FPS
                        ffmpeg_cmd = [
                            "ffmpeg", "-y",
                            "-framerate", str(fps),
                            "-i", os.path.join(temp_frame_dir, "frame_%04d.png"),
                            "-c:v", "libx264",
                            "-profile:v", "high",
                            "-crf", "18",  # Use CRF 18 for high quality
                            "-pix_fmt", "yuv420p",
                            output_path
                        ]
                        
                        # Run ffmpeg
                        subprocess.run(ffmpeg_cmd, check=True, capture_output=True)
                        
                        if os.path.exists(output_path):
                            elapsed = time.time() - start_time
                            logger.info(f"Video generated successfully in {elapsed:.2f} seconds: {output_path}")
                            return output_path
                        else:
                            logger.error("FFmpeg did not generate the output file")
                    except Exception as e:
                        logger.error(f"Error saving video frames: {e}")
                else:
                    logger.error("No video frames were generated")
            
            return None
        
        except Exception as e:
            logger.error(f"Error generating video: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None
    
    def cleanup(self):
        """Clean up temporary resources."""
        try:
            if hasattr(self, 'model') and self.model is not None:
                # Unload model from GPU
                if hasattr(self.model, 'to'):
                    self.model.to('cpu')
                del self.model
                self.model = None
                
                # Clear CUDA cache
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
            
            # Remove temporary directory
            if hasattr(self, 'session_dir') and os.path.exists(self.session_dir):
                shutil.rmtree(self.session_dir, ignore_errors=True)
                logger.info(f"Cleaned up temporary directory: {self.session_dir}")
            
            self.initialized = False
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")


# Simple command-line interface
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate videos with Wan 2.1 T2V model")
    parser.add_argument("--model-dir", required=True, help="Path to Wan 2.1 T2V model directory")
    parser.add_argument("--prompt", required=True, help="Text prompt for video generation")
    parser.add_argument("--output", required=True, help="Output path for the generated video")
    parser.add_argument("--negative", default="", help="Negative prompt")
    parser.add_argument("--resolution", default="720p", choices=["480p", "720p", "1080p"], help="Video resolution")
    parser.add_argument("--duration", type=int, default=5, help="Video duration in seconds")
    parser.add_argument("--fps", type=int, default=24, help="Frames per second")
    parser.add_argument("--gpu-type", default="L4", choices=["L4", "T4"], help="GPU type to optimize for")
    
    args = parser.parse_args()
    
    # Configure basic logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Create generator
    generator = WanVideoGenerator(
        model_dir=args.model_dir,
        resolution=args.resolution,
        gpu_type=args.gpu_type
    )
    
    # Generate video
    try:
        video_path = generator.generate_video(
            prompt=args.prompt,
            negative_prompt=args.negative,
            output_path=args.output,
            duration=args.duration,
            fps=args.fps
        )
        
        if video_path:
            print(f"Video generated successfully: {video_path}")
            sys.exit(0)
        else:
            print("Failed to generate video")
            sys.exit(1)
    finally:
        # Always clean up resources
        generator.cleanup() 