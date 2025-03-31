#!/usr/bin/env python3
# /Users/vanshshah/Desktop/OWLmarketing/scheduling/post_manager.py

import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
import time
import random

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import platform handlers
try:
    from scheduling.platform_handlers.tiktok_handler import TikTokHandler, post_to_tiktok
    from scheduling.platform_handlers.instagram_handler import InstagramHandler, post_to_instagram
except ImportError:
    # Fallback to just the function versions if class versions aren't available
    from scheduling.platform_handlers.tiktok_handler import post_to_tiktok
    from scheduling.platform_handlers.instagram_handler import post_to_instagram

# For backward compatibility
try:
    from scheduling.platform_handlers.youtube_handler import post_to_youtube
except ImportError:
    def post_to_youtube(*args, **kwargs):
        logging.warning("YouTube handler not available")
        return False

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

class PostManager:
    """
    Post manager class for scheduling and posting videos to multiple social media platforms.
    Handles:
    - Posting to TikTok, Instagram, and YouTube
    - Scheduling posts based on avatar-specific accounts
    - Managing multiple accounts per platform
    - Tracking post status and history
    """
    
    def __init__(self, accounts_file: str = None):
        """
        Initialize the post manager.
        
        Args:
            accounts_file: Path to the accounts configuration file
        """
        # Set up directories
        self.output_dir = Path("data/scheduled_posts")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.history_dir = Path("data/post_history")
        self.history_dir.mkdir(parents=True, exist_ok=True)
        
        # Load account configurations
        if accounts_file is None:
            accounts_file = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) / "config" / "accounts.json"
        
        self.accounts = self._load_accounts(accounts_file)
        
        # Initialize platform handlers
        self.platform_handlers = {}
        self._initialize_platform_handlers()
        
        logger.info(f"PostManager initialized with {len(self.accounts)} account configurations")
    
    def _load_accounts(self, accounts_file: str) -> Dict[str, Any]:
        """
        Load account configurations from a JSON file.
        
        Args:
            accounts_file: Path to the accounts configuration file
            
        Returns:
            Dictionary of account configurations
        """
        accounts = {}
        
        try:
            if os.path.exists(accounts_file):
                with open(accounts_file, 'r') as f:
                    accounts = json.load(f)
                logger.info(f"Loaded accounts from {accounts_file}")
            else:
                logger.warning(f"Accounts file not found: {accounts_file}")
        except Exception as e:
            logger.error(f"Error loading accounts: {e}")
        
        return accounts
    
    def _initialize_platform_handlers(self):
        """Initialize handlers for each supported platform."""
        
        # TikTok handler
        try:
            if 'TikTokHandler' in globals():
                self.platform_handlers["tiktok"] = TikTokHandler(
                    accounts=self.accounts.get("tiktok", {})
                )
                logger.info("TikTok handler initialized")
        except Exception as e:
            logger.warning(f"Could not initialize TikTok handler: {e}")
        
        # Instagram handler
        try:
            if 'InstagramHandler' in globals():
                self.platform_handlers["instagram"] = InstagramHandler(
                    accounts=self.accounts.get("instagram", {})
                )
                logger.info("Instagram handler initialized")
        except Exception as e:
            logger.warning(f"Could not initialize Instagram handler: {e}")
    
    def get_account_for_avatar(self, avatar: str, platform: str) -> Dict[str, Any]:
        """
        Get account information for a specific avatar and platform.
        
        Args:
            avatar: Avatar name
            platform: Platform name
            
        Returns:
            Account information dictionary
        """
        try:
            # Check if we have avatar-specific accounts
            if avatar in self.accounts.get("avatars", {}):
                avatar_accounts = self.accounts["avatars"][avatar].get(platform, [])
                if avatar_accounts:
                    # Pick a random account if multiple are available
                    return random.choice(avatar_accounts)
            
            # Fall back to general platform accounts
            platform_accounts = self.accounts.get(platform, [])
            if platform_accounts:
                return random.choice(platform_accounts)
            
            logger.warning(f"No account found for avatar {avatar} on {platform}")
            return {}
            
        except Exception as e:
            logger.error(f"Error getting account for avatar {avatar} on {platform}: {e}")
            return {}
    
    def schedule_post(self, 
                    video_path: str, 
                    caption: str, 
                    avatar: str,
                    platform: str = "tiktok",
                    hashtags: List[str] = None,
                    scheduled_time: Optional[datetime] = None) -> Dict[str, Any]:
        """
        Schedule a post for later.
        
        Args:
            video_path: Path to the video file
            caption: Caption for the post
            avatar: Avatar name
            platform: Platform to post to
            hashtags: List of hashtags to include
            scheduled_time: Time to post (default: 1 hour from now)
            
        Returns:
            Dictionary with scheduling information
        """
        try:
            if not os.path.exists(video_path):
                logger.error(f"Video file not found: {video_path}")
                return {"success": False, "error": "Video file not found"}
            
            # Get account for this avatar and platform
            account = self.get_account_for_avatar(avatar, platform)
            if not account:
                logger.error(f"No account found for avatar {avatar} on {platform}")
                return {"success": False, "error": "No account found"}
            
            # Set default scheduled time if not provided
            if scheduled_time is None:
                scheduled_time = datetime.now() + timedelta(hours=1)
            
            # Create scheduled post entry
            scheduled_post = {
                "id": f"post_{int(time.time())}_{random.randint(1000, 9999)}",
                "video_path": video_path,
                "caption": caption,
                "hashtags": hashtags or [],
                "avatar": avatar,
                "platform": platform,
                "account": account.get("username"),
                "scheduled_time": scheduled_time.isoformat(),
                "status": "scheduled",
                "created_at": datetime.now().isoformat()
            }
            
            # Save scheduled post to file
            post_file = self.output_dir / f"{scheduled_post['id']}.json"
            with open(post_file, 'w') as f:
                json.dump(scheduled_post, f, indent=2)
            
            logger.info(f"Scheduled post {scheduled_post['id']} for {scheduled_time.isoformat()}")
            return {
                "success": True, 
                "id": scheduled_post['id'],
                "scheduled_time": scheduled_time.isoformat(),
                "platform": platform,
                "account": account.get("username")
            }
            
        except Exception as e:
            logger.error(f"Error scheduling post: {e}")
            return {"success": False, "error": str(e)}
    
    def post_now(self, 
                video_path: str, 
                caption: str, 
                avatar: str = None,
                platform: str = "tiktok",
                hashtags: List[str] = None,
                account_username: str = None) -> Tuple[bool, Dict[str, Any]]:
        """
        Post a video immediately.
        
        Args:
            video_path: Path to the video file
            caption: Caption for the post
            avatar: Avatar name (optional)
            platform: Platform to post to
            hashtags: List of hashtags to include
            account_username: Specific account username to use (optional)
            
        Returns:
            Tuple containing (success, result_dict)
        """
        try:
            if not os.path.exists(video_path):
                logger.error(f"Video file not found: {video_path}")
                return False, {"error": "Video file not found"}
            
            # Use platform handler if available
            if platform in self.platform_handlers:
                handler = self.platform_handlers[platform]
                return handler.post_video(
                    video_path=video_path,
                    caption=caption,
                    hashtags=hashtags,
                    account=account_username
                )
            
            # Fall back to legacy posting functions
            # Get account for this avatar and platform
            if account_username:
                # Try to find the specific account
                account = None
                platform_accounts = self.accounts.get(platform, [])
                for acct in platform_accounts:
                    if acct.get("username") == account_username:
                        account = acct
                        break
                
                if not account and avatar:
                    # Check avatar-specific accounts
                    avatar_accounts = self.accounts.get("avatars", {}).get(avatar, {}).get(platform, [])
                    for acct in avatar_accounts:
                        if acct.get("username") == account_username:
                            account = acct
                            break
            else:
                # Get account based on avatar
                account = self.get_account_for_avatar(avatar, platform)
            
            if not account:
                logger.error(f"No account found for posting on {platform}")
                return False, {"error": "No account found"}
            
            # Add avatar to account info for tracking
            account["avatar"] = avatar
            
            # Post using legacy functions
            success = False
            if platform == "tiktok":
                success = post_to_tiktok(video_path, caption, account)
            elif platform == "instagram":
                success = post_to_instagram(video_path, caption, account)
            elif platform == "youtube":
                success = post_to_youtube(video_path, caption, account)
            else:
                logger.error(f"Unsupported platform: {platform}")
                return False, {"error": f"Unsupported platform: {platform}"}
            
            # Record the post in history
            if success:
                self._record_post(video_path, caption, avatar, platform, account.get("username"))
                return True, {
                    "platform": platform,
                    "account": account.get("username"),
                    "post_time": time.time(),
                    "caption": caption
                }
            else:
                return False, {"error": f"Failed to post to {platform}"}
                
        except Exception as e:
            logger.error(f"Error posting video: {e}")
            return False, {"error": str(e)}
    
    def _record_post(self, video_path, caption, avatar, platform, account_username):
        """
        Record a successful post in the history.
        
        Args:
            video_path: Path to the video file
            caption: Caption for the post
            avatar: Avatar name
            platform: Platform name
            account_username: Account username used
        """
        try:
            post_record = {
                "id": f"post_{int(time.time())}_{random.randint(1000, 9999)}",
                "video_path": video_path,
                "caption": caption,
                "avatar": avatar,
                "platform": platform,
                "account": account_username,
                "posted_time": datetime.now().isoformat(),
                "status": "posted"
            }
            
            # Save post record to file
            record_file = self.history_dir / f"{post_record['id']}.json"
            with open(record_file, 'w') as f:
                json.dump(post_record, f, indent=2)
            
            logger.info(f"Recorded post {post_record['id']} to {platform}")
            
        except Exception as e:
            logger.error(f"Error recording post: {e}")
    
    def check_scheduled_posts(self) -> int:
        """
        Check for scheduled posts that are due and post them.
        
        Returns:
            Number of posts processed
        """
        now = datetime.now()
        posts_processed = 0
        
        try:
            # Get all scheduled post files
            scheduled_files = list(self.output_dir.glob("*.json"))
            
            for post_file in scheduled_files:
                try:
                    with open(post_file, 'r') as f:
                        scheduled_post = json.load(f)
                    
                    # Skip posts that are not in scheduled status
                    if scheduled_post.get("status") != "scheduled":
                        continue
                    
                    # Check if post is due
                    scheduled_time = datetime.fromisoformat(scheduled_post["scheduled_time"])
                    
                    if scheduled_time <= now:
                        logger.info(f"Processing scheduled post {scheduled_post['id']}")
                        
                        # Post now
                        success, result = self.post_now(
                            video_path=scheduled_post["video_path"],
                            caption=scheduled_post["caption"],
                            avatar=scheduled_post["avatar"],
                            platform=scheduled_post["platform"],
                            hashtags=scheduled_post.get("hashtags"),
                            account_username=scheduled_post.get("account")
                        )
                        
                        # Update post status
                        if success:
                            scheduled_post["status"] = "posted"
                            scheduled_post["posted_time"] = datetime.now().isoformat()
                            scheduled_post["post_result"] = result
                        else:
                            scheduled_post["status"] = "failed"
                            scheduled_post["failure_time"] = datetime.now().isoformat()
                            scheduled_post["error"] = result.get("error", "Unknown error")
                        
                        # Save updated post
                        with open(post_file, 'w') as f:
                            json.dump(scheduled_post, f, indent=2)
                        
                        posts_processed += 1
                        
                except Exception as e:
                    logger.error(f"Error processing scheduled post {post_file}: {e}")
            
            return posts_processed
            
        except Exception as e:
            logger.error(f"Error checking scheduled posts: {e}")
            return posts_processed
    
    def get_post_history(self, days: int = 7, platform: str = None, avatar: str = None) -> List[Dict[str, Any]]:
        """
        Get post history for the specified time period.
        
        Args:
            days: Number of days to look back
            platform: Filter by platform
            avatar: Filter by avatar
            
        Returns:
            List of post records
        """
        cutoff = datetime.now() - timedelta(days=days)
        history = []
        
        try:
            # Get all history files
            history_files = list(self.history_dir.glob("*.json"))
            
            for history_file in history_files:
                try:
                    with open(history_file, 'r') as f:
                        post_record = json.load(f)
                    
                    # Filter by time
                    posted_time = datetime.fromisoformat(post_record.get("posted_time", "2000-01-01T00:00:00"))
                    if posted_time < cutoff:
                        continue
                    
                    # Filter by platform
                    if platform and post_record.get("platform") != platform:
                        continue
                    
                    # Filter by avatar
                    if avatar and post_record.get("avatar") != avatar:
                        continue
                    
                    history.append(post_record)
                    
                except Exception as e:
                    logger.error(f"Error reading history file {history_file}: {e}")
            
            # Sort by posted time (newest first)
            history.sort(key=lambda x: x.get("posted_time", ""), reverse=True)
            
            return history
            
        except Exception as e:
            logger.error(f"Error getting post history: {e}")
            return []


