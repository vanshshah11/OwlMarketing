#!/usr/bin/env python3
# /Users/vanshshah/Desktop/OWLmarketing/video_generation/avatar_manager.py

import os
import json
import logging
from video_generation.avatar_config import AVATAR_CONFIGS

# Configure logging to include time, level, and message
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s: %(message)s')

# Simple Avatar class to replace AvatarModel
class Avatar:
    def __init__(self, name, config=None):
        self.name = name
        self.config = config or {}
        self.current_emotion = "neutral"
    
    def set_emotion(self, emotion):
        self.current_emotion = emotion
        logging.info(f"Set {self.name}'s emotion to {emotion}")
    
    def display_info(self):
        logging.info(f"Avatar: {self.name}")
        logging.info(f"Current emotion: {self.current_emotion}")
        if self.config:
            logging.info(f"Base prompt: {self.config.get('base_prompt', 'N/A')[:50]}...")
            logging.info(f"Variation types: {list(self.config.get('variations', {}).keys())}")

# Define the base folder for storing individual avatar data
BASE_AVATAR_FOLDER = os.path.join(os.path.dirname(__file__), "avatars")

def ensure_base_folder():
    """Ensure the base folder for avatars exists."""
    if not os.path.exists(BASE_AVATAR_FOLDER):
        os.makedirs(BASE_AVATAR_FOLDER)
        logging.info("Created base avatars folder: %s", BASE_AVATAR_FOLDER)
    else:
        logging.info("Base avatars folder already exists: %s", BASE_AVATAR_FOLDER)

def save_avatar(avatar):
    """
    Save the avatar's characteristics to a JSON file in its dedicated folder.
    """
    avatar_folder = os.path.join(BASE_AVATAR_FOLDER, avatar.name)
    if not os.path.exists(avatar_folder):
        os.makedirs(avatar_folder)
        logging.info("Created folder for avatar %s: %s", avatar.name, avatar_folder)
    else:
        logging.info("Folder for avatar %s exists: %s", avatar.name, avatar_folder)
    
    data = {
        "name": avatar.name,
        "current_emotion": avatar.current_emotion
    }
    json_file = os.path.join(avatar_folder, "characteristics.json")
    with open(json_file, "w") as f:
        json.dump(data, f, indent=4)
    logging.info("Saved characteristics for avatar %s to %s", avatar.name, json_file)

def load_avatar(name: str):
    """
    Load an avatar's characteristics from its folder, if available.
    """
    # Check if avatar exists in AVATAR_CONFIGS
    if name not in AVATAR_CONFIGS:
        logging.warning(f"Avatar '{name}' not found in AVATAR_CONFIGS")
        return None
    
    # Get config from AVATAR_CONFIGS
    config = AVATAR_CONFIGS[name]
    
    # Create Avatar instance
    avatar = Avatar(name, config)
    
    # Try to load saved state if it exists
    avatar_folder = os.path.join(BASE_AVATAR_FOLDER, name)
    json_file = os.path.join(avatar_folder, "characteristics.json")
    if os.path.exists(json_file):
        with open(json_file, "r") as f:
            data = json.load(f)
        logging.info("Loaded avatar %s from %s", name, json_file)
        avatar.current_emotion = data.get("current_emotion", "neutral")
    else:
        logging.warning("No saved data for avatar %s. Using defaults.", name)
    
    return avatar

def create_and_save_avatars():
    """
    Create avatar models for each config and save them.
    """
    ensure_base_folder()
    
    avatars = []
    for name in AVATAR_CONFIGS.keys():
        # Check if an avatar with this name already exists
        existing_avatar = load_avatar(name)
        if existing_avatar:
            avatar = existing_avatar
            logging.info("Using existing avatar for %s", name)
        else:
            avatar = Avatar(name, AVATAR_CONFIGS[name])
            logging.info("Creating new avatar for %s", name)
        # Save avatar details for consistency
        save_avatar(avatar)
        avatars.append(avatar)
    
    return avatars

if __name__ == "__main__":
    logging.info("Starting creation and persistence of AI avatar models with consistent characteristics.")
    avatar_list = create_and_save_avatars()
    
    # Set a default emotion and display info for each avatar
    for avatar in avatar_list:
        avatar.set_emotion("happy")
        avatar.display_info()
    
    logging.info("All avatar models created and saved successfully.")
