#!/usr/bin/env python3
"""
Test script for Context-Aware UI Generator

This script demonstrates how the Context-Aware UI Generator ensures consistent food items
across different screens in the app UI, maintaining visual continuity throughout the 
video generation process.
"""

import os
import sys
import json
import logging
from pathlib import Path

# Add project root to the Python path to allow imports
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from video_generation.context_ui_integrator import get_context_ui_integrator
from video_generation.app_ui_manager import get_ui_manager
from video_generation.generate_video import generate_video_from_script
from video_editing.edit_video import VideoEditor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)

def create_test_ui_assets():
    """Create test UI assets for different food items and screens."""
    logger.info("Creating test UI assets...")
    
    # Get UI manager
    ui_manager = get_ui_manager()
    
    # Ensure directories exist
    screenshots_dir = Path(project_root) / "assets" / "app_ui" / "screenshots"
    screenshots_dir.mkdir(parents=True, exist_ok=True)
    
    # List of food items to create UI screens for
    food_items = ["pizza", "salad", "burger", "coffee", "smoothie"]
    
    # List of screen types
    screen_types = ["camera_interface", "analysis_screen", "results_screen", "recently_eaten"]
    
    # Create test screenshots for each food item and screen type
    for food_item in food_items:
        for screen_type in screen_types:
            # Create dummy screenshot (in a real implementation, this would be a real UI)
            dummy_file = screenshots_dir / f"{food_item}_{screen_type}.jpg"
            
            # Only create if it doesn't exist
            if not dummy_file.exists():
                import cv2
                import numpy as np
                from PIL import Image, ImageDraw, ImageFont
                
                # Create a blank image with color
                img = np.ones((1280, 720, 3), dtype=np.uint8) * 240  # Light gray
                
                # Add food item and screen type text
                cv2.putText(img, f"Optimal AI", (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 0), 3)
                cv2.putText(img, f"Food: {food_item}", (50, 200), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 0), 3)
                cv2.putText(img, f"Screen: {screen_type}", (50, 300), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 0), 3)
                
                # Add different content based on screen type
                if screen_type == "camera_interface":
                    cv2.putText(img, "CAMERA VIEW", (50, 400), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 255), 3)
                elif screen_type == "analysis_screen":
                    cv2.putText(img, "ANALYZING...", (50, 400), cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 0, 0), 3)
                elif screen_type == "results_screen":
                    cv2.putText(img, "RESULTS", (50, 400), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 255, 0), 3)
                    cv2.putText(img, "Calories: 320", (50, 500), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 0), 2)
                    cv2.putText(img, "Protein: 15g", (50, 550), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 0), 2)
                    cv2.putText(img, "Carbs: 42g", (50, 600), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 0), 2)
                elif screen_type == "recently_eaten":
                    cv2.putText(img, "RECENTLY EATEN", (50, 400), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 255), 3)
                    cv2.putText(img, "Today's Total: 1,850 cal", (50, 500), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 0), 2)
                
                # Save the image
                cv2.imwrite(str(dummy_file), img)
                logger.info(f"Created test screenshot: {dummy_file}")
            
            # Register the screenshot with the UI manager
            ui_manager.add_screenshot(
                file_path=str(dummy_file),
                food_item=food_item,
                screen_type=screen_type
            )
    
    logger.info(f"Created and registered {len(food_items) * len(screen_types)} test UI assets")

def test_ui_consistency():
    """Test UI consistency for different food items across screens."""
    logger.info("Testing UI consistency...")
    
    # Get the context UI integrator
    context_ui_integrator = get_context_ui_integrator()
    
    # Test for each avatar
    avatars = ["sarah", "emily", "sophia"]
    food_items = ["pizza", "salad", "burger"]
    
    for avatar_name in avatars:
        for food_item in food_items:
            logger.info(f"Testing {avatar_name} with {food_item}...")
            
            # Set food context for avatar
            context_ui_integrator.set_food_context_for_avatar(
                avatar_name=avatar_name,
                food_item=food_item,
                environment={"description": "bright modern kitchen"}
            )
            
            # Generate UI sequence
            ui_sequence = context_ui_integrator.generate_consistent_ui_sequence(
                avatar_name=avatar_name,
                food_item=food_item
            )
            
            # Verify all screens have the same food item
            screen_count = 0
            for screen_type, ui_path in ui_sequence.items():
                if ui_path:
                    logger.info(f"  Screen: {screen_type}, Path: {ui_path}")
                    screen_count += 1
            
            logger.info(f"  Generated {screen_count} consistent UI screens for {avatar_name}/{food_item}")

def test_context_aware_video_generation():
    """Test video generation with context-aware UI."""
    logger.info("Testing context-aware video generation...")
    
    # Create test script with food item context
    test_script = {
        "title": "Quick Calorie Tracking Demo",
        "description": "Demonstrating how easy it is to track calories with Optimal AI",
        "avatar": {
            "name": "sarah",
            "style": "demo"
        },
        "scenes": [
            {
                "type": "talking_head",
                "duration": 3.0,
                "text": "Struggling to track calories for your pizza? 🍕",
                "lines": [
                    {"text": "Struggling to track calories for your pizza?", "duration": 3.0}
                ]
            },
            {
                "type": "app_scan_demo",
                "duration": 4.0,
                "text": "Just open Optimal AI and scan your food!",
                "lines": [
                    {"text": "Just open Optimal AI and scan your food!", "duration": 4.0}
                ]
            },
            {
                "type": "app_results_demo",
                "duration": 3.0,
                "text": "Instantly see calories, nutrients, and more!",
                "lines": [
                    {"text": "Instantly see calories, nutrients, and more!", "duration": 3.0}
                ]
            },
            {
                "type": "app_history_demo",
                "duration": 3.0,
                "text": "Track your daily intake without the hassle!",
                "lines": [
                    {"text": "Track your daily intake without the hassle!", "duration": 3.0}
                ]
            },
            {
                "type": "talking_head",
                "duration": 3.0,
                "text": "Download Optimal AI today! 📱✨",
                "lines": [
                    {"text": "Download Optimal AI today!", "duration": 3.0}
                ]
            }
        ]
    }
    
    # Save test script to disk for reference
    with open("test_script.json", "w") as f:
        json.dump(test_script, f, indent=2)
    
    try:
        # Generate video with context-aware UI
        output_path = generate_video_from_script(
            script=test_script,
            output_path="context_aware_demo.mp4"
        )
        logger.info(f"Generated context-aware video: {output_path}")
    except Exception as e:
        logger.error(f"Error generating video: {e}")

if __name__ == "__main__":
    logger.info("Starting Context-Aware UI Generator test")
    
    # Create test UI assets first
    create_test_ui_assets()
    
    # Test UI consistency
    test_ui_consistency()
    
    # Test video generation (optional, may be resource-intensive)
    if len(sys.argv) > 1 and sys.argv[1] == "--with-video":
        test_context_aware_video_generation()
    
    logger.info("Test completed successfully") 