#!/usr/bin/env python3
"""
UI Consistency Test Script - Verifies that the UI generation system maintains consistency
across all screens in a demo sequence for the Optimal AI app.

This script:
1. Loads pre-defined food items from config
2. Generates complete demo sequences for each food item
3. Creates a test video that demonstrates UI consistency
4. Outputs a report of consistency checks

Usage:
    python scripts/test_ui_consistency.py --output-dir ./test_output
"""

import os
import sys
import json
import logging
import argparse
from pathlib import Path
import time
import shutil

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(project_root)

# Import local modules
from video_generation.app_ui_manager import get_ui_manager
from video_generation.ui_generator import get_ui_generator
from video_generation.video_demo_generator import get_demo_generator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('ui_consistency_test')

def load_food_items():
    """Load food items from config file."""
    config_path = os.path.join(project_root, 'config', 'app_ui_config.json')
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
            food_items = config.get('common_food_items', [])
            logger.info(f"Loaded {len(food_items)} food items from config")
            return food_items
    except Exception as e:
        logger.error(f"Failed to load food items: {e}")
        return []

def generate_test_sequences(food_items, output_dir, sequence_names=None):
    """Generate test sequences for each food item."""
    if sequence_names is None:
        sequence_names = ['scan_to_result', 'browse_food_log', 'result_to_log']
    
    demo_generator = get_demo_generator()
    results = []
    
    for food_item in food_items:
        food_name = food_item['name']
        logger.info(f"Generating test sequences for food item: {food_name}")
        
        food_dir = os.path.join(output_dir, food_name.lower().replace(' ', '_'))
        os.makedirs(food_dir, exist_ok=True)
        
        for sequence_name in sequence_names:
            sequence_dir = os.path.join(food_dir, sequence_name)
            os.makedirs(sequence_dir, exist_ok=True)
            
            output_video = os.path.join(food_dir, f"{sequence_name}.mp4")
            
            try:
                start_time = time.time()
                sequence = demo_generator.generate_demo_sequence(
                    sequence_name=sequence_name,
                    food_item=food_item,
                    output_dir=sequence_dir,
                    output_video=output_video
                )
                elapsed_time = time.time() - start_time
                
                result = {
                    'food_item': food_item,
                    'sequence_name': sequence_name,
                    'output_video': output_video,
                    'output_dir': sequence_dir,
                    'success': True,
                    'elapsed_time': elapsed_time,
                    'screens': len(sequence.get('screens', [])),
                    'metadata': sequence
                }
            except Exception as e:
                logger.error(f"Error generating sequence {sequence_name} for {food_name}: {e}")
                result = {
                    'food_item': food_item,
                    'sequence_name': sequence_name,
                    'output_dir': sequence_dir,
                    'success': False,
                    'error': str(e)
                }
            
            results.append(result)
    
    return results

def verify_consistency(results):
    """Verify food item consistency across screens."""
    logger.info("Verifying UI consistency across sequences")
    consistency_report = []
    
    for result in results:
        if not result.get('success'):
            continue
            
        food_item = result['food_item']
        food_name = food_item['name']
        sequence_name = result['sequence_name']
        
        # Check if metadata contains food item
        metadata = result.get('metadata', {})
        metadata_food_item = metadata.get('food_item', {})
        
        # Check if food item in metadata matches the original food item
        food_consistent = metadata_food_item.get('name') == food_name
        
        # Check if screens maintain food item consistency
        screens = metadata.get('screens', [])
        screen_consistency = []
        
        for screen in screens:
            screen_food_item = screen.get('food_item', {})
            screen_consistent = screen_food_item.get('name') == food_name
            screen_consistency.append({
                'screen_type': screen.get('type'),
                'consistent': screen_consistent
            })
        
        # Overall consistency for this sequence
        all_screens_consistent = all(sc['consistent'] for sc in screen_consistency)
        
        consistency_report.append({
            'food_item': food_name,
            'sequence_name': sequence_name,
            'metadata_consistent': food_consistent,
            'screens_consistent': all_screens_consistent,
            'screen_details': screen_consistency,
            'overall_consistent': food_consistent and all_screens_consistent
        })
    
    return consistency_report

