#!/usr/bin/env python3
# /Users/vanshshah/Desktop/OWLmarketing/scripts/run_pipeline.py

import os
import sys
import argparse
import logging
import random
from pathlib import Path
import time

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from video_editing.video_analyzer import VideoAnalyzer
from video_editing.edit_video import VideoEditor
from video_generation.generate_video import generate_video_from_script
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

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Run the complete automated video pipeline")
    parser.add_argument("--analyze", action="store_true", help="Force reanalysis of training videos")
    parser.add_argument("--app-name", default="Optimal AI", help="App name to use in templates")
    parser.add_argument("--avatar", default="sarah", help="Avatar to use for video")
    parser.add_argument("--music", default=None, help="Path to background music file")
    parser.add_argument("--output-dir", default="data/final_videos", help="Output directory for final videos")
    parser.add_argument("--count", type=int, default=1, help="Number of videos to generate")
    return parser.parse_args()

def create_script(app_name, avatar):
    """Create a random script for video generation."""
    return {
        "avatar": avatar,
        "app_name": app_name,
        "hook_template": random.choice(HOOK_TEMPLATES)
    }

def main():
    """Run the complete automated video pipeline."""
    args = parse_args()
    
    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Step 1: Analyze training videos (once, or when forced)
    logging.info("Step 1: Analyzing training videos")
    analyzer = VideoAnalyzer()
    patterns = analyzer.analyze_training_set(force_reanalyze=args.analyze)
    logging.info(f"Analysis complete. Found {len(patterns.get('duration', []))} videos with patterns")
    
    # Initialize video editor with learned patterns
    editor = VideoEditor()
    
    # Generate multiple videos if requested
    for i in range(args.count):
        video_id = int(time.time()) + i
        
        try:
            # Step 2: Generate raw video
            logging.info(f"Step 2: Generating raw video {i+1}/{args.count}")
            script = create_script(args.app_name, args.avatar)
            raw_video = generate_video_from_script(script)
            
            # Step 3: Edit video with style patterns
            logging.info(f"Step 3: Editing video with learned style patterns")
            
            # Create captions from the script
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
            
            # Apply video editing with the learned patterns
            final_video = editor.edit_video(
                input_video_path=raw_video,
                output_video_path=str(output_dir / f"final_video_{video_id}.mp4"),
                captions=captions,
                music_path=args.music,
                effects=['brighten', 'contrast']
            )
            
            logging.info(f"✅ Pipeline complete! Final video saved to: {final_video}")
            
        except Exception as e:
            logging.error(f"❌ Error in pipeline for video {i+1}: {str(e)}")
    
    logging.info("All requested videos completed.")

if __name__ == "__main__":
    main() 