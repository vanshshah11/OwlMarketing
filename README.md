# OWLmarketing: Automated AI UGC Video Pipeline

This project is an end-to-end, fully automated pipeline designed to generate and post short-form, UGC-style videos on multiple social media accounts (TikTok, Instagram, and YouTube) using AI agents to market the Optimal AI calorie tracking app.

## Important Implementation Guidelines

The pipeline includes:
- **Content Analysis & Ideation:** Using a multi-agent system (OWL/CAMEL-AI) to analyze existing reels and generate creative scripts.
- **Video Generation:** Leveraging text-to-video and avatar models to create raw video content.
- **Dynamic App UI Generation:** Creating authentic, consistent UI demonstrations of the Optimal AI app.
- **Video Editing & Post-Processing:** Automatically editing the raw videos by cropping, adding captions, transitions, and trendy music.
- **Scheduling & Automated Posting:** Automating the posting process on multiple social media accounts using browser automation.

**CRITICAL: The system requires actual Optimal AI app UI assets to function properly.**

- Before generating videos, the system must be trained with:
  - Screenshots of all key app screens
  - Screen recordings of key user interactions
  - Proper app icon and branding assets
  - Color scheme and UI element details

The system ensures that all UI elements in the videos precisely match the actual Optimal AI app's look and feel:

- **Visual Consistency:** When an avatar scans a food item (e.g., avocado toast), that same food appears consistently across all UI screens (results screen, food log) with matching nutritional information.
- **Color Scheme Matching:** All generated UI uses the exact color scheme from the actual app, ensuring brand consistency.
- **Real Assets Priority:** The system prioritizes using actual app screenshots when available, only falling back to generated UI when necessary.

### 2. High-Quality Video Generation

- **Authentic UGC Style:** Videos have the authentic, slightly imperfect feel of user-generated content that performs well on social platforms.
- **Seamless App Demonstrations:** The integration between avatar video and app UI is smooth and realistic.
- **Dynamic Captions:** Automatically generated captions highlight key value propositions.

### 3. Multi-Platform Optimization

- Videos are automatically optimized for different social media platforms.
- Resolution, aspect ratio, and duration are adjusted for platform-specific requirements.
- Posting schedule is optimized for peak engagement times.

## Getting Started

### Prerequisites

- Python 3.8+
- FFmpeg
- Required Python packages (see requirements.txt)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/your-org/OWLmarketing.git
cd OWLmarketing
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up configuration files in the `config/` directory:
   - `app_ui_config.json`: Defines app UI elements, colors, and screen layouts
   - `pipeline_config.json`: Pipeline settings and parameters

4. Create necessary asset directories:
```bash
mkdir -p assets/audio/music assets/fonts assets/effects assets/app_ui/brand
```

### Running the Pipeline

- All videos use the following avatars: Emily, Sophia, Olivia, Emma, Ava, Isabella, Mia, Charlotte, Amelia, and Harper
- Each avatar has its own dedicated social media accounts across TikTok, Instagram, and YouTube
- The system posts 2 videos per day per avatar on each platform
- Avatars do not speak but are shown with background music
- Videos maintain a duration of 5-16 seconds, with an average of 8 seconds

```bash
python scripts/run_content_pipeline.py --output-dir ./output --topics "calorie tracking, meal planning"
```

- Videos focus on authentic demonstration without sales language
- Value proposition and call-to-action sections are removed
- Hooks and demonstrations are tailored to each avatar's style
- Background music is upbeat and trendy, without voice

```bash
python scripts/run_content_pipeline.py --script-file ./scripts/example_script.json
```

The pipeline includes:
- **Content Analysis & Ideation:** Using a multi-agent system (OWL/CAMEL-AI) to analyze existing reels and generate creative scripts.
- **Video Generation:** Leveraging text-to-video and avatar models (e.g., DreamBooth with Stable Diffusion) to create raw video content.
- **Video Editing & Post-Processing:** Automatically editing the raw videos by cropping, adding captions, transitions, and trendy music.
- **Scheduling & Automated Posting:** Automating the posting process on multiple social media accounts using browser automation (Playwright).

## Folder Structure

- **agents/**: Contains the multi-agent system for content analysis and ideation.
- **video_generation/**: Holds the models and scripts for generating video content.
- **video_editing/**: Contains scripts for post-processing and editing videos.
- **scheduling/**: Scripts for automating video uploads and scheduling posts.
- **scripts/**: The master pipeline orchestration script.
- **config/**: Configuration files including API keys, account credentials, and other settings.
- **assets/app_ui/**: Contains app UI assets for demo generation.
- **docs/**: Documentation for specific components.

### UI Generation Architecture

The UI generation system consists of three main components:

1. **UIPatternLearner**: Analyzes existing app screenshots to learn color schemes, UI layouts, and interaction patterns from the actual Optimal AI app.
2. **AppUIManager**: Manages UI assets and provides context-aware access to screenshots and recordings, ensuring consistent food items across different UI screens.
3. **VideoDemoGenerator**: Creates video sequences that maintain consistent UI representation and food items throughout the entire demo flow.

## Configuration

### App UI Configuration

The `app_ui_config.json` file defines all UI elements, screens, and demo sequences:

- **Color Scheme**: Defines primary, secondary, and accent colors
- **UI Elements**: Buttons, cards, input fields with styling
- **Screens**: Home screen, camera interface, results screen, food log
- **Demo Sequences**: Pre-defined sequences like "scan to result" or "browse food log"
- **Common Food Items**: Library of food items with nutritional information

## Contributing

```bash
python scripts/run_content_pipeline.py --dry-run
```

## Environment Setup

 refer to the requirements.txt file for all necessary dependencies.

## Strategy and Roadmap

See [Strategy.md](./Strategy.md) for the complete plan and future roadmap of the project.

Happy coding!
