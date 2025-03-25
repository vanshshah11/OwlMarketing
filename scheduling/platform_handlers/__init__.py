#!/usr/bin/env python3
# platform_handlers module

"""
Platform Handlers Package - Handles posting to different social media platforms.

This package contains handlers for various social media platforms:
- TikTokHandler: For posting to TikTok
- InstagramHandler: For posting to Instagram
- Other platforms as needed
"""

# Import platform handlers
try:
    from .tiktok_handler import TikTokHandler
except ImportError:
    pass

try:
    from .instagram_handler import InstagramHandler
except ImportError:
    pass

from scheduling.platform_handlers.tiktok_handler import post_to_tiktok
from scheduling.platform_handlers.instagram_handler import post_to_instagram
from scheduling.platform_handlers.youtube_handler import post_to_youtube

__all__ = ['post_to_tiktok', 'post_to_instagram', 'post_to_youtube'] 