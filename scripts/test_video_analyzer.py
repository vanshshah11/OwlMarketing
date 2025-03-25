#!/usr/bin/env python3
import os
import sys
import logging
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from video_editing.video_analyzer import VideoAnalyzer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s'
)

def test_video_analyzer():
    """Test the video analyzer module independently."""
    logging.info("Starting video analyzer test...")
    
    # Initialize analyzer
    analyzer = VideoAnalyzer(
        training_videos_dir="data/training_videos",
        cache_file="data/test_style_patterns.json"
    )
    
    # Analyze a single video if possible
    single_video_path = None
    for account_dir in Path("data/training_videos").iterdir():
        if account_dir.is_dir() and not account_dir.name.startswith('.'):
            for video_file in account_dir.glob('*.mp4'):
                single_video_path = video_file
                break
        if single_video_path:
            break
    
    if single_video_path:
        logging.info(f"Testing analysis on single video: {single_video_path}")
        try:
            results = analyzer.analyze_video(str(single_video_path))
            logging.info(f"Single video analysis results: {results}")
        except Exception as e:
            logging.error(f"Error analyzing single video: {e}")
    else:
        logging.warning("No test video found in training_videos directory")
    
    # Test full training set analysis
    try:
        logging.info("Testing full training set analysis...")
        patterns = analyzer.analyze_training_set(force_reanalyze=True)
        logging.info(f"Analysis complete. Found patterns: {patterns}")
        
        # Verify cached results
        logging.info("Testing cached analysis results...")
        cached_patterns = analyzer.analyze_training_set(force_reanalyze=False)
        logging.info(f"Cached analysis complete. Found patterns: {cached_patterns}")
        
    except Exception as e:
        logging.error(f"Error in full analysis: {e}")

if __name__ == "__main__":
    test_video_analyzer() 