def create_consistency_report(consistency_report, output_dir):
    """Create a human-readable report of consistency checks."""
    report_path = os.path.join(output_dir, 'consistency_report.txt')
    
    with open(report_path, 'w') as f:
        f.write("# UI Consistency Test Report\n\n")
        f.write(f"Generated on: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        # Overall summary
        consistent_count = sum(1 for r in consistency_report if r['overall_consistent'])
        total_count = len(consistency_report)
        f.write(f"## Summary\n\n")
        f.write(f"- Total sequences tested: {total_count}\n")
        f.write(f"- Consistent sequences: {consistent_count}\n")
        f.write(f"- Consistency rate: {consistent_count/total_count*100:.2f}%\n\n")
        
        # Detailed report
        f.write("## Detailed Results\n\n")
        
        for report in consistency_report:
            f.write(f"### {report['food_item']} - {report['sequence_name']}\n\n")
            f.write(f"- Metadata consistent: {'✅' if report['metadata_consistent'] else '❌'}\n")
            f.write(f"- All screens consistent: {'✅' if report['screens_consistent'] else '❌'}\n")
            f.write(f"- Overall consistent: {'✅' if report['overall_consistent'] else '❌'}\n\n")
            
            if not report['screens_consistent']:
                f.write("Screen consistency details:\n")
                for screen in report['screen_details']:
                    f.write(f"- {screen['screen_type']}: {'✅' if screen['consistent'] else '❌'}\n")
                f.write("\n")
    
    logger.info(f"Consistency report written to {report_path}")
    return report_path

def create_combined_video(results, output_dir):
    """Create a combined video demonstrating UI consistency."""
    # Find ffmpeg
    import shutil
    ffmpeg_path = shutil.which('ffmpeg')
    if not ffmpeg_path:
        logger.error("ffmpeg not found, skipping combined video creation")
        return None
    
    # Get successful results with videos
    successful_results = [r for r in results if r.get('success') and os.path.exists(r.get('output_video', ''))]
    if not successful_results:
        logger.error("No successful demo sequences to combine")
        return None
    
    # Create a file with video paths
    videos_file = os.path.join(output_dir, 'videos_list.txt')
    with open(videos_file, 'w') as f:
        for result in successful_results:
            f.write(f"file '{os.path.abspath(result['output_video'])}'\n")
    
    # Output combined video
    combined_video = os.path.join(output_dir, 'ui_consistency_demo.mp4')
    
    # Run ffmpeg to concatenate videos
    cmd = [
        ffmpeg_path, '-y', '-f', 'concat', '-safe', '0',
        '-i', videos_file, '-c', 'copy', combined_video
    ]
    
    try:
        import subprocess
        subprocess.run(cmd, check=True)
        logger.info(f"Created combined demo video: {combined_video}")
        return combined_video
    except Exception as e:
        logger.error(f"Failed to create combined video: {e}")
        return None

def main():
    """Main function."""
    # Parse arguments
    parser = argparse.ArgumentParser(description="Test UI consistency in demo sequences")
    parser.add_argument('--output-dir', type=str, default='test_output',
                       help='Directory to save test output')
    parser.add_argument('--food-items', type=str, default=None,
                       help='Comma-separated list of food items to test (default: all)')
    parser.add_argument('--sequences', type=str, default='scan_to_result',
                       help='Comma-separated list of sequences to test')
    
    args = parser.parse_args()
    
    # Create output directory
    output_dir = os.path.abspath(args.output_dir)
    os.makedirs(output_dir, exist_ok=True)
    
    # Load food items
    all_food_items = load_food_items()
    
    # Filter food items if specified
    if args.food_items:
        food_names = [name.strip() for name in args.food_items.split(',')]
        food_items = [item for item in all_food_items if item['name'] in food_names]
        if not food_items:
            logger.error(f"No matching food items found for: {args.food_items}")
            return 1
    else:
        # Use only the first item if none specified to keep the test quick
        food_items = [all_food_items[0]]
    
    # Parse sequences
    sequences = [seq.strip() for seq in args.sequences.split(',')]
    
    # Generate test sequences
    results = generate_test_sequences(food_items, output_dir, sequences)
    
    # Verify consistency
    consistency_report = verify_consistency(results)
    
    # Create consistency report
    report_path = create_consistency_report(consistency_report, output_dir)
    
    # Create combined video
    combined_video = create_combined_video(results, output_dir)
    
    # Print summary
    print("\nUI Consistency Test Completed")
    print(f"- Tested {len(food_items)} food items across {len(sequences)} sequences")
    
    consistent_count = sum(1 for r in consistency_report if r['overall_consistent'])
    total_count = len(consistency_report)
    consistency_rate = consistent_count/total_count*100 if total_count > 0 else 0
    
    print(f"- Consistency rate: {consistency_rate:.2f}%")
    print(f"- Report saved to: {report_path}")
    
    if combined_video:
        print(f"- Demo video saved to: {combined_video}")
    
    # Return success if all were consistent
    return 0 if consistent_count == total_count else 1

if __name__ == "__main__":
    sys.exit(main()) 