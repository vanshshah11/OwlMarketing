#!/usr/bin/env python3
# YouTube video posting handler
import os
import time
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from playwright.sync_api import sync_playwright, Page, Error

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s - %(name)s: %(message)s')
logger = logging.getLogger("youtube_handler")

def post_to_youtube(video_path: str, caption: str, account: Dict) -> bool:
    """
    Post a video to YouTube using the specified account.
    
    Args:
        video_path: Path to the video file to post
        caption: Caption text for the post (used as video title and description)
        account: Dictionary containing account credentials and avatar info
    
    Returns:
        True if posting was successful, False otherwise
    """
    username = account.get("username", "")
    password = account.get("password", "")
    avatar = account.get("avatar", "unknown")
    
    if not username or not password:
        logger.error(f"Missing credentials for YouTube account (avatar: {avatar})")
        return False
    
    if not os.path.exists(video_path):
        logger.error(f"Video file not found: {video_path}")
        return False
    
    # Create title and description from caption
    # Convert username to proper format if it starts with @
    channel_name = username
    if username.startswith("@"):
        channel_name = username[1:]  # Remove @ symbol
    
    # Format video title
    title = f"Optimal AI Calorie Tracker Demo by {channel_name.replace('.', ' ')}"
    if len(caption) < 60:  # If caption is short enough, use it as title
        title = caption
    
    # Format description with hashtags and additional info
    description = caption
    if "#" not in description:
        description += "\n\n#OptimalAI #CalorieTracking #NutritionApp"
    
    # Add call to action
    description += "\n\nDownload Optimal AI today and start tracking your calories effortlessly!"
    
    # Use generic tags
    tags = ["OptimalAI", "Calorie Tracking", "AI App", "Nutrition", "Health", "Fitness"]
    
    logger.info(f"Posting to YouTube for avatar {avatar} with account {username}")
    logger.info(f"Video path: {video_path}")
    logger.info(f"Title: {title}")
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False, slow_mo=50)
            context = browser.new_context(
                viewport={"width": 1280, "height": 920},
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36"
            )
            
            # Set longer timeout for YouTube
            context.set_default_timeout(180000)  # 3 minutes (YouTube uploads can be slow)
            
            page = context.new_page()
            
            # Log in to YouTube/Google
            result = _login_to_youtube(page, username, password)
            if not result:
                browser.close()
                return False
            
            # Navigate to upload page
            logger.info("Navigating to YouTube upload page")
            try:
                page.goto("https://studio.youtube.com", wait_until="domcontentloaded")
                page.wait_for_load_state("networkidle")
                
                # Look for the create button
                logger.info("Looking for create button")
                page.wait_for_selector("button#create-icon, ytcp-button#create-button", timeout=60000)
                page.click("button#create-icon, ytcp-button#create-button")
                
                # Click upload video option
                logger.info("Clicking upload video option")
                page.wait_for_selector("tp-yt-paper-item:has-text('Upload video')", timeout=30000)
                page.click("tp-yt-paper-item:has-text('Upload video')")
                
                # Wait for upload page
                page.wait_for_selector("input[type='file']", timeout=60000)
                
                # Upload the video
                logger.info("Uploading video file")
                page.set_input_files("input[type='file']", video_path)
                
                # Wait for upload to start processing
                logger.info("Waiting for video to start processing")
                page.wait_for_selector("span:has-text('Upload complete'), ytcp-video-upload-progress:has-text('Upload complete')", timeout=300000)
                
                # Fill in details
                logger.info("Filling in video details")
                
                # Enter title
                title_input = page.wait_for_selector("div[id='textbox'][aria-label='Add a title that describes your video']", timeout=60000)
                # Clear existing text
                title_input.click()
                title_input.press("Control+a")
                title_input.press("Backspace")
                # Enter new title
                title_input.fill(title)
                
                # Enter description
                logger.info("Entering description")
                description_input = page.query_selector("div[id='textbox'][aria-label='Tell viewers about your video']")
                description_input.click()
                description_input.press("Control+a")
                description_input.press("Backspace")
                description_input.fill(description)
                
                # Set as "Not made for kids"
                logger.info("Setting audience as 'Not made for kids'")
                page.click("tp-yt-paper-radio-button#audience-toggle-button")
                
                # Click Next
                logger.info("Clicking Next button")
                page.click("div#next-button")
                
                # Navigate through the elements tab
                logger.info("Navigating through elements tab")
                page.wait_for_selector("div#next-button:not([disabled])", timeout=30000)
                page.click("div#next-button")
                
                # Navigate through the checks tab
                logger.info("Navigating through checks tab")
                page.wait_for_selector("div#next-button:not([disabled])", timeout=30000)
                page.click("div#next-button")
                
                # On visibility tab, select Public
                logger.info("Setting video to Public")
                page.wait_for_selector("tp-yt-paper-radio-button[name='PUBLIC']", timeout=30000)
                page.click("tp-yt-paper-radio-button[name='PUBLIC']")
                
                # Verify that the Publish button is clickable
                logger.info("Preparing to publish")
                page.wait_for_selector("div#done-button:not([disabled])", timeout=60000)
                
                # Click Publish
                logger.info("Clicking Publish button")
                page.click("div#done-button")
                
                # Wait for confirmation
                logger.info("Waiting for publish confirmation")
                page.wait_for_selector("ytcp-video-preview[active]", timeout=120000)
                
                logger.info("Video successfully published to YouTube")
                time.sleep(5)  # Wait a moment before closing
                
                browser.close()
                return True
                
            except Error as e:
                logger.error(f"Error during YouTube video upload: {e}")
                browser.close()
                return False
                
    except Exception as e:
        logger.error(f"Error posting to YouTube: {e}")
        return False

