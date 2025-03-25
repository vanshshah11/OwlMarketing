#!/usr/bin/env python3
import os
import sys
import logging
import random
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.master_pipeline import VideoProcessor
from video_editing.hooks_templates import HOOK_TEMPLATES, VALUE_PROP_TEMPLATES, CTA_TEMPLATES

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s'
)

def test_video_processor():
    """Test the video processor module independently."""
    logging.info("Starting video processor test...")
    
    # Create test directories
    test_output_dir = Path("data/test_outputs")
    test_output_dir.mkdir(parents=True, exist_ok=True)
    
    # Find a test video
    test_video_path = None
    for account_dir in Path("data/training_videos").iterdir():
        if account_dir.is_dir() and not account_dir.name.startswith('.'):
            for video_file in account_dir.glob('*.mp4'):
                test_video_path = video_file
                break
        if test_video_path:
            break
    
    if not test_video_path:
        logging.error("No test video found in training_videos directory")
        return
    
    logging.info(f"Using test video: {test_video_path}")
    
    # Initialize processor
    processor = VideoProcessor(
        output_dir=str(test_output_dir),
        font_path="data/fonts/Montserrat-Bold.ttf" if Path("data/fonts/Montserrat-Bold.ttf").exists() else None
    )
    
    # Create test captions
    app_name = "Optimal AI"
    captions = [
        {
            'text': random.choice(HOOK_TEMPLATES).format(app_name=app_name),
            'start': 0,
            'duration': 3,
            'style': 'title',
            'animation': 'fade'
        },
        {
            'text': f"Look at how fast {app_name} tracks everything! It's CRAZY efficient!",
            'start': 3,
            'duration': 4,
            'style': 'body',
            'animation': 'slide'
        },
        {
            'text': random.choice(VALUE_PROP_TEMPLATES).format(app_name=app_name),
            'start': 7,
            'duration': 3,
            'style': 'body',
            'animation': 'slide'
        },
        {
            'text': random.choice(CTA_TEMPLATES).format(app_name=app_name),
            'start': 10,
            'duration': 5,
            'style': 'title',
            'animation': 'zoom'
        }
    ]
    
    # Test video processing with different effects
    try:
        # Test 1: Basic processing
        logging.info("Test 1: Basic video processing...")
        output_path = str(test_output_dir / "test_basic.mp4")
        processor.process_video(
            input_path=str(test_video_path),
            output_path=output_path,
            captions=captions[:2],  # Only first two captions
            effects=None
        )
        logging.info(f"Basic processing saved to: {output_path}")
        
        # Test 2: With effects
        logging.info("Test 2: Video processing with effects...")
        output_path = str(test_output_dir / "test_with_effects.mp4")
        processor.process_video(
            input_path=str(test_video_path),
            output_path=output_path,
            captions=captions,  # All captions
            effects=['brighten', 'contrast']
        )
        logging.info(f"Processing with effects saved to: {output_path}")
        
        # Test 3: Find music if available and test with music
        music_files = list(Path("data").glob("**/*.mp3"))
        if music_files:
            logging.info("Test 3: Video processing with music...")
            output_path = str(test_output_dir / "test_with_music.mp4")
            processor.process_video(
                input_path=str(test_video_path),
                output_path=output_path,
                captions=captions,
                music_path=str(music_files[0]),
                effects=['brighten']
            )
            logging.info(f"Processing with music saved to: {output_path}")
        else:
            logging.warning("No music files found for testing")
    
    except Exception as e:
        logging.error(f"Error in video processing test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_video_processor() 