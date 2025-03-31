#!/usr/bin/env python3
"""
App UI Setup Script

This script guides users through the process of adding Optimal AI app UI assets
for accurate demo generation. It helps organize screenshots, recordings, and brand assets.
"""

import os
import sys
import json
import shutil
import logging
from pathlib import Path
import argparse
from typing import List, Dict

# Add parent directory to path to import modules
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(project_root)

# Import UI manager
from video_generation.app_ui_manager import AppUIManager, get_ui_manager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('setup_app_ui')

def create_directory_structure():
    """Create the directory structure for app UI assets."""
    logger.info("Creating directory structure for app UI assets...")
    
    # Create directories
    dirs = [
        Path(project_root) / "assets" / "app_ui" / "screenshots",
        Path(project_root) / "assets" / "app_ui" / "recordings",
        Path(project_root) / "assets" / "app_ui" / "brand"
    ]
    
    for directory in dirs:
        directory.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created directory: {directory}")
    
    logger.info("Directory structure created successfully!")

def print_section(title: str):
    """Print a section title."""
    print("\n" + "=" * 50)
    print(f"{title}")
    print("=" * 50 + "\n")

def list_files_in_directory(directory: Path) -> List[str]:
    """List files in a directory."""
    if not directory.exists():
        return []
    
    return [f.name for f in directory.iterdir() if f.is_file()]

def setup_screenshots(ui_manager: AppUIManager):
    """Guide the user through setting up screenshots."""
    print_section("SCREENSHOTS SETUP")
    print("To create accurate demos, we need screenshots of key app screens.")
    print("Screenshots should be high resolution and show clear UI elements.")
    
    # Show current screenshots if any
    screenshots_dir = ui_manager.screenshots_dir
    existing_screenshots = list_files_in_directory(screenshots_dir)
    
    if existing_screenshots:
        print(f"\nCurrent screenshots ({len(existing_screenshots)}):")
        for i, screenshot in enumerate(existing_screenshots, 1):
            print(f"  {i}. {screenshot}")
    else:
        print("\nNo screenshots have been added yet.")
    
    print("\nTo add screenshots:")
    print("1. Copy your screenshots to:")
    print(f"   {screenshots_dir}")
    print("2. Then run:")
    print("   python scripts/setup_app_ui.py --map-screenshots")

def setup_recordings(ui_manager: AppUIManager):
    """Guide the user through setting up recordings."""
    print_section("RECORDINGS SETUP")
    print("To create dynamic demos, we need screen recordings of key app interactions.")
    print("Recordings should be clear, focused, and show the app's features in action.")
    
    # Show current recordings if any
    recordings_dir = ui_manager.recordings_dir
    existing_recordings = list_files_in_directory(recordings_dir)
    
    if existing_recordings:
        print(f"\nCurrent recordings ({len(existing_recordings)}):")
        for i, recording in enumerate(existing_recordings, 1):
            print(f"  {i}. {recording}")
    else:
        print("\nNo recordings have been added yet.")
    
    print("\nTo add recordings:")
    print("1. Copy your screen recordings to:")
    print(f"   {recordings_dir}")
    print("2. Then run:")
    print("   python scripts/setup_app_ui.py --map-recordings")

def setup_brand_assets(ui_manager: AppUIManager):
    """Guide the user through setting up brand assets."""
    print_section("BRAND ASSETS SETUP")
    print("Brand assets help ensure consistent visual identity in generated videos.")
    
    # Show current brand assets if any
    brand_dir = ui_manager.brand_dir
    existing_assets = list_files_in_directory(brand_dir)
    
    if existing_assets:
        print(f"\nCurrent brand assets ({len(existing_assets)}):")
        for i, asset in enumerate(existing_assets, 1):
            print(f"  {i}. {asset}")
    else:
        print("\nNo brand assets have been added yet.")
    
    print("\nRequired brand assets:")
    print("  - logo.png: The Optimal AI logo (transparent background recommended)")
    print("  - app_icon.png: The app icon used on devices")
    
    print("\nTo add brand assets:")
    print("1. Copy your brand assets to:")
    print(f"   {brand_dir}")
    print("2. Ensure they are named appropriately (logo.png, app_icon.png)")
    print("3. Then run:")
    print("   python scripts/setup_app_ui.py --validate")

