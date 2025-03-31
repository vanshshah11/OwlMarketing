#!/usr/bin/env python3
# generate_avatar.py: Script to generate avatar images using Stable Diffusion:
# Generates base images and variations for each avatar
# Uses optimized prompts for consistent style
# Saves images in organized directories

import os
import logging
import torch
from pathlib import Path
from diffusers import StableDiffusionPipeline
from video_generation.avatar_config import AVATAR_CONFIGS

# Configure logging
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s: %(message)s')

class AvatarGenerator:
    def __init__(self, model_path=None, output_dir="data/generated_avatars"):
        """
        Initialize the avatar generator with a Stable Diffusion model.
        
        Args:
            model_path (str): Path to fine-tuned model or model ID from HuggingFace
            output_dir (str): Directory to save generated images
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Use default model if no specific model path provided
        if model_path is None:
            model_path = "stabilityai/stable-diffusion-xl-base-1.0"
        
        # Initialize Stable Diffusion pipeline
        logging.info(f"Loading Stable Diffusion XL model from {model_path}")
        
        # Check for GPU availability and optimize accordingly
        if torch.cuda.is_available():
            # Get GPU information
            gpu_name = torch.cuda.get_device_name(0)
            gpu_memory = torch.cuda.get_device_properties(0).total_memory / (1024 ** 3)  # Convert to GB
            logging.info(f"GPU detected: {gpu_name} with {gpu_memory:.2f}GB memory")
            
            # Load with optimizations for powerful GPUs like RTX 4090
            self.pipe = StableDiffusionPipeline.from_pretrained(
                model_path,
                torch_dtype=torch.float16,  # Use half precision for better performance
                use_safetensors=True,
                variant="fp16"  # Use FP16 variant if available
            )
            
            # Move to GPU
            self.pipe = self.pipe.to("cuda")
            
            # Apply memory optimizations
            self.pipe.enable_vae_slicing()  # Reduces VRAM usage during generation
            
            # Enable attention slicing for memory efficiency
            self.pipe.enable_attention_slicing(slice_size="auto")
            
            # For RTX 4090 and similar high-end GPUs, enable xformers for even better performance
            try:
                import xformers
                self.pipe.enable_xformers_memory_efficient_attention()
                logging.info("Using xformers memory efficient attention for maximum performance")
            except ImportError:
                logging.info("xformers package not found, using standard attention mechanism")
                
            # For newer versions of diffusers that support torch compile
            if hasattr(torch, 'compile') and hasattr(self.pipe, 'unet'):
                try:
                    self.pipe.unet = torch.compile(self.pipe.unet, mode="reduce-overhead", fullgraph=True)
                    logging.info("Using torch.compile for even faster inference")
                except Exception as e:
                    logging.warning(f"Could not use torch.compile: {e}")
            
            logging.info("Using CUDA with optimized settings for high-end GPU")
        else:
            # CPU fallback with basic settings
            self.pipe = StableDiffusionPipeline.from_pretrained(
                model_path,
                torch_dtype=torch.float32,
                use_safetensors=True
            )
            logging.info("Using CPU for generation (this will be slow)")
    
    def generate_avatar_set(self, avatar_key, num_variations=3):
        """
        Generate a set of images for a specific avatar persona.
        
        Args:
            avatar_key (str): Key of the avatar in AVATAR_CONFIGS
            num_variations (int): Number of variations to generate per prompt
        """
        if avatar_key not in AVATAR_CONFIGS:
            raise ValueError(f"Avatar key '{avatar_key}' not found in config")
        
        avatar_config = AVATAR_CONFIGS[avatar_key]
        avatar_dir = self.output_dir / avatar_key
        avatar_dir.mkdir(exist_ok=True)
        
        # Generate base avatar images
        logging.info(f"Generating base images for {avatar_config['name']}")
        self._generate_images(
            prompt=f"{avatar_config['base_prompt']}, {avatar_config['style_prompt']}",
            negative_prompt=avatar_config['negative_prompt'],
            output_dir=avatar_dir,
            prefix="base",
            num_images=num_variations
        )
        
        # Generate variations for different content types
        for variation_type, variation_prompt in avatar_config['variations'].items():
            logging.info(f"Generating {variation_type} variations for {avatar_config['name']}")
            self._generate_images(
                prompt=f"{variation_prompt}, {avatar_config['style_prompt']}",
                negative_prompt=avatar_config['negative_prompt'],
                output_dir=avatar_dir,
                prefix=variation_type,
                num_images=num_variations
            )
    
    def _generate_images(self, prompt, negative_prompt, output_dir, prefix, num_images=1):
        """
        Generate multiple images for a given prompt.
        
        Args:
            prompt (str): The positive prompt for image generation
            negative_prompt (str): The negative prompt for image generation
            output_dir (Path): Directory to save generated images
            prefix (str): Prefix for the image filenames
            num_images (int): Number of images to generate
        """
        # Ensure prompts don't exceed token limits (CLIP has 77 token limit)
        max_prompt_length = 77
        prompt_words = prompt.split()
        shortened_prompt = " ".join(prompt_words[:min(len(prompt_words), max_prompt_length - 5)])
        
        for i in range(num_images):
            try:
                # Safely generate the image, handling potential errors
                try:
                    # Generate image with optimized parameters for avatars
                    result = self.pipe(
                        prompt=shortened_prompt,
                        negative_prompt=negative_prompt,
                        num_inference_steps=40,  # Reduced from 50 for better speed/quality balance
                        guidance_scale=8.0,      # Slightly increased for better prompt adherence
                        width=1024,             # SDXL supports higher resolution
                        height=1024
                    )
                    
                    # Check if the model returned valid images
                    if result is None or not hasattr(result, 'images') or result.images is None or len(result.images) == 0:
                        raise ValueError("Model did not return any images")
                        
                    image = result.images[0]
                except Exception as model_error:
                    logging.error(f"Error from model: {str(model_error)}")
                    # Create a fallback image
                    image = self._create_fallback_image(prefix)
                    logging.info(f"Created fallback image for {prefix}")
                
                # Save image
                image_path = output_dir / f"{prefix}_{i+1}.png"
                image.save(str(image_path))
                logging.info(f"Generated image saved to {image_path}")
                
            except Exception as e:
                logging.error(f"Error generating image {i+1} for {prefix}: {str(e)}")
                # Create an emergency fallback
                self._create_emergency_fallback(output_dir, prefix, i+1)
    
    def _create_fallback_image(self, prefix):
        """Create a fallback image when model generation fails."""
        from PIL import Image, ImageDraw, ImageFont
        import random
        
        # Create a gradient background
        img = Image.new('RGB', (1024, 1024), color=(255, 255, 255))
        draw = ImageDraw.Draw(img)
        
        # Add color gradient
        for y in range(1024):
            r = int(200 + 55 * (y / 1024))
            g = int(200 + 55 * (1 - y / 1024))
            b = int(200 + 55 * (0.5 - abs(0.5 - y / 1024)))
            draw.line([(0, y), (1024, y)], fill=(r, g, b))
        
        # Try to load a font
        try:
            font = ImageFont.truetype("Arial", 60)
        except:
            font = ImageFont.load_default()
        
        # Add text explaining this is a fallback
        text = f"Generated Avatar\n{prefix.title()}"
        draw.multiline_text((512, 512), text, fill=(0, 0, 0), font=font, anchor="mm", align="center")
        
        # Add some random shapes for visual interest
        for _ in range(20):
            x = random.randint(50, 974)
            y = random.randint(50, 974)
            size = random.randint(10, 50)
            r = random.randint(0, 255)
            g = random.randint(0, 255)
            b = random.randint(0, 255)
            draw.ellipse((x, y, x+size, y+size), fill=(r, g, b, 128))
        
        logging.info(f"Created fallback image for {prefix}")
        return img
    
    def _create_emergency_fallback(self, output_dir, prefix, index):
        """Create an emergency fallback image when all else fails."""
        try:
            from PIL import Image, ImageDraw
            
            # Create a simple colored image
            img = Image.new('RGB', (1024, 1024), color=(200, 200, 200))
            draw = ImageDraw.Draw(img)
            
            # Draw a colored rectangle
            draw.rectangle((100, 100, 924, 924), fill=(240, 240, 240), outline=(180, 180, 180), width=5)
            
            # Save the image
            image_path = output_dir / f"{prefix}_{index}.png"
            img.save(str(image_path))
            logging.warning(f"Created emergency fallback image at {image_path}")
        except Exception as e:
            logging.critical(f"Failed to create even emergency fallback: {e}")
            # Nothing more we can do here

def generate_avatar_set(avatar_key, style=None, output_dir=None, num_variations=3):
    """
    Generate a set of avatar images for the specified avatar.
    
    Args:
        avatar_key (str): Key of the avatar in AVATAR_CONFIGS (e.g. "sarah", "charlotte")
        style (str, optional): Specific style variation to generate. If None, generates all variations.
        output_dir (str, optional): Custom output directory for avatar images
        num_variations (int): Number of variations to generate per style
        
    Returns:
        dict: Dictionary containing paths to generated avatar images and videos
    """
    try:
        # Initialize generator with custom output dir if provided
        generator = AvatarGenerator(output_dir=output_dir or "data/generated_avatars")
        
        # Generate avatar images
        if style and style in AVATAR_CONFIGS[avatar_key]["variations"]:
            # Generate only the specified style
            avatar_dir = Path(generator.output_dir) / avatar_key
            avatar_dir.mkdir(exist_ok=True)
            
            logging.info(f"Generating {style} style for {avatar_key}")
            generator._generate_images(
                prompt=f"{AVATAR_CONFIGS[avatar_key]['variations'][style]}, {AVATAR_CONFIGS[avatar_key]['style_prompt']}",
                negative_prompt=AVATAR_CONFIGS[avatar_key]['negative_prompt'],
                output_dir=avatar_dir,
                prefix=style,
                num_images=num_variations
            )
            
            # Return paths to generated files
            avatar_image = str(avatar_dir / f"{style}_1.png")
            avatar_video = create_avatar_video(avatar_image, f"{avatar_key}_{style}")
            
            return {
                "avatar_key": avatar_key,
                "style": style,
                "avatar_image": avatar_image,
                "avatar_video": avatar_video or ""
            }
            
        else:
            # Generate all variations
            generator.generate_avatar_set(avatar_key, num_variations)
            
            # Return paths to generated files
            avatar_dir = Path(generator.output_dir) / avatar_key
            styles = list(AVATAR_CONFIGS[avatar_key]["variations"].keys())
            default_style = styles[0] if styles else "base"
            
            avatar_image = str(avatar_dir / f"{default_style}_1.png")
            avatar_video = create_avatar_video(avatar_image, f"{avatar_key}_{default_style}")
            
            return {
                "avatar_key": avatar_key,
                "style": default_style,
                "avatar_image": avatar_image,
                "avatar_video": avatar_video or ""
            }
            
    except Exception as e:
        logging.error(f"Error generating avatar set: {e}")
        return {
            "avatar_key": avatar_key,
            "error": str(e)
        }

def create_avatar_video(image_path, name, duration=5.0):
    """
    Create a simple video from a static avatar image.
    This is a placeholder until we have proper video generation.
    
    Args:
        image_path (str): Path to the avatar image
        name (str): Name for the output video file
        duration (float): Duration of the video in seconds
        
    Returns:
        str: Path to the generated video or None if failed
    """
    try:
        from PIL import Image, ImageDraw, ImageFont
        import cv2
        import numpy as np
        import os
        
        # Check if the image exists
        image_exists = os.path.isfile(image_path)
        
        # If image doesn't exist, create a fallback image
        if not image_exists:
            logging.warning(f"Image does not exist: {image_path}, creating fallback")
            # Extract avatar name and style from the name parameter
            parts = name.split('_')
            avatar_name = parts[0] if parts else "avatar"
            style = parts[1] if len(parts) > 1 else "default"
            
            # Create a fallback image
            img = Image.new('RGB', (1024, 1024), color=(200, 200, 230))
            draw = ImageDraw.Draw(img)
            
            # Add gradient background
            for y in range(1024):
                r = int(180 + 70 * (y / 1024))
                g = int(180 + 70 * (1 - y / 1024))
                b = int(220)
                draw.line([(0, y), (1024, y)], fill=(r, g, b))
            
            # Try to load a font
            try:
                font = ImageFont.truetype("Arial", 80)
                small_font = ImageFont.truetype("Arial", 40)
            except:
                font = ImageFont.load_default()
                small_font = ImageFont.load_default()
            
            # Add text
            draw.text((512, 400), avatar_name.title(), fill=(0, 0, 0), font=font, anchor="mm")
            draw.text((512, 500), f"Style: {style}", fill=(0, 0, 0), font=small_font, anchor="mm")
            
            # Save to a temporary location
            temp_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "temp")
            os.makedirs(temp_dir, exist_ok=True)
            image_path = os.path.join(temp_dir, f"{name}_fallback.png")
            img.save(image_path)
            logging.info(f"Created fallback image for video at {image_path}")
        
        # Create output directory if it doesn't exist
        video_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "output", "videos")
        os.makedirs(video_dir, exist_ok=True)
        
        # Output video path
        video_path = os.path.join(video_dir, f"{name}.mp4")
        
        # Load image and convert to RGB
        img = Image.open(image_path)
        img = img.convert("RGB")
        
        # Resize to 1080x1920 (portrait mode for short-form video)
        img = img.resize((1080, 1920), Image.LANCZOS)
        
        # Convert to numpy array for OpenCV
        img_np = np.array(img)
        
        # Create small animation effect
        fps = 30
        frame_count = int(duration * fps)
        
        # Initialize video writer
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        video = cv2.VideoWriter(video_path, fourcc, fps, (1080, 1920))
        
        # Generate frames with small animation (slight zoom and pan)
        for i in range(frame_count):
            # Calculate zoom and pan parameters based on frame number
            zoom_factor = 1.0 + 0.05 * np.sin(i / frame_count * np.pi)
            pan_x = int(20 * np.sin(i / frame_count * np.pi * 2))
            pan_y = int(20 * np.cos(i / frame_count * np.pi * 2))
            
            # Create a slightly larger frame to accommodate zoom and pan
            h, w = img_np.shape[:2]
            zoomed_h, zoomed_w = int(h * zoom_factor), int(w * zoom_factor)
            
            # Resize image with zoom
            zoomed_img = cv2.resize(img_np, (zoomed_w, zoomed_h))
            
            # Calculate crop region with pan
            x1 = max(0, (zoomed_w - w) // 2 + pan_x)
            y1 = max(0, (zoomed_h - h) // 2 + pan_y)
            x2 = min(zoomed_w, x1 + w)
            y2 = min(zoomed_h, y1 + h)
            
            # Ensure we have enough image to crop
            if x2 - x1 < w or y2 - y1 < h:
                # Adjust crop region if needed
                cropped = zoomed_img[
                    max(0, min(zoomed_h - h, y1)):max(h, min(zoomed_h, y1 + h)),
                    max(0, min(zoomed_w - w, x1)):max(w, min(zoomed_w, x1 + w))
                ]
                # Resize to ensure correct dimensions
                cropped = cv2.resize(cropped, (w, h))
            else:
                # Crop the zoomed image to original size with pan effect
                cropped = zoomed_img[y1:y1+h, x1:x1+w]
            
            # Convert BGR to RGB (OpenCV uses BGR)
            frame = cv2.cvtColor(cropped, cv2.COLOR_RGB2BGR)
            
            # Write frame to video
            video.write(frame)
        
        # Release video writer
        video.release()
        
        logging.info(f"Created avatar video: {video_path}")
        return video_path
        
    except Exception as e:
        logging.error(f"Error creating avatar video: {e}")
        return None

def main():
    # Initialize generator
    generator = AvatarGenerator()
    
    # Generate avatar sets for each persona
    for avatar_key in AVATAR_CONFIGS.keys():
        try:
            generator.generate_avatar_set(avatar_key)
        except Exception as e:
            logging.error(f"Error generating avatar set for {avatar_key}: {str(e)}")

if __name__ == "__main__":
    main() 