#!/usr/bin/env python3
"""
Context-Aware UI Integrator: Ensures visual consistency across app demonstrations by
maintaining context about food items, environments, and visual elements throughout
the video generation process.
"""

import os
import logging
import json
from typing import Dict, List, Optional, Tuple, Union
from pathlib import Path

from video_generation.app_ui_manager import get_ui_manager, SceneContextManager
from video_generation.avatar_manager import load_avatar
from video_generation.avatar_config import AVATAR_CONFIGS

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('context_ui_integrator')

class ContextAwareUIIntegrator:
    """
    Integrates context-aware UI generation with the video generation pipeline.
    
    This class:
    - Manages scene context across the entire video generation process
    - Ensures consistent food items, lighting, and environments in UI sequences
    - Provides parametrized UI screens that match the avatar's environment
    """
    
    def __init__(self):
        """Initialize the Context-Aware UI Integrator."""
        # Get UI manager singleton
        self.ui_manager = get_ui_manager()
        
        # Dictionary to track food items shown by each avatar
        self.avatar_food_context = {}
        
        # Cache of generated UI sequences for reuse
        self.ui_sequence_cache = {}
        
        logger.info("Context-Aware UI Integrator initialized")
    
    def get_food_context_for_avatar(self, avatar_name: str) -> Dict:
        """
        Get the current food context for an avatar.
        
        Args:
            avatar_name: Name of the avatar
            
        Returns:
            Dict containing the food context
        """
        return self.avatar_food_context.get(avatar_name, {
            'food_item': None,
            'environment': None,
            'lighting_conditions': None
        })
    
    def set_food_context_for_avatar(self, 
                                   avatar_name: str, 
                                   food_item: str, 
                                   environment: Dict = None) -> Dict:
        """
        Set the food context for an avatar.
        
        Args:
            avatar_name: Name of the avatar
            food_item: Food item being scanned
            environment: Environment description and parameters
            
        Returns:
            Updated context dictionary
        """
        # Extract avatar-specific environment parameters from avatar config
        avatar_config = AVATAR_CONFIGS.get(avatar_name.lower(), None)
        avatar_environment = "generic environment"
        
        if avatar_config:
            variation = avatar_config.get('variations', {}).get('demo', '')
            if variation:
                # Extract environment from variation description
                avatar_environment = variation.split(', at ')[1].split(', ')[0] if ', at ' in variation else variation
        
        # Ensure we have environment parameters
        if environment is None:
            environment = {}
        
        # Create environment description if not provided
        if 'description' not in environment:
            environment['description'] = avatar_environment
        
        # Default lighting conditions based on environment
        if 'lighting_conditions' not in environment:
            if 'bright' in avatar_environment:
                environment['lighting_conditions'] = {'brightness': 30, 'contrast': 10}
            elif 'dark' in avatar_environment:
                environment['lighting_conditions'] = {'brightness': -30, 'contrast': 20}
            else:
                environment['lighting_conditions'] = {'brightness': 0, 'contrast': 0}
        
        # Create or update avatar food context
        context = {
            'food_item': food_item,
            'environment': environment.get('description', avatar_environment),
            'lighting_conditions': environment.get('lighting_conditions', {}),
            'avatar_name': avatar_name
        }
        
        # Store in avatar context map
        self.avatar_food_context[avatar_name] = context
        
        # Update the active context in the UI manager
        self.ui_manager.set_active_food_context(
            food_item=food_item,
            environment=context['environment'],
            lighting_conditions=context['lighting_conditions'],
            avatar_name=avatar_name
        )
        
        logger.info(f"Set food context for avatar {avatar_name}: {food_item} in {context['environment']}")
        return context
    
    def generate_consistent_ui_sequence(self,
                                       avatar_name: str,
                                       food_item: str = None,
                                       environment: Dict = None,
                                       screens: List[str] = None) -> Dict[str, str]:
        """
        Generate a consistent UI sequence for an avatar and food item.
        
        Args:
            avatar_name: Name of the avatar
            food_item: Food item to show (uses existing context if None)
            environment: Environment parameters
            screens: List of screen types to include
            
        Returns:
            Dict mapping screen types to UI image paths
        """
        # Use existing context if available
        if food_item is None:
            context = self.get_food_context_for_avatar(avatar_name)
            food_item = context.get('food_item')
            
            if food_item is None:
                logger.warning(f"No food context for avatar {avatar_name}, using default")
                food_item = "salad"  # Default food item
        
        # Set food context if new
        if avatar_name not in self.avatar_food_context or self.avatar_food_context[avatar_name].get('food_item') != food_item:
            self.set_food_context_for_avatar(avatar_name, food_item, environment)
        
        # Check cache for existing sequence
        cache_key = f"{avatar_name}_{food_item}"
        if cache_key in self.ui_sequence_cache:
            logger.info(f"Using cached UI sequence for {avatar_name} with {food_item}")
            return self.ui_sequence_cache[cache_key]
        
        # Generate new UI sequence
        logger.info(f"Generating consistent UI sequence for {avatar_name} with {food_item}")
        ui_sequence = self.ui_manager.generate_ui_sequence(
            food_item=food_item,
            environment=self.avatar_food_context[avatar_name]['environment'],
            avatar_name=avatar_name,
            screens=screens
        )
        
        # Cache the sequence
        self.ui_sequence_cache[cache_key] = ui_sequence
        
        return ui_sequence
    
    def get_ui_for_scene(self, 
                        avatar_name: str, 
                        scene_name: str, 
                        food_item: str = None) -> str:
        """
        Get the appropriate UI screen image for a specific scene and avatar.
        
        Args:
            avatar_name: Name of the avatar
            scene_name: Scene name (e.g., 'scanning', 'results', 'recently_eaten')
            food_item: Optional food item override
            
        Returns:
            Path to UI screen image
        """
        # Map scene names to UI screen types
        scene_to_screen_map = {
            'scanning': 'camera_interface',
            'analysis': 'analysis_screen',
            'results': 'results_screen',
            'history': 'recently_eaten',
            'recently_eaten': 'recently_eaten',
            'home': 'home_screen'
        }
        
        screen_type = scene_to_screen_map.get(scene_name, scene_name)
        
        # Get context for avatar
        context = self.get_food_context_for_avatar(avatar_name)
        
        # If no context or overriding food item, set it
        if context.get('food_item') is None or (food_item is not None and food_item != context.get('food_item')):
            self.set_food_context_for_avatar(avatar_name, food_item or "salad")
            context = self.get_food_context_for_avatar(avatar_name)
        
        # Get UI screen from manager
        ui_image = self.ui_manager.get_screenshot(
            screen=screen_type,
            food_item=context.get('food_item')
        )
        
        if ui_image is None:
            logger.warning(f"No UI image found for {avatar_name}/{scene_name}, using fallback")
            # Fallback to any screenshot for this screen type
            ui_image = self.ui_manager.get_screenshot(screen=screen_type)
        
        return ui_image
    
    def integrate_with_script(self, script: Dict) -> Dict:
        """
        Enhance a video script with consistent UI references.
        
        Args:
            script: Video script dictionary
            
        Returns:
            Enhanced script with UI context information
        """
        enhanced_script = script.copy()
        
        # Extract avatar name from script
        avatar_name = script.get('avatar', {}).get('name', 'emily')
        
        # Find the food items mentioned in the script
        food_items = self._extract_food_items_from_script(script)
        
        if food_items:
            # Use the first food item as the primary one
            primary_food = food_items[0]
            logger.info(f"Setting primary food context for script: {primary_food}")
            
            # Set the food context for this avatar
            self.set_food_context_for_avatar(avatar_name, primary_food)
            
            # Generate UI sequence for this food item
            ui_sequence = self.generate_consistent_ui_sequence(
                avatar_name=avatar_name,
                food_item=primary_food
            )
            
            # Enhance script with UI context
            if 'scenes' in enhanced_script:
                for scene in enhanced_script['scenes']:
                    scene_type = scene.get('type', '')
                    
                    # For app demonstration scenes, add UI context
                    if 'app' in scene_type or 'demo' in scene_type or 'scan' in scene_type:
                        # Map scene type to UI screen type
                        if 'scan' in scene_type:
                            screen_type = 'camera_interface'
                        elif 'result' in scene_type:
                            screen_type = 'results_screen'
                        elif 'history' in scene_type:
                            screen_type = 'recently_eaten'
                        else:
                            screen_type = 'analysis_screen'
                        
                        # Add UI path if available
                        if screen_type in ui_sequence:
                            scene['ui_screen'] = ui_sequence[screen_type]
                            
                        # Add food context
                        if 'context' not in scene:
                            scene['context'] = {}
                        
                        scene['context']['food_item'] = primary_food
                        scene['context']['environment'] = self.avatar_food_context[avatar_name]['environment']
        
        return enhanced_script
    
    def _extract_food_items_from_script(self, script: Dict) -> List[str]:
        """
        Extract food items mentioned in the script.
        
        Args:
            script: Video script dictionary
            
        Returns:
            List of food items mentioned
        """
        food_items = []
        
        # Common food items to look for
        common_foods = [
            "pizza", "salad", "burger", "sandwich", "pasta", "sushi", 
            "coffee", "smoothie", "breakfast", "lunch", "dinner", "snack",
            "bread", "rice", "chicken", "steak", "fish", "vegetables"
        ]
        
        # Check script lines for food mentions
        if 'scenes' in script:
            for scene in script['scenes']:
                if 'lines' in scene:
                    for line in scene['lines']:
                        text = line.get('text', '').lower()
                        
                        # Check for common foods in text
                        for food in common_foods:
                            if food in text and food not in food_items:
                                food_items.append(food)
        
        # If no foods found, look in script description
        if not food_items and 'description' in script:
            description = script['description'].lower()
            for food in common_foods:
                if food in description and food not in food_items:
                    food_items.append(food)
        
        # Default to salad if nothing found
        if not food_items:
            food_items = ["salad"]
        
        return food_items

# Singleton instance
_integrator_instance = None

def get_context_ui_integrator() -> ContextAwareUIIntegrator:
    """Get or create the context UI integrator singleton."""
    global _integrator_instance
    if _integrator_instance is None:
        _integrator_instance = ContextAwareUIIntegrator()
    return _integrator_instance 