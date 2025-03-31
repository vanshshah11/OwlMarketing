#!/usr/bin/env python3

import os
import logging
import ffmpeg
from pathlib import Path
import shutil
from typing import List, Optional
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s'
)

class VideoFrameExtractor:
    def __init__(
        self,
        input_dir: str = "data/training_videos",
        output_dir: str = "data/extracted_frames",
        temp_dir: str = "data/temp",
        fps: int = 1,
        categories: dict = None
    ):
        """
        Initialize the frame extractor with directory paths and extraction parameters.
        
        Args:
            input_dir: Directory containing input MP4 files
            output_dir: Directory to save extracted frames
            temp_dir: Directory for temporary files
            fps: Number of frames to extract per second
            categories: Dictionary of content categories and their patterns
        """
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.temp_dir = Path(temp_dir)
        self.fps = fps
        
        # Default content categories if none provided
        self.categories = categories or {
            "talking_head": ["review", "testimonial", "talking"],
            "app_demo": ["demo", "tutorial", "howto"],
            "lifestyle": ["day", "routine", "lifestyle"],
            "transformation": ["progress", "journey", "results"],
            "hook_moments": ["reveal", "surprise", "reaction"]
        }
        
        # Create directories if they don't exist
        for directory in [self.input_dir, self.output_dir, self.temp_dir]:
            directory.mkdir(parents=True, exist_ok=True)
            
        # Create category directories
        for category in self.categories.keys():
            (self.output_dir / category).mkdir(parents=True, exist_ok=True)
    
    def categorize_video(self, video_path: Path) -> str:
        """Determine the category of a video based on its filename and metadata."""
        video_name = video_path.stem.lower()
        
        # Check each category's patterns
        for category, patterns in self.categories.items():
            if any(pattern in video_name for pattern in patterns):
                return category
                
        # Default to "uncategorized" if no patterns match
        return "uncategorized"
    
    def get_video_files(self) -> List[Path]:
        """Get all MP4 files from the input directory and subdirectories."""
        return list(self.input_dir.glob("**/*.mp4"))
    
    def extract_frames(self, video_path: Path, output_prefix: Optional[str] = None) -> None:
        """
        Extract frames from a single video file.
        
        Args:
            video_path: Path to the input video file
            output_prefix: Prefix for output frame filenames
        """
        if output_prefix is None:
            output_prefix = video_path.stem
            
        # Determine the category and create the output path
        category = self.categorize_video(video_path)
        category_dir = self.output_dir / category
        output_pattern = str(category_dir / f"{output_prefix}_%04d.jpg")
        
        try:
            # Get video information
            probe = ffmpeg.probe(str(video_path))
            video_info = next(s for s in probe['streams'] if s['codec_type'] == 'video')
            duration = float(probe['format']['duration'])
            
            # Only process videos between 15-60 seconds
            if not (15 <= duration <= 60):
                logging.info(f"Skipping {video_path.name} - duration {duration}s outside target range")
                return
            
            logging.info(f"Processing video: {video_path.name}")
            logging.info(f"Category: {category}")
            logging.info(f"Duration: {duration}s")
            logging.info(f"Resolution: {video_info['width']}x{video_info['height']}")
            
            # Extract frames using ffmpeg
            stream = ffmpeg.input(str(video_path))
            stream = ffmpeg.filter(stream, 'fps', fps=self.fps)
            stream = ffmpeg.output(stream, output_pattern)
            
            # Run the ffmpeg command
            ffmpeg.run(stream, capture_stdout=True, capture_stderr=True)
            
            logging.info(f"Frames extracted successfully to {category_dir}")
            
        except ffmpeg.Error as e:
            logging.error(f"Error processing {video_path.name}: {e.stderr.decode()}")
        except Exception as e:
            logging.error(f"Unexpected error processing {video_path.name}: {str(e)}")
    
    def process_all_videos(self) -> None:
        """Process all MP4 files in the input directory."""
        videos = self.get_video_files()
        if not videos:
            logging.warning(f"No MP4 files found in {self.input_dir}")
            return
        
        logging.info(f"Found {len(videos)} videos to process")
        for video in videos:
            self.extract_frames(video)
    
    def cleanup(self) -> None:
        """Clean up temporary files."""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
            self.temp_dir.mkdir(parents=True, exist_ok=True)
            logging.info("Temporary files cleaned up")

def main():
    # Define content categories specific to calorie tracking apps
    categories = {
        "app_demos": ["demo", "tutorial", "howto", "track", "app"],
        "testimonials": ["review", "testimonial", "results", "progress"],
        "lifestyle": ["routine", "daily", "meal", "food"],
        "hook_moments": ["reveal", "surprise", "reaction", "transform"],
        "educational": ["tips", "learn", "guide", "explain"]
    }
    
    # Initialize the frame extractor with custom categories
    extractor = VideoFrameExtractor(categories=categories)
    
    try:
        # Process all videos
        extractor.process_all_videos()
    except Exception as e:
        logging.error(f"Error during processing: {str(e)}")
    finally:
        # Clean up temporary files
        extractor.cleanup()

if __name__ == "__main__":
    main() 