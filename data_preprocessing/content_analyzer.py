#!/usr/bin/env python3

import os
import logging
from pathlib import Path
from typing import Dict, List, Set
import json
import shutil
from collections import defaultdict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s'
)

class ContentAnalyzer:
    def __init__(
        self,
        frames_dir: str = "data/extracted_frames",
        output_dir: str = "data/analyzed_content",
        brand_name: str = "Optimal AI"
    ):
        self.frames_dir = Path(frames_dir)
        self.output_dir = Path(output_dir)
        self.brand_name = brand_name
        
        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Content patterns for Optimal AI
        self.content_patterns = {
            "hook_patterns": [
                "Tired of guessing calories?",
                f"Meet {brand_name}",
                "Track calories in seconds",
                "AI-powered food tracking",
                "No more manual logging"
            ],
            "value_props": [
                "Instant calorie counting",
                "AI-powered accuracy",
                "Save hours daily",
                "Track anything, anywhere",
                "Smart meal suggestions"
            ],
            "user_personas": [
                "busy_professional",
                "fitness_enthusiast",
                "health_conscious",
                "weight_loss_journey",
                "meal_prep_lover"
            ]
        }
        
    def analyze_frame_categories(self) -> Dict[str, List[str]]:
        """Analyze the distribution of frames across categories."""
        category_stats = defaultdict(list)
        
        for category_dir in self.frames_dir.iterdir():
            if category_dir.is_dir():
                frames = list(category_dir.glob("*.jpg"))
                category_stats[category_dir.name] = [
                    frame.name for frame in frames
                ]
                
                logging.info(f"Category {category_dir.name}: {len(frames)} frames")
                
        return dict(category_stats)
    
    def generate_content_plan(self, category_stats: Dict[str, List[str]]) -> Dict:
        """Generate a content repurposing plan based on analyzed frames."""
        content_plan = {
            "optimal_ai_specific": {
                "hooks": [],
                "demonstrations": [],
                "testimonials": [],
                "educational": []
            }
        }
        
        # Generate hooks based on different categories
        if "hook_moments" in category_stats:
            content_plan["optimal_ai_specific"]["hooks"] = [
                {
                    "frame_reference": frame,
                    "suggested_hook": hook,
                    "target_persona": persona
                }
                for frame, hook, persona in zip(
                    category_stats["hook_moments"][:5],
                    self.content_patterns["hook_patterns"],
                    self.content_patterns["user_personas"]
                )
            ]
        
        # Plan app demonstrations
        if "app_demos" in category_stats:
            content_plan["optimal_ai_specific"]["demonstrations"] = [
                {
                    "frame_reference": frame,
                    "value_prop": value_prop,
                    "focus": "Optimal AI interface simplicity"
                }
                for frame, value_prop in zip(
                    category_stats["app_demos"][:5],
                    self.content_patterns["value_props"]
                )
            ]
        
        return content_plan
    
    def save_content_plan(self, content_plan: Dict) -> None:
        """Save the content plan to a JSON file."""
        output_file = self.output_dir / "content_plan.json"
        
        with open(output_file, 'w') as f:
            json.dump(content_plan, f, indent=2)
            
        logging.info(f"Content plan saved to {output_file}")
    
    def analyze_and_plan(self) -> None:
        """Main method to analyze content and generate a plan."""
        try:
            # Analyze frame categories
            category_stats = self.analyze_frame_categories()
            
            # Generate content plan
            content_plan = self.generate_content_plan(category_stats)
            
            # Save the plan
            self.save_content_plan(content_plan)
            
            logging.info("Content analysis and planning completed successfully")
            
        except Exception as e:
            logging.error(f"Error during content analysis: {str(e)}")

def main():
    analyzer = ContentAnalyzer(brand_name="Optimal AI")
    analyzer.analyze_and_plan()

if __name__ == "__main__":
    main() 