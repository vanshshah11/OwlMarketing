#!/usr/bin/env python3
import logging
from playwright.sync_api import sync_playwright

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s: %(message)s')

def post_video(video_path, caption, account):
    logging.info("Starting video post for account: %s", account['username'])
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        
        # Navigate to TikTok login (example URL; adjust as necessary)
        logging.info("Navigating to TikTok login page.")
        page.goto("https://www.tiktok.com/login")
        page.wait_for_timeout(10000)  # Wait for manual login
        
        # Navigate to video upload page
        logging.info("Navigating to TikTok upload page.")
        page.goto("https://www.tiktok.com/upload")
        
        # Upload video file
        logging.info("Uploading video from %s", video_path)
        page.set_input_files("input[type='file']", video_path)
        
        # Fill in caption details
        logging.info("Entering caption: %s", caption)
        page.fill("textarea[name='caption']", caption)
        
        # Submit the post
        logging.info("Submitting the video post.")
        page.click("button[type='submit']")
        page.wait_for_timeout(5000)  # Wait for post completion
        
        logging.info("Video posted successfully for account: %s", account['username'])
        browser.close()

if __name__ == "__main__":
    test_account = {"username": "test_user", "password": "test_pass"}
    post_video("edited_video.mp4", "Test caption", test_account)
