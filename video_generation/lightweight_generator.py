#!/usr/bin/env python3
# /Users/vanshshah/Desktop/OWLmarketing/video_generation/lightweight_generator.py

import os
import torch
import logging
import traceback
from PIL import Image, ImageFont, ImageDraw
import time

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def generate_keyframe(prompt, scene_num, keyframe_num):
    """
    Generates a keyframe image using a lightweight Stable Diffusion approach
    optimized for CPU usage on older MacBooks.
    
    Args:
        prompt (str): The text prompt to generate the image from
        scene_num (int): The scene number for logging
        keyframe_num (int): The keyframe number for logging
        
    Returns:
        PIL.Image: The generated image or a fallback image if generation fails
    """
    try:
        # Import diffusers only when needed to save memory
        from diffusers import StableDiffusionPipeline

        # Use a smaller model with fewer parameters
        model_id = "runwayml/stable-diffusion-v1-5"  # Smaller than SDXL
        
        logger.info(f"Initializing lightweight SD pipeline with model {model_id}")
        
        # Create pipeline with minimal components
        pipe = StableDiffusionPipeline.from_pretrained(
            model_id,
            safety_checker=None,  # Disable safety checker to save memory
            requires_safety_checker=False,
            use_safetensors=True,  # More memory efficient
        )
        
        # Move to CPU and optimize
        pipe = pipe.to("cpu")
        pipe.enable_attention_slicing()  # Reduces memory usage
        
        # Use a lower precision to save memory
        if hasattr(pipe, "unet"):
            pipe.unet.to(torch.float32)
        
        logger.info(f"Successfully initialized lightweight pipeline for scene {scene_num}, keyframe {keyframe_num}")
        
        # Simplify prompt to essential elements
        simple_prompt = f"A person using a smartphone app to track calories. {prompt[:100]}"
        logger.debug(f"Using simplified prompt: {simple_prompt}")
        
        # Generate with minimal parameters
        generation_start = time.time()
        output = pipe(
            prompt=simple_prompt,
            height=512,  # Smaller resolution
            width=512,
            num_inference_steps=8,  # Minimal steps
            guidance_scale=7.0,
            num_images_per_prompt=1,
        )
        
        generation_time = time.time() - generation_start
        logger.info(f"Lightweight image generation took {generation_time:.2f} seconds")
        
        # Check if we got a valid image
        if output and hasattr(output, "images") and len(output.images) > 0:
            image = output.images[0]
            logger.info(f"Successfully generated lightweight image for scene {scene_num}, keyframe {keyframe_num}")
            return image
        else:
            logger.error(f"Lightweight pipeline returned no images for scene {scene_num}, keyframe {keyframe_num}")
            return _create_fallback_image(scene_num, keyframe_num, prompt)
            
    except Exception as e:
        logger.error(f"Error in lightweight image generation for scene {scene_num}, keyframe {keyframe_num}: {e}")
        logger.debug(traceback.format_exc())
        return _create_fallback_image(scene_num, keyframe_num, prompt)

def _create_fallback_image(scene_num, keyframe_num, prompt):
    """
    Creates a fallback image with text when image generation fails
    
    Args:
        scene_num (int): The scene number
        keyframe_num (int): The keyframe number
        prompt (str): The original prompt text
    
    Returns:
        PIL.Image: A simple text-based image
    """
    logger.info(f"Creating fallback image for scene {scene_num}, keyframe {keyframe_num}")
    
    # Create a blank image
    img = Image.new('RGB', (512, 512), color=(53, 53, 53))
    draw = ImageDraw.Draw(img)
    
    try:
        # Try to load a font, use default if not available
        font = ImageFont.truetype("Arial", 20)
    except IOError:
        font = ImageFont.load_default()
    
    # Add text to the image
    text = f"Scene {scene_num}, Frame {keyframe_num}\n\n{prompt[:200]}"
    
    # Draw text with wrapped lines
    lines = []
    words = text.split()
    current_line = ""
    
    for word in words:
        test_line = current_line + " " + word if current_line else word
        text_width = draw.textlength(test_line, font=font)
        
        if text_width <= 480:  # Leave some margin
            current_line = test_line
        else:
            lines.append(current_line)
            current_line = word
    
    if current_line:
        lines.append(current_line)
    
    # Draw each line
    y_position = 100
    for line in lines:
        draw.text((30, y_position), line, font=font, fill=(255, 255, 255))
        y_position += 30
    
    # Add app logo text
    draw.text((200, 30), "Optimal AI", font=font, fill=(255, 215, 0))
    
    logger.info(f"Created fallback image with text for scene {scene_num}, keyframe {keyframe_num}")
    return img 