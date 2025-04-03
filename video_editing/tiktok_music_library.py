#!/usr/bin/env python3
"""
TikTok Commercial Music Library Integration

This module provides access to TikTok's Commercial Music Library and trending music
from social platforms for use in OWLmarketing videos.

The TikTok Commercial Music Library contains tracks that are pre-cleared for commercial use,
allowing businesses to use trending sounds without copyright concerns.
"""

import os
import json
import random
import logging
import requests
import time
from typing import Dict, List, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

# TikTok API configuration
TIKTOK_API_KEY = os.environ.get("TIKTOK_API_KEY", "")
RAPIDAPI_KEY = os.environ.get("RAPIDAPI_KEY", "")

# Cache directory for downloaded music
CACHE_DIR = Path(os.path.dirname(__file__)) / ".." / "data" / "music_cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# Cache file for trend data
TRENDS_CACHE_FILE = CACHE_DIR / "trends_cache.json"
CACHE_EXPIRY = 24 * 60 * 60  # 24 hours in seconds

# Fallback commercial music library URLs (royalty-free but trending-style music)
# These are backup options if API integration fails
COMMERCIAL_LIBRARY = {
    "fitness": [
        "https://assets.mixkit.co/music/download/mixkit-fitness-motivation-722.mp3",
        "https://assets.mixkit.co/music/download/mixkit-gym-training-126.mp3",
        "https://cdn.pixabay.com/download/audio/2022/03/10/audio_b4e4134ae3.mp3?filename=powerful-motivation-uplifting-ambient-159151.mp3",
    ],
    "health_tech": [
        "https://assets.mixkit.co/music/download/mixkit-tech-startup-156.mp3",
        "https://assets.mixkit.co/music/download/mixkit-digital-technology-168.mp3",
        "https://cdn.pixabay.com/download/audio/2022/01/18/audio_dc39bcdba1.mp3?filename=technology-corporate-159074.mp3",
    ],
    "lifestyle": [
        "https://assets.mixkit.co/music/download/mixkit-chill-afternoon-vibes-109.mp3",
        "https://assets.mixkit.co/music/download/mixkit-serene-view-142.mp3",
        "https://cdn.pixabay.com/download/audio/2022/03/25/audio_47688d9464.mp3?filename=lofi-chill-medium-version-159456.mp3",
    ],
    "upbeat_viral": [
        "https://assets.mixkit.co/music/download/mixkit-hip-hop-02-738.mp3",
        "https://assets.mixkit.co/music/download/mixkit-raising-me-higher-34.mp3",
        "https://cdn.pixabay.com/download/audio/2022/05/16/audio_99297ee0c7.mp3?filename=house-deep-beats-144235.mp3",
    ]
}

# Avatar to style mapping
AVATAR_STYLE_MAPPING = {
    "emma": "fitness",
    "sophia": "health_tech",
    "olivia": "upbeat_viral",
    "ava": "lifestyle",
    "isabella": "fitness",
    "mia": "upbeat_viral",
    "charlotte": "health_tech",
    "amelia": "lifestyle",
    "harper": "upbeat_viral",
    "sarah": "health_tech"
}

def fetch_tiktok_commercial_tracks(category: str = None) -> List[Dict]:
    """
    Fetch tracks from TikTok's Commercial Music Library using RapidAPI.
    
    Args:
        category: Music category/mood to filter by
        
    Returns:
        List of track data dictionaries with download URLs
    """
    # Check for RapidAPI key in environment variables first
    api_key = os.environ.get("RAPIDAPI_KEY", RAPIDAPI_KEY)
    
    if not api_key:
        logger.warning("No RapidAPI key found. Using fallback commercial library.")
        return []
    
    try:
        # Using RapidAPI's TikTok API to access commercial sounds
        url = "https://tiktok-trending-songs.p.rapidapi.com/commercial"
        if category:
            url += f"?category={category}"
            
        headers = {
            "X-RapidAPI-Key": api_key,
            "X-RapidAPI-Host": "tiktok-trending-songs.p.rapidapi.com"
        }
        
        logger.info(f"Fetching commercial tracks from TikTok API with category: {category}")
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        data = response.json()
        if "tracks" in data and isinstance(data["tracks"], list):
            logger.info(f"Fetched {len(data['tracks'])} commercial tracks from TikTok API")
            return data["tracks"]
        
        logger.warning(f"Unexpected response format from TikTok API")
        return []
        
    except Exception as e:
        logger.error(f"Error fetching TikTok commercial tracks: {e}")
        return []

