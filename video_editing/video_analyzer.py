#!/usr/bin/env python3
# /Users/vanshshah/Desktop/OWLmarketing/video_editing/video_analyzer.py

import logging
import os
import json
from pathlib import Path
import numpy as np
import tempfile
import time
import subprocess
from typing import List, Dict, Tuple, Optional
import cv2
from collections import defaultdict
from scipy import stats
from PIL import Image, ImageDraw, ImageFont

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

class VideoAnalyzer:
    def __init__(self, training_videos_dir: str = "data/training_videos", cache_file: str = "data/style_patterns.json", pose_model: str = "movenet"):
        """
        Initialize the video analyzer.
        
        Args:
            training_videos_dir (str): Directory containing training videos
            cache_file (str): Path to cache analyzed style patterns
            pose_model (str): Model to use for pose detection ('movenet' or 'openpose')
        """
        self.training_dir = Path(training_videos_dir)
        self.cache_file = Path(cache_file)
        self.pose_model = pose_model
        
        # Create training directory if it doesn't exist
        if not self.training_dir.exists():
            logger.warning(f"Training videos directory {training_videos_dir} does not exist, creating it")
            self.training_dir.mkdir(parents=True, exist_ok=True)
        
        self.style_patterns = {
            'duration': [],
            'transitions': defaultdict(int),
            'brightness': [],
            'contrast': [],
            'text_positions': [],
            'audio_levels': []
        }
        
        # Create cache directory if it doesn't exist
        self.cache_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Try to load cached patterns first
        if self.cache_file.exists():
            self.load_patterns()
        
        # Initialize pose detection model
        self._init_pose_model()
    
    def _init_pose_model(self):
        """Initialize the pose estimation model."""
        try:
            if self.pose_model == "movenet":
                # Use TensorFlow Lite for MoveNet
                try:
                    import tensorflow as tf
                    import tensorflow_hub as hub
                    
                    # Load MoveNet model
                    self.pose_detector = hub.load("https://tfhub.dev/google/movenet/singlepose/lightning/4")
                    self.has_pose_model = True
                    logger.info("MoveNet pose estimation model loaded successfully")
                except ImportError as e:
                    logger.warning(f"Could not import TensorFlow/TF Hub: {e}")
                    self.has_pose_model = False
                except Exception as e:
                    logger.warning(f"Could not load MoveNet model: {e}")
                    self.has_pose_model = False
                
            elif self.pose_model == "openpose":
                try:
                    # Use OpenCV's DNN module with OpenPose model
                    model_dir = Path("video_generation/models/pose")
                    prototxt_path = model_dir / "openpose_pose_coco.prototxt"
                    model_path = model_dir / "openpose_pose_coco.caffemodel"
                    
                    if prototxt_path.exists() and model_path.exists():
                        self.pose_net = cv2.dnn.readNetFromCaffe(
                            str(prototxt_path), 
                            str(model_path)
                        )
                        self.has_pose_model = True
                        logger.info("OpenPose model loaded successfully")
                    else:
                        logger.warning(f"OpenPose model files not found in {model_dir}")
                        self.has_pose_model = False
                except Exception as e:
                    logger.warning(f"Could not load OpenPose model: {e}")
                    self.has_pose_model = False
            else:
                logger.warning(f"Unknown pose model: {self.pose_model}")
                self.has_pose_model = False
                
        except Exception as e:
            logger.warning(f"Could not initialize pose model: {e}")
            self.has_pose_model = False
        
    def save_patterns(self) -> None:
        """Save analyzed patterns to cache file."""
        # Convert numpy arrays and other non-serializable types to lists
        serializable_patterns = {
            'duration': self.style_patterns['duration'],
            'transitions': dict(self.style_patterns['transitions']),
            'brightness': self.style_patterns['brightness'],
            'contrast': self.style_patterns['contrast'],
            'text_positions': [list(pos) for pos in self.style_patterns['text_positions']],
            'audio_levels': self.style_patterns['audio_levels']
        }
        
        # Create directory if it doesn't exist
        self.cache_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Save to file
        with open(self.cache_file, 'w') as f:
            json.dump(serializable_patterns, f)
        
        logging.info(f"Saved style patterns to {self.cache_file}")
    
    def load_patterns(self) -> bool:
        """
        Load analyzed patterns from cache file.
        
        Returns:
            bool: True if patterns were loaded successfully
        """
        try:
            with open(self.cache_file, 'r') as f:
                patterns = json.load(f)
            
            # Convert back to appropriate types
            self.style_patterns = {
                'duration': patterns['duration'],
                'transitions': defaultdict(int, patterns['transitions']),
                'brightness': patterns['brightness'],
                'contrast': patterns['contrast'],
                'text_positions': [tuple(pos) for pos in patterns['text_positions']],
                'audio_levels': patterns['audio_levels']
            }
            
            logging.info(f"Loaded style patterns from {self.cache_file}")
            return True
            
        except Exception as e:
            logging.warning(f"Could not load cached patterns: {str(e)}")
            return False
    
    def analyze_video(self, video_path: str) -> Dict:
        """
        Analyze a single video for style patterns.
        
        Args:
            video_path (str): Path to the video file
            
        Returns:
            Dict: Analysis results
        """
        logging.info(f"Analyzing video: {video_path}")
        
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"Could not open video: {video_path}")
        
        # Get video properties
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = frame_count / fps if fps > 0 else 0
        
        # Add duration to patterns
        self.style_patterns['duration'].append(duration)
        
        # Sample frames for analysis
        frames = []
        sample_points = np.linspace(0, frame_count-1, num=10, dtype=int)
        
        for frame_idx in sample_points:
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
            ret, frame = cap.read()
            if ret:
                frames.append(frame)
                
                # Calculate brightness
                brightness = np.mean(frame)
                self.style_patterns['brightness'].append(brightness)
                
                # Calculate contrast
                contrast = np.std(frame)
                self.style_patterns['contrast'].append(contrast)
        
        # Analyze scene transitions
        transitions = self._detect_transitions(frames)
        for t_type in transitions:
            self.style_patterns['transitions'][t_type] += 1
        
        # For text positions, we need more sophisticated analysis
        # We'll add placeholder positions for now
        self.style_patterns['text_positions'].append((0.5, 0.8))  # Bottom center
        
        # Audio levels analysis would require additional processing
        # We'll add placeholder values for now
        self.style_patterns['audio_levels'].append(0.5)
        
        cap.release()
        return dict(self.style_patterns)
    
    def analyze_training_set(self, force_reanalyze: bool = False) -> Dict:
        """
        Analyze all videos in the training set.
        
        Args:
            force_reanalyze (bool): Whether to reanalyze videos even if patterns are cached
        
        Returns:
            Dict: Aggregated style patterns
        """
        # If patterns already cached and not forcing reanalysis, return cached patterns
        if self.cache_file.exists() and not force_reanalyze and self.style_patterns:
            logging.info("Using cached style patterns")
            return self.style_patterns
        
        analyzed_videos = 0
        
        # Check if training directory has video files
        has_video_files = False
        for root, _, files in os.walk(self.training_dir):
            for file in files:
                if file.lower().endswith(('.mp4', '.mov', '.avi')):
                    has_video_files = True
                    break
            if has_video_files:
                break
                
        if not has_video_files:
            logging.warning(f"No video files found in {self.training_dir}. Using default style patterns.")
            # Create default style patterns
            self.style_patterns = {
                'duration': [10.0, 15.0, 20.0],  # Default durations in seconds
                'transitions': defaultdict(int, {'fade': 2, 'cut': 5, 'dissolve': 1}),
                'brightness': [128.0, 150.0, 170.0],  # Middle to bright values
                'contrast': [40.0, 50.0, 60.0],  # Medium contrast values
                'text_positions': [(0.5, 0.8), (0.5, 0.2), (0.1, 0.5)],  # Bottom center, top center, left middle
                'audio_levels': [-18.0, -15.0, -12.0]  # Standard audio levels in dB
            }
            # Save default patterns
            self.save_patterns()
            return self.style_patterns
        
        # Clear existing patterns if reanalyzing
        if force_reanalyze:
            self.style_patterns = {
                'duration': [],
                'transitions': defaultdict(int),
                'brightness': [],
                'contrast': [],
                'text_positions': [],
                'audio_levels': []
            }
        
        # Analyze each video in training directory
        for influencer_dir in self.training_dir.iterdir():
            if not influencer_dir.is_dir():
                continue
                
            for video_file in influencer_dir.glob("*.mp4"):
                try:
                    self.analyze_video(str(video_file))
                    analyzed_videos += 1
                    if analyzed_videos % 10 == 0:
                        # Save intermediate results to avoid losing work
                        self.save_patterns()
                except Exception as e:
                    logging.error(f"Error analyzing {video_file}: {str(e)}")
        
        # Save patterns to cache file
        if analyzed_videos > 0:
            self.save_patterns()
        
        # Perform additional analysis on aggregated data
        self._aggregate_results()
        
        return self.style_patterns
    
    def _aggregate_results(self) -> Dict:
        """Aggregate analyzed patterns into results."""
        # Handle empty patterns gracefully
        if not self.style_patterns['duration']:
            return {
                'avg_duration': 0,
                'std_duration': 0,
                'popular_transitions': {},
                'avg_brightness': 128,
                'avg_contrast': 50,
                'common_text_positions': [(0.5, 0.8)],
                'audio_profile': {
                    'mean_level': 0.5,
                    'peak_level': 0.8
                }
            }
            
        return {
            'avg_duration': np.mean(self.style_patterns['duration']),
            'std_duration': np.std(self.style_patterns['duration']),
            'popular_transitions': dict(sorted(
                self.style_patterns['transitions'].items(),
                key=lambda x: x[1],
                reverse=True
            )),
            'avg_brightness': np.mean(self.style_patterns['brightness']),
            'avg_contrast': np.mean(self.style_patterns['contrast']),
            'common_text_positions': self._find_common_positions(
                self.style_patterns['text_positions']
            ),
            'audio_profile': {
                'mean_level': np.mean(self.style_patterns['audio_levels']),
                'peak_level': np.percentile(self.style_patterns['audio_levels'], 95) if self.style_patterns['audio_levels'] else 0.8
            }
        }
    
    def _detect_transitions(self, frames: List[np.ndarray]) -> Dict[str, int]:
        """
        Detect transition types between consecutive frames.
        
        Args:
            frames (List[np.ndarray]): List of video frames
            
        Returns:
            Dict[str, int]: Count of each transition type
        """
        if len(frames) < 2:
            return {"unknown": 1}
            
        transitions = defaultdict(int)
        
        for i in range(len(frames) - 1):
            frame1 = cv2.cvtColor(frames[i], cv2.COLOR_BGR2GRAY)
            frame2 = cv2.cvtColor(frames[i + 1], cv2.COLOR_BGR2GRAY)
            
            # Calculate frame difference
            diff = cv2.absdiff(frame1, frame2)
            mean_diff = np.mean(diff)
            
            # Classify transition type
            if mean_diff < 10:
                transitions['cut'] += 1
            elif mean_diff < 30:
                transitions['fade'] += 1
            else:
                transitions['dissolve'] += 1
        
        return dict(transitions)
    
    def _find_common_positions(self, positions: List[Tuple]) -> List[Tuple]:
        """
        Find common text positions using clustering.
        
        Args:
            positions (List[Tuple]): List of (x, y) positions
            
        Returns:
            List[Tuple]: Common position clusters
        """
        if not positions:
            return [(0.5, 0.8)]  # Default to bottom center
        
        if len(positions) < 2:
            return positions
            
        # Convert to numpy array
        pos_array = np.array(positions)
        
        try:
            # Use kernel density estimation to find hotspots
            kde_x = stats.gaussian_kde(pos_array[:, 0])
            kde_y = stats.gaussian_kde(pos_array[:, 1])
            
            # Find peaks
            x_peaks = self._find_peaks(kde_x, pos_array[:, 0])
            y_peaks = self._find_peaks(kde_y, pos_array[:, 1])
            
            # If no peaks found, return original positions
            if not x_peaks or not y_peaks:
                return positions
                
            return list(zip(x_peaks, y_peaks))
            
        except Exception as e:
            logging.warning(f"Error finding common positions: {e}")
            return [(0.5, 0.8)]  # Default to bottom center
    
    def _find_peaks(self, kde, data: np.ndarray) -> List[float]:
        """
        Find peaks in kernel density estimation.
        
        Args:
            kde: Kernel density estimation object
            data (np.ndarray): Input data
            
        Returns:
            List[float]: Peak positions
        """
        if len(data) == 0:
            return [0.5]  # Default middle value
            
        x_grid = np.linspace(min(data), max(data), 100)
        density = kde(x_grid)
        peaks = []
        
        for i in range(1, len(density) - 1):
            if density[i] > density[i-1] and density[i] > density[i+1]:
                peaks.append(x_grid[i])
        
        # If no peaks found, use the max density point
        if not peaks and len(density) > 0:
            peaks.append(x_grid[np.argmax(density)])
            
        return peaks
    
    def _extract_frames(self, video_path: str, start_time: float, duration: float) -> List[np.ndarray]:
        """Extract frames from a video file for the specified duration."""
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"Could not open video: {video_path}")
        
        # Get video properties
        fps = cap.get(cv2.CAP_PROP_FPS)
        
        # Calculate frame range
        start_frame = int(start_time * fps)
        num_frames = int(duration * fps)
        
        # Set frame position
        cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
        
        # Read frames
        frames = []
        for _ in range(num_frames):
            ret, frame = cap.read()
            if not ret:
                break
            frames.append(frame)
        
        cap.release()
        return frames
    
    def _add_text_overlay(self, frame: np.ndarray, text: str) -> np.ndarray:
        """Add text overlay to a frame."""
        # Convert frame to PIL Image for text rendering
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        pil_image = Image.fromarray(frame_rgb)
        draw = ImageDraw.Draw(pil_image)
        
        # Use default font for now
        font_size = 40
        try:
            font = ImageFont.truetype("arial.ttf", font_size)
        except IOError:
            # Fallback to default font if arial is not available
            font = ImageFont.load_default()
        
        # Calculate text size and position
        try:
            text_width, text_height = draw.textsize(text, font=font)
        except AttributeError:
            # For newer versions of PIL/Pillow
            text_width, text_height = draw.textbbox((0, 0), text, font=font)[2:]
        
        x = (frame.shape[1] - text_width) // 2
        y = frame.shape[0] - text_height - 20
        
        # Draw text with background
        draw.rectangle([(x-10, y-10), (x+text_width+10, y+text_height+10)], 
                      fill=(0, 0, 0, 128))
        draw.text((x, y), text, font=font, fill=(255, 255, 255))
        
        # Convert back to OpenCV format
        return cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
    
    def _detect_pose(self, frame: np.ndarray) -> Dict:
        """
        Detect human pose in a frame.
        
        Args:
            frame (np.ndarray): Input frame
            
        Returns:
            Dict: Detected pose keypoints
        """
        if not self.has_pose_model:
            logger.warning("Pose model not available. Returning empty pose.")
            return {"keypoints": []}
        
        try:
            if self.pose_model == "movenet":
                # Preprocess the image
                import tensorflow as tf
                img = tf.convert_to_tensor(cv2.resize(frame, (192, 192)))
                img = tf.expand_dims(img, axis=0)
                img = tf.cast(img, dtype=tf.int32)
                
                # Detect pose - Fix: Access the signatures correctly
                # MoveNet expects input to be passed to its serving_default signature
                if hasattr(self.pose_detector, 'signatures'):
                    # The correct way to call the model
                    results = self.pose_detector.signatures['serving_default'](tf.cast(img, tf.int32))
                    keypoints = results['output_0'].numpy().squeeze()
                else:
                    # Fallback for older TF Hub versions
                    model_fn = self.pose_detector.signatures['serving_default']
                    results = model_fn(tf.cast(img, tf.int32))
                    keypoints = results['output_0'].numpy().squeeze()
                
                # Convert to usable format
                pose_data = {"keypoints": []}
                for i in range(17):  # MoveNet uses 17 keypoints
                    y, x, score = keypoints[i]
                    if score > 0.3:  # Confidence threshold
                        pose_data["keypoints"].append({
                            "id": i,
                            "x": float(x),
                            "y": float(y),
                            "score": float(score)
                        })
                
                return pose_data
                
            elif self.pose_model == "openpose":
                # Preprocess image for OpenPose
                height, width = frame.shape[:2]
                blob = cv2.dnn.blobFromImage(frame, 1.0 / 255, (368, 368), (127.5, 127.5, 127.5), swapRB=True, crop=False)
                self.pose_net.setInput(blob)
                
                # Forward pass
                output = self.pose_net.forward()
                
                # Process output
                pose_data = {"keypoints": []}
                for i in range(output.shape[1]):  # OpenPose uses 18 keypoints
                    # Extract heatmap for current keypoint
                    heatmap = output[0, i, :, :]
                    _, conf, _, point = cv2.minMaxLoc(heatmap)
                    
                    if conf > 0.1:  # Confidence threshold
                        x = int((point[0] * width) / output.shape[3])
                        y = int((point[1] * height) / output.shape[2])
                        
                        pose_data["keypoints"].append({
                            "id": i,
                            "x": x / width,  # Normalize to 0-1
                            "y": y / height,  # Normalize to 0-1
                            "score": float(conf)
                        })
                
                return pose_data
        
        except Exception as e:
            logger.error(f"Error in pose detection: {e}")
            return {"keypoints": []}
    
    def _create_pose_control_image(self, pose_data: Dict, width: int, height: int) -> np.ndarray:
        """
        Create a control image for the pose data.
        
        Args:
            pose_data (Dict): Detected pose keypoints
            width (int): Image width
            height (int): Image height
            
        Returns:
            np.ndarray: Pose control image
        """
        # Create a blank image
        control_image = np.zeros((height, width, 3), dtype=np.uint8)
        
        # Define keypoint connections (pairs of keypoints that should be connected by lines)
        connections = [
            (0, 1), (0, 2), (1, 3), (2, 4),  # Head and shoulders
            (5, 6), (5, 7), (7, 9), (6, 8), (8, 10),  # Arms
            (5, 11), (6, 12), (11, 13), (12, 14), (13, 15), (14, 16)  # Legs
        ]
        
        # Create dictionary for quick keypoint lookup
        keypoints_dict = {kp["id"]: (int(kp["x"] * width), int(kp["y"] * height)) 
                          for kp in pose_data["keypoints"]}
        
        # Draw keypoints
        for kp in pose_data["keypoints"]:
            point = (int(kp["x"] * width), int(kp["y"] * height))
            cv2.circle(control_image, point, 3, (255, 255, 255), -1)
        
        # Draw connections
        for conn in connections:
            if conn[0] in keypoints_dict and conn[1] in keypoints_dict:
                pt1 = keypoints_dict[conn[0]]
                pt2 = keypoints_dict[conn[1]]
                cv2.line(control_image, pt1, pt2, (255, 255, 255), 2)
        
        return control_image
    
    def _generate_avatar_frame(self, avatar_key: str, pose_control: np.ndarray, avatar_config: Dict) -> np.ndarray:
        """
        Generate an avatar frame based on pose control image.
        
        Args:
            avatar_key (str): Key of the avatar to use
            pose_control (np.ndarray): Pose control image
            avatar_config (Dict): Avatar configuration dictionary
            
        Returns:
            np.ndarray: Generated avatar frame
        """
        # In a real implementation, this would use ControlNet or a similar model to generate
        # an avatar image with the pose from the control image
        
        # For now, we'll create a placeholder colored silhouette
        avatar_frame = np.copy(pose_control)
        # Convert to RGB for visualization if needed
        if len(avatar_frame.shape) == 2 or avatar_frame.shape[2] == 1:
            avatar_frame = cv2.cvtColor(avatar_frame, cv2.COLOR_GRAY2BGR)
        
        # Apply color based on avatar
        if avatar_key == "sarah":
            color_mask = np.array([0, 255, 0], dtype=np.uint8)  # Green for Sarah
        elif avatar_key == "jessica":
            color_mask = np.array([255, 0, 0], dtype=np.uint8)  # Blue for Jessica
        elif avatar_key == "mike":
            color_mask = np.array([0, 0, 255], dtype=np.uint8)  # Red for Mike
        else:
            color_mask = np.array([128, 128, 128], dtype=np.uint8)  # Gray for unknown
        
        # Apply color mask to non-zero pixels - Fix array shape mismatch
        # Create a 3D mask for RGB channels
        mask = np.any(pose_control > 0, axis=2) if len(pose_control.shape) > 2 else (pose_control > 0)
        
        # Apply to each channel separately
        for c in range(3):
            avatar_frame[:, :, c][mask] = color_mask[c]
        
        return avatar_frame
    
    def replace_human_in_frame(self, frame: np.ndarray, avatar_key: str, avatar_config: Dict) -> np.ndarray:
        """
        Detect human in frame and replace with an AI avatar.
        
        Args:
            frame (np.ndarray): Input frame
            avatar_key (str): Avatar to use for replacement
            avatar_config (Dict): Avatar configuration dictionary
            
        Returns:
            np.ndarray: Frame with human replaced by avatar
        """
        # 1. Detect human pose
        pose_data = self._detect_pose(frame)
        
        # If no pose detected, return original frame
        if not pose_data["keypoints"]:
            return frame
        
        # 2. Create pose control image
        height, width = frame.shape[:2]
        pose_control = self._create_pose_control_image(pose_data, width, height)
        
        # 3. Generate avatar frame
        avatar_frame = self._generate_avatar_frame(avatar_key, pose_control, avatar_config)
        
        # 4. Blend avatar with original background
        # Create a mask for the avatar (non-zero pixels)
        mask = np.any(avatar_frame > 0, axis=2).astype(np.uint8) * 255
        mask_inv = cv2.bitwise_not(mask)
        
        # Convert to 3-channel masks
        mask_3ch = cv2.merge([mask, mask, mask]) / 255.0
        mask_inv_3ch = cv2.merge([mask_inv, mask_inv, mask_inv]) / 255.0
        
        # Blend avatar with original background
        result = (avatar_frame * mask_3ch + frame * mask_inv_3ch).astype(np.uint8)
        
        return result
    
    def replace_humans_in_video(self, 
                              video_path: str, 
                              avatar_key: str, 
                              avatar_config: Dict,
                              output_path: Optional[str] = None,
                              output_dir: str = "data/generated_videos") -> str:
        """
        Replace humans in a video with an AI avatar.
        
        Args:
            video_path (str): Path to input video
            avatar_key (str): Avatar to use for replacement
            avatar_config (Dict): Avatar configuration dictionary
            output_path (str, optional): Path to save output video
            output_dir (str): Directory to save output video if output_path is not provided
            
        Returns:
            str: Path to output video
        """
        # Open video
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"Could not open video: {video_path}")
        
        # Get video properties
        fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        # Create output path if not provided
        if output_path is None:
            # Create output directory if it doesn't exist
            output_dir_path = Path(output_dir)
            output_dir_path.mkdir(parents=True, exist_ok=True)
            
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            output_path = str(output_dir_path / f"avatar_{avatar_key}_{timestamp}.mp4")
        
        # Create video writer
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
        
        # Process each frame
        frame_count = 0
        processed_frame = None
        
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            
            # Process frame every 2nd frame to save time (can be adjusted)
            if frame_count % 2 == 0:
                # Replace human with avatar
                processed_frame = self.replace_human_in_frame(frame, avatar_key, avatar_config)
                
                # Write processed frame
                out.write(processed_frame)
                
                # Log progress
                if frame_count % 30 == 0:
                    logger.info(f"Processing frame {frame_count}/{total_frames} ({frame_count/total_frames*100:.1f}%)")
            else:
                # Skip processing and use previous frame
                if processed_frame is not None:
                    out.write(processed_frame)  # Use the last processed frame
            
            frame_count += 1
        
        # Clean up
        cap.release()
        out.release()
        
        logger.info(f"Video processing complete. Output saved to {output_path}")
        return output_path

if __name__ == "__main__":
    analyzer = VideoAnalyzer()
    results = analyzer.analyze_training_set(force_reanalyze=True)
    logging.info("Analysis results:")
    for key, value in results.items():
        logging.info(f"{key}: {value}")