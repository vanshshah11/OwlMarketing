#!/usr/bin/env python3
"""
Instagram Handler - Module for posting videos to Instagram using Playwright.

This module provides functionality for uploading videos to Instagram
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
    logger.warning("Playwright is not installed. Instagram posting will not be available.")
    PLAYWRIGHT_AVAILABLE = False

# Constants
INSTAGRAM_URL = "https://www.instagram.com"
INSTAGRAM_LOGIN_URL = f"{INSTAGRAM_URL}/accounts/login/"
INSTAGRAM_COOKIES_DIR = Path("config/cookies/instagram")
INSTAGRAM_COOKIES_DIR.mkdir(parents=True, exist_ok=True)

class InstagramHandler:
    """
    Instagram Handler class for managing video uploads to Instagram.
    
    This class handles:
    - Instagram authentication with session management
    - Video uploads with captions and hashtags
    - Account validation and status checks
    """
    
    def __init__(self, accounts: Dict[str, Any] = None):
        """
        Initialize the Instagram handler.
        
        Args:
            accounts: Dictionary of Instagram accounts
        """
        self.accounts = accounts or {}
        self.cookie_dir = INSTAGRAM_COOKIES_DIR
        self.browser = None
        self.context = None
        
        # Create cookie directory if it doesn't exist
        self.cookie_dir.mkdir(parents=True, exist_ok=True)
        
        # Validate accounts
        self._validate_accounts()
        
        if not PLAYWRIGHT_AVAILABLE:
            logger.warning("Playwright is not available. Instagram posting will not function.")
    
    def _validate_accounts(self):
        """Validate the account configuration."""
        if not self.accounts:
            logger.warning("No Instagram accounts configured")
            return
        
        valid_accounts = {}
        for username, account in self.accounts.items():
            if not username or not account.get("password"):
                logger.warning(f"Invalid Instagram account config: missing username or password for {username}")
                continue
            
            # Ensure the account has the required fields
            valid_accounts[username] = {
                "username": username,
                "password": account.get("password"),
                "two_factor_auth": account.get("two_factor_auth", False),
                "email": account.get("email", ""),
                "phone": account.get("phone", ""),
                "enabled": account.get("enabled", True)
            }
        
        self.accounts = valid_accounts
        logger.info(f"Validated {len(valid_accounts)} Instagram accounts")
    
    def post_video(self, video_path: str, caption: str, hashtags: List[str] = None, account: str = None) -> Tuple[bool, Dict[str, Any]]:
        """
        Post a video to Instagram.
        
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
                return False, {"error": "No enabled Instagram accounts available"}
            
            username = random.choice(list(enabled_accounts.keys()))
            selected_account = enabled_accounts[username]
        else:
            return False, {"error": "No Instagram accounts configured"}
        
        # Add hashtags to caption if provided
        full_caption = caption
        if hashtags:
            hashtag_text = " ".join([f"#{tag}" for tag in hashtags if tag.strip()])
            if hashtag_text:
                full_caption = f"{caption}\n\n{hashtag_text}"
        
        # Post the video
        try:
            success, result = self._post_to_instagram(
                video_path=video_path,
                caption=full_caption,
                account=selected_account
            )
            
            if success:
                return True, {
                    "platform": "instagram",
                    "account": selected_account["username"],
                    "post_time": datetime.now().isoformat(),
                    "video_path": video_path,
                    "caption": caption,
                    "hashtags": hashtags or []
                }
            else:
                return False, result
                
        except Exception as e:
            logger.error(f"Error posting to Instagram: {e}")
            return False, {"error": str(e)}
    
    def _post_to_instagram(self, video_path: str, caption: str, account: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        """
        Internal method to post a video to Instagram.
        
        Args:
            video_path: Path to the video file
            caption: Caption including hashtags
            account: Account dictionary with credentials
            
        Returns:
            Tuple of (success, result_info)
        """
        username = account["username"]
        password = account["password"]
        
        logger.info(f"Posting to Instagram as @{username}")
        
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
                        logger.info(f"Loaded cookies for Instagram account @{username}")
                    except Exception as e:
                        logger.warning(f"Failed to load cookies for Instagram account @{username}: {e}")
                
                # Create a new page
                page = context.new_page()
                
                # Check if we're already logged in
                page.goto(INSTAGRAM_URL)
                time.sleep(3)  # Give time for redirects
                
                if "Login" in page.title() or "Log In" in page.content():
                    # Need to log in
                    logger.info(f"Logging into Instagram as @{username}")
                    logged_in = self._login_to_instagram(page, username, password, account.get("two_factor_auth", False))
                    
                    if not logged_in:
                        logger.error(f"Failed to log in to Instagram as @{username}")
                        return False, {"error": "Login failed"}
                    
                    # Save cookies for future use
                    cookies = context.cookies()
                    cookie_file.write_text(json.dumps(cookies))
                    logger.info(f"Saved cookies for Instagram account @{username}")
                
                # Now we should be logged in
                # Navigate to the upload page
                time.sleep(3)  # Give some time for the page to load
                
                # Click on the "Create" button (may vary depending on Instagram UI)
                try:
                    # Try different selectors for the create button
                    create_selectors = [
                        "svg[aria-label='New post']",
                        "svg[aria-label='Create']",
                        "[aria-label='New post']",
                        "[aria-label='Create']"
                    ]
                    
                    for selector in create_selectors:
                        if page.locator(selector).count() > 0:
                            page.click(selector)
                            break
                    
                    # Wait for the file input to appear
                    time.sleep(2)
                    
                    # Upload the video file
                    file_input = page.locator("input[type='file']")
                    file_input.set_input_files(video_path)
                    
                    # Wait for upload to complete and next button to appear
                    page.wait_for_selector("button:has-text('Next')")
                    time.sleep(2)
                    page.click("button:has-text('Next')")
                    
                    # Wait for filters page and click next
                    time.sleep(2)
                    page.click("button:has-text('Next')")
                    
                    # Set the caption
                    time.sleep(2)
                    caption_textarea = page.locator("textarea[aria-label='Write a caption...']")
                    caption_textarea.fill(caption)
                    
                    # Click share button
                    time.sleep(2)
                    page.click("button:has-text('Share')")
                    
                    # Wait for success
                    time.sleep(10)
                    
                    logger.info(f"Successfully posted to Instagram as @{username}")
                    
                    context.close()
                    browser.close()
                    
                    return True, {
                        "platform": "instagram",
                        "account": username,
                        "post_time": datetime.now().isoformat()
                    }
                    
                except Exception as e:
                    logger.error(f"Error during Instagram upload process: {e}")
                    
                    try:
                        # Take a screenshot for debugging
                        screenshot_path = f"debug_instagram_{username}_{int(time.time())}.png"
                        page.screenshot(path=screenshot_path)
                        logger.info(f"Saved debug screenshot to {screenshot_path}")
                    except:
                        pass
                    
                    context.close()
                    browser.close()
                    
                    return False, {"error": f"Upload process failed: {str(e)}"}
                
            except Exception as e:
                logger.error(f"Instagram posting failed: {e}")
                return False, {"error": str(e)}
    
    def _login_to_instagram(self, page: Page, username: str, password: str, two_factor: bool = False) -> bool:
        """
        Log in to Instagram.
        
        Args:
            page: Playwright page object
            username: Instagram username
            password: Instagram password
            two_factor: Whether to expect 2FA
            
        Returns:
            True if login was successful
        """
        try:
            # Go to Instagram login page
            page.goto(INSTAGRAM_LOGIN_URL)
            time.sleep(3)  # Wait for page to load
            
            # Fill username and password
            page.fill("input[name='username']", username)
            page.fill("input[name='password']", password)
            
            # Click login button
            page.click("button[type='submit']")
            
            # Wait for login to complete
            time.sleep(5)
            
            # Check if 2FA is required
            if two_factor and "two-factor" in page.url:
                logger.info("Two-factor authentication required")
                
                # Prompt for 2FA code
                two_factor_code = input(f"Enter 2FA code for Instagram account @{username}: ")
                
                # Enter the code
                page.fill("input[name='verificationCode']", two_factor_code)
                page.click("button[type='submit']")
                
                # Wait for 2FA to complete
                time.sleep(5)
            
            # Check if login was successful by looking for feed
            if "feed" in page.url or "dashboard" in page.url:
                logger.info(f"Successfully logged in to Instagram as @{username}")
                return True
            
            # Check for "Save Your Login Info" dialog
            if page.locator("button:has-text('Save Info')").count() > 0:
                page.click("button:has-text('Save Info')")
                time.sleep(2)
                return True
                
            if page.locator("button:has-text('Not Now')").count() > 0:
                page.click("button:has-text('Not Now')")
                time.sleep(2)
                return True
            
            logger.warning(f"Unable to confirm successful login for Instagram account @{username}")
            return "feed" in page.content() or "profile" in page.content()
            
        except Exception as e:
            logger.error(f"Error during Instagram login: {e}")
            return False
    
    def check_account_status(self, username: str) -> Dict[str, Any]:
        """
        Check the status of an Instagram account.
        
        Args:
            username: Instagram username
            
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
                page.goto(INSTAGRAM_URL)
                time.sleep(3)
                
                if "Login" in page.title() or "Log In" in page.content():
                    # Cookies are invalid
                    context.close()
                    browser.close()
                    return {"status": "logged_out", "message": "Session expired"}
                
                # Get account info if possible
                context.close()
                browser.close()
                return {"status": "logged_in", "message": "Session valid"}
                
        except Exception as e:
            logger.error(f"Error checking Instagram account status: {e}")
            return {"status": "error", "error": str(e)}


# Legacy function for backward compatibility
def post_to_instagram(video_path: str, caption: str, account: Dict[str, Any]) -> bool:
    """
    Legacy function to post a video to Instagram.
    
    Args:
        video_path: Path to the video file
        caption: Caption for the post
        account: Account dictionary with credentials
        
    Returns:
        True if posting was successful
    """
    handler = InstagramHandler({account["username"]: account})
    success, _ = handler.post_video(video_path, caption, account=account["username"])
    return success


if __name__ == "__main__":
    # Example usage
    import argparse
    
    parser = argparse.ArgumentParser(description="Post a video to Instagram")
    
    parser.add_argument("--video", type=str, required=True,
                       help="Path to the video file")
    
    parser.add_argument("--caption", type=str, required=True,
                       help="Caption for the post")
    
    parser.add_argument("--username", type=str, required=True,
                       help="Instagram username")
    
    parser.add_argument("--password", type=str, required=True,
                       help="Instagram password")
    
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
    handler = InstagramHandler(account)
    success, result = handler.post_video(
        video_path=args.video,
        caption=args.caption,
        hashtags=hashtags,
        account=args.username
    )
    
    if success:
        print(f"Successfully posted to Instagram as @{args.username}")
    else:
        print(f"Failed to post to Instagram: {result.get('error', 'Unknown error')}") 