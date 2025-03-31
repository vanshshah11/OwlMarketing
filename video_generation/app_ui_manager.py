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
        camera_duration = 2.0  # 2 seconds on camera screen
        loading_duration = 0.5  # 0.5 seconds loading
        results_duration = duration - camera_duration - loading_duration  # Remaining time for results
        
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
        
        # Get screenshots for camera and results
        camera_screenshot = self._get_camera_screenshot(food_item)
        results_screenshot = self._get_results_screenshot(food_item)
        
        # Create demo sequence
        sequence = [
            {"type": "camera", "image": camera_screenshot, "duration": camera_duration},
            {"type": "loading", "duration": loading_duration},
            {"type": "results", "image": results_screenshot, "duration": results_duration,
             "animations": [
                 {"type": "macro_bars", "start": 0.2, "duration": 0.5},
                 {"type": "calorie_count", "start": 0.0, "duration": 0.3}
             ]}
        ]
        
        # Generate the UI sequence
        return self._generate_ui_sequence(sequence, output_path, food_item)
    
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
            for item in sequence:
                item_frames = int(item["duration"] * fps)
                
                if item["type"] == "camera":
                    # Camera UI frames
                    for i in range(item_frames):
                        progress = i / item_frames
                        frame_path = os.path.join(temp_dir, f"frame_{frame_count:04d}.png")
                        self._create_camera_frame(item["image"], frame_path, progress)
                        frame_paths.append(frame_path)
                        frame_count += 1
                
                elif item["type"] == "loading":
                    # Loading indicator frames
                    for i in range(item_frames):
                        progress = i / item_frames
                        frame_path = os.path.join(temp_dir, f"frame_{frame_count:04d}.png")
                        self._create_loading_frame(frame_path, progress)
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
                            anim_start = current_time + anim["start"]
                            anim_end = anim_start + anim["duration"]
                            frame_time = current_time + (i * (1/fps))
                            
                            if anim_start <= frame_time <= anim_end:
                                # Calculate animation progress (0 to 1)
                                anim_progress = (frame_time - anim_start) / anim["duration"]
                                active_animations[anim["type"]] = min(1.0, anim_progress)
                        
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
    
    def _create_camera_frame(self, image_path: str, output_path: str, progress: float):
        """Create a frame showing the camera UI."""
        # Load camera screenshot or create a simulated one
        if image_path and os.path.exists(image_path):
            img = Image.open(image_path)
        else:
            # Create simulated camera UI
            img = Image.new('RGB', (1080, 1920), self.theme['colors']['background']['primary']['dark'])
            draw = ImageDraw.Draw(img)
            
            # Draw camera frame guide (corners only, as in the app)
            w, h = img.size
            center_w, center_h = w//2, h//2
            frame_w, frame_h = int(w * 0.8), int(h * 0.4)
            left = center_w - frame_w//2
            top = center_h - frame_h//2
            right = center_w + frame_w//2
            bottom = center_h + frame_h//2
            
            # Draw corners
            corner_length = 50
            corner_width = 4
            corner_color = self.theme['colors']['text']['primary']['dark']
            
            # Top left corner
            draw.line([(left, top), (left + corner_length, top)], fill=corner_color, width=corner_width)
            draw.line([(left, top), (left, top + corner_length)], fill=corner_color, width=corner_width)
            
            # Top right corner
            draw.line([(right - corner_length, top), (right, top)], fill=corner_color, width=corner_width)
            draw.line([(right, top), (right, top + corner_length)], fill=corner_color, width=corner_width)
            
            # Bottom left corner
            draw.line([(left, bottom - corner_length), (left, bottom)], fill=corner_color, width=corner_width)
            draw.line([(left, bottom), (left + corner_length, bottom)], fill=corner_color, width=corner_width)
            
            # Bottom right corner
            draw.line([(right - corner_length, bottom), (right, bottom)], fill=corner_color, width=corner_width)
            draw.line([(right, bottom - corner_length), (right, bottom)], fill=corner_color, width=corner_width)
            
            # Draw capture button at bottom
            button_radius = 40
            button_center = (center_w, h - 100)
            draw.ellipse(
                [
                    button_center[0] - button_radius, 
                    button_center[1] - button_radius,
                    button_center[0] + button_radius, 
                    button_center[1] + button_radius
                ], 
                fill=corner_color
            )
        
        # Add subtle animation to indicate active scanning (optional)
        if progress > 0.7:  # Add capture flash effect near the end
            overlay = Image.new('RGBA', img.size, (255, 255, 255, int(50 * (1.0 - (progress - 0.7) / 0.3))))
            img = Image.alpha_composite(img.convert('RGBA'), overlay)
        
        img.save(output_path)
    
    def _create_loading_frame(self, output_path: str, progress: float):
        """Create a frame showing the loading indicator."""
        # Create dark background
        img = Image.new('RGB', (1080, 1920), self.theme['colors']['background']['primary']['dark'])
        draw = ImageDraw.Draw(img)
        
        # Draw loading spinner (simulate iOS spinner with dots)
        center_x, center_y = img.width // 2, img.height // 2
        radius = 40
        num_dots = 8
        dot_radius = 5
        
        for i in range(num_dots):
            # Calculate position on the circle
            angle = 2 * np.pi * i / num_dots + (progress * 2 * np.pi)
            x = center_x + radius * np.cos(angle)
            y = center_y + radius * np.sin(angle)
            
            # Calculate opacity based on position (iOS spinner has fading dots)
            opacity = int(255 * (0.3 + 0.7 * (i / num_dots)))
            
            # Draw the dot
            dot_color = (255, 255, 255, opacity)
            draw.ellipse(
                [(x - dot_radius, y - dot_radius), (x + dot_radius, y + dot_radius)],
                fill=dot_color
            )
        
        img.save(output_path)
    
    def _create_results_frame(self, image_path: str, output_path: str, food_item: Dict, animations: Dict):
        """Create a frame showing the results UI with animations."""
        # Load results screenshot or create a simulated one
        if image_path and os.path.exists(image_path):
            img = Image.open(image_path)
        else:
            # Create simulated results UI
            img = Image.new('RGB', (1080, 1920), self.theme['colors']['background']['primary']['light'])
            draw = ImageDraw.Draw(img)
            
            # Define layout measurements
            margin = self.theme['spacing']['m']
            top_margin = 120
            content_width = img.width - (margin * 2)
            
            # Load and draw logo
            if os.path.exists(self.logo_path):
                logo = Image.open(self.logo_path)
                logo_width = 100
                logo_height = int(logo.height * (logo_width / logo.width))
                logo = logo.resize((logo_width, logo_height), Image.LANCZOS)
                img.paste(logo, (margin, margin), logo if logo.mode == 'RGBA' else None)
            
            # Add food image placeholder
            image_height = int(img.width * 0.5)  # 1:2 aspect ratio
            draw.rectangle(
                [(margin, top_margin), (img.width - margin, top_margin + image_height)],
                fill="#CCCCCC"
            )
            
            # Add food name
            font_title = self._get_font(24, bold=True)
            food_name = food_item["name"]
            draw.text(
                (margin, top_margin + image_height + margin),
                food_name,
                fill=self.theme['colors']['text']['primary']['light'],
                font=font_title
            )
            
            # Calculate calorie count animation
            calories = food_item["calories"]
            if "calorie_count" in animations:
                # Animate counting up
                displayed_calories = int(calories * animations["calorie_count"])
            else:
                displayed_calories = calories
                
            # Add calorie count
            font_large = self._get_font(40, bold=True)
            calorie_text = str(displayed_calories)
            draw.text(
                (margin, top_margin + image_height + margin + 50),
                calorie_text,
                fill=self.theme['colors']['text']['primary']['light'],
                font=font_large
            )
            
            # Add "calories" label
            font_small = self._get_font(14)
            draw.text(
                (margin + font_large.getsize(calorie_text)[0] + 10, top_margin + image_height + margin + 70),
                "calories",
                fill=self.theme['colors']['text']['primary']['light'],
                font=font_small
            )
            
            # Add macro bars
            bar_y_start = top_margin + image_height + margin + 120
            bar_height = 30
            bar_spacing = 50
            bar_width = content_width
            
            # Function to draw a macro bar
            def draw_macro_bar(y_pos, label, value, max_value, color, progress=1.0):
                # Calculate the bar width based on the value and animation progress
                value_width = int((value / max_value) * bar_width * progress)
                
                # Draw label
                draw.text(
                    (margin, y_pos), 
                    f"{label}: {value}g",
                    fill=self.theme['colors']['text']['primary']['light'],
                    font=font_small
                )
                
                # Draw background bar
                draw.rectangle(
                    [(margin, y_pos + 25), (margin + bar_width, y_pos + 25 + bar_height)],
                    fill="#EEEEEE",
                    outline=None,
                    width=0
                )
                
                # Draw filled bar
                if value_width > 0:
                    draw.rectangle(
                        [(margin, y_pos + 25), (margin + value_width, y_pos + 25 + bar_height)],
                        fill=color,
                        outline=None,
                        width=0
                    )
            
            # Get macro bar animation progress
            bar_progress = animations.get("macro_bars", 1.0)
            
            # Calculate max value for proportional bars
            max_macro = max(food_item["protein"], food_item["carbs"], food_item["fat"])
            
            # Draw macro bars
            draw_macro_bar(
                bar_y_start,
                "Protein",
                food_item["protein"],
                max_macro,
                self.theme['colors']['macro']['protein'],
                bar_progress
            )
            
            draw_macro_bar(
                bar_y_start + bar_spacing,
                "Carbs",
                food_item["carbs"],
                max_macro,
                self.theme['colors']['macro']['carbs'],
                bar_progress
            )
            
            draw_macro_bar(
                bar_y_start + bar_spacing * 2,
                "Fat",
                food_item["fat"],
                max_macro,
                self.theme['colors']['macro']['fat'],
                bar_progress
            )
            
            # Add "Add to Log" button
            button_y = bar_y_start + bar_spacing * 3 + 20
            button_height = 60
            draw.rectangle(
                [(margin, button_y), (img.width - margin, button_y + button_height)],
                fill=self.theme['colors']['text']['primary']['light'],
                outline=None,
                width=0
            )
            
            # Add button text
            button_font = self._get_font(20, bold=True)
            button_text = "Add to Log"
            text_width, text_height = button_font.getsize(button_text)
            text_x = (img.width - text_width) // 2
            text_y = button_y + (button_height - text_height) // 2
            draw.text(
                (text_x, text_y),
                button_text,
                fill=self.theme['colors']['background']['primary']['dark'],
                font=button_font
            )
        
        img.save(output_path)
    
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