#!/usr/bin/env python3
"""
Post Scheduler - Schedules and manages social media posts across multiple platforms.

This module provides functionality for:
1. Scheduling posts across multiple platforms (TikTok, Instagram)
2. Managing post queues based on frequency and optimal posting times
3. Coordinating with platform-specific handlers
4. Tracking post status and analytics
"""

import os
import sys
import json
import logging
import random
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import traceback
import threading
import queue

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(project_root)

# Import local modules
from scheduling.post_manager import PostManager
try:
    from scheduling.platform_handlers.tiktok_handler import TikTokHandler
    from scheduling.platform_handlers.instagram_handler import InstagramHandler
except ImportError:
    # Log the error but continue - we'll handle this gracefully
    logging.warning("Could not import one or more platform handlers. Some platforms may not be available.")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('post_scheduler')

class PostScheduler:
    """Manages scheduling and posting of content across multiple platforms."""
    
    def __init__(self, 
                 config_path: Optional[str] = None, 
                 accounts_path: Optional[str] = None,
                 status_db_path: Optional[str] = None):
        """
        Initialize the post scheduler.
        
        Args:
            config_path: Path to the scheduler configuration file
            accounts_path: Path to the accounts configuration file
            status_db_path: Path to the status database file
        """
        self.config_path = config_path or os.path.join(project_root, "config", "content_creation_config.json")
        self.accounts_path = accounts_path or os.path.join(project_root, "config", "accounts.json")
        self.status_db_path = status_db_path or os.path.join(project_root, "data", "scheduler_status.json")
        
        # Load configurations
        self.config = self._load_config()
        self.accounts = self._load_accounts()
        self.post_status = self._load_status_db()
        
        # Initialize platform handlers
        self.platform_handlers = self._initialize_platform_handlers()
        
        # Initialize post manager
        self.post_manager = PostManager()
        
        # Initialize posting queue
        self.post_queue = queue.PriorityQueue()
        
        # Scheduling thread
        self.scheduling_thread = None
        self.stop_scheduling = threading.Event()
        
        logger.info("PostScheduler initialized successfully")
    
    def _load_config(self) -> Dict[str, Any]:
        """Load the scheduler configuration."""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
                logger.info(f"Loaded scheduler configuration from {self.config_path}")
                return config
            else:
                logger.warning(f"Configuration file not found: {self.config_path}")
                # Return default configuration
                return {
                    "platforms": ["tiktok", "instagram"],
                    "posting_frequency": "daily",
                    "optimal_times": {
                        "tiktok": ["12:00", "18:00", "21:00"],
                        "instagram": ["11:00", "17:00", "20:00"]
                    },
                    "max_posts_per_day": {
                        "tiktok": 3,
                        "instagram": 2
                    },
                    "posting_interval_minutes": 30,
                    "retry_attempts": 3,
                    "retry_delay_minutes": 15
                }
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            return {}
    
    def _load_accounts(self) -> Dict[str, Any]:
        """Load the accounts configuration."""
        try:
            if os.path.exists(self.accounts_path):
                with open(self.accounts_path, 'r') as f:
                    accounts = json.load(f)
                logger.info(f"Loaded accounts configuration from {self.accounts_path}")
                return accounts
            else:
                logger.warning(f"Accounts file not found: {self.accounts_path}")
                return {}
        except Exception as e:
            logger.error(f"Error loading accounts: {e}")
            return {}
    
    def _load_status_db(self) -> Dict[str, Any]:
        """Load the scheduler status database."""
        try:
            if os.path.exists(self.status_db_path):
                with open(self.status_db_path, 'r') as f:
                    status = json.load(f)
                logger.info(f"Loaded status database from {self.status_db_path}")
                return status
            else:
                logger.info(f"Status database not found, creating new: {self.status_db_path}")
                status = {
                    "scheduled_posts": [],
                    "posted": [],
                    "failed": [],
                    "last_update": datetime.now().isoformat()
                }
                self._save_status_db(status)
                return status
        except Exception as e:
            logger.error(f"Error loading status database: {e}")
            return {
                "scheduled_posts": [],
                "posted": [],
                "failed": [],
                "last_update": datetime.now().isoformat()
            }
    
    def _save_status_db(self, status: Optional[Dict[str, Any]] = None) -> bool:
        """Save the scheduler status database."""
        try:
            if status is None:
                status = self.post_status
            
            status["last_update"] = datetime.now().isoformat()
            
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(self.status_db_path), exist_ok=True)
            
            with open(self.status_db_path, 'w') as f:
                json.dump(status, f, indent=2)
            
            logger.debug(f"Saved status database to {self.status_db_path}")
            return True
        except Exception as e:
            logger.error(f"Error saving status database: {e}")
            return False
    
    def _initialize_platform_handlers(self) -> Dict[str, Any]:
        """Initialize handlers for each supported platform."""
        handlers = {}
        
        # Try to initialize TikTok handler
        try:
            if "tiktok" in self.config.get("platforms", []):
                handlers["tiktok"] = TikTokHandler(
                    accounts=self.accounts.get("tiktok", {})
                )
                logger.info("TikTok handler initialized")
        except Exception as e:
            logger.warning(f"Could not initialize TikTok handler: {e}")
        
        # Try to initialize Instagram handler
        try:
            if "instagram" in self.config.get("platforms", []):
                handlers["instagram"] = InstagramHandler(
                    accounts=self.accounts.get("instagram", {})
                )
                logger.info("Instagram handler initialized")
        except Exception as e:
            logger.warning(f"Could not initialize Instagram handler: {e}")
        
        return handlers
    
    def schedule_posts(self, 
                      videos: List[str],
                      platforms: Optional[List[str]] = None,
                      frequency: Optional[str] = None,
                      optimal_times: Optional[List[str]] = None,
                      start_date: Optional[str] = None) -> Dict[str, Any]:
        """
        Schedule posts across specified platforms.
        
        Args:
            videos: List of video file paths to schedule
            platforms: List of platforms to post to (default from config)
            frequency: Posting frequency (default from config)
            optimal_times: List of optimal posting times (default from config)
            start_date: Starting date for scheduling (default: today)
            
        Returns:
            Dictionary with scheduling results
        """
        try:
            logger.info(f"Scheduling {len(videos)} videos for posting")
            
            # Use defaults if not specified
            if platforms is None:
                platforms = self.config.get("platforms", ["tiktok", "instagram"])
            
            if frequency is None:
                frequency = self.config.get("posting_frequency", "daily")
            
            if optimal_times is None:
                # Get platform-specific optimal times, or use defaults
                optimal_times = {}
                for platform in platforms:
                    platform_times = self.config.get("optimal_times", {}).get(platform, ["12:00", "18:00"])
                    optimal_times[platform] = platform_times
            
            # Parse start date
            if start_date is None:
                start_date_dt = datetime.now()
            else:
                try:
                    start_date_dt = datetime.strptime(start_date, "%Y-%m-%d")
                except ValueError:
                    logger.warning(f"Invalid start date format: {start_date}, using today")
                    start_date_dt = datetime.now()
            
            # Generate posting schedule
            schedule = self._generate_posting_schedule(
                videos=videos,
                platforms=platforms,
                frequency=frequency,
                optimal_times=optimal_times,
                start_date=start_date_dt
            )
            
            # Add to status database
            self.post_status["scheduled_posts"].extend(schedule)
            self._save_status_db()
            
            # Add to posting queue
            for post in schedule:
                post_time = datetime.fromisoformat(post["scheduled_time"])
                self.post_queue.put((post_time.timestamp(), post))
            
            # Start scheduling thread if not already running
            if self.scheduling_thread is None or not self.scheduling_thread.is_alive():
                self._start_scheduling_thread()
            
            logger.info(f"Scheduled {len(schedule)} posts")
            
            return {
                "scheduled_posts": schedule,
                "total_scheduled": len(schedule)
            }
            
        except Exception as e:
            logger.error(f"Error scheduling posts: {e}")
            logger.error(traceback.format_exc())
            return {
                "error": str(e),
                "scheduled_posts": []
            }
    
    def _generate_posting_schedule(self,
                                 videos: List[str],
                                 platforms: List[str],
                                 frequency: str,
                                 optimal_times: Dict[str, List[str]],
                                 start_date: datetime) -> List[Dict[str, Any]]:
        """
        Generate a posting schedule based on the provided parameters.
        
        Args:
            videos: List of video file paths
            platforms: List of platforms to post to
            frequency: Posting frequency (daily, weekly, etc.)
            optimal_times: Dictionary of optimal posting times per platform
            start_date: Starting date for scheduling
            
        Returns:
            List of scheduled posts with metadata
        """
        schedule = []
        
        # Get avatar names from each video (assuming they're in the path somewhere)
        avatar_mapping = {}
        for video_path in videos:
            for avatar_name in self.accounts.get("avatars", {}).keys():
                if avatar_name.lower() in os.path.basename(video_path).lower():
                    avatar_mapping[video_path] = avatar_name
                    break
            
            # Default to a random avatar if not found
            if video_path not in avatar_mapping:
                avatar_mapping[video_path] = random.choice(list(self.accounts.get("avatars", {}).keys()))
        
        # Start date should be tomorrow if it's after 8 PM
        if start_date.hour >= 20:
            start_date = start_date + timedelta(days=1)
        
        # Reset to start of day
        current_date = datetime(
            start_date.year, start_date.month, start_date.day, 
            0, 0, 0
        )
        
        # Schedule posts based on frequency
        if frequency == "daily":
            posts_per_day = min(
                len(videos),
                sum(self.config.get("max_posts_per_day", {}).get(p, 2) for p in platforms)
            )
            
            day_offset = 0
            video_index = 0
            
            # Keep scheduling until all videos are scheduled
            while video_index < len(videos):
                schedule_date = current_date + timedelta(days=day_offset)
                
                # Schedule for each platform
                for platform in platforms:
                    # Get optimal times for this platform
                    platform_times = optimal_times.get(platform, ["12:00", "18:00"])
                    
                    # Get max posts per day for this platform
                    max_platform_posts = self.config.get("max_posts_per_day", {}).get(platform, 2)
                    
                    # Schedule up to max_platform_posts
                    for i in range(min(max_platform_posts, len(videos) - video_index)):
                        if video_index >= len(videos):
                            break
                            
                        video_path = videos[video_index]
                        avatar_name = avatar_mapping[video_path]
                        
                        # Get account for this avatar and platform
                        account = self._get_account_for_avatar(avatar_name, platform)
                        
                        if not account:
                            logger.warning(f"No account found for avatar {avatar_name} on {platform}, skipping")
                            video_index += 1
                            continue
                        
                        # Choose a posting time
                        time_index = i % len(platform_times)
                        time_str = platform_times[time_index]
                        hour, minute = map(int, time_str.split(":"))
                        
                        # Add a small random offset to avoid posting at exactly the same time
                        minute_offset = random.randint(-5, 5)
                        
                        post_time = schedule_date.replace(
                            hour=hour,
                            minute=max(0, min(59, minute + minute_offset))
                        )
                        
                        # Create post entry
                        post = {
                            "id": f"post_{int(time.time())}_{len(schedule)}",
                            "video_path": video_path,
                            "platform": platform,
                            "account": account["username"],
                            "avatar": avatar_name,
                            "scheduled_time": post_time.isoformat(),
                            "status": "scheduled",
                            "caption": self._generate_caption(video_path, platform),
                            "hashtags": self._generate_hashtags(platform),
                            "created_at": datetime.now().isoformat()
                        }
                        
                        schedule.append(post)
                        video_index += 1
                
                # Move to next day
                day_offset += 1
            
        elif frequency == "weekly":
            # Weekly posting logic would go here
            # Similar to daily but with weekly intervals
            pass
        
        else:
            logger.warning(f"Unsupported frequency: {frequency}, using daily")
            # Fall back to daily logic
            pass
        
        return schedule
    
    def _get_account_for_avatar(self, avatar_name: str, platform: str) -> Dict[str, Any]:
        """Get the appropriate account for an avatar on a platform."""
        try:
            # Check if this avatar has specific accounts
            avatar_accounts = self.accounts.get("avatars", {}).get(avatar_name, {}).get(platform, [])
            
            if avatar_accounts:
                # Return a random account if multiple are available
                return random.choice(avatar_accounts)
            
            # Fall back to general accounts for this platform
            platform_accounts = self.accounts.get(platform, [])
            if platform_accounts:
                return random.choice(platform_accounts)
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting account for avatar {avatar_name} on {platform}: {e}")
            return None
    
    def _generate_caption(self, video_path: str, platform: str) -> str:
        """Generate a caption for the post based on the video content."""
        try:
            # Get base filename without extension
            filename = os.path.basename(video_path)
            base_name = os.path.splitext(filename)[0]
            
            # Try to extract info from the filename
            parts = base_name.split('_')
            
            # If it's a generated script from our system, try to load it
            script_path = None
            for part in parts:
                if part.startswith('script'):
                    potential_path = os.path.join(
                        project_root, 
                        "output", 
                        os.path.dirname(video_path).split("output")[-1].strip('/\\'),
                        "scripts",
                        f"{part}.json"
                    )
                    if os.path.exists(potential_path):
                        script_path = potential_path
                        break
            
            if script_path and os.path.exists(script_path):
                try:
                    with open(script_path, 'r') as f:
                        script = json.load(f)
                    
                    # Use the hook from the script as caption
                    if "hook" in script:
                        return script["hook"]
                except Exception as e:
                    logger.warning(f"Error loading script for caption: {e}")
            
            # Default captions per platform
            platform_captions = {
                "tiktok": "Check out this amazing calorie tracking app! #OptimalAI #calorietracking",
                "instagram": "This app changed my relationship with food tracking! #OptimalAI #nutrition"
            }
            
            return platform_captions.get(platform, "Optimal AI - Smart calorie tracking")
            
        except Exception as e:
            logger.error(f"Error generating caption: {e}")
            return "Optimal AI - Smart calorie tracking"
    
    def _generate_hashtags(self, platform: str) -> List[str]:
        """Generate appropriate hashtags for the platform."""
        try:
            # Platform-specific hashtags
            platform_hashtags = {
                "tiktok": [
                    "calorietracking", "OptimalAI", "nutrition", "healthylifestyle", 
                    "weightloss", "dietitian", "mealprep", "foodscanner"
                ],
                "instagram": [
                    "calorietacker", "OptimalAI", "nutritionapp", "fitnessjourney", 
                    "healthyeating", "mealtracking", "dietplan", "weightlossjourney"
                ]
            }
            
            # Get base hashtags for this platform
            base_hashtags = platform_hashtags.get(platform, ["OptimalAI", "calorietracking"])
            
            # Add 3-5 random hashtags from a larger set
            additional_hashtags = [
                "fooddiary", "macros", "proteinintake", "fitfood", "mealtips",
                "healthymeals", "nutritioncoach", "weightmanagement", "caloriedeficit",
                "foodscanner", "dietapp", "healthapp", "fitnessapp", "foodlog",
                "intuitiveeating", "balanceddiet", "mealplan", "healthgoals"
            ]
            
            random.shuffle(additional_hashtags)
            num_additional = random.randint(3, 5)
            
            return base_hashtags + additional_hashtags[:num_additional]
            
        except Exception as e:
            logger.error(f"Error generating hashtags: {e}")
            return ["OptimalAI", "calorietracking"]
    
    def _start_scheduling_thread(self):
        """Start the scheduling thread to process the posting queue."""
        if self.scheduling_thread is not None and self.scheduling_thread.is_alive():
            logger.info("Scheduling thread is already running")
            return
        
        # Reset stop event
        self.stop_scheduling.clear()
        
        # Create and start thread
        self.scheduling_thread = threading.Thread(
            target=self._scheduling_worker,
            daemon=True
        )
        self.scheduling_thread.start()
        
        logger.info("Started scheduling thread")
    
    def _scheduling_worker(self):
        """Worker function for scheduling thread."""
        logger.info("Scheduling worker started")
        
        while not self.stop_scheduling.is_set():
            try:
                # Check if there are any posts to process
                if self.post_queue.empty():
                    # Sleep for a bit and check again
                    time.sleep(30)
                    continue
                
                # Peek at the next post without removing it
                next_post_time, next_post = self.post_queue.queue[0]
                
                # Calculate time until next post
                now = time.time()
                time_until_post = next_post_time - now
                
                if time_until_post <= 0:
                    # Time to post
                    _, post = self.post_queue.get()
                    self._process_post(post)
                else:
                    # Sleep until next post time (but wake up periodically to check for stop)
                    sleep_time = min(time_until_post, 60)  # Wake up at least every minute
                    time.sleep(sleep_time)
                
            except Exception as e:
                logger.error(f"Error in scheduling worker: {e}")
                time.sleep(10)  # Sleep and try again
    
    def _process_post(self, post: Dict[str, Any]):
        """Process a post, sending it to the appropriate platform."""
        try:
            logger.info(f"Processing post {post['id']} for {post['platform']}")
            
            # Update post status
            post["status"] = "processing"
            post["process_start_time"] = datetime.now().isoformat()
            self._update_post_status(post)
            
            # Check if video exists
            if not os.path.exists(post["video_path"]):
                logger.error(f"Video file not found: {post['video_path']}")
                post["status"] = "failed"
                post["error"] = "Video file not found"
                self._update_post_status(post)
                return
            
            # Get platform handler
            platform = post["platform"]
            if platform not in self.platform_handlers:
                logger.error(f"No handler available for platform: {platform}")
                post["status"] = "failed"
                post["error"] = f"No handler for platform: {platform}"
                self._update_post_status(post)
                return
            
            handler = self.platform_handlers[platform]
            
            # Post video
            success, result = handler.post_video(
                video_path=post["video_path"],
                caption=post["caption"],
                hashtags=post["hashtags"],
                account=post["account"]
            )
            
            if success:
                logger.info(f"Successfully posted to {platform}: {post['id']}")
                post["status"] = "posted"
                post["post_url"] = result.get("post_url", "")
                post["post_id"] = result.get("post_id", "")
                post["posted_time"] = datetime.now().isoformat()
                
                # Move to posted list
                self.post_status["posted"].append(post)
                self._remove_from_scheduled(post["id"])
                
            else:
                logger.error(f"Failed to post to {platform}: {result.get('error', 'Unknown error')}")
                post["status"] = "failed"
                post["error"] = result.get("error", "Unknown error")
                post["failure_time"] = datetime.now().isoformat()
                
                # Add to retry queue if under max retries
                retries = post.get("retries", 0)
                max_retries = self.config.get("retry_attempts", 3)
                
                if retries < max_retries:
                    post["retries"] = retries + 1
                    
                    # Schedule retry
                    retry_delay = self.config.get("retry_delay_minutes", 15)
                    retry_time = datetime.now() + timedelta(minutes=retry_delay)
                    post["retry_time"] = retry_time.isoformat()
                    
                    # Add back to queue
                    self.post_queue.put((retry_time.timestamp(), post))
                    logger.info(f"Scheduled retry {retries + 1}/{max_retries} for post {post['id']}")
                    
                else:
                    # Max retries reached, move to failed list
                    logger.warning(f"Max retries reached for post {post['id']}")
                    self.post_status["failed"].append(post)
                    self._remove_from_scheduled(post["id"])
            
            # Save status
            self._save_status_db()
            
        except Exception as e:
            logger.error(f"Error processing post: {e}")
            logger.error(traceback.format_exc())
            
            post["status"] = "failed"
            post["error"] = str(e)
            post["failure_time"] = datetime.now().isoformat()
            
            # Save status
            self._update_post_status(post)
    
    def _update_post_status(self, post: Dict[str, Any]):
        """Update the status of a post in the status database."""
        try:
            post_id = post["id"]
            
            # Find and update post in scheduled_posts
            for i, p in enumerate(self.post_status["scheduled_posts"]):
                if p["id"] == post_id:
                    self.post_status["scheduled_posts"][i] = post
                    break
            
            # Save status database
            self._save_status_db()
            
        except Exception as e:
            logger.error(f"Error updating post status: {e}")
    
    def _remove_from_scheduled(self, post_id: str):
        """Remove a post from the scheduled posts list."""
        try:
            self.post_status["scheduled_posts"] = [
                p for p in self.post_status["scheduled_posts"] 
                if p["id"] != post_id
            ]
        except Exception as e:
            logger.error(f"Error removing post from scheduled list: {e}")
    
    def get_posting_status(self, days_back: int = 7) -> Dict[str, Any]:
        """Get posting status for the past X days."""
        try:
            now = datetime.now()
            cutoff = now - timedelta(days=days_back)
            
            # Filter posts by date
            scheduled = [
                p for p in self.post_status["scheduled_posts"]
                if datetime.fromisoformat(p["created_at"]) >= cutoff
            ]
            
            posted = [
                p for p in self.post_status["posted"]
                if "posted_time" in p and datetime.fromisoformat(p["posted_time"]) >= cutoff
            ]
            
            failed = [
                p for p in self.post_status["failed"]
                if "failure_time" in p and datetime.fromisoformat(p["failure_time"]) >= cutoff
            ]
            
            # Group by platform
            platforms = {}
            for platform in self.config.get("platforms", []):
                platforms[platform] = {
                    "scheduled": len([p for p in scheduled if p["platform"] == platform]),
                    "posted": len([p for p in posted if p["platform"] == platform]),
                    "failed": len([p for p in failed if p["platform"] == platform])
                }
            
            # Group by avatar
            avatars = {}
            for avatar in self.accounts.get("avatars", {}).keys():
                avatars[avatar] = {
                    "scheduled": len([p for p in scheduled if p.get("avatar") == avatar]),
                    "posted": len([p for p in posted if p.get("avatar") == avatar]),
                    "failed": len([p for p in failed if p.get("avatar") == avatar])
                }
            
            return {
                "time_period": f"Last {days_back} days",
                "total": {
                    "scheduled": len(scheduled),
                    "posted": len(posted),
                    "failed": len(failed)
                },
                "by_platform": platforms,
                "by_avatar": avatars,
                "last_updated": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting posting status: {e}")
            return {
                "error": str(e),
                "time_period": f"Last {days_back} days",
                "total": {
                    "scheduled": 0,
                    "posted": 0,
                    "failed": 0
                }
            }
    
    def stop(self):
        """Stop the scheduler."""
        if self.scheduling_thread and self.scheduling_thread.is_alive():
            logger.info("Stopping scheduling thread")
            self.stop_scheduling.set()
            self.scheduling_thread.join(timeout=5)
            logger.info("Scheduling thread stopped")


# Simplified function for direct use by the pipeline
def schedule_posts(videos: List[str],
                  platforms: Optional[List[str]] = None,
                  frequency: Optional[str] = None,
                  optimal_times: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Schedule posts across specified platforms (simplified interface for pipeline).
    
    Args:
        videos: List of video file paths to schedule
        platforms: List of platforms to post to
        frequency: Posting frequency
        optimal_times: List of optimal posting times
        
    Returns:
        Dictionary with scheduling results
    """
    try:
        scheduler = PostScheduler()
        
        # If optimal_times is a list, convert to dict format for internal use
        optimal_times_dict = None
        if optimal_times:
            if isinstance(optimal_times, list):
                optimal_times_dict = {}
                for platform in platforms or scheduler.config.get("platforms", []):
                    optimal_times_dict[platform] = optimal_times
        
        result = scheduler.schedule_posts(
            videos=videos,
            platforms=platforms,
            frequency=frequency,
            optimal_times=optimal_times_dict
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error in schedule_posts: {e}")
        logger.error(traceback.format_exc())
        return {
            "error": str(e),
            "scheduled_posts": []
        }


if __name__ == "__main__":
    # Example usage
    import argparse
    
    parser = argparse.ArgumentParser(description="Schedule social media posts")
    
    parser.add_argument("--videos", type=str, nargs="+", required=True,
                       help="List of video files to schedule")
    
    parser.add_argument("--platforms", type=str, nargs="+", default=None,
                       help="List of platforms to post to")
    
    parser.add_argument("--frequency", type=str, default=None,
                       help="Posting frequency (daily, weekly)")
    
    parser.add_argument("--start-date", type=str, default=None,
                       help="Start date (YYYY-MM-DD)")
    
    parser.add_argument("--status", action="store_true",
                       help="Show posting status")
    
    args = parser.parse_args()
    
    if args.status:
        scheduler = PostScheduler()
        status = scheduler.get_posting_status()
        print(json.dumps(status, indent=2))
    else:
        result = schedule_posts(
            videos=args.videos,
            platforms=args.platforms,
            frequency=args.frequency
        )
        
        print(f"Scheduled {len(result.get('scheduled_posts', []))} posts")
        if "error" in result:
            print(f"Error: {result['error']}") 