def map_screenshots(ui_manager: AppUIManager):
    """Interactive tool to map screenshots to features and screens."""
    print_section("MAP SCREENSHOTS")
    print("Let's map your screenshots to app features and screens.")
    
    screenshots_dir = ui_manager.screenshots_dir
    screenshots = list_files_in_directory(screenshots_dir)
    
    if not screenshots:
        print("No screenshots found. Please add screenshots first.")
        return
    
    print(f"\nFound {len(screenshots)} screenshots:")
    for i, screenshot in enumerate(screenshots, 1):
        print(f"  {i}. {screenshot}")
    
    # Load UI mapping
    ui_mapping = ui_manager.ui_mapping
    
    # Features and screens from mapping
    features = [f["name"] for f in ui_mapping.get("features", [])]
    screens = [s["name"] for s in ui_mapping.get("screens", [])]
    
    print("\nAvailable features:")
    for i, feature in enumerate(features, 1):
        print(f"  {i}. {feature}")
    
    print("\nAvailable screens:")
    for i, screen in enumerate(screens, 1):
        print(f"  {i}. {screen}")
    
    # Map each screenshot
    print("\nFor each screenshot, enter the feature and screen numbers it belongs to.")
    print("You can enter multiple values separated by commas, or leave blank if not applicable.")
    
    for screenshot in screenshots:
        print(f"\nScreenshot: {screenshot}")
        
        # Get feature mapping
        feature_input = input("Feature numbers (comma-separated, or blank): ")
        feature_indices = []
        if feature_input.strip():
            try:
                feature_indices = [int(idx.strip()) - 1 for idx in feature_input.split(",")]
            except ValueError:
                print("Invalid input. Using no features.")
                feature_indices = []
        
        # Get screen mapping
        screen_input = input("Screen numbers (comma-separated, or blank): ")
        screen_indices = []
        if screen_input.strip():
            try:
                screen_indices = [int(idx.strip()) - 1 for idx in screen_input.split(",")]
            except ValueError:
                print("Invalid input. Using no screens.")
                screen_indices = []
        
        # Update the mapping
        for idx in feature_indices:
            if 0 <= idx < len(features):
                for feature in ui_mapping["features"]:
                    if feature["name"] == features[idx]:
                        if screenshot not in feature["screenshots"]:
                            feature["screenshots"].append(screenshot)
                            print(f"Added {screenshot} to feature: {features[idx]}")
        
        for idx in screen_indices:
            if 0 <= idx < len(screens):
                for screen in ui_mapping["screens"]:
                    if screen["name"] == screens[idx]:
                        if screenshot not in screen["screenshots"]:
                            screen["screenshots"].append(screenshot)
                            print(f"Added {screenshot} to screen: {screens[idx]}")
    
    # Save the updated mapping
    ui_manager._save_ui_mapping()
    print("\nScreenshot mapping completed and saved!")

def map_recordings(ui_manager: AppUIManager):
    """Interactive tool to map recordings to features and demo sequences."""
    print_section("MAP RECORDINGS")
    print("Let's map your recordings to app features and demo sequences.")
    
    recordings_dir = ui_manager.recordings_dir
    recordings = list_files_in_directory(recordings_dir)
    
    if not recordings:
        print("No recordings found. Please add recordings first.")
        return
    
    print(f"\nFound {len(recordings)} recordings:")
    for i, recording in enumerate(recordings, 1):
        print(f"  {i}. {recording}")
    
    # Load UI mapping
    ui_mapping = ui_manager.ui_mapping
    
    # Features and demo sequences from mapping
    features = [f["name"] for f in ui_mapping.get("features", [])]
    sequences = [s["name"] for s in ui_mapping.get("demo_sequences", [])]
    
    print("\nAvailable features:")
    for i, feature in enumerate(features, 1):
        print(f"  {i}. {feature}")
    
    print("\nAvailable demo sequences:")
    for i, sequence in enumerate(sequences, 1):
        print(f"  {i}. {sequence}")
    
    # Map each recording
    print("\nFor each recording, enter the feature and sequence numbers it belongs to.")
    print("For features, you can enter multiple values separated by commas.")
    print("For sequences, enter a single number or leave blank.")
    
    for recording in recordings:
        print(f"\nRecording: {recording}")
        
        # Get feature mapping
        feature_input = input("Feature numbers (comma-separated, or blank): ")
        feature_indices = []
        if feature_input.strip():
            try:
                feature_indices = [int(idx.strip()) - 1 for idx in feature_input.split(",")]
            except ValueError:
                print("Invalid input. Using no features.")
                feature_indices = []
        
        # Get sequence mapping
        sequence_input = input("Sequence number (single number, or blank): ")
        sequence_idx = None
        if sequence_input.strip():
            try:
                sequence_idx = int(sequence_input.strip()) - 1
            except ValueError:
                print("Invalid input. Using no sequence.")
                sequence_idx = None
        
        # Get duration if mapping to a sequence
        duration = None
        if sequence_idx is not None:
            duration_input = input("Duration in seconds (default is 4.0): ")
            if duration_input.strip():
                try:
                    duration = float(duration_input.strip())
                except ValueError:
                    print("Invalid input. Using default duration.")
                    duration = 4.0
            else:
                duration = 4.0
        
        # Update the mapping
        for idx in feature_indices:
            if 0 <= idx < len(features):
                for feature in ui_mapping["features"]:
                    if feature["name"] == features[idx]:
                        if recording not in feature["recordings"]:
                            feature["recordings"].append(recording)
                            print(f"Added {recording} to feature: {features[idx]}")
        
        if sequence_idx is not None and 0 <= sequence_idx < len(sequences):
            for sequence in ui_mapping["demo_sequences"]:
                if sequence["name"] == sequences[sequence_idx]:
                    sequence["recording"] = recording
                    if duration is not None:
                        sequence["duration"] = duration
                    print(f"Set {recording} as the recording for sequence: {sequences[sequence_idx]}")
    
    # Save the updated mapping
    ui_manager._save_ui_mapping()
    print("\nRecording mapping completed and saved!")