if __name__ == "__main__":
    # Example usage
    import argparse
    
    parser = argparse.ArgumentParser(description="Post videos to social media")
    
    parser.add_argument("--video", type=str, required=True,
                       help="Path to the video file to post")
    
    parser.add_argument("--caption", type=str, default="Check out OptimalAI - the smart calorie tracking app!",
                       help="Caption for the post")
    
    parser.add_argument("--platform", type=str, default="tiktok",
                       choices=["tiktok", "instagram", "youtube"],
                       help="Platform to post to")
    
    parser.add_argument("--avatar", type=str, default="emily",
                       help="Avatar to use")
    
    parser.add_argument("--schedule", type=str, default=None,
                       help="Schedule time (YYYY-MM-DDTHH:MM:SS)")
    
    parser.add_argument("--process-scheduled", action="store_true",
                       help="Process scheduled posts")
    
    parser.add_argument("--history", action="store_true",
                       help="Show post history")
    
    args = parser.parse_args()
    
    post_manager = PostManager()
    
    if args.process_scheduled:
        # Process scheduled posts
        posts_processed = post_manager.check_scheduled_posts()
        print(f"Processed {posts_processed} scheduled posts")
        
    elif args.history:
        # Show post history
        history = post_manager.get_post_history(platform=args.platform, avatar=args.avatar)
        print(f"Post history ({len(history)} posts):")
        for post in history:
            print(f"{post.get('posted_time')}: {post.get('platform')} - {post.get('avatar')} - {post.get('caption')[:30]}...")
            
    else:
        # Post or schedule
        if args.schedule:
            # Schedule for later
            try:
                scheduled_time = datetime.fromisoformat(args.schedule)
                result = post_manager.schedule_post(
                    video_path=args.video,
                    caption=args.caption,
                    avatar=args.avatar,
                    platform=args.platform,
                    scheduled_time=scheduled_time
                )
                
                if result.get("success"):
                    print(f"Scheduled post for {args.schedule}")
                else:
                    print(f"Failed to schedule post: {result.get('error')}")
                    
            except ValueError:
                print(f"Invalid schedule time format: {args.schedule}")
                print("Use format: YYYY-MM-DDTHH:MM:SS")
                
        else:
            # Post now
            success, result = post_manager.post_now(
                video_path=args.video,
                caption=args.caption,
                avatar=args.avatar,
                platform=args.platform
            )
            
            if success:
                print(f"Successfully posted to {args.platform}")
            else:
                print(f"Failed to post: {result.get('error')}") 