#!/usr/bin/env python3
# /Users/vanshshah/Desktop/OWLmarketing/video_editing/edit_video.py

import logging
import os
import subprocess
import tempfile
import cv2
from moviepy import CompositeVideoClip, VideoFileClip, concatenate_videoclips
import numpy as np
from pathlib import Path
from typing import List, Dict, Optional
from PIL import Image, ImageDraw, ImageFont
from .video_analyzer import VideoAnalyzer

# Configure logging
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s: %(message)s')

class VideoEditor:
    def __init__(self, 
                 workspace_dir: str = "data",
                 music_dir: str = "data/music",
                 font_path: str = "data/fonts/Montserrat-Bold.ttf",
                 training_videos_dir: str = "data/training_videos"):
        """
        Initialize the video editor with workspace and resource directories.
        
        Args:
            workspace_dir (str): Directory for temporary files and outputs
            music_dir (str): Directory containing background music tracks
            font_path (str): Path to the font file for text overlays
            training_videos_dir (str): Directory containing training videos
        """
        self.workspace_dir = Path(workspace_dir)
        self.music_dir = Path(music_dir)
        self.font_path = font_path
        
        # Ensure directories exist
        self.workspace_dir.mkdir(parents=True, exist_ok=True)
        self.music_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize video analyzer and get style patterns
        self.analyzer = VideoAnalyzer(training_videos_dir)
        self.style_patterns = self.analyzer.analyze_training_set()
        
        # Update style configurations based on analysis
        self.style_config = {
            'text': {
                'title_size': 48,
                'body_size': 32,
                'color': 'white',
                'stroke_color': 'black',
                'stroke_width': 2,
                'font': font_path,
                'positions': self.style_patterns.get('common_text_positions', [])
            },
            'transitions': {
                'duration': 0.5,
                'types': list(self.style_patterns.get('popular_transitions', {}).keys())
            },
            'aspect_ratio': (1080, 1920),  # 9:16 for vertical video
            'fps': 30,
            'video_effects': {
                'brightness': self.style_patterns.get('avg_brightness', 128),
                'contrast': self.style_patterns.get('avg_contrast', 50)
            },
            'audio': {
                'mean_level': self.style_patterns.get('audio_profile', {}).get('mean_level', 0.5),
                'peak_level': self.style_patterns.get('audio_profile', {}).get('peak_level', 0.8)
            }
        }

    def create_animated_text(self, 
                           text: str,
                           duration: float,
                           style: str = 'body',
                           animation: str = 'slide') -> Dict:
        """
        Create animated text with various effects using PIL instead of moviepy.
        
        Args:
            text (str): Text content
            duration (float): Duration in seconds
            style (str): Text style ('title' or 'body')
            animation (str): Animation type
            
        Returns:
            Dict: Animation configuration dictionary
        """
        # Get font size based on style
        size = self.style_config['text']['title_size'] if style == 'title' else self.style_config['text']['body_size']
        
        # Get optimal position from analysis
        if self.style_config['text']['positions']:
            position = self.style_config['text']['positions'][0]  # Use most common position
        else:
            position = ('center', 'bottom')
        
        # Create animation configuration
        text_config = {
            'text': text,
            'font_size': size,
            'color': self.style_config['text']['color'],
            'font': self.style_config['text']['font'],
            'stroke_color': self.style_config['text']['stroke_color'],
            'stroke_width': self.style_config['text']['stroke_width'],
            'position': position,
            'animation': animation,
            'duration': duration
        }
        
        return text_config

    def add_transition(self, 
                      clip1: VideoFileClip,
                      clip2: VideoFileClip,
                      transition_type: str = None) -> VideoFileClip:
        """
        Add transition effect between two video clips.
        
        Args:
            clip1 (VideoFileClip): First video clip
            clip2 (VideoFileClip): Second video clip
            transition_type (str): Type of transition
            
        Returns:
            VideoFileClip: Combined clip with transition
        """
        # Use most popular transition if none specified
        if transition_type is None and self.style_config['transitions']['types']:
            transition_type = self.style_config['transitions']['types'][0]
        elif transition_type is None:
            transition_type = 'fade'
        
        duration = self.style_config['transitions']['duration']
        
        if transition_type == 'fade':
            clip2 = clip2.crossfadein(duration)
            return concatenate_videoclips([clip1, clip2])
        elif transition_type == 'slide':
            clip2 = clip2.set_start(clip1.duration - duration)
            clip2 = clip2.set_position(lambda t: (t * clip1.w, 0))
            return CompositeVideoClip([clip1, clip2])
        elif transition_type == 'dissolve':
            clip2 = clip2.set_start(clip1.duration - duration)
            return CompositeVideoClip([
                clip1,
                clip2.set_opacity(lambda t: t/duration)
            ])
        
        return concatenate_videoclips([clip1, clip2])

    def mix_audio(self, 
                 video_path: str,
                 music_path: str,
                 output_path: str,
                 video_volume: float = None,
                 music_volume: float = None) -> str:
        """
        Mix video audio with background music using FFmpeg.
        
        Args:
            video_path (str): Path to video file
            music_path (str): Path to music file
            output_path (str): Path for output video
            video_volume (float): Volume of video audio
            music_volume (float): Volume of background music
            
        Returns:
            str: Path to output video with mixed audio
        """
        # Use analyzed audio levels if not specified
        if video_volume is None:
            video_volume = self.style_config['audio']['mean_level']
        if music_volume is None:
            music_volume = self.style_config['audio']['mean_level'] * 0.6  # Slightly lower than speech
        
        # Create FFmpeg command for mixing audio
        try:
            # Extract audio duration to check if looping is needed
            probe_cmd = ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', 
                        '-of', 'default=noprint_wrappers=1:nokey=1', video_path]
            video_duration = float(subprocess.check_output(probe_cmd).decode('utf-8').strip())
            
            # Mix audio and video using FFmpeg
            subprocess.run([
                'ffmpeg', '-y',
                '-i', video_path,                 # Input video
                '-i', music_path,                 # Input music
                '-filter_complex', 
                f'[0:a]volume={video_volume}[a];' # Adjust video audio
                f'[1:a]volume={music_volume},aloop=loop=-1:size=2e+09[b];' # Loop and adjust music
                '[a][b]amix=inputs=2:duration=longest[aout]',  # Mix audios
                '-map', '0:v',                    # Use original video
                '-map', '[aout]',                 # Use mixed audio
                '-c:v', 'copy',                   # Copy video codec
                '-c:a', 'aac',                    # AAC audio codec
                '-shortest',                      # Match shortest stream
                output_path
            ], check=True)
            
            return output_path
            
        except subprocess.CalledProcessError as e:
            logging.error(f"Error mixing audio: {e}")
            # Return original video if audio mixing fails
            return video_path

    def edit_video(self,
                  input_video_path: str,
                  output_video_path: str = "edited_video.mp4",
                  captions: List[Dict] = None,
                  music_path: Optional[str] = None,
                  effects: List[str] = None) -> str:
        """
        Main video editing function using OpenCV and FFmpeg instead of moviepy.
        
        Args:
            input_video_path (str): Path to input video
            output_video_path (str): Path for output video
            captions (List[Dict]): List of caption configs with timing
            music_path (str): Path to background music
            effects (List[str]): List of effects to apply
            
        Returns:
            str: Path to edited video
        """
        logging.info(f"Starting enhanced video editing for {input_video_path}")
        
        # Create temporary file for intermediate processing
        temp_dir = Path(tempfile.mkdtemp())
        temp_video = str(temp_dir / "temp_video.mp4")
        
        # Open the input video
        cap = cv2.VideoCapture(input_video_path)
        if not cap.isOpened():
            raise ValueError(f"Could not open video file: {input_video_path}")
        
        # Get video properties
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        # Resize to vertical format (9:16 aspect ratio)
        target_height = self.style_config['aspect_ratio'][1]
        target_width = self.style_config['aspect_ratio'][0]
        
        # Initialize video writer with target dimensions
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(temp_video, fourcc, fps, (target_width, target_height))
        
        # Process each frame
        frame_idx = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Calculate current time in seconds
            current_time = frame_idx / fps
            
            # Resize frame to vertical format
            current_height, current_width = frame.shape[:2]
            scale = target_height / current_height
            new_width = int(current_width * scale)
            
            # Apply smart cropping/padding
            if new_width < target_width:
                # Pad with blur if too narrow
                frame_resized = cv2.resize(frame, (new_width, target_height))
                
                # Create a blurred background
                frame_blurred = cv2.resize(frame, (target_width, target_height))
                frame_blurred = cv2.GaussianBlur(frame_blurred, (21, 21), 3)
                
                # Create a composite frame
                x_offset = (target_width - new_width) // 2
                frame_final = frame_blurred.copy()
                frame_final[:, x_offset:x_offset+new_width] = frame_resized
            else:
                # Crop if too wide
                frame_resized = cv2.resize(frame, (new_width, target_height))
                x1 = (new_width - target_width) // 2
                frame_final = frame_resized[:, x1:x1+target_width]
            
            # Apply video effects
            if effects:
                for effect in effects:
                    if effect == 'brighten':
                        # Simple brightness adjustment
                        target_brightness = self.style_config['video_effects']['brightness']
                        current_brightness = np.mean(frame_final)
                        adjustment = min(1.5, target_brightness / max(current_brightness, 1))
                        frame_final = cv2.convertScaleAbs(frame_final, alpha=adjustment, beta=10)
                    elif effect == 'contrast':
                        # Simple contrast adjustment
                        target_contrast = self.style_config['video_effects']['contrast']
                        current_contrast = np.std(frame_final)
                        adjustment = min(1.5, target_contrast / max(current_contrast, 1))
                        frame_final = cv2.convertScaleAbs(frame_final, alpha=adjustment, beta=0)
                    elif effect == 'stabilize':
                        # Stabilization would require more complex logic
                        # For now, we skip this effect
                        pass
            
            # Add captions with animation
            if captions:
                for caption in captions:
                    if caption['start'] <= current_time < (caption['start'] + caption['duration']):
                        # Create caption configuration
                        caption_config = self.create_animated_text(
                            text=caption['text'],
                            duration=caption['duration'],
                            style=caption.get('style', 'body'),
                            animation=caption.get('animation', 'slide')
                        )
                        
                        # Create text overlay image with PIL
                        overlay = Image.new('RGBA', (target_width, target_height), (0, 0, 0, 0))
                        draw = ImageDraw.Draw(overlay)
                        
                        # Get font
                        try:
                            font = ImageFont.truetype(caption_config['font'], caption_config['font_size'])
                        except:
                            font = ImageFont.load_default()
                        
                        # Calculate text size and position
                        text = caption_config['text']
                        text_bbox = draw.textbbox((0, 0), text, font=font)
                        text_width = text_bbox[2] - text_bbox[0]
                        text_height = text_bbox[3] - text_bbox[1]
                        
                        # Position based on configuration and animation
                        position = caption_config['position']
                        animation_type = caption_config['animation']
                        
                        # Position based on animation type and timing
                        rel_time = (current_time - caption['start']) / caption['duration']
                        
                        if position[0] == 'center':
                            x = (target_width - text_width) // 2
                        elif position[0] == 'left':
                            x = 20
                        else:  # right
                            x = target_width - text_width - 20
                            
                        if position[1] == 'center':
                            y = (target_height - text_height) // 2
                        elif position[1] == 'top':
                            y = 20
                        else:  # bottom
                            y = target_height - text_height - 50
                        
                        # Apply animation
                        if animation_type == 'slide':
                            # Slide from bottom to position
                            y = y + (1 - min(1, 2 * rel_time)) * 100
                        elif animation_type == 'fade':
                            # Control opacity with time
                            opacity = min(255, int(255 * min(1, 2 * rel_time))) if rel_time < 0.5 else min(255, int(255 * (2 - 2 * rel_time)))
                        elif animation_type == 'zoom':
                            # Zoom effect
                            zoom_factor = 1 + 0.1 * np.sin(rel_time * 2 * np.pi)
                            font = ImageFont.truetype(caption_config['font'], int(caption_config['font_size'] * zoom_factor))
                            # Recalculate text size
                            text_bbox = draw.textbbox((0, 0), text, font=font)
                            text_width = text_bbox[2] - text_bbox[0]
                            text_height = text_bbox[3] - text_bbox[1]
                            if position[0] == 'center':
                                x = (target_width - text_width) // 2
                            if position[1] == 'bottom':
                                y = target_height - text_height - 50
                        
                        # Draw background box
                        bg_bbox = (x-10, y-10, x+text_width+10, y+text_height+10)
                        bg_color = (0, 0, 0, 180)  # Black with transparency
                        draw.rectangle(bg_bbox, fill=bg_color)
                        
                        # Create text color with proper opacity
                        opacity = 255
                        if animation_type == 'fade':
                            opacity = min(255, int(255 * min(1, 2 * rel_time))) if rel_time < 0.5 else min(255, int(255 * (2 - 2 * rel_time)))
                        
                        # Draw stroke (outline)
                        stroke_color = caption_config['stroke_color']
                        if isinstance(stroke_color, tuple) and len(stroke_color) == 3:
                            stroke_color = stroke_color + (opacity,)
                        
                        # Draw text with stroke effect
                        stroke_width = caption_config['stroke_width']
                        for dx, dy in [(0,1), (1,0), (0,-1), (-1,0)]:
                            draw.text((x+dx, y+dy), text, font=font, fill=stroke_color)
                        
                        # Draw main text
                        text_color = caption_config['color']
                        if isinstance(text_color, tuple) and len(text_color) == 3:
                            text_color = text_color + (opacity,)
                        draw.text((x, y), text, font=font, fill=text_color)
                        
                        # Convert overlay to numpy array
                        overlay_array = np.array(overlay)
                        
                        # Convert frame to RGBA
                        frame_rgba = cv2.cvtColor(frame_final, cv2.COLOR_BGR2RGBA)
                        
                        # Alpha blend the overlay onto the frame
                        alpha = overlay_array[:,:,3] / 255.0
                        for c in range(3):
                            frame_rgba[:,:,c] = (1 - alpha) * frame_rgba[:,:,c] + alpha * overlay_array[:,:,c]
                        
                        # Convert back to BGR
                        frame_final = cv2.cvtColor(frame_rgba, cv2.COLOR_RGBA2BGR)
            
            # Write the frame
            out.write(frame_final)
            frame_idx += 1
            
            # Show progress periodically
            if frame_idx % 30 == 0:
                progress = (frame_idx / total_frames) * 100
                logging.info(f"Processing frames: {progress:.1f}% complete")
        
        # Release video capture and writer
        cap.release()
        out.release()
        
        # Add audio/music if specified
        if music_path:
            logging.info(f"Adding background music from {music_path}")
            final_path = self.mix_audio(temp_video, music_path, output_video_path)
        else:
            # Copy temp video to output path
            import shutil
            shutil.copy2(temp_video, output_video_path)
            final_path = output_video_path
        
        # Clean up temp directory
        import shutil
        shutil.rmtree(temp_dir)
        
        logging.info(f"Enhanced video saved at {final_path}")
        return final_path

def edit_video(input_video_path: str,
               output_video_path: str = "edited_video.mp4",
               captions: List[Dict] = None,
               music_path: Optional[str] = None,
               effects: List[str] = None) -> str:
    """
    Convenience function to edit a video without creating a VideoEditor instance.
    """
    editor = VideoEditor()
    return editor.edit_video(
        input_video_path=input_video_path,
        output_video_path=output_video_path,
        captions=captions,
        music_path=music_path,
        effects=effects
    )

if __name__ == "__main__":
    # Example usage with OpenCV and FFmpeg
    example_captions = [
        {
            'text': "Transform your fitness journey",
            'start': 0,
            'duration': 3,
            'style': 'title',
            'animation': 'fade'
        },
        {
            'text': "Track calories effortlessly with AI",
            'start': 3,
            'duration': 3,
            'style': 'body',
            'animation': 'slide'
        }
    ]
    
    editor = VideoEditor()
    edited = editor.edit_video(
        input_video_path="../data/raw_videos/sarah_base.mp4",
        output_video_path="edited_video.mp4",
        captions=example_captions,
        effects=['brighten', 'contrast']
    )
    logging.info(f"Final edited video: {edited}")