def validate_assets(ui_manager: AppUIManager):
    """Validate that the necessary app UI assets are available."""
    print_section("VALIDATE ASSETS")
    print("Validating app UI assets...")
    
    is_valid = ui_manager.validate_assets()
    
    if is_valid:
        print("\n✅ All necessary app UI assets are available!")
        print("The system is ready to generate accurate demos.")
    else:
        print("\n❌ Some assets are missing.")
        print("Please make sure you have:")
        print("  - Screenshots in assets/app_ui/screenshots/")
        print("  - Recordings in assets/app_ui/recordings/")
        print("  - Brand assets (logo.png, app_icon.png) in assets/app_ui/brand/")
    
    return is_valid

def verify_demo(ui_manager: AppUIManager, feature: str):
    """Create a demo video for a specific feature to verify."""
    print_section(f"VERIFY DEMO: {feature}")
    print(f"Creating a demo video for the '{feature}' feature...")
    
    output_dir = Path(project_root) / "data" / "generated_videos"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_path = str(output_dir / f"{feature}_demo_verification.mp4")
    
    # Create the demo
    result = ui_manager.create_feature_demo(feature, output_path)
    
    if result:
        print(f"\n✅ Demo created successfully: {output_path}")
        print("Please review the video to ensure it accurately represents your app.")
    else:
        print(f"\n❌ Failed to create demo for feature: {feature}")
        print("Make sure you have added appropriate recordings or screenshots for this feature.")

def main():
    """Main function to run the script."""
    parser = argparse.ArgumentParser(description="Set up app UI assets for video generation")
    
    # Command line arguments
    parser.add_argument("--create-dirs", action="store_true", help="Create directory structure")
    parser.add_argument("--map-screenshots", action="store_true", help="Map screenshots to features and screens")
    parser.add_argument("--map-recordings", action="store_true", help="Map recordings to features and demo sequences")
    parser.add_argument("--validate", action="store_true", help="Validate that all necessary assets are available")
    parser.add_argument("--verify", help="Verify demo for a specific feature")
    
    args = parser.parse_args()
    
    # Get UI manager
    ui_manager = get_ui_manager()
    
    # If no arguments provided, show full setup guide
    if not any(vars(args).values()):
        print_section("APP UI SETUP GUIDE")
        print("This script will help you set up app UI assets for accurate demo generation.")
        
        # Step 1: Create directory structure
        create_directory_structure()
        
        # Step 2: Setup screenshots
        setup_screenshots(ui_manager)
        
        # Step 3: Setup recordings
        setup_recordings(ui_manager)
        
        # Step 4: Setup brand assets
        setup_brand_assets(ui_manager)
        
        # Final instructions
        print_section("NEXT STEPS")
        print("1. Add your screenshots, recordings, and brand assets to the directories")
        print("2. Run 'python scripts/setup_app_ui.py --map-screenshots' to map screenshots")
        print("3. Run 'python scripts/setup_app_ui.py --map-recordings' to map recordings")
        print("4. Run 'python scripts/setup_app_ui.py --validate' to validate assets")
        print("5. Run 'python scripts/setup_app_ui.py --verify feature_name' to verify a demo")
        
        return
    
    # Process individual commands
    if args.create_dirs:
        create_directory_structure()
    
    if args.map_screenshots:
        map_screenshots(ui_manager)
    
    if args.map_recordings:
        map_recordings(ui_manager)
    
    if args.validate:
        validate_assets(ui_manager)
    
    if args.verify:
        verify_demo(ui_manager, args.verify)

if __name__ == "__main__":
    main() 