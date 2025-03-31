#!/usr/bin/env python3
"""
UI Pattern Learner - Analyzes Optimal AI app screenshots to learn UI patterns.
This system extracts UI components, learns layout patterns, and creates templates
for dynamic UI generation.
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
import tempfile
import torch
from transformers import DetrImageProcessor, DetrForObjectDetection
import pytesseract
from collections import defaultdict
import random

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('ui_pattern_learner')

# Get project root directory
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

class UIElement:
    """Represents a UI element with its properties."""
    def __init__(self, element_type, x, y, width, height, text=None, confidence=0.0):
        self.type = element_type
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.text = text
        self.confidence = confidence
        self.properties = {}
        
    def to_dict(self):
        """Convert element to dictionary."""
        return {
            'type': self.type,
            'x': self.x,
            'y': self.y,
            'width': self.width,
            'height': self.height,
            'text': self.text,
            'confidence': self.confidence,
            'properties': self.properties
        }
        
    @classmethod
    def from_dict(cls, data):
        """Create element from dictionary."""
        element = cls(
            data['type'], 
            data['x'], 
            data['y'], 
            data['width'], 
            data['height'], 
            data['text'],
            data['confidence']
        )
        element.properties = data.get('properties', {})
        return element
        
    def contains_point(self, x, y):
        """Check if element contains a point."""
        return (self.x <= x <= self.x + self.width and 
                self.y <= y <= self.y + self.height)
                
    def get_center(self):
        """Get center point of element."""
        return (self.x + self.width // 2, self.y + self.height // 2)
        
    def get_rect(self):
        """Get rectangle as (x1, y1, x2, y2)."""
        return (self.x, self.y, self.x + self.width, self.y + self.height)
        
    def get_area(self):
        """Get area of element."""
        return self.width * self.height
        
    def __repr__(self):
        return f"{self.type}({self.x},{self.y},{self.width},{self.height})"


class UIComponentExtractor:
    """Extract UI components from app screenshots."""
    
    def __init__(self, cache_dir=None):
        """Initialize the component extractor with detection models."""
        if cache_dir is None:
            cache_dir = os.path.join(project_root, "data", "ui_extraction_cache")
            os.makedirs(cache_dir, exist_ok=True)
        
        self.cache_dir = Path(cache_dir)
        logger.info(f"Initializing UI Component Extractor with cache directory: {self.cache_dir}")
        
        # Components for detection and recognition
        self.element_detector = None
        self.text_recognizer = None
        
    def _load_element_detector(self):
        """Lazy-load element detector model."""
        if self.element_detector is None:
            try:
                logger.info("Loading DETR model for UI element detection")
                model_name = "facebook/detr-resnet-50"
                self.processor = DetrImageProcessor.from_pretrained(model_name)
                self.element_detector = DetrForObjectDetection.from_pretrained(model_name)
                
                # Move to GPU if available
                if torch.cuda.is_available():
                    self.element_detector = self.element_detector.to("cuda")
                    logger.info("DETR model loaded on GPU")
                else:
                    logger.info("DETR model loaded on CPU")
            except Exception as e:
                logger.error(f"Error loading element detector: {e}")
                # Fallback to simpler detection if needed
                logger.info("Using fallback element detection methods")
                self.element_detector = "fallback"
        
        return self.element_detector
        
    def _detect_ui_elements_cv(self, image):
        """Detect UI elements using OpenCV methods (fallback)."""
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Apply edge detection
        edges = cv2.Canny(gray, 50, 150)
        
        # Find contours
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Process contours
        elements = []
        for contour in contours:
            # Filter out very small contours
            if cv2.contourArea(contour) < 100:
                continue
                
            # Get bounding box
            x, y, w, h = cv2.boundingRect(contour)
            
            # Classify element type based on shape, size, etc.
            element_type = self._classify_element(image, x, y, w, h)
            
            # Create UI element
            element = UIElement(element_type, x, y, w, h, confidence=0.7)
            elements.append(element)
            
        return elements
    
    def _classify_element(self, image, x, y, w, h):
        """Classify UI element type based on properties."""
        # Extract the element region
        roi = image[y:y+h, x:x+w]
        
        # Calculate aspect ratio
        aspect_ratio = w / h if h > 0 else 0
        
        # Detect if it might be a button
        if 1.5 < aspect_ratio < 5 and 50 < w < 500 and 30 < h < 100:
            return "button"
        
        # Detect if it might be a card
        elif 0.5 < aspect_ratio < 2 and w > 200 and h > 200:
            return "card"
            
        # Detect if it might be text
        elif aspect_ratio > 2 and h < 50:
            return "text"
            
        # Detect if it might be an image
        elif 0.5 < aspect_ratio < 2 and w > 100 and h > 100:
            # Check color variance (images typically have higher variance)
            if roi.size > 0:
                variance = np.var(roi)
                if variance > 2000:  # Threshold determined empirically
                    return "image"
        
        # Detect if it might be an input field
        elif 3 < aspect_ratio < 10 and 150 < w < 800 and 30 < h < 80:
            return "input"
            
        # Default to generic element
        return "element"
        
    def extract_components(self, screenshot_path):
        """Extract UI components from a screenshot."""
        # Check cache first
        cache_key = Path(screenshot_path).name
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        if cache_file.exists():
            try:
                with open(cache_file, 'r') as f:
                    cached_data = json.load(f)
                    logger.info(f"Loaded cached extraction for {cache_key}")
                    
                    # Convert dictionaries to UIElement objects
                    elements = [UIElement.from_dict(elem) for elem in cached_data['elements']]
                    
                    return {
                        'elements': elements,
                        'structure': cached_data['structure'],
                        'screenshot': screenshot_path
                    }
            except Exception as e:
                logger.warning(f"Error loading cache: {e}, will re-extract")
        
        # Load the screenshot
        image = cv2.imread(screenshot_path)
        if image is None:
            logger.error(f"Failed to load image: {screenshot_path}")
            return {'elements': [], 'structure': {}, 'screenshot': screenshot_path}
            
        height, width = image.shape[:2]
        
        # Detect UI elements
        detector = self._load_element_detector()
        if detector == "fallback":
            elements = self._detect_ui_elements_cv(image)
        else:
            # Use DETR model for better detection
            elements = self._detect_elements_detr(image)
            
        # Extract text from elements
        elements = self._extract_text_from_elements(image, elements)
        
        # Identify UI patterns and hierarchies
        ui_structure = self._identify_structure(elements, width, height)
        
        # Cache the results
        cache_data = {
            'elements': [elem.to_dict() for elem in elements],
            'structure': ui_structure,
            'screenshot': screenshot_path
        }
        
        try:
            with open(cache_file, 'w') as f:
                json.dump(cache_data, f)
                logger.info(f"Cached extraction for {cache_key}")
        except Exception as e:
            logger.warning(f"Error caching extraction: {e}")
            
        return {
            'elements': elements,
            'structure': ui_structure,
            'screenshot': screenshot_path
        }
        
    def _detect_elements_detr(self, image):
        """Detect elements using DETR model."""
        # Convert BGR to RGB
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # Prepare image for model
        inputs = self.processor(images=image_rgb, return_tensors="pt")
        
        # Move to GPU if available
        if torch.cuda.is_available():
            inputs = {k: v.to("cuda") for k, v in inputs.items()}
            
        # Get predictions
        with torch.no_grad():
            outputs = self.element_detector(**inputs)
            
        # Convert outputs to elements
        target_sizes = torch.tensor([image.shape[:2]])
        results = self.processor.post_process_object_detection(
            outputs, threshold=0.5, target_sizes=target_sizes
        )[0]
        
        elements = []
        for score, label, box in zip(results["scores"], results["labels"], results["boxes"]):
            box = [int(i) for i in box.tolist()]
            x1, y1, x2, y2 = box
            
            # Map model label to UI element type
            label_id = label.item()
            if label_id in [1, 3]:  # person, car - treat as images
                element_type = "image"
            elif label_id in [2, 7]:  # bicycle, truck - treat as icons
                element_type = "icon"
            elif label_id in [5, 6]:  # bus, train - treat as cards
                element_type = "card"
            else:
                element_type = "element"
                
            element = UIElement(
                element_type,
                x1, y1,
                x2 - x1, y2 - y1,
                confidence=score.item()
            )
            elements.append(element)
            
        return elements
        
    def _extract_text_from_elements(self, image, elements):
        """Extract text from UI elements."""
        try:
            # Initialize text recognition if needed
            if not self.text_recognizer:
                # Check if pytesseract is available
                try:
                    pytesseract.get_tesseract_version()
                    self.text_recognizer = "pytesseract"
                except Exception:
                    logger.warning("Tesseract not available, skipping text extraction")
                    self.text_recognizer = "unavailable"
            
            if self.text_recognizer == "unavailable":
                return elements
                
            # Extract text from elements
            for element in elements:
                if element.type in ['text', 'button', 'label', 'input']:
                    # Extract region of interest
                    x, y, w, h = element.x, element.y, element.width, element.height
                    roi = image[y:y+h, x:x+w]
                    
                    if roi.size == 0:
                        continue
                        
                    # Convert to grayscale
                    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
                    
                    # Apply basic preprocessing to improve text recognition
                    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
                    
                    # Recognize text
                    if self.text_recognizer == "pytesseract":
                        text = pytesseract.image_to_string(binary)
                        element.text = text.strip()
                        
        except Exception as e:
            logger.error(f"Error in text extraction: {e}")
            
        return elements
        
    def _identify_structure(self, elements, width, height):
        """Identify UI structure and relationship between elements."""
        # Basic layout sections
        sections = {
            'header': {'elements': [], 'y_range': (0, height * 0.2)},
            'body': {'elements': [], 'y_range': (height * 0.2, height * 0.8)},
            'footer': {'elements': [], 'y_range': (height * 0.8, height)}
        }
        
        # Assign elements to sections
        for element in elements:
            center_y = element.y + element.height / 2
            for section_name, section in sections.items():
                y_min, y_max = section['y_range']
                if y_min <= center_y < y_max:
                    section['elements'].append(element)
                    break
        
        # Find navigation elements (typically in footer)
        navigation_elements = [
            e for e in sections['footer']['elements']
            if (e.type in ['button', 'icon'] and e.width < width * 0.3)
        ]
        
        # Analyze body layout
        body_elements = sections['body']['elements']
        layout_type = self._determine_layout_type(body_elements, width, height)
        
        return {
            'sections': {
                name: {
                    'element_count': len(section['elements']),
                    'element_types': self._count_element_types(section['elements'])
                }
                for name, section in sections.items()
            },
            'navigation': {
                'count': len(navigation_elements),
                'positions': [e.get_center() for e in navigation_elements]
            },
            'layout_type': layout_type,
            'screen_size': (width, height)
        }
    
    def _count_element_types(self, elements):
        """Count occurrences of each element type."""
        counts = defaultdict(int)
        for element in elements:
            counts[element.type] += 1
        return dict(counts)
        
    def _determine_layout_type(self, elements, width, height):
        """Determine the layout type based on element arrangement."""
        if not elements:
            return "unknown"
            
        # Check for list layout
        list_candidates = [
            e for e in elements 
            if e.width > width * 0.7 and e.height < height * 0.2
        ]
        if len(list_candidates) > 2:
            return "list"
            
        # Check for grid layout
        grid_candidates = [
            e for e in elements
            if 0.2 < e.width / width < 0.5 and 0.1 < e.height / height < 0.3
        ]
        if len(grid_candidates) > 3:
            return "grid"
            
        # Check for card layout
        card_candidates = [
            e for e in elements
            if e.width > width * 0.7 and e.height > height * 0.2
        ]
        if len(card_candidates) > 0:
            return "card"
            
        # Check for form layout
        input_candidates = [
            e for e in elements
            if e.type in ['input', 'button'] and e.width > width * 0.5
        ]
        if len(input_candidates) > 2:
            return "form"
            
        # Default to generic
        return "generic"


class UIPatternLearner:
    """Learn UI patterns from app screenshots."""
    
    def __init__(self, cache_dir=None):
        """Initialize the UI pattern learner."""
        if cache_dir is None:
            cache_dir = os.path.join(project_root, "data", "ui_patterns")
            os.makedirs(cache_dir, exist_ok=True)
            
        self.cache_dir = Path(cache_dir)
        self.extractor = UIComponentExtractor()
        self.patterns = {
            'camera_interface': [],
            'results_screen': [],
            'food_log': [],
            'progress_tracking': [],
            'home_screen': []
        }
        self.templates = {}
        
        logger.info(f"Initialized UIPatternLearner with cache directory: {self.cache_dir}")
        
    def load_pattern_cache(self):
        """Load previously learned patterns from cache."""
        cache_file = self.cache_dir / "patterns.json"
        
        if cache_file.exists():
            try:
                with open(cache_file, 'r') as f:
                    cached_data = json.load(f)
                    
                if 'patterns' in cached_data:
                    self.patterns = cached_data['patterns']
                    
                if 'templates' in cached_data:
                    self.templates = cached_data['templates']
                    
                logger.info(f"Loaded patterns from cache: {len(self.patterns)} screen types, {len(self.templates)} templates")
                return True
            except Exception as e:
                logger.warning(f"Error loading pattern cache: {e}")
                
        return False
        
    def save_pattern_cache(self):
        """Save learned patterns to cache."""
        cache_file = self.cache_dir / "patterns.json"
        
        try:
            with open(cache_file, 'w') as f:
                json.dump({
                    'patterns': self.patterns,
                    'templates': self.templates
                }, f)
                
            logger.info(f"Saved patterns to cache: {len(self.patterns)} screen types, {len(self.templates)} templates")
            return True
        except Exception as e:
            logger.warning(f"Error saving pattern cache: {e}")
            return False
        
    def learn_from_screenshots(self, screenshots_dir, force_relearn=False):
        """Learn UI patterns from a directory of screenshots."""
        # Try to load from cache first, unless force_relearn is True
        if not force_relearn and self.load_pattern_cache():
            return self.patterns
            
        # Process each screenshot and learn patterns
        screenshots_dir = Path(screenshots_dir)
        logger.info(f"Learning UI patterns from: {screenshots_dir}")
        
        screenshot_files = list(screenshots_dir.glob("**/*.png")) + list(screenshots_dir.glob("**/*.jpg")) + list(screenshots_dir.glob("**/*.PNG"))
        logger.info(f"Found {len(screenshot_files)} screenshots")
        
        if not screenshot_files:
            logger.warning(f"No screenshots found in {screenshots_dir}")
            return self.patterns
            
        # Extract dominant colors from all screenshots to identify app's color scheme
        app_colors = self._extract_color_scheme(screenshot_files)
        logger.info(f"Extracted app color scheme: {app_colors}")
        
        # Store the color scheme in the patterns
        self.color_scheme = app_colors
        
        for screenshot in screenshot_files:
            # Extract components from the screenshot
            logger.info(f"Extracting components from: {screenshot.name}")
            components = self.extractor.extract_components(str(screenshot))
            
            # Add color scheme information to components
            components['color_scheme'] = self._extract_screenshot_colors(str(screenshot))
            
            # Determine screen type from filename or path
            screen_type = self._classify_screenshot(screenshot, components)
            
            # Add to patterns collection
            if screen_type in self.patterns:
                self.patterns[screen_type].append(components)
                logger.info(f"Added components to pattern: {screen_type}")
            else:
                logger.warning(f"Unknown screen type: {screen_type}")
                
        # Analyze patterns to find common elements and variations
        self._analyze_patterns()
        
        # Save to cache
        self.save_pattern_cache()
        
        return self.patterns
        
    def _extract_color_scheme(self, screenshot_files, sample_size=10):
        """Extract the dominant colors from app screenshots to identify color scheme."""
        try:
            import cv2
            import numpy as np
            from sklearn.cluster import KMeans
            
            # Sample a subset of screenshots if there are many
            if len(screenshot_files) > sample_size:
                screenshot_sample = random.sample(screenshot_files, sample_size)
            else:
                screenshot_sample = screenshot_files
            
            all_colors = []
            
            for screenshot in screenshot_sample:
                # Read image
                img = cv2.imread(str(screenshot))
                if img is None:
                    continue
                    
                # Convert to RGB
                img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                
                # Reshape to list of pixels
                pixels = img.reshape(-1, 3)
                
                # Sample pixels to make clustering faster
                pixel_sample = pixels[np.random.choice(pixels.shape[0], 
                                                      min(1000, pixels.shape[0]), 
                                                      replace=False)]
                
                all_colors.extend(pixel_sample)
            
            if not all_colors:
                return {}
            
            # Convert to numpy array
            all_colors = np.array(all_colors)
            
            # Cluster to find dominant colors
            kmeans = KMeans(n_clusters=5)
            kmeans.fit(all_colors)
            
            # Get the colors
            colors = kmeans.cluster_centers_
            
            # Convert to hex and get frequency
            color_scheme = {}
            labels = kmeans.labels_
            label_counts = np.bincount(labels)
            
            for i, color in enumerate(colors):
                hex_color = '#{:02x}{:02x}{:02x}'.format(int(color[0]), int(color[1]), int(color[2]))
                color_scheme[hex_color] = float(label_counts[i]) / len(labels)
            
            # Sort by frequency
            color_scheme = {k: v for k, v in sorted(color_scheme.items(), 
                                                   key=lambda item: item[1], 
                                                   reverse=True)}
            
            # Classify colors into primary, secondary, background, text, etc.
            classified_colors = {}
            color_list = list(color_scheme.keys())
            
            if len(color_list) >= 1:
                classified_colors['primary'] = color_list[0]
            if len(color_list) >= 2:
                classified_colors['secondary'] = color_list[1]
            if len(color_list) >= 3:
                classified_colors['background'] = color_list[2]
            if len(color_list) >= 4:
                classified_colors['text'] = color_list[3]
            if len(color_list) >= 5:
                classified_colors['accent'] = color_list[4]
            
            return {
                'dominant_colors': color_scheme,
                'classified_colors': classified_colors
            }
            
        except Exception as e:
            logger.warning(f"Error extracting color scheme: {e}")
            return {}

    def _extract_screenshot_colors(self, screenshot_path):
        """Extract colors from a single screenshot."""
        try:
            import cv2
            import numpy as np
            
            img = cv2.imread(screenshot_path)
            if img is None:
                return {}
            
            # Convert to RGB
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            
            # Create color regions
            height, width = img.shape[:2]
            
            # Header region (top 10%)
            header = img[0:int(height*0.1), :]
            
            # Content region (middle 80%)
            content = img[int(height*0.1):int(height*0.9), :]
            
            # Footer region (bottom 10%)
            footer = img[int(height*0.9):, :]
            
            # Calculate average colors for each region
            header_color = np.mean(header, axis=(0, 1)).astype(int)
            content_color = np.mean(content, axis=(0, 1)).astype(int)
            footer_color = np.mean(footer, axis=(0, 1)).astype(int)
            
            # Convert to hex
            header_hex = '#{:02x}{:02x}{:02x}'.format(header_color[0], header_color[1], header_color[2])
            content_hex = '#{:02x}{:02x}{:02x}'.format(content_color[0], content_color[1], content_color[2])
            footer_hex = '#{:02x}{:02x}{:02x}'.format(footer_color[0], footer_color[1], footer_color[2])
            
            return {
                'header': header_hex,
                'content': content_hex,
                'footer': footer_hex
            }
            
        except Exception as e:
            logger.warning(f"Error extracting screenshot colors: {e}")
            return {}
        
    def _classify_screenshot(self, screenshot_path, components):
        """Classify screenshot into a screen type."""
        # Try to determine from filename first
        name = screenshot_path.stem.lower()
        
        if 'camera' in name or 'scan' in name:
            return 'camera_interface'
        elif 'result' in name:
            return 'results_screen'
        elif 'log' in name or 'history' in name:
            return 'food_log'
        elif 'progress' in name or 'tracking' in name or 'chart' in name:
            return 'progress_tracking'
        elif 'home' in name or 'dashboard' in name:
            return 'home_screen'
            
        # If not determinable from filename, check the path
        path_str = str(screenshot_path).lower()
        
        if 'camera' in path_str:
            return 'camera_interface'
        elif 'result' in path_str:
            return 'results_screen'
        elif 'history' in path_str or 'log' in path_str:
            return 'food_log'
        elif 'progress' in path_str:
            return 'progress_tracking'
        elif 'home' in path_str:
            return 'home_screen'
            
        # If still not determined, use heuristics from components
        structure = components.get('structure', {})
        element_types = {}
        
        for section in structure.get('sections', {}).values():
            for type_name, count in section.get('element_types', {}).items():
                element_types[type_name] = element_types.get(type_name, 0) + count
                
        # Determine based on element composition
        if element_types.get('image', 0) > 3 and element_types.get('button', 0) > 1:
            # Camera interface typically has image preview and capture buttons
            return 'camera_interface'
        elif element_types.get('text', 0) > 5 and element_types.get('chart', 0) > 0:
            # Progress screens typically have lots of text and charts
            return 'progress_tracking'
        elif element_types.get('card', 0) > 1 and structure.get('layout_type') == 'list':
            # Food logs typically have list of card items
            return 'food_log'
        elif element_types.get('text', 0) > 5 and element_types.get('image', 0) > 0:
            # Results screens typically have text for nutrition and food image
            return 'results_screen'
            
        # Default to home screen
        return 'home_screen'
        
    def _analyze_patterns(self):
        """Analyze patterns to identify constants and variables."""
        for screen_type, components_list in self.patterns.items():
            if not components_list:
                continue
                
            logger.info(f"Analyzing patterns for screen type: {screen_type}")
                
            # Find elements that appear in all screenshots of this type
            constant_elements = self._find_constant_elements(components_list)
            
            # Identify variable elements and their possible values
            variable_elements = self._find_variable_elements(components_list)
            
            # Create a template for this screen type
            self.templates[screen_type] = {
                'constant_elements': constant_elements,
                'variable_elements': variable_elements,
                'layout': self._extract_layout_pattern(components_list)
            }
            
            logger.info(f"Created template for {screen_type} with {len(constant_elements)} constant elements and {len(variable_elements)} variable elements")
            
    def _find_constant_elements(self, components_list):
        """Find elements that appear consistently across screenshots."""
        if not components_list:
            return []
            
        # We need at least a reference set of elements
        reference = components_list[0]['elements']
        
        constant_candidates = []
        
        # For each element in the reference, check if similar elements exist in all others
        for ref_elem in reference:
            # Skip very small elements
            if ref_elem.width < 20 or ref_elem.height < 20:
                continue
                
            # Check if this element appears in all screenshots
            is_constant = True
            
            for components in components_list[1:]:
                # Try to find a matching element
                found_match = False
                
                for comp_elem in components['elements']:
                    # Check for similarity in position, size, and type
                    if (self._element_similarity(ref_elem, comp_elem) > 0.7):
                        found_match = True
                        break
                        
                if not found_match:
                    is_constant = False
                    break
                    
            if is_constant:
                constant_candidates.append(ref_elem.to_dict())
                
        return constant_candidates
        
    def _element_similarity(self, elem1, elem2):
        """Calculate similarity between two elements."""
        # Must be same type
        if elem1.type != elem2.type:
            return 0.0
            
        # Calculate position similarity (normalized to 0-1)
        pos_sim = 1.0 - min(
            abs(elem1.x - elem2.x) / 500,  # Normalize by assuming 1080px width
            1.0
        ) * min(
            abs(elem1.y - elem2.y) / 500,  # Normalize by assuming 1920px height
            1.0
        )
        
        # Calculate size similarity
        size_sim = 1.0 - min(
            abs(elem1.width - elem2.width) / max(elem1.width, 1),
            1.0
        ) * min(
            abs(elem1.height - elem2.height) / max(elem1.height, 1),
            1.0
        )
        
        # Text similarity if available
        text_sim = 1.0
        if elem1.text and elem2.text:
            # Simple text similarity
            text_sim = 0.0 if elem1.text.lower() != elem2.text.lower() else 1.0
            
        # Combine similarities (weighted)
        return 0.5 * pos_sim + 0.3 * size_sim + 0.2 * text_sim
        
    def _find_variable_elements(self, components_list):
        """Identify variable elements that change across screenshots."""
        if len(components_list) < 2:
            return []
            
        variable_elements = []
        
        # Get a reference set
        reference = components_list[0]
        ref_struct = reference['structure']
        
        # Define regions of interest based on the reference
        regions = {
            'food_image': {'y_range': (0.2, 0.5), 'x_range': (0.1, 0.9), 'min_size': 100},
            'calorie_value': {'y_range': (0.4, 0.7), 'x_range': (0.1, 0.9), 'min_size': 40},
            'macro_values': {'y_range': (0.5, 0.8), 'x_range': (0.1, 0.9), 'min_size': 30},
            'food_name': {'y_range': (0.3, 0.6), 'x_range': (0.1, 0.9), 'min_size': 30}
        }
        
        # For each region, find elements that vary significantly
        width, height = ref_struct.get('screen_size', (1080, 1920))
        
        for region_name, region in regions.items():
            # Convert relative to absolute coordinates
            y_min, y_max = int(region['y_range'][0] * height), int(region['y_range'][1] * height)
            x_min, x_max = int(region['x_range'][0] * width), int(region['x_range'][1] * width)
            
            # Find elements in this region across all screenshots
            region_elements = []
            
            for components in components_list:
                matching_elements = []
                
                for elem in components['elements']:
                    # Check if element is in the region
                    elem_center_x, elem_center_y = elem.get_center()
                    
                    if (x_min <= elem_center_x <= x_max and
                        y_min <= elem_center_y <= y_max and
                        elem.width >= region['min_size'] and
                        elem.height >= region['min_size']):
                        matching_elements.append(elem)
                        
                # Choose best candidate (largest or most centered)
                if matching_elements:
                    # Sort by size
                    matching_elements.sort(key=lambda e: e.get_area(), reverse=True)
                    region_elements.append(matching_elements[0])
                    
            # Check if these elements differ sufficiently
            if len(region_elements) > 1:
                differs = False
                
                # For text elements, check text content
                if region_elements[0].type in ['text', 'label', 'button'] and region_elements[0].text:
                    texts = [e.text for e in region_elements if e.text]
                    if len(set(texts)) > 1:
                        differs = True
                        
                # For image elements, assume they differ
                elif region_elements[0].type in ['image', 'icon']:
                    differs = True
                    
                # For other elements, check position/size variance
                else:
                    positions = [(e.x, e.y) for e in region_elements]
                    sizes = [(e.width, e.height) for e in region_elements]
                    
                    pos_variance = np.var([p[0] for p in positions]) + np.var([p[1] for p in positions])
                    size_variance = np.var([s[0] for s in sizes]) + np.var([s[1] for s in sizes])
                    
                    if pos_variance > 100 or size_variance > 100:  # Threshold
                        differs = True
                        
                if differs:
                    # This is a variable element
                    variable_elements.append({
                        'name': region_name,
                        'type': region_elements[0].type,
                        'position': (
                            sum(e.x for e in region_elements) / len(region_elements),
                            sum(e.y for e in region_elements) / len(region_elements)
                        ),
                        'size': (
                            sum(e.width for e in region_elements) / len(region_elements),
                            sum(e.height for e in region_elements) / len(region_elements)
                        ),
                        'observed_values': [
                            {'text': e.text} if e.text else {} for e in region_elements
                        ]
                    })
                    
        return variable_elements
                    
    def _extract_layout_pattern(self, components_list):
        """Extract general layout pattern from components."""
        if not components_list:
            return {}
            
        # Combine layout information from all screenshots
        layouts = [comp['structure'].get('layout_type', 'generic') for comp in components_list]
        sections = [comp['structure'].get('sections', {}) for comp in components_list]
        
        # Get most common layout type
        layout_type = max(set(layouts), key=layouts.count)
        
        # Aggregate section information
        aggregated_sections = {}
        
        for section_data in sections:
            for section_name, section_info in section_data.items():
                if section_name not in aggregated_sections:
                    aggregated_sections[section_name] = {
                        'element_counts': [],
                        'element_types': defaultdict(int)
                    }
                    
                aggregated_sections[section_name]['element_counts'].append(
                    section_info.get('element_count', 0)
                )
                
                for elem_type, count in section_info.get('element_types', {}).items():
                    aggregated_sections[section_name]['element_types'][elem_type] += count
                    
        # Calculate average element counts
        for section_name, section_info in aggregated_sections.items():
            counts = section_info['element_counts']
            section_info['avg_element_count'] = sum(counts) / len(counts) if counts else 0
            del section_info['element_counts']
            
        return {
            'layout_type': layout_type,
            'sections': aggregated_sections
        }
    
    def get_template(self, screen_type):
        """Get a template for a specific screen type."""
        return self.templates.get(screen_type, None)


class UITemplateBuilder:
    """Build UI templates for dynamic generation."""
    
    def __init__(self, pattern_learner):
        """Initialize with learned patterns."""
        self.pattern_learner = pattern_learner
        
    def create_ui_template(self, screen_type):
        """Create a UI template for a specific screen type."""
        template = self.pattern_learner.get_template(screen_type)
        
        if not template:
            logger.warning(f"No template available for screen type: {screen_type}")
            return None
            
        # Create a basic template with constant elements
        ui_template = {
            'type': screen_type,
            'constant_elements': template.get('constant_elements', []),
            'variable_slots': {},
            'layout': template.get('layout', {})
        }
        
        # Add slots for variable elements
        for var_element in template.get('variable_elements', []):
            ui_template['variable_slots'][var_element['name']] = {
                'type': var_element['type'],
                'position': var_element['position'],
                'size': var_element['size'],
                'possible_values': var_element.get('observed_values', [])
            }
            
        return ui_template


# Singleton pattern to access the same learner instance
_pattern_learner_instance = None

def get_pattern_learner(force_new=False):
    """Get the singleton pattern learner instance."""
    global _pattern_learner_instance
    
    if _pattern_learner_instance is None or force_new:
        _pattern_learner_instance = UIPatternLearner()
        
    return _pattern_learner_instance


if __name__ == "__main__":
    # Test the pattern learner on a directory of screenshots
    import argparse
    
    parser = argparse.ArgumentParser(description="Learn UI patterns from app screenshots")
    parser.add_argument("--screenshots", type=str, default=os.path.join(project_root, "assets/app_ui/screenshots"),
                        help="Directory containing app screenshots")
    parser.add_argument("--force", action="store_true",
                        help="Force relearning patterns")
    
    args = parser.parse_args()
    
    # Initialize pattern learner
    learner = UIPatternLearner()
    
    # Learn patterns
    patterns = learner.learn_from_screenshots(args.screenshots, args.force)
    
    # Print results
    for screen_type, components in patterns.items():
        print(f"{screen_type}: {len(components)} screenshots")
        
    # Print templates
    for screen_type, template in learner.templates.items():
        print(f"\nTemplate for {screen_type}:")
        print(f"  Constant elements: {len(template['constant_elements'])}")
        print(f"  Variable elements: {len(template['variable_elements'])}")
        
        for var_element in template['variable_elements']:
            print(f"    {var_element['name']} ({var_element['type']})") 