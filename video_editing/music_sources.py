#!/usr/bin/env python3
"""
Music Sources for OWLmarketing Videos

This module provides access to trending music sources suitable for the Optimal AI marketing videos.
It contains categorized links to royalty-free music that can be used without copyright issues.
"""

import random
import logging
import requests
import json
import os
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

# Royalty-free music platforms with API support
MUSIC_PLATFORMS = {
    "pixabay": "https://pixabay.com/api/videos/",
    "mixkit": "https://mixkit.co/free-stock-music/",
    "audiojungle": "https://audiojungle.net/",
}

# Trending music categories with pre-validated royalty-free sources
TRENDING_MUSIC = {
    "fitness": [
        "https://elements.envato.com/motivational-corporate-technology-U2JBMA6",
        "https://elements.envato.com/upbeat-motivational-corporate-PVDK9ZK",
        "https://pixabay.com/music/beats-powerful-motivation-uplifting-ambient-159151/",
        "https://pixabay.com/music/future-bass-get-ready-for-fitness-159473/",
        "https://elements.envato.com/power-sport-intense-YWCNHCH",
    ],
    "health_tech": [
        "https://elements.envato.com/technology-intro-P6YZ9ZE",
        "https://elements.envato.com/upbeat-technology-QFP2LDU",
        "https://pixabay.com/music/beautiful-plays-beautiful-inspiring-piano-164960/",
        "https://pixabay.com/music/upbeat-tech-technology-corporate-159074/",
        "https://elements.envato.com/business-technology-USZLPDU",
    ],
    "lifestyle": [
        "https://elements.envato.com/summer-positive-acoustic-UHE2WDM",
        "https://pixabay.com/music/beats-lofi-study-112191/",
        "https://elements.envato.com/happy-corporate-technology-6TRZ6A4",
        "https://pixabay.com/music/upbeat-chill-lofi-130874/",
        "https://elements.envato.com/happy-acoustic-YP6JWGN",
    ],
    "upbeat_viral": [
        "https://elements.envato.com/pop-dance-P6EXRZU",
        "https://pixabay.com/music/beats-chill-jazzy-trap-beat-159538/",
        "https://elements.envato.com/pop-hip-hop-U3SHZTF",
        "https://pixabay.com/music/future-bass-future-bass-9478/",
        "https://elements.envato.com/light-pop-upbeat-BCNK76G",
    ]
}

# Custom style-to-music mapping for different avatar styles
AVATAR_MUSIC_MAPPING = {
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

# Use free API keys if available
PIXABAY_API_KEY = os.environ.get("PIXABAY_API_KEY", "")

def get_trending_music_for_avatar(avatar_name: str) -> str:
    """
    Get trending music URL based on avatar style preferences.
    
    Args:
        avatar_name: Name of the avatar
        
    Returns:
        URL to trending music suitable for the avatar
    """
    # Normalize avatar name (lowercase, remove spaces)
    avatar = avatar_name.lower().strip()
    
    # Get music category for this avatar
    category = AVATAR_MUSIC_MAPPING.get(avatar, "upbeat_viral")
    
    # Get music options for this category
    music_options = TRENDING_MUSIC.get(category, TRENDING_MUSIC["upbeat_viral"])
    
    # Select random track from options
    selected_music = random.choice(music_options)
    logger.info(f"Selected {category} music for avatar {avatar_name}: {selected_music}")
    
    return selected_music

def search_music_api(query: str, mood: str = None) -> Optional[str]:
    """
    Search for music using available APIs.
    
    Args:
        query: Search term for music
        mood: Desired mood/style
        
    Returns:
        URL to music if found, None otherwise
    """
    if PIXABAY_API_KEY:
        try:
            # Construct search query
            search_term = f"{query} {mood}" if mood else query
            url = f"https://pixabay.com/api/music/?key={PIXABAY_API_KEY}&q={search_term}"
            
            # Make API request
            response = requests.get(url)
            data = response.json()
            
            # Check if we have results
            if data.get("hits") and len(data["hits"]) > 0:
                # Sort by popularity
                sorted_hits = sorted(data["hits"], key=lambda x: x.get("downloads", 0), reverse=True)
                return sorted_hits[0].get("audio", None)
            
        except Exception as e:
            logger.error(f"Error searching Pixabay API: {e}")
    
    return None

def get_current_trending_tracks(limit: int = 5) -> List[str]:
    """
    Get current trending tracks from available APIs.
    
    Args:
        limit: Maximum number of tracks to return
        
    Returns:
        List of trending track URLs
    """
    combined_tracks = []
    
    # Gather all tracks from our predefined categories
    for category in TRENDING_MUSIC:
        combined_tracks.extend(TRENDING_MUSIC[category])
    
    # Shuffle to randomize selection
    random.shuffle(combined_tracks)
    
    # Return requested number of tracks
    return combined_tracks[:limit]

def download_music(url: str, output_path: str) -> bool:
    """
    Download music from URL to local file.
    
    Args:
        url: URL of music file
        output_path: Path to save downloaded file
        
    Returns:
        True if successful, False otherwise
    """
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        logger.info(f"Downloaded music from {url} to {output_path}")
        return True
        
    except Exception as e:
        logger.error(f"Error downloading music from {url}: {e}")
        return False

if __name__ == "__main__":
    # Simple test of the module
    logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s: %(message)s')
    
    # Test getting music for different avatars
    for avatar in AVATAR_MUSIC_MAPPING.keys():
        music_url = get_trending_music_for_avatar(avatar)
        print(f"Avatar {avatar}: {music_url}")
    
    # Test getting trending tracks
    trending = get_current_trending_tracks(3)
    print(f"Top 3 trending tracks: {trending}") 