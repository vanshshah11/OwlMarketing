#!/usr/bin/env python3
"""
Test script for UI generation.
"""

import os
import sys
import logging

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('test_ui')

def main():
    """Run a test of UI generation."""
    try:
        # Create output directory if it doesn't exist
        os.makedirs('../output', exist_ok=True)
        
        # Import UI generator
        from video_generation.ui_generator import UIGenerator
        ui_gen = UIGenerator()
        
        # Generate test screens
        logger.info("Generating home screen...")
        ui_gen.generate_ui_screen('home_screen', output_path='../output/test_home.png')
        
        logger.info("Generating camera screen...")
        ui_gen.generate_ui_screen('camera_interface', output_path='../output/test_camera.png')
        
        logger.info("Generating results screen...")
        ui_gen.generate_ui_screen('results_screen', 
                                 food_item={
                                     'name': 'Pizza', 
                                     'calories': 285, 
                                     'protein': 12, 
                                     'carbs': 36, 
                                     'fat': 10
                                 }, 
                                 output_path='../output/test_results.png')
        
        logger.info("UI generation test completed successfully!")
    except Exception as e:
        logger.error(f"Error during UI generation test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 