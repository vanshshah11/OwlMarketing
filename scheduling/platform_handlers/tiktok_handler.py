#!/usr/bin/env python3
"""
TikTok Handler - Module for posting videos to TikTok using Playwright.

This module provides functionality for uploading videos to TikTok
using browser automation with Playwright. It handles login, navigating
to the upload interface, and posting videos with captions and hashtags.
"""

import os
import sys
import time
import json
import logging
import tempfile
import random
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Union
import asyncio
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

try:
    from playwright.sync_api import sync_playwright, TimeoutError, Page, Browser
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    logger.warning("Playwright is not installed. TikTok posting will not be available.")
    PLAYWRIGHT_AVAILABLE = False

# Constants
TIKTOK_URL = "https://www.tiktok.com"
TIKTOK_LOGIN_URL = f"{TIKTOK_URL}/login"
TIKTOK_UPLOAD_URL = f"{TIKTOK_URL}/upload"
TIKTOK_COOKIES_DIR = Path("config/cookies/tiktok")
TIKTOK_COOKIES_DIR.mkdir(parents=True, exist_ok=True)

class TikTokHandler:
    """
    TikTok Handler class for managing video uploads to TikTok.
    
    This class handles:
    - TikTok authentication with session management
    - Video uploads with captions and hashtags
    - Account validation and status checks
    """
    
    def __init__(self, accounts: Dict[str, Any] = None):
        """
        Initialize the TikTok handler.
        
        Args:
            accounts: Dictionary of TikTok accounts
        """
        self.accounts = accounts or {}
        self.cookie_dir = TIKTOK_COOKIES_DIR
        self.browser = None
        self.context = None
        
        # Create cookie directory if it doesn't exist
        self.cookie_dir.mkdir(parents=True, exist_ok=True)
        
        # Validate accounts
        self._validate_accounts()
        
        if not PLAYWRIGHT_AVAILABLE:
            logger.warning("Playwright is not available. TikTok posting will not function.")
    
    def _validate_accounts(self):
        """Validate the account configuration."""
        if not self.accounts:
            logger.warning("No TikTok accounts configured")
            return
        
        valid_accounts = {}
        for username, account in self.accounts.items():
            if not username or not account.get("password"):
                logger.warning(f"Invalid TikTok account config: missing username or password for {username}")
                continue
            
            # Ensure the account has the required fields
            valid_accounts[username] = {
                "username": username,
                "password": account.get("password"),
                "email": account.get("email", ""),
                "phone": account.get("phone", ""),
                "enabled": account.get("enabled", True)
            }
        
        self.accounts = valid_accounts
        logger.info(f"Validated {len(valid_accounts)} TikTok accounts")
    
    def post_video(self, video_path: str, caption: str, hashtags: List[str] = None, account: str = None) -> Tuple[bool, Dict[str, Any]]:
        """
        Post a video to TikTok.
        
        Args:
            video_path: Path to the video file
            caption: Caption for the post
            hashtags: List of hashtags to include
            account: Specific account username to use (optional)
            
        Returns:
            Tuple of (success, result_info)
        """
        if not PLAYWRIGHT_AVAILABLE:
            return False, {"error": "Playwright not available"}
        
        if not os.path.exists(video_path):
            return False, {"error": f"Video file not found: {video_path}"}
        
        # Select an account
        if account and account in self.accounts:
            selected_account = self.accounts[account]
        elif self.accounts:
            # Pick a random enabled account
            enabled_accounts = {k: v for k, v in self.accounts.items() if v.get("enabled", True)}
            if not enabled_accounts:
                return False, {"error": "No enabled TikTok accounts available"}
            
            username = random.choice(list(enabled_accounts.keys()))
            selected_account = enabled_accounts[username]
        else:
            return False, {"error": "No TikTok accounts configured"}
        
        # Add hashtags to caption if provided
        full_caption = caption
        if hashtags:
            hashtag_text = " ".join([f"#{tag}" for tag in hashtags if tag.strip()])
            if hashtag_text:
                full_caption = f"{caption}\n\n{hashtag_text}"
        
        # Post the video
        try:
            success, result = self._post_to_tiktok(
                video_path=video_path,
                caption=full_caption,
                account=selected_account
            )
            
            if success:
                return True, {
                    "platform": "tiktok",
                    "account": selected_account["username"],
                    "post_time": datetime.now().isoformat(),
                    "video_path": video_path,
                    "caption": caption,
                    "hashtags": hashtags or []
                }
            else:
                return False, result
                
        except Exception as e:
            logger.error(f"Error posting to TikTok: {e}")
            return False, {"error": str(e)}
    
    def _post_to_tiktok(self, video_path: str, caption: str, account: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        """
        Internal method to post a video to TikTok.
        
        Args:
            video_path: Path to the video file
            caption: Caption including hashtags
            account: Account dictionary with credentials
            
        Returns:
            Tuple of (success, result_info)
        """
        username = account["username"]
        password = account["password"]
        
        logger.info(f"Posting to TikTok as @{username}")
        
        with sync_playwright() as playwright:
            try:
                # Launch the browser
                browser = playwright.chromium.launch(headless=False)
                
                # Check if we have cookies for this account
                cookie_file = self.cookie_dir / f"{username}.json"
                
                # Create a new browser context
                context = browser.new_context(
                    viewport={"width": 1280, "height": 800},
                    user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36"
                )
                
                # Load cookies if they exist
                if cookie_file.exists():
                    try:
                        cookies = json.loads(cookie_file.read_text())
                        context.add_cookies(cookies)
                        logger.info(f"Loaded cookies for TikTok account @{username}")
                    except Exception as e:
                        logger.warning(f"Failed to load cookies for TikTok account @{username}: {e}")
                
                # Create a new page
                page = context.new_page()
                
                # Check if we're already logged in
                page.goto(TIKTOK_URL)
                time.sleep(3)  # Give time for redirects
                
                # Check login status
                logged_in = True
                if "Log in" in page.content() or "Sign up" in page.content():
                    # Need to log in
                    logger.info(f"Logging into TikTok as @{username}")
                    logged_in = self._login_to_tiktok(page, username, password)
                    
                    if not logged_in:
                        logger.error(f"Failed to log in to TikTok as @{username}")
                        return False, {"error": "Login failed"}
                    
                    # Save cookies for future use
                    cookies = context.cookies()
                    cookie_file.write_text(json.dumps(cookies))
                    logger.info(f"Saved cookies for TikTok account @{username}")
                
                # Now we should be logged in
                # Navigate to the upload page
                page.goto(TIKTOK_UPLOAD_URL)
                time.sleep(3)  # Give some time for the page to load
                
                # Try to upload the video
                try:
                    # Wait for the file input to appear
                    page.wait_for_selector("input[type='file']", timeout=30000)
                    
                    # Upload video file
                    file_input = page.locator("input[type='file']")
                    file_input.set_input_files(video_path)
                    
                    # Wait for the video to be processed
                    logger.info("Waiting for video to be processed...")
                    page.wait_for_selector(".file-upload-container .progress-inner", state="visible", timeout=30000)
                    page.wait_for_selector(".file-upload-container .progress-inner", state="hidden", timeout=180000)
                    
                    # Enter caption
                    caption_area = page.locator("div[data-placeholder='Add a caption']")
                    if caption_area.count() > 0:
                        caption_area.click()
                        caption_area.fill(caption)
                    else:
                        # Try alternate selectors
                        alternate_selectors = [
                            "div.public-DraftEditor-content",
                            "div[contenteditable='true']",
                            "textarea[placeholder='Add a caption']"
                        ]
                        
                        for selector in alternate_selectors:
                            if page.locator(selector).count() > 0:
                                page.locator(selector).click()
                                page.locator(selector).fill(caption)
                                break
                    
                    # Wait for the post button to be enabled
                    page.wait_for_selector("button:has-text('Post'):not([disabled])", timeout=30000)
                    time.sleep(2)  # Give a moment to ensure everything is ready
                    
                    # Click the post button
                    post_button = page.locator("button:has-text('Post'):not([disabled])")
                    post_button.click()
                    
                    # Wait for post to be published
                    logger.info("Waiting for post to be published...")
                    
                    # Look for success message or redirect
                    time.sleep(10)  # Wait for upload to complete
                    
                    # Check for success indicators
                    if "Your video is being uploaded to TikTok!" in page.content() or "Your video is now being uploaded" in page.content():
                        logger.info(f"Successfully posted to TikTok as @{username}")
                        
                        context.close()
                        browser.close()
                        
                        return True, {
                            "platform": "tiktok",
                            "account": username,
                            "post_time": datetime.now().isoformat()
                        }
                    
                    # If we reach here without a clear success, make the best guess
                    context.close()
                    browser.close()
                    
                    logger.warning("Could not confirm successful upload, assuming success")
                    return True, {
                        "platform": "tiktok",
                        "account": username,
                        "post_time": datetime.now().isoformat(),
                        "warning": "Could not confirm upload success"
                    }
                    
                except Exception as e:
                    logger.error(f"Error during TikTok upload process: {e}")
                    
                    try:
                        # Take a screenshot for debugging
                        screenshot_path = f"debug_tiktok_{username}_{int(time.time())}.png"
                        page.screenshot(path=screenshot_path)
                        logger.info(f"Saved debug screenshot to {screenshot_path}")
                    except:
                        pass
                    
                    context.close()
                    browser.close()
                    
                    return False, {"error": f"Upload process failed: {str(e)}"}
                
            except Exception as e:
                logger.error(f"TikTok posting failed: {e}")
                return False, {"error": str(e)}
    
    def _login_to_tiktok(self, page: Page, username: str, password: str) -> bool:
        """
        Log in to TikTok.
        
        Args:
            page: Playwright page object
            username: TikTok username
            password: TikTok password
            
        Returns:
            True if login was successful
        """
        try:
            # Go to TikTok login page
            page.goto(TIKTOK_LOGIN_URL)
            time.sleep(3)  # Wait for page to load
            
            # Click on "Use phone / email / username" option
            login_method_selectors = [
                "button:has-text('Use phone / email / username')",
                "button:has-text('Log in with email or username')",
                "a:has-text('Use phone / email / username')"
            ]
            
            for selector in login_method_selectors:
                if page.locator(selector).count() > 0:
                    page.click(selector)
                    break
            
            time.sleep(2)
            
            # Click on "Log in with email / username" if available
            if page.locator("a:has-text('Log in with email / username')").count() > 0:
                page.click("a:has-text('Log in with email / username')")
                time.sleep(2)
            
            # Enter username
            username_selectors = [
                "input[name='username']",
                "input[placeholder='Email or username']",
                "input[type='text']"
            ]
            
            for selector in username_selectors:
                if page.locator(selector).count() > 0:
                    page.fill(selector, username)
                    break
            
            # Enter password
            page.fill("input[type='password']", password)
            
            # Click login button
            login_button_selectors = [
                "button:has-text('Log in')",
                "button[type='submit']"
            ]
            
            for selector in login_button_selectors:
                if page.locator(selector).count() > 0:
                    page.click(selector)
                    break
            
            # Wait for login to complete
            time.sleep(5)
            
            # Check for login verification
            if page.locator("text=Verify your account").count() > 0 or page.locator("text=Verify").count() > 0:
                logger.warning("Account verification required - manual intervention needed")
                
                # Wait for manual verification (up to 60 seconds)
                for _ in range(60):
                    if "Log in" not in page.content() and "Sign up" not in page.content():
                        break
                    time.sleep(1)
            
            # Check if login was successful
            if "Log in" not in page.content() and "Sign up" not in page.content():
                logger.info(f"Successfully logged in to TikTok as @{username}")
                return True
            
            logger.warning(f"Unable to confirm successful login for TikTok account @{username}")
            return False
            
        except Exception as e:
            logger.error(f"Error during TikTok login: {e}")
            return False
    
    def check_account_status(self, username: str) -> Dict[str, Any]:
        """
        Check the status of a TikTok account.
        
        Args:
            username: TikTok username
            
        Returns:
            Status information dictionary
        """
        if not username in self.accounts:
            return {"status": "unknown", "error": "Account not configured"}
        
        cookie_file = self.cookie_dir / f"{username}.json"
        
        if not cookie_file.exists():
            return {"status": "logged_out", "message": "No saved session"}
        
        # Check if cookies are valid
        try:
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch(headless=True)
                context = browser.new_context()
                
                # Load cookies
                cookies = json.loads(cookie_file.read_text())
                context.add_cookies(cookies)
                
                # Check if we're logged in
                page = context.new_page()
                page.goto(TIKTOK_URL)
                time.sleep(3)
                
                if "Log in" in page.content() or "Sign up" in page.content():
                    # Cookies are invalid
                    context.close()
                    browser.close()
                    return {"status": "logged_out", "message": "Session expired"}
                
                # Get account info if possible
                context.close()
                browser.close()
                return {"status": "logged_in", "message": "Session valid"}
                
        except Exception as e:
            logger.error(f"Error checking TikTok account status: {e}")
            return {"status": "error", "error": str(e)}


# Legacy function for backward compatibility
def post_to_tiktok(video_path: str, caption: str, account: Dict[str, Any]) -> bool:
    """
    Legacy function to post a video to TikTok.
    
    Args:
        video_path: Path to the video file
        caption: Caption for the post
        account: Account dictionary with credentials
        
    Returns:
        True if posting was successful
    """
    handler = TikTokHandler({account["username"]: account})
    success, _ = handler.post_video(video_path, caption, account=account["username"])
    return success


if __name__ == "__main__":
    # Example usage
    import argparse
    
    parser = argparse.ArgumentParser(description="Post a video to TikTok")
    
    parser.add_argument("--video", type=str, required=True,
                       help="Path to the video file")
    
    parser.add_argument("--caption", type=str, required=True,
                       help="Caption for the post")
    
    parser.add_argument("--username", type=str, required=True,
                       help="TikTok username")
    
    parser.add_argument("--password", type=str, required=True,
                       help="TikTok password")
    
    parser.add_argument("--hashtags", type=str, default="",
                       help="Comma-separated list of hashtags")
    
    args = parser.parse_args()
    
    # Parse hashtags
    hashtags = [tag.strip() for tag in args.hashtags.split(",") if tag.strip()]
    
    # Create account config
    account = {
        args.username: {
            "username": args.username,
            "password": args.password
        }
    }
    
    # Create handler and post
    handler = TikTokHandler(account)
    success, result = handler.post_video(
        video_path=args.video,
        caption=args.caption,
        hashtags=hashtags,
        account=args.username
    )
    
    if success:
        print(f"Successfully posted to TikTok as @{args.username}")
    else:
        print(f"Failed to post to TikTok: {result.get('error', 'Unknown error')}") 