#!/usr/bin/env python3
# Test script for social media posting

import os
import sys
import logging
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from scheduling.post_manager import PostManager

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s - %(name)s: %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("test_social_posting")

def test_schedule_post():
    """Test the schedule_post functionality with various avatars and platforms."""
    
    # Create a PostManager instance
    post_manager = PostManager()
    
    # Load account info
    accounts = post_manager.accounts
    logger.info(f"Loaded {len(accounts)} accounts")
    
    # Test scheduling posts for each avatar and platform
    test_video_path = "data/edited_videos/test_video.mp4"
    
    # Ensure test video exists
    if not os.path.exists(test_video_path):
        os.makedirs(os.path.dirname(test_video_path), exist_ok=True)
        
        # Create a simple test video if it doesn't exist
        logger.info(f"Creating test video at {test_video_path}")
        try:
            import cv2
            import numpy as np
            
            # Create a simple test video
            width, height = 1080, 1920
            fps = 30
            duration = 5  # seconds
            
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            writer = cv2.VideoWriter(test_video_path, fourcc, fps, (width, height))
            
            # Create frames with text
            for i in range(fps * duration):
                frame = np.zeros((height, width, 3), dtype=np.uint8)
                # Add background color
                frame[:, :] = (50, 50, 50)  # Dark gray background
                
                # Add "Test Video" text
                cv2.putText(frame, "OptimalAI Test Video", 
                           (width//2 - 200, height//2), 
                           cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 3)
                
                # Add frame number
                cv2.putText(frame, f"Frame: {i}/{fps * duration}", 
                           (width//2 - 100, height//2 + 100), 
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (200, 200, 200), 2)
                
                writer.write(frame)
            
            writer.release()
            logger.info(f"Created test video successfully")
        except ImportError:
            # If OpenCV is not available, create an empty file
            with open(test_video_path, 'wb') as f:
                f.write(b'Test video placeholder')
            logger.warning(f"Created placeholder video file (OpenCV not available)")
    
    # Test for each account
    for account in accounts:
        avatar = account.get("avatar")
        if not avatar:
            continue
        
        logger.info(f"Testing with avatar: {avatar}")
        
        # Test each platform for this avatar
        for platform in ["tiktok", "instagram", "youtube"]:
            if platform in account.get("platforms", {}):
                logger.info(f"Testing scheduling for {platform}...")
                
                # Generate a test caption
                caption = f"Testing OptimalAI calorie tracking app with avatar {avatar} on {platform}! #OptimalAI #Test"
                
                # Schedule a post
                result = post_manager.schedule_post(
                    video_path=test_video_path,
                    caption=caption,
                    avatar=avatar,
                    platform=platform
                )
                
                if result:
                    logger.info(f"Successfully scheduled {platform} post for {avatar}")
                else:
                    logger.error(f"Failed to schedule {platform} post for {avatar}")

def test_get_account_info():
    """Test the get_account_for_avatar functionality."""
    
    # Create a PostManager instance
    post_manager = PostManager()
    
    # Test each avatar and platform combination
    avatars = ["sarah", "emily", "sophia", "olivia", "emma"]
    platforms = ["tiktok", "instagram", "youtube"]
    
    for avatar in avatars:
        logger.info(f"Testing avatar: {avatar}")
        
        for platform in platforms:
            account_info = post_manager.get_account_for_avatar(avatar, platform)
            
            if account_info:
                logger.info(f"Found account for {avatar} on {platform}: {account_info['username']}")
            else:
                logger.warning(f"No account found for {avatar} on {platform}")

if __name__ == "__main__":
    logger.info("Starting social media posting tests")
    
    # Test get_account_info functionality
    logger.info("\n===== Testing account info retrieval =====")
    test_get_account_info()
    
    # Test schedule_post functionality
    logger.info("\n===== Testing post scheduling =====")
    test_schedule_post()
    
    logger.info("Social media posting tests completed") 