def _login_to_youtube(page: Page, username: str, password: str) -> bool:
    """
    Log in to YouTube via Google login using the provided credentials.
    
    Args:
        page: Playwright page object
        username: YouTube/Google username
        password: YouTube/Google password
        
    Returns:
        True if login was successful, False otherwise
    """
    try:
        logger.info(f"Logging in to YouTube as {username}")
        page.goto("https://accounts.google.com/signin/v2/identifier?service=youtube", wait_until="domcontentloaded")
        page.wait_for_load_state("networkidle")
        
        # Enter email/username
        logger.info("Entering email/username")
        page.wait_for_selector("input[type='email']", timeout=30000)
        page.fill("input[type='email']", username)
        
        # Click Next
        logger.info("Clicking Next after email")
        page.click("button:has-text('Next'), #identifierNext")
        
        # Enter password
        logger.info("Entering password")
        page.wait_for_selector("input[type='password']", timeout=30000)
        page.fill("input[type='password']", password)
        
        # Click Next
        logger.info("Clicking Next after password")
        page.click("button:has-text('Next'), #passwordNext")
        
        # Check for 2FA
        try:
            two_factor = page.wait_for_selector("input[aria-label='Enter code'], input[type='tel']", timeout=10000)
            if two_factor:
                logger.warning("Two-factor authentication required. Waiting 60 seconds for manual entry...")
                # Wait for manual 2FA entry
                for _ in range(60):
                    try:
                        # Check if we've reached YouTube
                        if page.url.startswith("https://www.youtube.com/") or page.url.startswith("https://studio.youtube.com/"):
                            break
                    except:
                        pass
                    time.sleep(1)
        except:
            logger.info("No two-factor authentication prompt detected")
        
        # Check if login was successful (wait for YouTube)
        try:
            # Wait to be redirected to YouTube
            page.wait_for_url("https://www.youtube.com/**", timeout=60000)
            logger.info("Login successful - redirected to YouTube")
            return True
        except:
            # Check if we're on YouTube Studio
            if page.url.startswith("https://studio.youtube.com/"):
                logger.info("Login successful - redirected to YouTube Studio")
                return True
            else:
                logger.error(f"Login failed - current URL: {page.url}")
                return False
                
    except Exception as e:
        logger.error(f"Error during YouTube login: {e}")
        return False

if __name__ == "__main__":
    # Test the YouTube posting functionality
    test_account = {
        "username": "test_username@gmail.com",
        "password": "test_password",
        "avatar": "test_avatar"
    }
    test_video = "path/to/test/video.mp4"
    post_to_youtube(test_video, "Testing OptimalAI calorie tracking app! #test", test_account) 