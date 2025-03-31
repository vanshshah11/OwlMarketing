#!/usr/bin/env python3
"""
Test script for UI generation to confirm our improvements.
"""

import os
import sys
import logging
from PIL import Image

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def main():
    """Test UI generation with the improved methods."""
    try:
        logger.info("Starting UI generation test")
        
        # Ensure output directory exists
        os.makedirs("output", exist_ok=True)
        
        # Load the UI generator module
        logger.info("Importing UI generator module")
        from video_generation.ui_generator import UIGenerator
        
        # Initialize the UI generator
        logger.info("Initializing UI generator")
        ui_gen = UIGenerator()
        
        # Generate a home screen
        logger.info("Generating home screen")
        home_screen = ui_gen.generate_ui_screen('home_screen', output_path='output/test_home.png')
        
        # Generate a camera screen
        logger.info("Generating camera screen")
        camera_screen = ui_gen.generate_ui_screen('camera_interface', output_path='output/test_camera.png')
        
        # Generate a results screen with a food item
        logger.info("Generating results screen")
        food_item = {
            'name': 'Pizza',
            'calories': 285,
            'protein': 12,
            'carbs': 36,
            'fat': 10
        }
        results_screen = ui_gen.generate_ui_screen('results_screen', food_item=food_item, output_path='output/test_results.png')
        
        logger.info("UI generation test completed successfully")
        logger.info("Generated images saved to output/test_*.png")
        
    except Exception as e:
        logger.error(f"Error in UI generation test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 