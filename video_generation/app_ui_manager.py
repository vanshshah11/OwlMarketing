#!/usr/bin/env python3
"""
App UI Manager: Handles the management and integration of Optimal AI app UI assets
for video generation. This ensures that only authentic app UI is used in demos.

Enhanced with dynamic UI generation capabilities for creating realistic app demonstrations
with contextual awareness of the video content.
"""

import os
import json
import random
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Union
import shutil
import subprocess
import tempfile
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import math

# Local imports
from .ui_generator import get_ui_generator, FoodItem
from .video_demo_generator import get_demo_generator, VideoDemoSequence

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('app_ui_manager')

# Get project root directory
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

class AppUIManager:
    """
    Manages app UI assets for use in video generation.
    
    This class:
    - Loads and validates app UI assets (screenshots, recordings)
    - Provides access to assets for video generation
    - Ensures only authentic app UI is used in demos
    - Dynamically generates UI screens and sequences for realistic app demos
    """
    
    def __init__(self, ui_generator=None, pattern_learner=None, base_dir: str = None):
        self.logger = logging.getLogger(__name__)
        self._base_dir = base_dir or os.getcwd()
        self._ui_mapping = self._load_ui_mapping()
        self._ui_generator = ui_generator  # Lazy loaded
        self._pattern_learner = pattern_learner  # Lazy loaded
        self._config = self._load_ui_config()
        self.assets_validated = False
        
        # Add paths for app UI assets
        self.screenshots_dir = os.path.join(self._base_dir, 'assets', 'app_ui', 'screenshots')
        self.recordings_dir = os.path.join(self._base_dir, 'assets', 'app_ui', 'recordings')
        self.brand_dir = os.path.join(self._base_dir, 'assets', 'app_ui', 'brand')
        
        # Define app theme colors from theme.js
        self.theme = {
            'colors': {
                'background': {
                    'primary': {
                        'light': '#EBE9E8',
                        'dark': '#1C1C1E'
                    }
                },
                'text': {
                    'primary': {
                        'light': '#000000',
                        'dark': '#FFFFFF'
                    }
                },
                'macro': {
                    'protein': '#FF3B30',  # RED
                    'carbs': '#FF9500',    # ORANGE
                    'fat': '#5AC8FA'       # BLUE
                }
            },
            'borderRadius': {
                'medium': 12,
                'small': 8
            },
            'spacing': {
                's': 8,
                'm': 16,
                'l': 24
            }
        }
        
        # Load logo for branding
        self.logo_path = os.path.join(self.brand_dir, 'OptimalAI_logo.png')
        
    @property
    def ui_generator(self):
        """Lazy loading of UI generator."""
        if self._ui_generator is None:
            from video_generation.ui_generator import UIGenerator
            self._ui_generator = UIGenerator(self._pattern_learner)
        return self._ui_generator
    
    @property
    def pattern_learner(self):
        """Lazy loading of pattern learner."""
        if self._pattern_learner is None:
            try:
                from video_generation.ui_pattern_learner import UIPatternLearner
                self._pattern_learner = UIPatternLearner()
            except ImportError:
                self.logger.warning("UIPatternLearner not available.")
        return self._pattern_learner
        
    def _load_ui_config(self) -> Dict:
        """Load UI configuration from config file."""
        config_path = os.path.join('config', 'app_ui_config.json')
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
                self.logger.info(f"Loaded UI configuration from {config_path}")
                return config
        except (FileNotFoundError, json.JSONDecodeError) as e:
            self.logger.warning(f"Failed to load UI config: {e}")
            return {}
    
    def _load_ui_mapping(self) -> Dict:
        """Load the UI mapping from a JSON file."""
        # First try the config directory
        mapping_file = os.path.join('config', 'app_ui_mapping.json')
        if os.path.exists(mapping_file):
            try:
                with open(mapping_file, 'r') as f:
                    mapping = json.load(f)
                self.logger.info(f"Loaded UI mapping from {mapping_file}")
                return mapping
            except json.JSONDecodeError:
                self.logger.warning(f"Invalid JSON in {mapping_file}")
        
        # As a fallback, try the old path
        mapping_file = os.path.join(self._base_dir, 'assets', 'app_ui', 'ui_mapping.json')
        if os.path.exists(mapping_file):
            try:
                with open(mapping_file, 'r') as f:
                    mapping = json.load(f)
                self.logger.info(f"Loaded UI mapping from {mapping_file}")
                return mapping
            except json.JSONDecodeError:
                self.logger.warning(f"Invalid JSON in {mapping_file}")
        
        # Default mapping if file doesn't exist or is invalid
        self.logger.warning("No UI mapping file found, using default mapping")
        default_mapping = {
            'screenshots': {
                'home': 'home_screen.png',
                'camera': 'camera_screen.png',
                'results': 'results_screen.png',
                'food_log': 'food_log_screen.png'
            },
            'recordings': {
                'scan_food': 'scan_food_demo.mp4',
                'view_results': 'view_results_demo.mp4',
                'add_to_log': 'add_to_log_demo.mp4'
            },
            'food_items': {},
            'features': {
                'scan_food': {
                    'screens': ['camera', 'results'],
                    'recordings': ['scan_food'],
                    'food_items': []
                },
                'view_details': {
                    'screens': ['results'],
                    'recordings': ['view_results'],
                    'food_items': []
                },
                'log_meal': {
                    'screens': ['results', 'food_log'],
                    'recordings': ['add_to_log'],
                    'food_items': []
                }
            }
        }
        return default_mapping
    
    def _save_ui_mapping(self):
        """Save the UI mapping to a JSON file."""
        mapping_file = os.path.join(self._base_dir, 'assets', 'app_ui', 'ui_mapping.json')
        os.makedirs(os.path.dirname(mapping_file), exist_ok=True)
        with open(mapping_file, 'w') as f:
            json.dump(self._ui_mapping, f, indent=2)
        self.logger.info(f"Saved UI mapping to {mapping_file}")
    
    def get_screenshot_path(self, screen_type: str, variant: str = None, food_item: Dict = None) -> str:
        """
        Get the path to a UI screenshot by type.
        Will generate a dynamic screenshot if no static one exists.
        
        Args:
            screen_type: Type of screen (e.g., 'home_screen', 'camera_interface')
            variant: Optional variant (e.g., 'before_scan', 'after_scan')
            food_item: Optional food item to include in the screenshot
            
        Returns:
            Path to the screenshot
        """
        # First check if we have a specific screenshot for this screen type and variant in screens section
        for screen in self._ui_mapping.get('screens', []):
            if screen['name'] == screen_type:
                screenshots = screen.get('screenshots', [])
                if screenshots:
                    # If we have a food item, try to find a specific screenshot for it
                    if food_item and 'name' in food_item:
                        food_name = food_item['name'].lower()
                        for screenshot in screenshots:
                            if food_name in screenshot.lower():
                                self.logger.info(f"Using food-specific screenshot: {screenshot}")
                                return screenshot
                    
                    # No specific food item screenshot found, use the first one
                    self.logger.info(f"Using generic screenshot for {screen_type}: {screenshots[0]}")
                    return screenshots[0]
        
        # If we get here, no screenshot was found in the screens section
        # Try looking in the features section as a fallback
        for feature in self._ui_mapping.get('features', []):
            if feature['name'] == 'real_time_calorie_tracking':  # We only care about this feature
                screenshots = feature.get('screenshots', [])
                for screenshot in screenshots:
                    if screen_type.replace('_', '') in screenshot.lower():
                        if food_item and 'name' in food_item:
                            food_name = food_item['name'].lower()
                            if food_name in screenshot.lower():
                                self.logger.info(f"Using food-specific feature screenshot: {screenshot}")
                                return screenshot
                        elif variant:
                            if variant.lower() in screenshot.lower():
                                self.logger.info(f"Using variant-specific feature screenshot: {screenshot}")
                                return screenshot
                
                # No specific match, just return the first one of the right type
                for screenshot in screenshots:
                    if screen_type.replace('_', '') in screenshot.lower():
                        self.logger.info(f"Using generic feature screenshot: {screenshot}")
                        return screenshot
        
        # No static screenshot found, generate a dynamic one
        self.logger.info(f"No static screenshot found for {screen_type}, generating dynamically")
        return self._generate_dynamic_screenshot(screen_type, food_item)
    
    def get_recording_path(self, demo_type: str, food_item: Dict = None) -> str:
        """
        Get the path to a UI recording/demo by type.
        Will generate a dynamic recording if no static one exists.
        
        Args:
            demo_type: Type of demo (e.g., 'quick_scan_pizza', 'quick_scan_salad')
            food_item: Optional food item to include in the demo
            
        Returns:
            Path to the recording
        """
        # First check if we have a specific recording for this demo type in demo_sequences
        for sequence in self._ui_mapping.get('demo_sequences', []):
            if sequence['name'] == demo_type:
                if sequence.get('recording'):
                    self.logger.info(f"Using demo sequence recording: {sequence['recording']}")
                    return sequence['recording']
        
        # If we get here, try to find a recording in the features section
        for feature in self._ui_mapping.get('features', []):
            if feature['name'] == 'real_time_calorie_tracking':  # We only care about this feature
                recordings = feature.get('recordings', [])
                
                # If we have a specific food item, look for it
                if food_item and 'name' in food_item:
                    food_name = food_item['name'].lower()
                    for recording in recordings:
                        if food_name in recording.lower():
                            self.logger.info(f"Using food-specific feature recording: {recording}")
                            return recording
                
                # No specific food match, check if demo_type has a food type in it
                for recording in recordings:
                    # Extract the food type from demo_type (e.g., quick_scan_pizza -> pizza)
                    parts = demo_type.split('_')
                    if len(parts) > 2:
                        potential_food = parts[-1].lower()
                        if potential_food in recording.lower():
                            self.logger.info(f"Using demo-type-matched recording: {recording}")
                            return recording
                
                # No specific match, just return the first recording
                if recordings:
                    self.logger.info(f"Using first available feature recording: {recordings[0]}")
                    return recordings[0]
        
        # No static recording found, generate a dynamic one
        self.logger.info(f"No static recording found for {demo_type}, generating dynamically")
        return self._generate_dynamic_recording(demo_type, food_item)
    
    def get_screens_for_feature(self, feature: str) -> List[str]:
        """Get all screen types needed for a feature."""
        if feature in self._ui_mapping.get('features', {}):
            return self._ui_mapping['features'][feature].get('screens', [])
        return []
    
    def get_recordings_for_feature(self, feature: str) -> List[str]:
        """Get all recording types needed for a feature."""
        if feature in self._ui_mapping.get('features', {}):
            return self._ui_mapping['features'][feature].get('recordings', [])
        return []
    
    def get_food_items_for_feature(self, feature: str) -> List[Dict]:
        """Get all food items associated with a feature."""
        if feature in self._ui_mapping.get('features', {}):
            food_names = self._ui_mapping['features'][feature].get('food_items', [])
            return [self._get_food_item_by_name(name) for name in food_names]
        return []
    
    def _get_food_item_by_name(self, name: str) -> Dict:
        """Get a food item by name from the config or defaults."""
        # Try to get from config
        for item in self._config.get('common_food_items', []):
            if item.get('name', '').lower() == name.lower():
                return item
        
        # Return a default food item
        return {
            "name": name,
            "calories": random.randint(200, 500),
            "protein": random.randint(10, 30),
            "carbs": random.randint(10, 50),
            "fat": random.randint(5, 20)
        }
    
    def add_screenshot(self, screen_type: str, path: str, food_item: Dict = None):
        """Add a screenshot to the UI mapping."""
        # Ensure the path is relative to the assets directory
        if path.startswith(self._base_dir):
            path = os.path.relpath(path, os.path.join(self._base_dir, 'assets', 'app_ui', 'screenshots'))
        
        if food_item and 'name' in food_item:
            # Add food-specific screenshot
            food_name = food_item['name'].lower().replace(' ', '_')
            if 'food_items' not in self._ui_mapping:
                self._ui_mapping['food_items'] = {}
            if food_name not in self._ui_mapping['food_items']:
                self._ui_mapping['food_items'][food_name] = {'screenshots': {}, 'recordings': {}}
            self._ui_mapping['food_items'][food_name]['screenshots'][screen_type] = path
        else:
            # Add general screenshot
            if 'screenshots' not in self._ui_mapping:
                self._ui_mapping['screenshots'] = {}
            self._ui_mapping['screenshots'][screen_type] = path
        
        self._save_ui_mapping()
    
    def add_recording(self, demo_type: str, path: str, food_item: Dict = None):
        """Add a recording to the UI mapping."""
        # Ensure the path is relative to the assets directory
        if path.startswith(self._base_dir):
            path = os.path.relpath(path, os.path.join(self._base_dir, 'assets', 'app_ui', 'recordings'))
        
        if food_item and 'name' in food_item:
            # Add food-specific recording
            food_name = food_item['name'].lower().replace(' ', '_')
            if 'food_items' not in self._ui_mapping:
                self._ui_mapping['food_items'] = {}
            if food_name not in self._ui_mapping['food_items']:
                self._ui_mapping['food_items'][food_name] = {'screenshots': {}, 'recordings': {}}
            self._ui_mapping['food_items'][food_name]['recordings'][demo_type] = path
        else:
            # Add general recording
            if 'recordings' not in self._ui_mapping:
                self._ui_mapping['recordings'] = {}
            self._ui_mapping['recordings'][demo_type] = path
        
        self._save_ui_mapping()
    
    def add_food_item_to_feature(self, feature: str, food_item: Dict):
        """Associate a food item with a feature."""
        if feature not in self._ui_mapping.get('features', {}):
            self.logger.warning(f"Feature '{feature}' not found in UI mapping")
            return
        
        food_name = food_item['name'].lower().replace(' ', '_')
        
        # Add to food items if not already there
        if 'food_items' not in self._ui_mapping:
            self._ui_mapping['food_items'] = {}
        if food_name not in self._ui_mapping['food_items']:
            self._ui_mapping['food_items'][food_name] = {
                'name': food_item['name'],
                'calories': food_item.get('calories', 0),
                'screenshots': {},
                'recordings': {}
            }
        
        # Add to feature's food items if not already there
        if 'food_items' not in self._ui_mapping['features'][feature]:
            self._ui_mapping['features'][feature]['food_items'] = []
        if food_name not in self._ui_mapping['features'][feature]['food_items']:
            self._ui_mapping['features'][feature]['food_items'].append(food_name)
        
        self._save_ui_mapping()
    
    def _generate_dynamic_screenshot(self, screen_type: str, food_item: Dict = None) -> str:
        """Generate a dynamic screenshot using the UI generator."""
        if self.ui_generator is None:
            self.logger.error("No UI generator available for dynamic screenshot generation")
            # Return a placeholder or default image
            return os.path.join(self._base_dir, 'assets', 'app_ui', 'default_screen.png')
        
        # Map app_ui_manager screen types to ui_generator screen types
        screen_type_mapping = {
            'home': 'home_screen',
            'camera': 'camera_interface',
            'results': 'results_screen',
            'food_log': 'food_log'
        }
        
        generator_screen_type = screen_type_mapping.get(screen_type, screen_type)
        
        # Define output path
        os.makedirs(os.path.join(self._base_dir, 'assets', 'app_ui', 'screenshots', 'generated'), exist_ok=True)
        
        if food_item and 'name' in food_item:
            food_name = food_item['name'].lower().replace(' ', '_')
            output_filename = f"{generator_screen_type}_{food_name}_generated.png"
        else:
            output_filename = f"{generator_screen_type}_generated.png"
        
        output_path = os.path.join(self._base_dir, 'assets', 'app_ui', 'screenshots', 'generated', output_filename)
        
        # Generate the screenshot
        self.ui_generator.generate_ui_screen(generator_screen_type, food_item, output_path)
        
        # Add to mapping
        self.add_screenshot(screen_type, os.path.join('generated', output_filename), food_item)
        
        return output_path
    
    def _generate_dynamic_recording(self, demo_type: str, food_item: Dict = None) -> str:
        """Generate a dynamic recording/demo using the Video Demo Generator."""
        from video_generation.video_demo_generator import VideoDemoGenerator
        
        # Map app_ui_manager demo types to sequence names
        sequence_mapping = {
            'scan_food': 'scan_to_result',
            'view_results': 'browse_food_log',
            'add_to_log': 'result_to_log'
        }
        
        sequence_name = sequence_mapping.get(demo_type, demo_type)
        
        # Define output directory
        os.makedirs(os.path.join(self._base_dir, 'assets', 'app_ui', 'recordings', 'generated'), exist_ok=True)
        
        if food_item and 'name' in food_item:
            food_name = food_item['name'].lower().replace(' ', '_')
            output_dir = os.path.join(self._base_dir, 'assets', 'app_ui', 'recordings', 'generated', f"{sequence_name}_{food_name}")
            output_filename = f"{sequence_name}_{food_name}_generated.mp4"
        else:
            output_dir = os.path.join(self._base_dir, 'assets', 'app_ui', 'recordings', 'generated', sequence_name)
            output_filename = f"{sequence_name}_generated.mp4"
        
        output_path = os.path.join(self._base_dir, 'assets', 'app_ui', 'recordings', 'generated', output_filename)
        
        # Generate the demo sequence
        demo_generator = VideoDemoGenerator(self.ui_generator)
        demo_generator.generate_demo_sequence(sequence_name, food_item, output_dir, output_path)
        
        # Add to mapping
        self.add_recording(demo_type, os.path.join('generated', output_filename), food_item)
        
        return output_path
    
    def validate_assets(self, required_features: List[str] = None) -> bool:
        """
        Validate that all required assets exist or can be generated.
        
        Args:
            required_features: List of features that need assets
            
        Returns:
            bool: True if all assets are valid, False otherwise
        """
        if required_features is None:
            required_features = ["food scanning", "meal tracking"]
        
        valid = True
        
        # Check for required screenshots
        for feature in required_features:
            screens = self.get_screens_for_feature(feature)
            
            for screen in screens:
                # Check if screenshot paths exist or can be dynamically generated
                path = self.get_screenshot_path(screen)
                if path is None:
                    self.logger.warning(f"Missing screenshot: {screen}")
                    valid = False
        
        # Check for required recordings
        for feature in required_features:
            recordings = self.get_recordings_for_feature(feature)
            
            for recording in recordings:
                # Check if recording paths exist or can be dynamically generated
                path = self.get_recording_path(recording)
                if path is None:
                    self.logger.warning(f"Missing recording: {recording}")
                    valid = False
        
        self.assets_validated = valid
        return valid

    def create_feature_demo(self, feature: str, output_path: str, food_item: Dict = None, duration: float = 6.0) -> str:
        """
        Create an accurate feature demo video focusing on real-time tracking.
        
        Args:
            feature: Feature to demonstrate (always defaults to real-time tracking)
            output_path: Path to save the demo video
            food_item: Food item to scan
            duration: Total duration of the demo (5-7 seconds)
            
        Returns:
            Path to the created demo video
        """
        # Always use real-time tracking feature
        feature = "realtime_tracking"
        
        # Set default food item if not provided
        if not food_item:
            food_item = {
                "name": "Avocado Toast",
                "calories": 350,
                "protein": 12, 
                "carbs": 38,
                "fat": 18
            }
        
        # Calculate exact timings for a concise demo
        # Adjusted timings based on analysis of real recordings
        home_duration = 0.8  # Brief glimpse of home screen
        camera_duration = 1.8  # 1.8 seconds on camera screen
        loading_duration = 0.7  # 0.7 seconds loading - increased for visibility
        results_duration = duration - home_duration - camera_duration - loading_duration  # Remaining time for results
        
        # Find relevant UI assets (prioritize existing recordings)
        recording_path = None
        for recording in os.listdir(self.recordings_dir):
            if feature in recording.lower() and food_item["name"].lower().replace(" ", "_") in recording.lower():
                recording_path = os.path.join(self.recordings_dir, recording)
                break
        
        # If no exact match, use any real-time tracking recording
        if not recording_path:
            for recording in os.listdir(self.recordings_dir):
                if feature in recording.lower():
                    recording_path = os.path.join(self.recordings_dir, recording)
                    break
        
        if recording_path and os.path.exists(recording_path):
            self.logger.info(f"Using existing recording: {recording_path}")
            # Process existing recording to match desired duration
            return self._trim_recording(recording_path, output_path, duration)
        
        # If no recording available, create accurate UI sequence
        self.logger.info(f"Creating accurate UI sequence for {feature} with {food_item['name']}")
        
        # Get screenshots for each screen in the sequence (including home screen)
        home_screenshot = self._get_home_screenshot(food_item, before_scan=True) 
        camera_screenshot = self._get_camera_screenshot(food_item)
        results_screenshot = self._get_results_screenshot(food_item)
        
        # Create demo sequence with proper transitions and animations
        sequence = [
            {"type": "home", "image": home_screenshot, "duration": home_duration,
             "animations": [
                 {"type": "tap_button", "start": 0.2, "duration": 0.2, "target": "scan_button"}
             ]},
            {"type": "camera", "image": camera_screenshot, "duration": camera_duration,
             "animations": [
                 {"type": "scan_guide", "start": 0.3, "duration": 0.6},
                 {"type": "flash", "start": camera_duration - 0.4, "duration": 0.2}
             ]},
            {"type": "loading", "duration": loading_duration,
             "animations": [
                 {"type": "pulse", "start": 0.1, "duration": loading_duration - 0.2}
             ]},
            {"type": "results", "image": results_screenshot, "duration": results_duration,
             "animations": [
                 {"type": "calorie_count", "start": 0.2, "duration": 0.6},
                 {"type": "protein_bar", "start": 0.4, "duration": 0.6},
                 {"type": "carbs_bar", "start": 0.6, "duration": 0.6},
                 {"type": "fat_bar", "start": 0.8, "duration": 0.6},
                 {"type": "success_indicator", "start": results_duration - 0.8, "duration": 0.5}
             ]}
        ]
        
        # Generate the UI sequence
        return self._generate_ui_sequence(sequence, output_path, food_item)

    def _get_home_screenshot(self, food_item: Dict, before_scan: bool = True) -> str:
        """Get a home screen screenshot."""
        # Search for a matching home screenshot
        if before_scan:
            home_path = os.path.join(self.screenshots_dir, "home_beforelog", "home_nothing_logged.PNG")
        else:
            # Try to find a matching food item
            food_name = food_item["name"].lower()
            for file in os.listdir(os.path.join(self.screenshots_dir, "home_afterlog")):
                if food_name in file.lower():
                    home_path = os.path.join(self.screenshots_dir, "home_afterlog", file)
                    break
            else:
                # Default to first available
                home_files = list(Path(os.path.join(self.screenshots_dir, "home_afterlog")).glob("*.PNG"))
                if home_files:
                    home_path = str(home_files[0])
                else:
                    # Fallback if no files found
                    home_path = os.path.join(self.screenshots_dir, "home_beforelog", "home_nothing_logged.PNG")
        
        return home_path

    def _get_camera_screenshot(self, food_item: Dict) -> str:
        """Get the most appropriate camera screenshot for the food item."""
        # Look for exact match
        food_name = food_item["name"].lower().replace(" ", "_")
        camera_dir = os.path.join(self.screenshots_dir, "camera")
        
        for file in os.listdir(camera_dir):
            if food_name in file.lower() and file.endswith((".png", ".PNG")):
                return os.path.join(camera_dir, file)
        
        # Fallback to any food camera screenshot
        for file in os.listdir(camera_dir):
            if "scan" in file.lower() and not "blank" in file.lower() and file.endswith((".png", ".PNG")):
                return os.path.join(camera_dir, file)
        
        # Ultimate fallback to blank camera
        return os.path.join(camera_dir, "camera_scan_blank.PNG")
    
    def _get_results_screenshot(self, food_item: Dict) -> str:
        """Get the most appropriate results screenshot for the food item."""
        # Look for exact match
        food_name = food_item["name"].lower().replace(" ", "_")
        results_dir = os.path.join(self.screenshots_dir, "results")
        
        for file in os.listdir(results_dir):
            if food_name in file.lower() and file.endswith((".png", ".PNG")):
                return os.path.join(results_dir, file)
        
        # Fallback to any results screenshot
        if os.listdir(results_dir):
            return os.path.join(results_dir, os.listdir(results_dir)[0])
        
        # Should never reach here if assets are properly set up
        self.logger.warning("No results screenshots found, will generate dynamically")
        return None
    
    def _generate_ui_sequence(self, sequence: List[Dict], output_path: str, food_item: Dict) -> str:
        """Generate a video sequence with accurate UI overlays."""
        # Create temporary directory for frames
        temp_dir = tempfile.mkdtemp()
        fps = 30  # Standard FPS for smooth playback
        
        try:
            frame_paths = []
            frame_count = 0
            
            # Generate frames for each sequence item
            current_time = 0
            previous_image = None
            
            for item in sequence:
                item_frames = int(item["duration"] * fps)
                
                if item["type"] == "home":
                    # Home screen UI frames
                    for i in range(item_frames):
                        progress = i / item_frames
                        frame_path = os.path.join(temp_dir, f"frame_{frame_count:04d}.png")
                        
                        # Get animation states
                        active_animations = {}
                        for anim in item.get("animations", []):
                            anim_start = item["duration"] * anim["start"] / item["duration"]
                            anim_end = anim_start + anim["duration"]
                            frame_time = item["duration"] * (i / item_frames)
                            
                            if anim_start <= frame_time <= anim_end:
                                # Calculate animation progress (0 to 1)
                                anim_progress = (frame_time - anim_start) / anim["duration"]
                                active_animations[anim["type"]] = min(1.0, anim_progress)
                        
                        # Use PIL to create a frame from the screenshot
                        self._create_home_frame(item["image"], frame_path, progress, active_animations)
                        frame_paths.append(frame_path)
                        frame_count += 1
                        previous_image = item["image"]
                
                elif item["type"] == "camera":
                    # Camera UI frames
                    for i in range(item_frames):
                        progress = i / item_frames
                        frame_path = os.path.join(temp_dir, f"frame_{frame_count:04d}.png")
                        
                        # Get animation states
                        active_animations = {}
                        for anim in item.get("animations", []):
                            anim_start = item["duration"] * anim["start"] / item["duration"]
                            anim_end = anim_start + anim["duration"]
                            frame_time = item["duration"] * (i / item_frames)
                            
                            if anim_start <= frame_time <= anim_end:
                                # Calculate animation progress (0 to 1)
                                anim_progress = (frame_time - anim_start) / anim["duration"]
                                active_animations[anim["type"]] = min(1.0, anim_progress)
                        
                        # For the first few frames, blend from home to camera for smooth transition
                        if previous_image and i < fps * 0.2:  # 0.2 seconds transition
                            blend_ratio = i / (fps * 0.2)
                            self._create_transition_frame(previous_image, item["image"], frame_path, blend_ratio)
                        else:
                            self._create_camera_frame(item["image"], frame_path, progress, active_animations)
                        
                        frame_paths.append(frame_path)
                        frame_count += 1
                        previous_image = item["image"]
                
                elif item["type"] == "loading":
                    # Loading indicator frames 
                    for i in range(item_frames):
                        progress = i / item_frames
                        frame_path = os.path.join(temp_dir, f"frame_{frame_count:04d}.png")
                        
                        # Get animation states
                        active_animations = {}
                        for anim in item.get("animations", []):
                            anim_start = item["duration"] * anim["start"] / item["duration"]
                            anim_end = anim_start + anim["duration"]
                            frame_time = item["duration"] * (i / item_frames)
                            
                            if anim_start <= frame_time <= anim_end:
                                # Calculate animation progress (0 to 1)
                                anim_progress = (frame_time - anim_start) / anim["duration"]
                                active_animations[anim["type"]] = min(1.0, anim_progress)
                                
                        self._create_loading_frame(frame_path, progress, active_animations)
                        frame_paths.append(frame_path)
                        frame_count += 1
                
                elif item["type"] == "results":
                    # Results UI frames with animations
                    for i in range(item_frames):
                        progress = i / item_frames
                        frame_path = os.path.join(temp_dir, f"frame_{frame_count:04d}.png")
                
                        # Determine which animations are active
                        active_animations = {}
                        for anim in item.get("animations", []):
                            anim_start = item["duration"] * anim["start"] / item["duration"]
                            anim_end = anim_start + anim["duration"]
                            frame_time = item["duration"] * (i / item_frames)
                            
                            if anim_start <= frame_time <= anim_end:
                                # Calculate animation progress (0 to 1)
                                anim_progress = (frame_time - anim_start) / anim["duration"]
                                active_animations[anim["type"]] = min(1.0, anim_progress)
                        
                        # For the first few frames, blend from loading to results for smooth transition
                        if i < fps * 0.2:  # 0.2 seconds transition
                            blend_ratio = i / (fps * 0.2)
                            # Create a blank loading frame to transition from
                            temp_loading_path = os.path.join(temp_dir, "temp_loading.png")
                            self._create_loading_frame(temp_loading_path, 0.9, {"pulse": 0.9})
                            self._create_transition_frame(temp_loading_path, item["image"], frame_path, blend_ratio, 
                                                         keep_animations=True, result_animations=active_animations, 
                                                         food_item=food_item)
                        else:
                            self._create_results_frame(item["image"], frame_path, food_item, active_animations)
                        
                        frame_paths.append(frame_path)
                        frame_count += 1
                
                current_time += item["duration"]
            
            # Combine frames into video
            self._frames_to_video(frame_paths, output_path, fps)
            
            return output_path
            
        finally:
            # Clean up temporary directory
            shutil.rmtree(temp_dir)
    
    def _create_home_frame(self, image_path: str, output_path: str, progress: float, animations: Dict = None):
        """Create a frame showing the home screen with potential animations."""
        if animations is None:
            animations = {}
            
        try:
            # Load base image
            img = Image.open(image_path).convert("RGBA")
            
            # Create a drawing context
            draw = ImageDraw.Draw(img)
            
            # Handle tap animation on scan button if present
            if "tap_button" in animations and animations["tap_button"] > 0:
                # Locate the scan button position (approximate based on UI)
                button_x, button_y = img.width // 2, int(img.height * 0.9)
                button_radius = int(img.width * 0.1)
                
                # Draw tap animation
                tap_progress = animations["tap_button"]
                tap_color = (255, 255, 255, int(128 * (1 - tap_progress)))
                draw.ellipse(
                    (button_x - button_radius, button_y - button_radius,
                     button_x + button_radius, button_y + button_radius),
                    fill=tap_color, outline=None
                )
            
            # Save the frame
            img.save(output_path, format="PNG")
            
        except Exception as e:
            self.logger.error(f"Error creating home frame: {e}")
            # Fallback to just copying the original image
            shutil.copy(image_path, output_path)
    
    def _create_transition_frame(self, from_image: str, to_image: str, output_path: str, blend_ratio: float, 
                                keep_animations: bool = False, result_animations: Dict = None, food_item: Dict = None):
        """Create a transition frame blending between two screens."""
        try:
            # Load images
            from_img = Image.open(from_image).convert("RGBA")
            to_img = Image.open(to_image).convert("RGBA")
            
            # Resize if needed
            if from_img.size != to_img.size:
                to_img = to_img.resize(from_img.size, Image.LANCZOS)
            
            # Blend images
            blended = Image.blend(from_img, to_img, blend_ratio)
            
            # If keeping animations for results screen transitions
            if keep_animations and result_animations and food_item:
                draw = ImageDraw.Draw(blended)
                
                # Draw results animations on top if needed
                if blend_ratio > 0.5 and any(k in result_animations for k in ["calorie_count", "protein_bar", "carbs_bar", "fat_bar"]):
                    # Draw partial results animations based on the blend ratio
                    animation_progress = (blend_ratio - 0.5) * 2  # Scale to 0-1 range
                    
                    # Create temporary animations dict with scaled progress
                    scaled_animations = {}
                    for k, v in result_animations.items():
                        scaled_animations[k] = v * animation_progress
                    
                    # Apply result animations to the blended image
                    self._apply_result_animations(blended, draw, food_item, scaled_animations)
            
            # Save the frame
            blended.save(output_path, format="PNG")
            
        except Exception as e:
            self.logger.error(f"Error creating transition frame: {e}")
            # Fallback to just copying the target image
            shutil.copy(to_image, output_path)
    
    def _create_camera_frame(self, image_path: str, output_path: str, progress: float, animations: Dict = None):
        """Create a frame showing the camera UI with scanning animation."""
        if animations is None:
            animations = {}
            
        try:
            # Load base image
            img = Image.open(image_path).convert("RGBA")
            
            # Create a drawing context
            draw = ImageDraw.Draw(img)
            
            # Add scan guide animation
            if "scan_guide" in animations and animations["scan_guide"] > 0:
                scan_progress = animations["scan_guide"]
                
                # Calculate scanning line position
                scan_y = int(img.height * 0.4 + (img.height * 0.2 * scan_progress))
                
                # Draw scanning line
                line_color = (75, 181, 67, 180)  # Semi-transparent green
                line_width = 2
                draw.line([(int(img.width * 0.2), scan_y), (int(img.width * 0.8), scan_y)], 
                          fill=line_color, width=line_width)
                
                # Draw small circle indicators at ends
                circle_radius = 5
                draw.ellipse((int(img.width * 0.2) - circle_radius, scan_y - circle_radius,
                             int(img.width * 0.2) + circle_radius, scan_y + circle_radius),
                             fill=line_color)
                draw.ellipse((int(img.width * 0.8) - circle_radius, scan_y - circle_radius,
                             int(img.width * 0.8) + circle_radius, scan_y + circle_radius),
                             fill=line_color)
            
            # Add capture button flash animation
            if "flash" in animations and animations["flash"] > 0:
                flash_progress = animations["flash"]
                
                # Create a semi-transparent white layer for flash effect
                flash_opacity = int(200 * (1 - flash_progress))  # Fade out
                flash_overlay = Image.new("RGBA", img.size, (255, 255, 255, flash_opacity))
                
                # Composite the flash over the image
                img = Image.alpha_composite(img, flash_overlay)
            
            # Save the frame
            img.save(output_path, format="PNG")
            
        except Exception as e:
            self.logger.error(f"Error creating camera frame: {e}")
            # Fallback to just copying the original image
            shutil.copy(image_path, output_path)

    def _create_loading_frame(self, output_path: str, progress: float, animations: Dict = None):
        """Create a loading animation frame."""
        if animations is None:
            animations = {}
            
        try:
            # Set up frame dimensions to match typical screenshots
            width, height = 1080, 2340
            
            # Create base image (dark translucent background)
            img = Image.new("RGBA", (width, height), (0, 0, 0, 180))
            draw = ImageDraw.Draw(img)
            
            # Get colors from config
            color_scheme = self._ui_config.get("color_scheme", {})
            primary_color = color_scheme.get("primary", "#000000")
            accent_color = color_scheme.get("accent", "#FF9500")
            
            # Convert hex to RGB
            def hex_to_rgb(hex_color):
                hex_color = hex_color.lstrip('#')
                return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
            
            accent_rgb = hex_to_rgb(accent_color)
            
            # Add "Analyzing" text
            font_size = 36
            font = self._get_font(font_size, bold=True)
            text = "Analyzing..."
            text_width = draw.textlength(text, font=font)
            text_position = ((width - text_width) // 2, height // 2 - 100)
            draw.text(text_position, text, fill=(255, 255, 255, 255), font=font)
            
            # Draw loading spinner animation
            center_x, center_y = width // 2, height // 2
            outer_radius = 50
            inner_radius = 40
            
            # Handle pulsing animation
            pulse_scale = 1.0
            if "pulse" in animations:
                # Calculate pulse effect (0.8 to 1.2 scale)
                pulse_progress = animations["pulse"]
                pulse_scale = 0.8 + 0.4 * abs(math.sin(pulse_progress * math.pi))
            
            # Adjust radii with pulse
            outer_radius = int(outer_radius * pulse_scale)
            inner_radius = int(inner_radius * pulse_scale)
            
            # Rotating progress arc
            start_angle = progress * 360 * 5  # Rotate 5 times during the animation
            arc_length = 120  # 120 degrees arc
            
            # Draw background circle
            draw.ellipse((center_x - outer_radius, center_y - outer_radius,
                          center_x + outer_radius, center_y + outer_radius),
                         fill=(255, 255, 255, 50))
            
            # Draw progress arc
            # Since PIL doesn't have direct arc drawing with width, we'll use the difference
            # between two ellipses to create a thick arc
            # This is a simplified approach - a proper arc would require more complex calculations
            
            # Convert arc angles to coordinates on the circle
            def get_point_on_circle(center, radius, angle_degrees):
                angle_rad = math.radians(angle_degrees)
                x = center[0] + radius * math.cos(angle_rad)
                y = center[1] + radius * math.sin(angle_rad)
                return (x, y)
            
            # Draw several small segments to approximate an arc
            segments = 20
            arc_color = accent_rgb + (255,)  # Add alpha channel
            arc_thickness = outer_radius - inner_radius
            
            for i in range(segments + 1):
                angle = start_angle + (i * arc_length / segments)
                point = get_point_on_circle((center_x, center_y), (outer_radius + inner_radius) / 2, angle)
                circle_radius = arc_thickness / 2
                draw.ellipse((point[0] - circle_radius, point[1] - circle_radius,
                              point[0] + circle_radius, point[1] + circle_radius),
                             fill=arc_color)
            
            # Save the frame
            img.save(output_path, format="PNG")
            
        except Exception as e:
            self.logger.error(f"Error creating loading frame: {e}")
            # Create a simple fallback frame
            fallback_img = Image.new("RGB", (1080, 2340), (0, 0, 0))
            fallback_img.save(output_path, format="PNG")

    def _create_results_frame(self, image_path: str, output_path: str, food_item: Dict, animations: Dict = None):
        """Create a results screen frame with animated elements."""
        if animations is None:
            animations = {}
            
        try:
            # Load base image
            img = Image.open(image_path).convert("RGBA")
            draw = ImageDraw.Draw(img)
            
            # Apply result animations
            self._apply_result_animations(img, draw, food_item, animations)
            
            # Save the frame
            img.save(output_path, format="PNG")
            
        except Exception as e:
            self.logger.error(f"Error creating results frame: {e}")
            # Fallback to just copying the original image
            shutil.copy(image_path, output_path)
    
    def _apply_result_animations(self, img, draw, food_item: Dict, animations: Dict):
        """Apply results screen animations to the provided image."""
        width, height = img.size
        
        # Get colors from config
        color_scheme = self._ui_config.get("color_scheme", {})
        macro_colors = color_scheme.get("macro", {})
        protein_color = macro_colors.get("protein", "#FF3B30")
        carbs_color = macro_colors.get("carbs", "#FF9500")
        fat_color = macro_colors.get("fat", "#007AFF")
        
        # Convert hex to RGB
        def hex_to_rgb(hex_color):
            hex_color = hex_color.lstrip('#')
            return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        
        # Extract macro values
        calories = food_item.get("calories", 0)
        protein = food_item.get("protein", 0)
        carbs = food_item.get("carbs", 0)
        fat = food_item.get("fat", 0)
        
        # Define regions for animations (approximate based on standard results screen)
        calorie_region = (width // 2, int(height * 0.35))
        macro_bar_y = {
            "protein": int(height * 0.5),
            "carbs": int(height * 0.6),
            "fat": int(height * 0.7)
        }
        macro_bar_width = int(width * 0.7)
        macro_bar_height = int(height * 0.03)
        macro_bar_x_start = int(width * 0.15)
        
        # Handle calorie counter animation
        if "calorie_count" in animations and animations["calorie_count"] > 0:
            # Animate counting up to the calorie value
            calorie_progress = animations["calorie_count"]
            displayed_calories = int(calories * calorie_progress)
            
            # Create a semi-transparent overlay to "erase" the original calorie text
            # Note: This is a simplified approach, a proper implementation would identify the exact location
            calorie_overlay = Image.new("RGBA", (300, 100), (255, 255, 255, 0))
            calorie_overlay_draw = ImageDraw.Draw(calorie_overlay)
            calorie_font = self._get_font(64, bold=True)
            calorie_text = f"{displayed_calories}"
            calorie_overlay_draw.text((150, 50), calorie_text, fill=(0, 0, 0, 255), font=calorie_font, anchor="mm")
            
            # Position the overlay over the calorie text area
            calorie_position = (calorie_region[0] - 150, calorie_region[1] - 50)
            img.paste(calorie_overlay, calorie_position, calorie_overlay)
        
        # Handle macro bar animations
        for macro, color_hex, value in [
            ("protein_bar", protein_color, protein),
            ("carbs_bar", carbs_color, carbs),
            ("fat_bar", fat_color, fat)
        ]:
            if macro in animations and animations[macro] > 0:
                # Calculate bar fill based on animation progress
                macro_key = macro.split("_")[0]  # Extract macro name (protein, carbs, fat)
                bar_progress = animations[macro]
                
                # Convert color to RGB
                color_rgb = hex_to_rgb(color_hex)
                
                # Get y position for this macro bar
                y_pos = macro_bar_y.get(macro_key, 0)
                
                # Draw background bar (light gray)
                draw.rectangle(
                    (macro_bar_x_start, y_pos, macro_bar_x_start + macro_bar_width, y_pos + macro_bar_height),
                    fill=(230, 230, 230, 255)
                )
                
                # Calculate fill width based on animation progress and value
                # Assuming a reasonable max value for scaling (adjust as needed)
                max_values = {"protein": 50, "carbs": 100, "fat": 40}
                max_value = max_values.get(macro_key, 100)
                value_ratio = min(1.0, value / max_value)
                fill_width = int(macro_bar_width * value_ratio * bar_progress)
                
                # Draw the colored fill bar
                draw.rectangle(
                    (macro_bar_x_start, y_pos, macro_bar_x_start + fill_width, y_pos + macro_bar_height),
                    fill=color_rgb + (255,)  # Add alpha channel
                )
                
                # Add value text if the bar has progressed enough
                if bar_progress > 0.9:
                    value_font = self._get_font(24, bold=True)
                    value_text = f"{value}g"
                    text_position = (macro_bar_x_start + macro_bar_width + 20, y_pos + macro_bar_height // 2)
                    draw.text(text_position, value_text, fill=(0, 0, 0, 255), font=value_font, anchor="lm")
        
        # Handle success indicator animation (checkmark or confirmation)
        if "success_indicator" in animations and animations["success_indicator"] > 0:
            success_progress = animations["success_indicator"]
            
            # Draw a checkmark or success message
            success_text = "Added to today"
            success_font = self._get_font(28, bold=True)
            success_position = (width // 2, int(height * 0.85))
            
            # Animate appearance (fade in)
            success_alpha = int(255 * success_progress)
            success_color = (0, 170, 0, success_alpha)  # Green with animated opacity
            
            # Draw text with animated opacity
            draw.text(success_position, success_text, fill=success_color, font=success_font, anchor="mm")
            
            # Optionally add checkmark icon
            checkmark_radius = 15
            checkmark_position = (width // 2 - 100, int(height * 0.85))
            
            # Draw circle background
            draw.ellipse(
                (checkmark_position[0] - checkmark_radius, checkmark_position[1] - checkmark_radius,
                 checkmark_position[0] + checkmark_radius, checkmark_position[1] + checkmark_radius),
                fill=(0, 170, 0, success_alpha)
            )
            
            # Draw checkmark
            check_width = int(checkmark_radius * 1.2)
            check_height = int(checkmark_radius * 0.8)
            
            # Calculate checkmark points
            point1 = (checkmark_position[0] - check_width//2, checkmark_position[1])
            point2 = (checkmark_position[0] - check_width//4, checkmark_position[1] + check_height//2)
            point3 = (checkmark_position[0] + check_width//2, checkmark_position[1] - check_height//2)
            
            # Draw checkmark line
            draw.line([point1, point2, point3], fill=(255, 255, 255, success_alpha), width=3)

    def _get_font(self, size, bold=False):
        """Get a font with the specified size."""
        try:
            if bold:
                return ImageFont.truetype("Arial Bold.ttf", size)
            return ImageFont.truetype("Arial.ttf", size)
        except IOError:
            # Fallback to default font
            return ImageFont.load_default()
    
    def _frames_to_video(self, frame_paths, output_path, fps=30):
        """Combine frames into a video."""
        try:
            first_frame = Image.open(frame_paths[0])
            width, height = first_frame.size
            
            # Use ffmpeg for efficient video creation
            cmd = [
                'ffmpeg', '-y',
                '-framerate', str(fps),
                '-i', os.path.join(os.path.dirname(frame_paths[0]), 'frame_%04d.png'),
                '-c:v', 'libx264',
                '-profile:v', 'high',
                '-crf', '18',
                '-pix_fmt', 'yuv420p',
                output_path
            ]
            
            subprocess.check_call(cmd)
            return output_path
            
        except Exception as e:
            self.logger.error(f"Error creating video from frames: {e}")
            return None
    
    def _trim_recording(self, recording_path, output_path, target_duration):
        """Trim an existing recording to the target duration."""
        try:
            cmd = [
                'ffmpeg', '-y',
                '-i', recording_path,
                '-t', str(target_duration),
                '-c:v', 'libx264',
                '-crf', '18',
                '-preset', 'fast',
                output_path
            ]
            
            subprocess.check_call(cmd)
            return output_path
            
        except Exception as e:
            self.logger.error(f"Error trimming recording: {e}")
            return recording_path  # Return original as fallback


# Singleton instance
_ui_manager_instance = None

class SceneContextManager:
    """
    Manages scene context for consistent video generation.
    
    This class:
    - Tracks food items associated with different scenes
    - Maintains visual consistency across UI sequences
    - Provides context-aware screen generation
    """
    
    def __init__(self):
        """Initialize the Scene Context Manager."""
        self.logger = logging.getLogger(__name__)
        self.food_context = {}
        self.scene_context = {}
        
    def set_food_for_scene(self, scene_name: str, food_item: Dict):
        """Set the food item for a specific scene."""
        self.food_context[scene_name] = food_item
        self.logger.info(f"Set food {food_item['name']} for scene {scene_name}")
        
    def get_food_for_scene(self, scene_name: str) -> Dict:
        """Get the food item for a specific scene."""
        if scene_name in self.food_context:
            return self.food_context[scene_name]
        return None
        
    def add_scene_context(self, scene_name: str, context: Dict):
        """Add context information for a scene."""
        self.scene_context[scene_name] = context
        self.logger.info(f"Added context for scene {scene_name}")
        
    def get_scene_context(self, scene_name: str) -> Dict:
        """Get context information for a scene."""
        if scene_name in self.scene_context:
            return self.scene_context[scene_name]
        return {}

def get_ui_manager() -> AppUIManager:
    """
    Get the singleton AppUIManager instance.
    
    Returns:
        AppUIManager instance
    """
    global _ui_manager_instance
    
    if _ui_manager_instance is None:
        _ui_manager_instance = AppUIManager()
        
    return _ui_manager_instance


if __name__ == "__main__":
    # Test the UI manager
    ui_manager = get_ui_manager()
    
    # Test getting a screenshot
    screenshot = ui_manager.get_screenshot_path(screen_type="home")
    print(f"Screenshot: {screenshot}")
    
    # Test creating a feature demo
    demo = ui_manager.get_recording_path(demo_type="scan_food")
    print(f"Demo: {demo}") 