def fetch_trending_tracks() -> Dict[str, List[Dict]]:
    """
    Fetch trending tracks from TikTok and Instagram using available APIs.
    Uses caching to reduce API calls.
    
    Returns:
        Dictionary of categories with lists of track data
    """
    # Check if we have valid cached data
    if TRENDS_CACHE_FILE.exists():
        try:
            with open(TRENDS_CACHE_FILE, 'r') as f:
                cache_data = json.load(f)
                
            # Check if cache is still valid
            if time.time() - cache_data.get("timestamp", 0) < CACHE_EXPIRY:
                logger.info("Using cached trending tracks data")
                return cache_data.get("trends", {})
        except Exception as e:
            logger.warning(f"Error reading trends cache: {e}")
    
    # Initialize trends data structure
    trends = {
        "fitness": [],
        "health_tech": [],
        "lifestyle": [],
        "upbeat_viral": []
    }
    
    # Check for RapidAPI key in environment variables first
    api_key = os.environ.get("RAPIDAPI_KEY", RAPIDAPI_KEY)
    
    if api_key:
        try:
            # Using RapidAPI's TikTok Trends API
            url = "https://tiktok-trending-video-and-music.p.rapidapi.com/music/trending"
            headers = {
                "X-RapidAPI-Key": api_key,
                "X-RapidAPI-Host": "tiktok-trending-video-and-music.p.rapidapi.com"
            }
            
            logger.info("Fetching trending tracks from TikTok API")
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            data = response.json()
            if isinstance(data, list) and len(data) > 0:
                # Process and categorize trending tracks
                for track in data:
                    # Attempt to categorize tracks based on tags, description, etc.
                    track_name = track.get("music_info", {}).get("title", "").lower()
                    author = track.get("music_info", {}).get("author", "").lower()
                    
                    # Simple categorization based on track attributes
                    if any(word in track_name for word in ["workout", "gym", "power", "energy"]):
                        trends["fitness"].append(track)
                    elif any(word in track_name for word in ["tech", "future", "digital", "innovation"]):
                        trends["health_tech"].append(track)
                    elif any(word in track_name for word in ["chill", "relax", "calm", "lofi"]):
                        trends["lifestyle"].append(track)
                    else:
                        # Default to upbeat_viral for uncategorized tracks
                        trends["upbeat_viral"].append(track)
                
                logger.info(f"Fetched and categorized {len(data)} trending tracks from TikTok API")
                
                # Cache the results
                with open(TRENDS_CACHE_FILE, 'w') as f:
                    json.dump({
                        "timestamp": time.time(),
                        "trends": trends
                    }, f)
                
                return trends
                
        except Exception as e:
            logger.error(f"Error fetching trending tracks: {e}")
    
    # If API fails or no API key, return empty structure
    logger.warning("Could not fetch trending tracks. Using fallback commercial library.")
    return trends

def get_track_download_url(track_data: Dict) -> Optional[str]:
    """
    Extract download URL from track data returned by APIs.
    
    Args:
        track_data: Track data dictionary from API
        
    Returns:
        Download URL if available, None otherwise
    """
    # Handle TikTok API response format
    if "music_info" in track_data and "play_url" in track_data["music_info"]:
        return track_data["music_info"]["play_url"]
    
    # Handle Commercial Library API format
    if "download_url" in track_data:
        return track_data["download_url"]
    
    if "url" in track_data:
        return track_data["url"]
    
    return None

