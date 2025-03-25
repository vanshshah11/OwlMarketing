#!/usr/bin/env python3
import os
import json
import shutil
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s: %(message)s')

BASE_INFLUENCER_DIR = os.path.join(os.path.dirname(__file__), "influencer_data")

def ensure_influencer_base():
    if not os.path.exists(BASE_INFLUENCER_DIR):
        os.makedirs(BASE_INFLUENCER_DIR)
        logging.info("Created influencer base directory: %s", BASE_INFLUENCER_DIR)
    else:
        logging.info("Influencer base directory exists: %s", BASE_INFLUENCER_DIR)

def add_influencer(name, metadata, image_paths):
    """
    Add a new influencer's data.
    :param name: Influencer's name (used as folder name)
    :param metadata: A dictionary containing influencer's metadata (e.g., appearance, bio, etc.)
    :param image_paths: List of paths to image files to be copied to the influencer's folder.
    """
    ensure_influencer_base()
    influencer_folder = os.path.join(BASE_INFLUENCER_DIR, name)
    images_folder = os.path.join(influencer_folder, "images")
    
    if not os.path.exists(influencer_folder):
        os.makedirs(influencer_folder)
        logging.info("Created folder for influencer %s", name)
    if not os.path.exists(images_folder):
        os.makedirs(images_folder)
        logging.info("Created images folder for influencer %s", name)
    
    # Save metadata
    metadata_path = os.path.join(influencer_folder, "metadata.json")
    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=4)
    logging.info("Saved metadata for influencer %s at %s", name, metadata_path)
    
    # Copy images
    for image_path in image_paths:
        if os.path.exists(image_path):
            dest_path = os.path.join(images_folder, os.path.basename(image_path))
            shutil.copy(image_path, dest_path)
            logging.info("Copied image %s to %s", image_path, dest_path)
        else:
            logging.warning("Image path %s does not exist.", image_path)

def get_influencer(name):
    """
    Retrieve the metadata and image list for a given influencer.
    :param name: Influencer's name.
    :return: Dictionary with metadata and list of image paths.
    """
    influencer_folder = os.path.join(BASE_INFLUENCER_DIR, name)
    metadata_path = os.path.join(influencer_folder, "metadata.json")
    images_folder = os.path.join(influencer_folder, "images")
    
    if not os.path.exists(metadata_path):
        logging.error("Metadata for influencer %s not found.", name)
        return None

    with open(metadata_path, "r") as f:
        metadata = json.load(f)
    image_files = []
    if os.path.exists(images_folder):
        for file in os.listdir(images_folder):
            if file.endswith(".png") or file.endswith(".jpg"):
                image_files.append(os.path.join(images_folder, file))
    else:
        logging.warning("Images folder for influencer %s does not exist.", name)
    
    logging.info("Loaded data for influencer %s", name)
    return {"metadata": metadata, "images": image_files}

def list_influencers():
    """
    List all influencers stored in the base directory.
    :return: List of influencer names.
    """
    ensure_influencer_base()
    influencers = [name for name in os.listdir(BASE_INFLUENCER_DIR) if os.path.isdir(os.path.join(BASE_INFLUENCER_DIR, name))]
    logging.info("Found %d influencers.", len(influencers))
    return influencers

if __name__ == "__main__":
    # Example usage:
    influencer_name = "Influencer_Alice"
    metadata = {
        "appearance": "white, slim, blue eyes, blonde hair",
        "bio": "Lifestyle influencer focusing on technology and fashion.",
        "traits": ["energetic", "modern", "confident"]
    }
    # Replace these paths with your actual image paths for testing
    image_paths = [
        "/Users/vanshshah/Desktop/OWLmarketing/sample_images/alice1.png",
        "/Users/vanshshah/Desktop/OWLmarketing/sample_images/alice2.jpg"
    ]
    add_influencer(influencer_name, metadata, image_paths)
    
    data = get_influencer(influencer_name)
    print("Influencer Data:", data)
    
    influencers = list_influencers()
    print("All influencers:", influencers)
