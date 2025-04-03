#!/usr/bin/env python3
"""
Dynamic UI Generator - Generates app UI screens for video production.
This module uses learned UI patterns to create realistic, dynamic app interfaces.
"""

import os
import sys
import json
import logging
import cv2
import numpy as np
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from typing import Dict, List, Tuple, Optional, Union
import random
import tempfile
from datetime import datetime

# Local imports
try:
    from .ui_pattern_learner import get_pattern_learner, UITemplateBuilder
except ImportError:
    from .ui_pattern_learner import get_pattern_learner, UITemplateBuilder

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('ui_generator')

# Get project root directory
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

class FoodItem:
    """Represents a food item with its properties."""
    def __init__(self, name, calories, protein=0, carbs=0, fat=0, image_path=None):
        self.name = name
        self.calories = calories
        self.protein = protein
        self.carbs = carbs
        self.fat = fat
        self.image_path = image_path
        
    def to_dict(self):
        """Convert to dictionary."""
        return {
            'name': self.name,
            'calories': self.calories,
            'protein': self.protein,
            'carbs': self.carbs,
            'fat': self.fat,
            'image_path': self.image_path
        }
        
    @classmethod
    def from_dict(cls, data):
        """Create from dictionary."""
        return cls(
            data['name'],
            data['calories'],
            data.get('protein', 0),
            data.get('carbs', 0),
            data.get('fat', 0),
            data.get('image_path', None)
        )