def get_trending_music_for_avatar(avatar_name: str) -> str:
    """
    Get trending commercial music appropriate for the specified avatar.
    
    Args:
        avatar_name: Name of the avatar
        
    Returns:
        URL to appropriate trending music
    """
    # Get style category for this avatar
    avatar = avatar_name.lower().strip()
    category = AVATAR_STYLE_MAPPING.get(avatar, "upbeat_viral")
    
    # Try to get commercial tracks from TikTok
    commercial_tracks = fetch_tiktok_commercial_tracks(category)
    
    # If commercial tracks are available, select one randomly
    if commercial_tracks:
        selected_track = random.choice(commercial_tracks)
        download_url = get_track_download_url(selected_track)
        
        if download_url:
            logger.info(f"Selected TikTok commercial track for {avatar_name}: {download_url}")
            return download_url
    
    # Try to get tracks from trending API
    trending_tracks = fetch_trending_tracks()
    category_tracks = trending_tracks.get(category, [])
    
    if category_tracks:
        selected_track = random.choice(category_tracks)
        download_url = get_track_download_url(selected_track)
        
        if download_url:
            logger.info(f"Selected trending track for {avatar_name}: {download_url}")
            return download_url
    
    # Fallback to our pre-defined commercial library
    fallback_tracks = COMMERCIAL_LIBRARY.get(category, COMMERCIAL_LIBRARY["upbeat_viral"])
    selected_url = random.choice(fallback_tracks)
    logger.info(f"Using fallback commercial track for {avatar_name}: {selected_url}")
    
    return selected_url

def download_music(url: str, output_path: str) -> bool:
    """
    Download music from URL to local file with caching.
    
    Args:
        url: URL of music file
        output_path: Path to save downloaded file
        
    Returns:
        True if successful, False otherwise
    """
    # Create a cache key from the URL
    from hashlib import md5
    url_hash = md5(url.encode()).hexdigest()
    cache_path = CACHE_DIR / f"{url_hash}.mp3"
    
    # Check if we already have this file cached
    if cache_path.exists():
        logger.info(f"Using cached music file for {url}")
        
        # Copy from cache to output path
        import shutil
        shutil.copy2(cache_path, output_path)
        return True
    
    # Download the file
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        # Save to cache
        with open(cache_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        # Copy to output path
        import shutil
        shutil.copy2(cache_path, output_path)
        
        logger.info(f"Downloaded and cached music from {url}")
        return True
        
    except Exception as e:
        logger.error(f"Error downloading music from {url}: {e}")
        return False

def get_music_recommendations(mood: str = None, limit: int = 5) -> List[str]:
    """
    Get music recommendations based on mood/style.
    
    Args:
        mood: Music mood/style
        limit: Maximum number of recommendations
        
    Returns:
        List of music URLs
    """
    # Try commercial tracks first
    commercial_tracks = fetch_tiktok_commercial_tracks(mood)
    urls = []
    
    # Extract URLs from commercial tracks
    for track in commercial_tracks[:limit]:
        url = get_track_download_url(track)
        if url:
            urls.append(url)
    
    # If we don't have enough, add from trending
    if len(urls) < limit:
        trending = fetch_trending_tracks()
        mood_category = mood if mood in trending else "upbeat_viral"
        
        for track in trending.get(mood_category, [])[:limit - len(urls)]:
            url = get_track_download_url(track)
            if url:
                urls.append(url)
    
    # If still not enough, add from fallback library
    if len(urls) < limit:
        mood_category = mood if mood in COMMERCIAL_LIBRARY else "upbeat_viral"
        urls.extend(COMMERCIAL_LIBRARY[mood_category][:limit - len(urls)])
    
    return urls[:limit]

if __name__ == "__main__":
    # Simple test function
    logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s: %(message)s')
    
    # Test getting music for different avatars
    for avatar in AVATAR_STYLE_MAPPING.keys():
        music_url = get_trending_music_for_avatar(avatar)
        print(f"Avatar {avatar}: {music_url}")
    
    # Test recommendations
    for mood in ["fitness", "lifestyle", "upbeat_viral"]:
        recommendations = get_music_recommendations(mood, 2)
        print(f"Recommendations for {mood}: {recommendations}") 