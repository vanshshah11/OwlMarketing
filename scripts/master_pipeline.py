#!/usr/bin/env python3
# /Users/vanshshah/Desktop/OWLmarketing/scripts/master_pipeline.py

import os
import sys
import argparse
import logging
import random
from pathlib import Path
import time
import cv2
import numpy as np
from typing import List, Dict, Optional
import json
import torch
from PIL import Image, ImageDraw, ImageFont
import soundfile as sf
import librosa

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from video_editing.video_analyzer import VideoAnalyzer
from video_editing.hooks_templates import HOOK_TEMPLATES, VALUE_PROP_TEMPLATES, CTA_TEMPLATES

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler("pipeline.log"),
        logging.StreamHandler()
    ]
)

class VideoProcessor:
    def __init__(self, 
                 output_dir: str = "data/final_videos",
                 font_path: str = "data/fonts/Montserrat-Bold.ttf",
                 fps: int = 30,
                 resolution: tuple = (1080, 1920)):  # 9:16 aspect ratio
        """
        Initialize video processor with configuration.
        
        Args:
            output_dir (str): Directory for output videos
            font_path (str): Path to font file for text overlay
            fps (int): Frames per second for output video
            resolution (tuple): Output video resolution (width, height)
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.font_path = font_path
        self.fps = fps
        self.resolution = resolution
        
        # Load font for text overlay
        try:
            self.font = ImageFont.truetype(font_path, 40)
            self.title_font = ImageFont.truetype(font_path, 48)
        except Exception as e:
            logging.warning(f"Could not load font {font_path}, using default")
            self.font = ImageFont.load_default()
            self.title_font = ImageFont.load_default()
    
    def create_text_overlay(self, 
                          text: str,
                          size: tuple,
                          style: str = 'body') -> np.ndarray:
        """Create text overlay image with alpha channel."""
        # Create transparent image
        img = Image.new('RGBA', size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # Select font based on style
        font = self.title_font if style == 'title' else self.font
        
        # Calculate text size and position
        text_bbox = draw.textbbox((0, 0), text, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        
        x = (size[0] - text_width) // 2
        y = size[1] - text_height - 20  # 20px padding from bottom
        
        # Draw text with background
        bg_bbox = (x-10, y-10, x+text_width+10, y+text_height+10)
        draw.rectangle(bg_bbox, fill=(0, 0, 0, 128))
        draw.text((x, y), text, font=font, fill=(255, 255, 255, 255))
        
        return np.array(img)
    
    def apply_text_animation(self,
                           text_overlay: np.ndarray,
                           frame_num: int,
                           total_frames: int,
                           animation: str = 'slide') -> np.ndarray:
        """Apply animation to text overlay."""
        if animation == 'fade':
            alpha = min(frame_num / (total_frames * 0.2), 1.0)  # Fade in first 20% of duration
            text_overlay = text_overlay.copy()
            text_overlay[:, :, 3] = text_overlay[:, :, 3] * alpha
            
        elif animation == 'slide':
            offset = int((1 - min(frame_num / (total_frames * 0.3), 1.0)) * 100)  # Slide up in first 30%
            text_overlay = np.roll(text_overlay, offset, axis=0)
            
        elif animation == 'zoom':
            scale = 1 + 0.2 * np.sin(frame_num / total_frames * 2 * np.pi)  # Pulsing zoom
            center = (text_overlay.shape[1] // 2, text_overlay.shape[0] // 2)
            M = cv2.getRotationMatrix2D(center, 0, scale)
            text_overlay = cv2.warpAffine(text_overlay, M, (text_overlay.shape[1], text_overlay.shape[0]))
            
        return text_overlay
    
    def process_video(self,
                     input_path: str,
                     output_path: str,
                     captions: List[Dict],
                     music_path: Optional[str] = None,
                     effects: List[str] = None) -> str:
        """
        Process video with captions, effects, and music.
        
        Args:
            input_path (str): Path to input video
            output_path (str): Path for output video
            captions (List[Dict]): List of caption configurations
            music_path (Optional[str]): Path to background music
            effects (List[str]): List of effects to apply
            
        Returns:
            str: Path to processed video
        """
        cap = cv2.VideoCapture(input_path)
        if not cap.isOpened():
            raise ValueError(f"Could not open video: {input_path}")
        
        # Get video properties
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        input_fps = cap.get(cv2.CAP_PROP_FPS)
        
        # Create video writer
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, self.fps, self.resolution)
        
        # Prepare captions
        caption_overlays = {}
        for caption in captions:
            start_frame = int(caption['start'] * self.fps)
            end_frame = int((caption['start'] + caption['duration']) * self.fps)
            overlay = self.create_text_overlay(
                caption['text'],
                self.resolution,
                caption.get('style', 'body')
            )
            caption_overlays[caption['text']] = {
                'overlay': overlay,
                'start': start_frame,
                'end': end_frame,
                'animation': caption.get('animation', 'slide')
            }
        
        frame_num = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Resize frame to target resolution
            frame = cv2.resize(frame, self.resolution)
            
            # Apply effects
            if effects:
                if 'brighten' in effects:
                    frame = cv2.convertScaleAbs(frame, alpha=1.2, beta=10)
                if 'contrast' in effects:
                    frame = cv2.convertScaleAbs(frame, alpha=1.3, beta=0)
                if 'stabilize' in effects:
                    # Simple stabilization - you might want to implement more sophisticated methods
                    if frame_num > 0:
                        frame = cv2.addWeighted(prev_frame, 0.5, frame, 0.5, 0)
            
            # Apply captions
            for caption_info in caption_overlays.values():
                if caption_info['start'] <= frame_num <= caption_info['end']:
                    overlay = self.apply_text_animation(
                        caption_info['overlay'],
                        frame_num - caption_info['start'],
                        caption_info['end'] - caption_info['start'],
                        caption_info['animation']
                    )
                    
                    # Blend overlay with frame
                    alpha = overlay[:, :, 3:] / 255.0
                    rgb = overlay[:, :, :3]
                    frame = frame * (1 - alpha) + rgb * alpha
            
            # Write frame
            out.write(frame.astype(np.uint8))
            prev_frame = frame.copy()
            frame_num += 1
            
            # Progress logging
            if frame_num % 30 == 0:
                progress = (frame_num / total_frames) * 100
                logging.info(f"Processing video: {progress:.1f}% complete")
        
        # Release resources
        cap.release()
        out.release()
        
        # Add audio if provided
        if music_path:
            self._add_audio(output_path, music_path)
        
        return output_path
    
    def _add_audio(self, video_path: str, audio_path: str):
        """Add background music to video."""
        # Load audio
        audio, sr = librosa.load(audio_path)
        
        # Get video duration
        cap = cv2.VideoCapture(video_path)
        video_duration = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) / self.fps)
        cap.release()
        
        # Trim or loop audio to match video duration
        if len(audio) / sr > video_duration:
            audio = audio[:int(video_duration * sr)]
        else:
            repeats = int(np.ceil(video_duration * sr / len(audio)))
            audio = np.tile(audio, repeats)[:int(video_duration * sr)]
        
        # Save processed audio
        temp_audio = "temp_audio.wav"
        sf.write(temp_audio, audio, sr)
        
        # Combine video and audio using ffmpeg
        output_with_audio = video_path.replace(".mp4", "_with_audio.mp4")
        os.system(f'ffmpeg -i {video_path} -i {temp_audio} -c:v copy -c:a aac {output_with_audio}')
        
        # Clean up
        os.remove(temp_audio)
        os.rename(output_with_audio, video_path)

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Run the complete video generation pipeline")
    parser.add_argument("--analyze", action="store_true", help="Force reanalysis of training videos")
    parser.add_argument("--app-name", default="Optimal AI", help="App name to use in templates")
    parser.add_argument("--avatar", default="sarah", help="Avatar to use for video")
    parser.add_argument("--music", default=None, help="Path to background music file")
    parser.add_argument("--output-dir", default="data/final_videos", help="Output directory for final videos")
    parser.add_argument("--count", type=int, default=1, help="Number of videos to generate")
    parser.add_argument("--font", default="data/fonts/Montserrat-Bold.ttf", help="Path to font file")
    return parser.parse_args()

def create_script(app_name: str, avatar: str) -> Dict:
    """Create a random script for video generation."""
    return {
        "avatar": avatar,
        "app_name": app_name,
        "hook_template": random.choice(HOOK_TEMPLATES)
    }

def main():
    """Run the complete video generation pipeline."""
    args = parse_args()
    
    try:
        # Step 1: Analyze training videos (once, or when forced)
        logging.info("Step 1: Analyzing training videos")
        analyzer = VideoAnalyzer()
        patterns = analyzer.analyze_training_set(force_reanalyze=args.analyze)
        logging.info(f"Analysis complete. Found {len(patterns.get('duration', []))} videos with patterns")
        
        # Initialize video processor
        processor = VideoProcessor(
            output_dir=args.output_dir,
            font_path=args.font
        )
        
        # Generate multiple videos if requested
        for i in range(args.count):
            video_id = int(time.time()) + i
            
            try:
                # Step 2: Generate script and captions
                logging.info(f"Step 2: Generating video {i+1}/{args.count}")
                script = create_script(args.app_name, args.avatar)
                
                # Create captions with authentic hooks
                captions = [
                    {
                        'text': script['hook_template'].format(app_name=script['app_name']),
                        'start': 0,
                        'duration': 3,
                        'style': 'title',
                        'animation': 'fade'
                    },
                    {
                        'text': f"Look at how fast {script['app_name']} tracks everything! It's CRAZY efficient!",
                        'start': 3,
                        'duration': 4,
                        'style': 'body',
                        'animation': 'slide'
                    },
                    {
                        'text': random.choice(VALUE_PROP_TEMPLATES).format(app_name=script['app_name']),
                        'start': 7,
                        'duration': 3,
                        'style': 'body',
                        'animation': 'slide'
                    },
                    {
                        'text': random.choice(CTA_TEMPLATES).format(app_name=script['app_name']),
                        'start': 10,
                        'duration': 5,
                        'style': 'title',
                        'animation': 'zoom'
                    }
                ]
                
                # Step 3: Process video with learned patterns
                output_path = str(Path(args.output_dir) / f"final_video_{video_id}.mp4")
                final_video = processor.process_video(
                    input_path=f"data/raw_videos/{script['avatar']}_base.mp4",
                    output_path=output_path,
                    captions=captions,
                    music_path=args.music,
                    effects=['brighten', 'contrast']
                )
                
                logging.info(f"✅ Video {i+1} complete! Saved to: {final_video}")
                
            except Exception as e:
                logging.error(f"❌ Error processing video {i+1}: {str(e)}")
                continue
        
        logging.info("All requested videos completed successfully!")
        
    except Exception as e:
        logging.error(f"❌ Pipeline failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
