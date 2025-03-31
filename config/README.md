# Configuration Files Overview

This directory contains configuration files for the OWLmarketing project. These files hold settings and credentials necessary for the pipeline to function.

## Files

- **config.json:**  
  Contains general settings such as API keys, video settings (format, resolution), and posting schedules.

- **accounts.json:**  
  Lists details for each social media account (e.g., TikTok and Instagram credentials, posting times).

## Example Content

### config.json
```json
{
  "api_keys": {
    "openai": "YOUR_OPENAI_API_KEY",
    "music_service": "YOUR_MUSIC_API_KEY"
  },
  "video_settings": {
    "format": "vertical",
    "resolution": "1080x1920"
  },
  "posting_schedule": "2025-03-15T12:00:00"
}