class UIGenerator:
    """Generates realistic app UI components for Optimal AI calorie tracker app."""
    
    def __init__(self, pattern_learner=None):
        self.logger = logging.getLogger(__name__)
        self.pattern_learner = pattern_learner
        self.config = self._load_config()
        self.fonts = self._load_fonts()
        
    def _load_config(self) -> Dict:
        """Load UI configuration from the config file."""
        config_path = os.path.join('config', 'app_ui_config.json')
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            self.logger.info(f"Loaded UI configuration from {config_path}")
            return config
        except (FileNotFoundError, json.JSONDecodeError) as e:
            self.logger.warning(f"Failed to load UI config: {e}")
            # Return default config if file not found or invalid
            return {
                "app_name": "Optimal AI",
                "color_scheme": {
                    "primary": "#4a90e2",
                    "secondary": "#50e3c2",
                    "background": "#f5f8fa",
                    "text": "#333333"
                }
            }
    
    def _load_fonts(self) -> Dict:
        """Load fonts for UI generation."""
        fonts = {}
        font_dir = os.path.join('assets', 'fonts')
        
        # Default system fonts as fallback
        system_fonts = {
            'regular': ImageFont.load_default(),
            'bold': ImageFont.load_default()
        }
        
        try:
            # Try to load custom fonts if available
            if os.path.exists(font_dir):
                font_files = os.listdir(font_dir)
                for file in font_files:
                    if file.endswith(('.ttf', '.otf')):
                        if 'bold' in file.lower():
                            fonts['bold'] = ImageFont.truetype(os.path.join(font_dir, file), 24)
                        else:
                            fonts['regular'] = ImageFont.truetype(os.path.join(font_dir, file), 24)
            
            # Use system fonts as fallback if needed
            if 'regular' not in fonts:
                fonts['regular'] = system_fonts['regular']
            if 'bold' not in fonts:
                fonts['bold'] = system_fonts['bold']
                
            self.logger.info(f"Loaded fonts: {', '.join(fonts.keys())}")
            return fonts
        except Exception as e:
            self.logger.warning(f"Error loading fonts: {e}")
            return system_fonts
    
    def generate_ui_screen(self, screen_type: str, food_item: Dict = None, output_path: str = None) -> Image.Image:
        """
        Generate a UI screen based on the specified type and food item.
        
        Args:
            screen_type: Type of screen to generate (e.g., 'home_screen', 'results_screen')
            food_item: Dictionary containing food item details
            output_path: Path to save the generated image
            
        Returns:
            PIL Image object of the generated UI screen
        """
        self.logger.info(f"Generating UI screen: {screen_type}")
        
        # Check if we can use a real screenshot first
        screenshot_path = self._find_real_screenshot(screen_type, food_item)
        if screenshot_path:
            try:
                self.logger.info(f"Using real screenshot: {screenshot_path}")
                image = Image.open(screenshot_path)
                
                # Save image if output path provided
                if output_path:
                    os.makedirs(os.path.dirname(output_path), exist_ok=True)
                    image.save(output_path)
                    self.logger.info(f"Saved real screenshot to {output_path}")
                
                return image
            except Exception as e:
                self.logger.warning(f"Failed to use real screenshot: {e}, falling back to generated UI")
        
        # Get screen configuration
        if screen_type not in self.config.get('screens', {}):
            self.logger.warning(f"Screen type '{screen_type}' not found in config, using default")
            screen_config = self._get_default_screen_config(screen_type)
        else:
            screen_config = self.config['screens'][screen_type]
        
        # If no food item provided and screen needs one, use a default
        if food_item is None and screen_type in ['results_screen', 'food_log']:
            food_item = self._get_default_food_item()
        
        # Create base image
        width, height = 375, 812  # iPhone X dimensions
        image = Image.new('RGB', (width, height), self._hex_to_rgb(self.config['color_scheme']['background']))
        draw = ImageDraw.Draw(image)
        
        # Draw screen elements based on screen type
        if screen_type == 'home_screen':
            self._draw_home_screen(draw, image, screen_config)
        elif screen_type == 'camera_interface':
            self._draw_camera_interface_optimal(draw, image, screen_config)
        elif screen_type == 'results_screen':
            self._draw_results_screen(draw, image, screen_config, food_item)
        elif screen_type == 'food_log':
            self._draw_food_log(draw, image, screen_config, food_item)
        else:
            # Generic screen with basic elements
            self._draw_generic_screen(draw, image, screen_config, screen_type)
        
        # Add iPhone notch and home indicator
        image = self._add_iphone_frame(image)
        
        # Save image if output path provided
        if output_path:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            image.save(output_path)
            self.logger.info(f"Saved UI screen to {output_path}")
        
        return image
    
    def _find_real_screenshot(self, screen_type: str, food_item: Dict = None) -> str:
        """Find a real screenshot matching the screen type and food item if available."""
        # Check in app_ui_mapping.json for relevant screenshots
        mapping_config = self.config.get('screens', {}).get(screen_type, {}).get('variants', {})
        
        # For home screen, choose variant based on whether food items exist
        if screen_type == 'home_screen':
            variant = 'after_scan' if food_item else 'before_scan'
            screenshots = mapping_config.get(variant, {}).get('source_screenshots', [])
            if screenshots:
                # Return a random screenshot from the appropriate variant
                return random.choice(screenshots)
        
        # For results screen, try to match the food item
        elif screen_type == 'results_screen' and food_item:
            screenshots = mapping_config.get('result', {}).get('source_screenshots', [])
            if screenshots:
                # Try to find a screenshot matching the food item name
                if 'name' in food_item:
                    food_name = food_item['name'].lower()
                    matching_screenshots = [s for s in screenshots if food_name in s.lower()]
                    if matching_screenshots:
                        return random.choice(matching_screenshots)
                # Fall back to random screenshot
                return random.choice(screenshots)
        
        # For camera interface
        elif screen_type == 'camera_interface':
            variant = 'scanning' if food_item else 'blank'
            screenshots = mapping_config.get(variant, {}).get('source_screenshots', [])
            if screenshots:
                # Try to match food item if scanning
                if variant == 'scanning' and food_item and 'name' in food_item:
                    food_name = food_item['name'].lower()
                    matching_screenshots = [s for s in screenshots if food_name in s.lower()]
                    if matching_screenshots:
                        return random.choice(matching_screenshots)
                # Fall back to random screenshot
                return random.choice(screenshots)
        
        # No matching screenshot found
        return None
    
    def _get_default_screen_config(self, screen_type: str) -> Dict:
        """Return default configuration for a screen type."""
        return {
            "layout": "vertical_scroll",
            "elements": [
                {
                    "type": "header",
                    "title": "Optimal AI"
                }
            ]
        }
    
    def _get_default_food_item(self) -> Dict:
        """Return a default food item from config."""
        if 'common_food_items' in self.config and self.config['common_food_items']:
            return random.choice(self.config['common_food_items'])
        return {
            "name": "Chicken Salad",
            "calories": 350,
            "protein": 30,
            "carbs": 15,
            "fat": 20
        }
    
    def _hex_to_rgb(self, hex_color: str) -> Tuple[int, int, int]:
        """Convert hex color to RGB tuple."""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    def _draw_home_screen(self, draw: ImageDraw.Draw, image: Image.Image, config: Dict):
        """Draw home screen UI elements."""
        # Fill with light background
        draw.rectangle([(0, 0), (image.width, image.height)], 
                       fill=self._hex_to_rgb(self.config['color_scheme']['background']))
        
        # Use BlurView effect by drawing slightly transparent white
        draw.rectangle([(0, 0), (image.width, image.height)], 
                       fill=self._hex_to_rgb_with_alpha('#FFFFFF', 0.7))
        
        # Draw header
        y_offset = 60  # Start below the status bar
        header_text = "Optimal AI"
        for element in config.get('elements', []):
            if element.get('type') == 'header':
                header_text = element.get('title', header_text)
                break
        
        # App title with specific styling
        draw.text((25, y_offset), header_text, 
                 fill=self._hex_to_rgb(self.config['color_scheme']['text']),
                 font=self.fonts.get('medium', ImageFont.load_default()),
                 anchor="lt")
        
        y_offset += 50
        
        # Streak Card (rounded white card with shadow)
        card_height = 80
        draw.rectangle([(20, y_offset), (image.width - 20, y_offset + card_height)],
                      fill="#FFFFFF")
        
        # Streak info
        draw.text((40, y_offset + 20), "Current Streak",
                 fill=self._hex_to_rgb(self.config['color_scheme']['text_secondary']),
                 font=self.fonts.get('regular', ImageFont.load_default()),
                 anchor="lt")
        
        draw.text((40, y_offset + 50), "3 days",
                 fill=self._hex_to_rgb(self.config['color_scheme']['text']),
                 font=self.fonts.get('semibold', ImageFont.load_default()),
                 anchor="lt")
        
        # Longest streak on the right
        draw.text((image.width - 40, y_offset + 20), "Longest Streak",
                 fill=self._hex_to_rgb(self.config['color_scheme']['text_secondary']),
                 font=self.fonts.get('regular', ImageFont.load_default()),
                 anchor="rt")
        
        draw.text((image.width - 40, y_offset + 50), "14 days",
                 fill=self._hex_to_rgb(self.config['color_scheme']['text']),
                 font=self.fonts.get('semibold', ImageFont.load_default()),
                 anchor="rt")
        
        y_offset += card_height + 20
        
        # Date selector (horizontal with selected date highlighted)
        date_selector_height = 50
        dates = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
        date_width = (image.width - 40) // 7
        selected_index = 3  # Wednesday is selected
        
        for i, date in enumerate(dates):
            x = 20 + i * date_width
            
            # Draw selected date with black background
            if i == selected_index:
                draw.rectangle([(x, y_offset), (x + date_width, y_offset + date_selector_height)],
                              fill="#000000")
                text_color = "#FFFFFF"
            else:
                text_color = self.config['color_scheme']['text']
            
            # Draw day name
            draw.text((x + date_width // 2, y_offset + 15), date,
                     fill=text_color,
                     font=self.fonts.get('regular', ImageFont.load_default()),
                     anchor="mm")
            
            # Draw date number
            draw.text((x + date_width // 2, y_offset + 35), str(i + 10),
                     fill=text_color,
                     font=self.fonts.get('regular', ImageFont.load_default()),
                     anchor="mm")
        
        y_offset += date_selector_height + 20
        
        # Calories left card (frosted glass effect)
        calories_card_height = 80
        draw.rectangle([(20, y_offset), (image.width - 20, y_offset + calories_card_height)],
                      fill="#FFFFFF")
        
        # Calories remaining text on left
        draw.text((40, y_offset + 20), "Calories left",
                 fill=self._hex_to_rgb(self.config['color_scheme']['text_secondary']),
                 font=self.fonts.get('regular', ImageFont.load_default()),
                 anchor="lt")
        
        draw.text((40, y_offset + 50), "1,200",
                 fill=self._hex_to_rgb(self.config['color_scheme']['text']),
                 font=self.fonts.get('bold', ImageFont.load_default()),
                 anchor="lt")
        
        # Progress circle on right
        circle_x = image.width - 60
        circle_y = y_offset + calories_card_height // 2
        circle_radius = 30
        
        # Background circle
        draw.ellipse([(circle_x - circle_radius, circle_y - circle_radius),
                     (circle_x + circle_radius, circle_y + circle_radius)],
                    fill="#E5E5E5")
        
        # Progress arc (about 40% complete)
        self._draw_arc(draw, circle_x, circle_y, circle_radius, 0, 144, 
                      fill="#FF9500", width=4)
        
        y_offset += calories_card_height + 20
        
        # Macro container with three equal cards
        macro_height = 80
        macro_width = (image.width - 60) // 3
        
        macro_data = [
            {"title": "Protein left", "value": "120g", "color": "#FF3B30"},
            {"title": "Carbs left", "value": "150g", "color": "#FF9500"},
            {"title": "Fat left", "value": "40g", "color": "#007AFF"}
        ]
        
        for i, macro in enumerate(macro_data):
            x = 20 + i * (macro_width + 10)
            
            # Draw card
            draw.rectangle([(x, y_offset), (x + macro_width, y_offset + macro_height)],
                          fill="#FFFFFF")
            
            # Draw title
            draw.text((x + macro_width // 2, y_offset + 20), macro["title"],
                     fill=self._hex_to_rgb(self.config['color_scheme']['text_secondary']),
                     font=self.fonts.get('regular', ImageFont.load_default()),
                     anchor="mm")
            
            # Draw value
            draw.text((x + macro_width // 2, y_offset + 50), macro["value"],
                     fill=self._hex_to_rgb(macro["color"]),
                     font=self.fonts.get('bold', ImageFont.load_default()),
                     anchor="mm")
            
            # Draw progress bar
            bar_width = macro_width - 20
            bar_height = 5
            bar_x = x + 10
            bar_y = y_offset + 65
            
            # Background bar
            draw.rectangle([(bar_x, bar_y), (bar_x + bar_width, bar_y + bar_height)],
                          fill="#E5E5E5")
            
            # Filled bar (random progress between 30% and 70%)
            fill_width = int(bar_width * (0.3 + (i * 0.2)))
            draw.rectangle([(bar_x, bar_y), (bar_x + fill_width, bar_y + bar_height)],
                          fill=macro["color"])
        
        y_offset += macro_height + 20
        
        # Recently eaten section title
        draw.text((25, y_offset), "Recently eaten",
                 fill=self._hex_to_rgb(self.config['color_scheme']['text']),
                 font=self.fonts.get('semibold', ImageFont.load_default()),
                 anchor="lt")
        
        y_offset += 40
        
        # Recent meals from config or sample food items
        meals = self.config.get('common_food_items', [])[:3]
        if not meals:
            meals = [self._get_default_food_item() for _ in range(3)]
        
        for meal in meals:
            # Meal card
            card_height = 80
            draw.rectangle([(20, y_offset), (image.width - 20, y_offset + card_height)],
                          fill="#FFFFFF")
            
            # Food image placeholder (left square)
            img_size = 60
            img_x = 40
            img_y = y_offset + card_height // 2 - img_size // 2
            draw.rectangle([(img_x, img_y), (img_x + img_size, img_y + img_size)],
                          fill="#E5E5EA")
            
            # Meal name and calories
            text_x = img_x + img_size + 20
            draw.text((text_x, y_offset + 25), meal['name'],
                     fill=self._hex_to_rgb(self.config['color_scheme']['text']),
                     font=self.fonts.get('semibold', ImageFont.load_default()),
                     anchor="lt")
            
            draw.text((text_x, y_offset + 55), f"{meal['calories']} cal",
                     fill=self._hex_to_rgb(self.config['color_scheme']['text_secondary']),
                     font=self.fonts.get('regular', ImageFont.load_default()),
                     anchor="lt")
            
            # Macros on the right
            macro_x = image.width - 70
            
            # Draw macro circles with letters
            p_circle_y = y_offset + 25
            draw.ellipse([(macro_x - 10, p_circle_y - 10), (macro_x + 10, p_circle_y + 10)],
                        fill="#FF3B30")
            draw.text((macro_x, p_circle_y), "P",
                     fill="#FFFFFF",
                     font=self.fonts.get('bold', ImageFont.load_default()),
                     anchor="mm")
            draw.text((macro_x + 20, p_circle_y), f"{meal.get('protein', 0)}g",
                     fill=self._hex_to_rgb(self.config['color_scheme']['text']),
                     font=self.fonts.get('regular', ImageFont.load_default()),
                     anchor="lt")
            
            c_circle_y = y_offset + 50
            draw.ellipse([(macro_x - 10, c_circle_y - 10), (macro_x + 10, c_circle_y + 10)],
                        fill="#FF9500")
            draw.text((macro_x, c_circle_y), "C",
                     fill="#FFFFFF",
                     font=self.fonts.get('bold', ImageFont.load_default()),
                     anchor="mm")
            draw.text((macro_x + 20, c_circle_y), f"{meal.get('carbs', 0)}g",
                     fill=self._hex_to_rgb(self.config['color_scheme']['text']),
                     font=self.fonts.get('regular', ImageFont.load_default()),
                     anchor="lt")
            
            f_circle_y = y_offset + 75
            draw.ellipse([(macro_x - 10, f_circle_y - 10), (macro_x + 10, f_circle_y + 10)],
                        fill="#007AFF")
            draw.text((macro_x, f_circle_y), "F",
                     fill="#FFFFFF",
                     font=self.fonts.get('bold', ImageFont.load_default()),
                     anchor="mm")
            draw.text((macro_x + 20, f_circle_y), f"{meal.get('fat', 0)}g",
                     fill=self._hex_to_rgb(self.config['color_scheme']['text']),
                     font=self.fonts.get('regular', ImageFont.load_default()),
                     anchor="lt")
            
            y_offset += card_height + 15
    
    def _draw_camera_interface(self, draw: ImageDraw.Draw, image: Image.Image, config: Dict):
        """Draw camera interface UI elements based on the Optimal AI app."""
        # Fill with dark background to simulate camera viewfinder
        draw.rectangle([(0, 0), (image.width, image.height)], fill=(20, 20, 20))
        
        # Status bar area (top)
        status_bar_height = 44
        
        # Header with title
        header_height = 50
        header_y = status_bar_height
        
        # Draw header title
        draw.text((image.width // 2, header_y + header_height // 2), "Capture Food",
                 fill="#FFFFFF",
                 font=self.fonts.get('semibold', ImageFont.load_default()),
                 anchor="mm")
        
        # Back button (top left)
        back_button_radius = 20
        back_button_x = 40
        back_button_y = header_y + header_height // 2
        
        # Draw circular button background
        draw.ellipse([(back_button_x - back_button_radius, back_button_y - back_button_radius),
                     (back_button_x + back_button_radius, back_button_y + back_button_radius)],
                    fill=(255, 255, 255, 77))  # Semi-transparent white
        
        # Draw chevron left
        draw.text((back_button_x, back_button_y), "←",
                 fill="#FFFFFF",
                 font=self.fonts.get('bold', ImageFont.load_default()),
                 anchor="mm")
        
        # Camera guide overlay with corners
        guide_width, guide_height = image.width * 0.7, image.width * 0.7
        left = (image.width - guide_width) / 2
        top = (image.height - guide_height) / 2.5  # Position a bit higher than center
        right = left + guide_width
        bottom = top + guide_height
        
        # Draw corner indicators instead of full rectangle
        corner_length = 40
        line_width = 3
        corner_color = (255, 255, 255, 77)  # Semi-transparent white
        
        # Top left corner
        draw.line([(left, top), (left + corner_length, top)], fill=corner_color, width=line_width)
        draw.line([(left, top), (left, top + corner_length)], fill=corner_color, width=line_width)
        
        # Top right corner
        draw.line([(right - corner_length, top), (right, top)], fill=corner_color, width=line_width)
        draw.line([(right, top), (right, top + corner_length)], fill=corner_color, width=line_width)
        
        # Bottom left corner
        draw.line([(left, bottom - corner_length), (left, bottom)], fill=corner_color, width=line_width)
        draw.line([(left, bottom), (left + corner_length, bottom)], fill=corner_color, width=line_width)
        
        # Bottom right corner
        draw.line([(right - corner_length, bottom), (right, bottom)], fill=corner_color, width=line_width)
        draw.line([(right, bottom), (right, bottom - corner_length)], fill=corner_color, width=line_width)
        
        # Flash button (bottom left)
        flash_button_radius = 20
        flash_button_x = 40
        flash_button_y = image.height - 100
        
        # Draw circular button background
        draw.ellipse([(flash_button_x - flash_button_radius, flash_button_y - flash_button_radius),
                     (flash_button_x + flash_button_radius, flash_button_y + flash_button_radius)],
                    fill=(255, 255, 255, 77))  # Semi-transparent white
        
        # Draw flash icon
        draw.text((flash_button_x, flash_button_y), "⚡",
                 fill="#FFFFFF",
                 font=self.fonts.get('bold', ImageFont.load_default()),
                 anchor="mm")
        
        # Capture button at bottom center
        capture_button_radius = 36
        inner_button_radius = 32
        circle_center = (image.width // 2, image.height - 100)
        
        # Outer circle
        draw.ellipse([(circle_center[0] - capture_button_radius, circle_center[1] - capture_button_radius),
                     (circle_center[0] + capture_button_radius, circle_center[1] + capture_button_radius)],
                    fill=(255, 255, 255, 128))  # Semi-transparent white
        
        # Inner circle
        draw.ellipse([(circle_center[0] - inner_button_radius, circle_center[1] - inner_button_radius),
                     (circle_center[0] + inner_button_radius, circle_center[1] + inner_button_radius)],
                    fill="#FFFFFF")
    
    def _draw_results_screen(self, draw: ImageDraw.Draw, image: Image.Image, config: Dict, food_item: Dict):
        """Draw results screen UI elements with provided food item."""
        if not food_item:
            food_item = self._get_default_food_item()
            
        # Background
        draw.rectangle([(0, 0), (image.width, image.height)], fill=self._hex_to_rgb(self.config['color_scheme']['background']))
        
        # Status bar area
        status_bar_height = 44
        
        # Header with back button
        header_height = 50
        header_y = status_bar_height
        
        draw.text((image.width // 2, header_y + header_height // 2), "Food Details",
                 fill=self._hex_to_rgb(self.config['color_scheme']['text']),
                 font=self.fonts.get('semibold', ImageFont.load_default()),
                 anchor="mm")
        
        # Back button
        back_x, back_y = 40, header_y + header_height // 2
        draw.text((back_x, back_y), "←",
                 fill=self._hex_to_rgb(self.config['color_scheme']['text']),
                 font=self.fonts.get('bold', ImageFont.load_default()),
                 anchor="mm")
        
        y_offset = header_y + header_height + 20
        
        # Food image placeholder
        img_height = 200
        draw.rounded_rectangle([(20, y_offset), (image.width - 20, y_offset + img_height)],
                      radius=12,
                      fill="#E5E5EA")
        
        # Add food name as image caption
        draw.text((image.width // 2, y_offset + img_height // 2), food_item.get('name', 'Food'),
                 fill="#666666",
                 font=self.fonts.get('semibold', ImageFont.load_default()),
                 anchor="mm")
        
        y_offset += img_height + 20
        
        # Food name
        draw.text((image.width // 2, y_offset), food_item.get('name', 'Food'),
                 fill=self._hex_to_rgb(self.config['color_scheme']['text']),
                 font=self.fonts.get('bold', ImageFont.load_default()),
                 anchor="mt")
        
        y_offset += 40
        
        # Calories in large font
        draw.text((image.width // 2, y_offset), str(food_item.get('calories', 0)),
                 fill=self._hex_to_rgb(self.config['color_scheme']['text']),
                 font=self.fonts.get('bold', ImageFont.load_default()),
                 anchor="mt")
        
        # "calories" label below
        draw.text((image.width // 2, y_offset + 30), "calories",
                 fill=self._hex_to_rgb(self.config['color_scheme']['text_secondary']),
                 font=self.fonts.get('regular', ImageFont.load_default()),
                 anchor="mt")
        
        y_offset += 70
        
        # Metric cards (P, C, F) in a row
        metrics = [
            {"symbol": "P", "label": "Protein", "value": f"{food_item.get('protein', 0)}g", "color": "#FF3B30"},
            {"symbol": "C", "label": "Carbs", "value": f"{food_item.get('carbs', 0)}g", "color": "#FF9500"},
            {"symbol": "F", "label": "Fat", "value": f"{food_item.get('fat', 0)}g", "color": "#007AFF"}
        ]
        
        metric_width = (image.width - 40) // 3
        for i, metric in enumerate(metrics):
            card_x = 20 + i * metric_width
            
            # Card background
            draw.rounded_rectangle([(card_x, y_offset), (card_x + metric_width - 10, y_offset + 90)],
                          radius=12,
                          fill="#FFFFFF")
            
            # Symbol circle
            circle_x = card_x + (metric_width - 10) // 2
            circle_y = y_offset + 25
            circle_radius = 15
            
            draw.ellipse([(circle_x - circle_radius, circle_y - circle_radius),
                         (circle_x + circle_radius, circle_y + circle_radius)],
                        fill=metric["color"])
            
            draw.text((circle_x, circle_y), metric["symbol"],
                     fill="#FFFFFF",
                     font=self.fonts.get('bold', ImageFont.load_default()),
                     anchor="mm")
            
            # Metric label
            draw.text((circle_x, y_offset + 55), metric["label"],
                     fill=self._hex_to_rgb(self.config['color_scheme']['text_secondary']),
                     font=self.fonts.get('regular', ImageFont.load_default()),
                     anchor="mt")
            
            # Metric value
            draw.text((circle_x, y_offset + 75), metric["value"],
                     fill=self._hex_to_rgb(self.config['color_scheme']['text']),
                     font=self.fonts.get('semibold', ImageFont.load_default()),
                     anchor="mt")
        
        y_offset += 110
        
        # Portion control
        portion_height = 60
        draw.rounded_rectangle([(20, y_offset), (image.width - 20, y_offset + portion_height)],
                      radius=12,
                      fill="#FFFFFF")
        
        # Portion label
        draw.text((40, y_offset + portion_height // 2), "Portion",
                 fill=self._hex_to_rgb(self.config['color_scheme']['text']),
                 font=self.fonts.get('semibold', ImageFont.load_default()),
                 anchor="lm")
        
        # Portion stepper (- 1 +)
        stepper_x = image.width - 150
        stepper_y = y_offset + portion_height // 2
        
        # Minus button
        draw.ellipse([(stepper_x - 15, stepper_y - 15), (stepper_x + 15, stepper_y + 15)],
                    outline=self._hex_to_rgb(self.config['color_scheme']['text']),
                    width=2)
        draw.text((stepper_x, stepper_y), "-",
                 fill=self._hex_to_rgb(self.config['color_scheme']['text']),
                 font=self.fonts.get('bold', ImageFont.load_default()),
                 anchor="mm")
        
        # Value
        draw.text((stepper_x + 40, stepper_y), "1",
                 fill=self._hex_to_rgb(self.config['color_scheme']['text']),
                 font=self.fonts.get('bold', ImageFont.load_default()),
                 anchor="mm")
        
        # Plus button
        draw.ellipse([(stepper_x + 65, stepper_y - 15), (stepper_x + 95, stepper_y + 15)],
                    outline=self._hex_to_rgb(self.config['color_scheme']['text']),
                    width=2)
        draw.text((stepper_x + 80, stepper_y), "+",
                 fill=self._hex_to_rgb(self.config['color_scheme']['text']),
                 font=self.fonts.get('bold', ImageFont.load_default()),
                 anchor="mm")
        
        y_offset += portion_height + 20
        
        # Nutrition details card
        nutrition_height = 150
        draw.rounded_rectangle([(20, y_offset), (image.width - 20, y_offset + nutrition_height)],
                      radius=12,
                      fill="#FFFFFF")
        
        # Nutrition title
        draw.text((40, y_offset + 20), "Nutrition Details",
                 fill=self._hex_to_rgb(self.config['color_scheme']['text']),
                 font=self.fonts.get('semibold', ImageFont.load_default()),
                 anchor="lt")
        
        # Nutrition rows
        nutrients = [
            {"name": "Calories", "value": f"{food_item.get('calories', 0)} cal"},
            {"name": "Protein", "value": f"{food_item.get('protein', 0)}g"},
            {"name": "Carbs", "value": f"{food_item.get('carbs', 0)}g"},
            {"name": "Fat", "value": f"{food_item.get('fat', 0)}g"}
        ]
        
        for i, nutrient in enumerate(nutrients):
            row_y = y_offset + 50 + i * 25
            
            # Nutrient name
            draw.text((40, row_y), nutrient["name"],
                     fill=self._hex_to_rgb(self.config['color_scheme']['text']),
                     font=self.fonts.get('regular', ImageFont.load_default()),
                     anchor="lt")
            
            # Nutrient value
            draw.text((image.width - 40, row_y), nutrient["value"],
                     fill=self._hex_to_rgb(self.config['color_scheme']['text']),
                     font=self.fonts.get('semibold', ImageFont.load_default()),
                     anchor="rt")
        
        y_offset += nutrition_height + 30
        
        # Add to Log button
        button_height = 50
        draw.rounded_rectangle([(20, y_offset), (image.width - 20, y_offset + button_height)],
                      radius=8,
                      fill="#000000")
        
        draw.text((image.width // 2, y_offset + button_height // 2), "Add to Log",
                 fill="#FFFFFF",
                 font=self.fonts.get('semibold', ImageFont.load_default()),
                 anchor="mm")
    
    def _hex_to_rgb_with_alpha(self, hex_color: str, alpha: float) -> Tuple[int, int, int, int]:
        """Convert hex color to RGBA tuple with alpha value (0-1)."""
        hex_color = hex_color.lstrip('#')
        r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        return (r, g, b, int(alpha * 255))
    
    def _draw_arc(self, draw: ImageDraw.Draw, x: int, y: int, radius: int, 
                 start_angle: int, end_angle: int, fill: str, width: int = 1):
        """Draw an arc on the image.
        
        Args:
            draw: ImageDraw instance
            x, y: Center coordinates
            radius: Radius of arc
            start_angle, end_angle: Start and end angles in degrees (0-360)
            fill: Color to use for the arc
            width: Line width
        """
        bbox = [(x - radius, y - radius), (x + radius, y + radius)]
        draw.arc(bbox, start_angle, end_angle, fill=fill, width=width)
    
    def _draw_food_log(self, draw: ImageDraw.Draw, image: Image.Image, config: Dict, food_item: Dict):
        """Draw food log UI elements with provided food item."""
        # Similar implementation as the other screens...
        # ... existing code ...
    
    def _draw_generic_screen(self, draw: ImageDraw.Draw, image: Image.Image, config: Dict, screen_type: str):
        """Draw a generic screen for types not specifically implemented."""
        # Background
        draw.rectangle([(0, 0), (image.width, image.height)], fill=self._hex_to_rgb(self.config['color_scheme']['background']))
        
        # Header
        y_offset = 60
        header_height = 50
        
        draw.text((image.width // 2, y_offset + header_height // 2), screen_type.replace('_', ' ').title(),
                 fill=self._hex_to_rgb(self.config['color_scheme']['text']),
                 font=self.fonts.get('bold', ImageFont.load_default()),
                 anchor="mm")
        
        y_offset += header_height + 40
        
        # Generic content placeholder
        content_height = 400
        draw.rectangle([(20, y_offset), (image.width - 20, y_offset + content_height)],
                      fill="#FFFFFF",
                      radius=12)
        
        draw.text((image.width // 2, y_offset + content_height // 2), "Screen Content",
                 fill=self._hex_to_rgb(self.config['color_scheme'].get('text_secondary', '#767676')),
                 font=self.fonts.get('regular', ImageFont.load_default()),
                 anchor="mm")
    
    def _add_iphone_frame(self, image: Image.Image) -> Image.Image:
        """Add iPhone notch and home indicator to the image."""
        draw = ImageDraw.Draw(image)
        
        # Notch
        notch_width = 170
        notch_height = 30
        notch_x = (image.width - notch_width) // 2
        
        draw.rectangle([(notch_x, 0), (notch_x + notch_width, notch_height)],
                      fill=(0, 0, 0))
        
        # Home indicator
        indicator_width = 140
        indicator_height = 5
        indicator_x = (image.width - indicator_width) // 2
        indicator_y = image.height - 5 - indicator_height
        
        draw.rectangle([(indicator_x, indicator_y), 
                      (indicator_x + indicator_width, indicator_y + indicator_height)],
                     fill=(0, 0, 0))
        
        return image
    
    def generate_screen_sequence(self, sequence_name: str, food_item: Dict = None, output_dir: str = None) -> List[str]:
        """Generate a sequence of UI screens based on the defined sequences in config."""
        if sequence_name not in self.config.get('demo_sequences', {}):
            self.logger.warning(f"Sequence '{sequence_name}' not found in config")
            return []
            
        sequence = self.config['demo_sequences'][sequence_name]
        self.logger.info(f"Generating screen sequence: {sequence_name}")
        
        # Use provided food item or get default
        if food_item is None:
            food_item = self._get_default_food_item()
            
        output_paths = []
        
        # Generate each screen in the sequence
        for i, screen in enumerate(sequence.get('screens', [])):
            screen_type = screen.get('screen')
            variant = screen.get('variant', 'default')
            
            if output_dir:
                filename = f"{i+1:02d}_{screen_type}_{variant}.png"
                output_path = os.path.join(output_dir, filename)
            else:
                output_path = None
                
            # Generate the screen with consistent food item
            self.generate_ui_screen(screen_type, food_item, output_path)
            
            if output_path:
                output_paths.append(output_path)
                
        return output_paths

    def _draw_camera_interface_optimal(self, draw: ImageDraw.Draw, image: Image.Image, config: Dict):
        """Draw camera interface UI elements based on the Optimal AI app."""
        # Fill with dark background to simulate camera viewfinder
        draw.rectangle([(0, 0), (image.width, image.height)], fill=(20, 20, 20))
        
        # Status bar area (top)
        status_bar_height = 44
        
        # Header with title
        header_height = 50
        header_y = status_bar_height
        
        # Draw header title
        draw.text((image.width // 2, header_y + header_height // 2), "Capture Food",
                 fill="#FFFFFF",
                 font=self.fonts.get('semibold', ImageFont.load_default()),
                 anchor="mm")
        
        # Back button (top left)
        back_button_radius = 20
        back_button_x = 40
        back_button_y = header_y + header_height // 2
        
        # Draw circular button background
        draw.ellipse([(back_button_x - back_button_radius, back_button_y - back_button_radius),
                     (back_button_x + back_button_radius, back_button_y + back_button_radius)],
                    fill=(255, 255, 255, 77))  # Semi-transparent white
        
        # Draw chevron left
        draw.text((back_button_x, back_button_y), "←",
                 fill="#FFFFFF",
                 font=self.fonts.get('bold', ImageFont.load_default()),
                 anchor="mm")
        
        # Camera guide overlay with corners
        guide_width, guide_height = image.width * 0.7, image.width * 0.7
        left = (image.width - guide_width) / 2
        top = (image.height - guide_height) / 2.5  # Position a bit higher than center
        right = left + guide_width
        bottom = top + guide_height
        
        # Draw corner indicators instead of full rectangle
        corner_length = 40
        line_width = 3
        corner_color = (255, 255, 255, 77)  # Semi-transparent white
        
        # Top left corner
        draw.line([(left, top), (left + corner_length, top)], fill=corner_color, width=line_width)
        draw.line([(left, top), (left, top + corner_length)], fill=corner_color, width=line_width)
        
        # Top right corner
        draw.line([(right - corner_length, top), (right, top)], fill=corner_color, width=line_width)
        draw.line([(right, top), (right, top + corner_length)], fill=corner_color, width=line_width)
        
        # Bottom left corner
        draw.line([(left, bottom - corner_length), (left, bottom)], fill=corner_color, width=line_width)
        draw.line([(left, bottom), (left + corner_length, bottom)], fill=corner_color, width=line_width)
        
        # Bottom right corner
        draw.line([(right - corner_length, bottom), (right, bottom)], fill=corner_color, width=line_width)
        draw.line([(right, bottom), (right, bottom - corner_length)], fill=corner_color, width=line_width)
        
        # Flash button (bottom left)
        flash_button_radius = 20
        flash_button_x = 40
        flash_button_y = image.height - 100
        
        # Draw circular button background
        draw.ellipse([(flash_button_x - flash_button_radius, flash_button_y - flash_button_radius),
                     (flash_button_x + flash_button_radius, flash_button_y + flash_button_radius)],
                    fill=(255, 255, 255, 77))  # Semi-transparent white
        
        # Draw flash icon
        draw.text((flash_button_x, flash_button_y), "⚡",
                 fill="#FFFFFF",
                 font=self.fonts.get('bold', ImageFont.load_default()),
                 anchor="mm")
        
        # Capture button at bottom center
        capture_button_radius = 36
        inner_button_radius = 32
        circle_center = (image.width // 2, image.height - 100)
        
        # Outer circle
        draw.ellipse([(circle_center[0] - capture_button_radius, circle_center[1] - capture_button_radius),
                     (circle_center[0] + capture_button_radius, circle_center[1] + capture_button_radius)],
                    fill=(255, 255, 255, 128))  # Semi-transparent white
        
        # Inner circle
        draw.ellipse([(circle_center[0] - inner_button_radius, circle_center[1] - inner_button_radius),
                     (circle_center[0] + inner_button_radius, circle_center[1] + inner_button_radius)],
                    fill="#FFFFFF")


# Singleton pattern
_ui_generator_instance = None

def get_ui_generator(force_new=False):
    """Get the singleton UI generator instance."""
    global _ui_generator_instance
    
    if _ui_generator_instance is None or force_new:
        _ui_generator_instance = UIGenerator()
        
    return _ui_generator_instance


if __name__ == "__main__":
    # Test the UI generator
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate app UI for videos")
    parser.add_argument("--food", type=str, default=None,
                        help="Food item to generate UI for")
    parser.add_argument("--sequence", type=str, default="scan_to_result",
                        choices=["scan_to_result", "browse_food_log", "result_to_log"],
                        help="UI sequence to generate")
    
    args = parser.parse_args()
    
    # Initialize UI generator
    generator = UIGenerator()
    
    # Generate UI sequence
    sequence = generator.generate_screen_sequence(args.sequence, args.food)
    
    # Print results
    print(f"Generated {len(sequence)} UI screens:")
    for screen in sequence:
        print(f"  {screen}") 