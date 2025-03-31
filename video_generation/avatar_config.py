#!/usr/bin/env python3
# /Users/vanshshah/Desktop/OWLmarketing/video_generation/avatar_config.py
# avatar_config.py: Configuration file containing:
# Detailed avatar personas with prompts for different scenarios
# Video settings (resolution, duration, etc.)
# Hook templates and content structure


AVATAR_CONFIGS = {
    "sarah": {
        "name": "Fitness Enthusiast Sarah",
        "base_prompt": "A fit, athletic woman in her late 20s with a confident smile, wearing modern workout attire, natural makeup, in a bright, modern setting, ultra realistic, 8k uhd, highly detailed facial features, professional photography, cinematic lighting",
        "variations": {
            "talking_head": "Close-up selfie video of Sarah holding her phone with outstretched arm, recording herself, energetic expression, wearing athletic top, clean gym background, ultra realistic, 8k uhd, highly detailed facial features, professional photography, cinematic lighting",
            "demo": "Sarah demonstrating a calorie tracking app on one smartphone while recording herself with a second phone in her other hand, at a gym cafe, ultra realistic, 8k uhd, highly detailed facial features, professional photography, cinematic lighting",
            "lifestyle": "Sarah meal prepping in a modern kitchen, taking a selfie video while using phone to track ingredients, ultra realistic, 8k uhd, highly detailed facial features, professional photography, cinematic lighting"
        },
        "style_prompt": "Photorealistic, high quality, natural lighting, 8k uhd, highly detailed facial features, professional photography, cinematic lighting, masterpiece, best quality, extremely detailed",
        "negative_prompt": "cartoon, anime, illustration, low quality, blurry, deformed features, bad anatomy, bad proportions, extra limbs, missing limbs, disfigured, poorly drawn face, poorly drawn hands, poorly drawn feet, poorly drawn legs, deformed, bad anatomy, wrong anatomy, extra limb, missing limb, floating limbs, disconnected limbs, mutation, ugly, disgusting, amputation"
    },
    "emily": {
        "name": "Emily",
        "base_prompt": "A white, thin woman in her mid-20s with brown eyes and blonde hair, casual trendy outfit, natural makeup, in a bright setting, ultra realistic, 8k uhd, highly detailed facial features, professional photography, cinematic lighting",
        "variations": {
            "talking_head": "Close-up selfie video of Emily holding her phone with outstretched arm, recording herself, excited expression, in a car - driving a convertible, ultra realistic, 8k uhd, highly detailed facial features, professional photography, cinematic lighting",
            "demo": "Emily demonstrating a calorie tracking app on one smartphone while recording herself with a second phone in her other hand, in a convertible car, ultra realistic, 8k uhd, highly detailed facial features, professional photography, cinematic lighting",
            "lifestyle": "Emily eating a healthy meal in her car, taking a selfie video while using phone to track food, ultra realistic, 8k uhd, highly detailed facial features, professional photography, cinematic lighting"
        },
        "style_prompt": "Photorealistic, high quality, natural lighting, 8k uhd, highly detailed facial features, professional photography, cinematic lighting, masterpiece, best quality, extremely detailed",
        "negative_prompt": "cartoon, anime, illustration, low quality, blurry, deformed features, bad anatomy, bad proportions, extra limbs, missing limbs, disfigured, poorly drawn face, poorly drawn hands, poorly drawn feet, poorly drawn legs, deformed, bad anatomy, wrong anatomy, extra limb, missing limb, floating limbs, disconnected limbs, mutation, ugly, disgusting, amputation"
    },
    "sophia": {
        "name": "Sophia",
        "base_prompt": "A black, athletic woman in her 20s with dark eyes and curly hair, stylish athleisure wear, natural makeup, in a modern gym setting, ultra realistic, 8k uhd, highly detailed facial features, professional photography, cinematic lighting",
        "variations": {
            "talking_head": "Close-up selfie video of Sophia holding her phone with outstretched arm, recording herself, shocked expression with hand on mouth, in a fitness studio, ultra realistic, 8k uhd, highly detailed facial features, professional photography, cinematic lighting",
            "demo": "Sophia demonstrating a calorie tracking app on one smartphone while recording herself with a second phone in her other hand, in a gym, showing shocked expression, ultra realistic, 8k uhd, highly detailed facial features, professional photography, cinematic lighting",
            "lifestyle": "Sophia preparing a protein shake in a gym kitchen, taking a selfie video while using phone to track nutrition, looking shocked at the results, ultra realistic, 8k uhd, highly detailed facial features, professional photography, cinematic lighting"
        },
        "style_prompt": "Photorealistic, high quality, natural lighting, 8k uhd, highly detailed facial features, professional photography, cinematic lighting, masterpiece, best quality, extremely detailed",
        "negative_prompt": "cartoon, anime, illustration, low quality, blurry, deformed features, bad anatomy, bad proportions, extra limbs, missing limbs, disfigured, poorly drawn face, poorly drawn hands, poorly drawn feet, poorly drawn legs, deformed, bad anatomy, wrong anatomy, extra limb, missing limb, floating limbs, disconnected limbs, mutation, ugly, disgusting, amputation"
    },
    "olivia": {
        "name": "Olivia",
        "base_prompt": "A white, slender woman in her mid-20s with blue eyes and red hair, elegant casual attire, natural makeup, in a bright home setting, ultra realistic, 8k uhd, highly detailed facial features, professional photography, cinematic lighting",
        "variations": {
            "talking_head": "Close-up selfie video of Olivia holding her phone with outstretched arm, recording herself, smiling happily, in a bright modern kitchen, ultra realistic, 8k uhd, highly detailed facial features, professional photography, cinematic lighting",
            "demo": "Olivia demonstrating a calorie tracking app on one smartphone while recording herself with a second phone in her other hand, in a modern kitchen, smiling cheerfully, ultra realistic, 8k uhd, highly detailed facial features, professional photography, cinematic lighting",
            "lifestyle": "Olivia preparing a healthy meal at home, taking a selfie video while using phone to track ingredients, smiling at the camera, ultra realistic, 8k uhd, highly detailed facial features, professional photography, cinematic lighting"
        },
        "style_prompt": "Photorealistic, high quality, natural lighting, 8k uhd, highly detailed facial features, professional photography, cinematic lighting, masterpiece, best quality, extremely detailed",
        "negative_prompt": "cartoon, anime, illustration, low quality, blurry, deformed features, bad anatomy, bad proportions, extra limbs, missing limbs, disfigured, poorly drawn face, poorly drawn hands, poorly drawn feet, poorly drawn legs, deformed, bad anatomy, wrong anatomy, extra limb, missing limb, floating limbs, disconnected limbs, mutation, ugly, disgusting, amputation"
    },
    "emma": {
        "name": "Emma",
        "base_prompt": "An asian, petite woman in her 20s with almond eyes and black hair, modern business casual outfit, natural makeup, in a contemporary office setting, ultra realistic, 8k uhd, highly detailed facial features, professional photography, cinematic lighting",
        "variations": {
            "talking_head": "Close-up selfie video of Emma holding her phone with outstretched arm, recording herself, serious confident expression, in a modern office, ultra realistic, 8k uhd, highly detailed facial features, professional photography, cinematic lighting",
            "demo": "Emma demonstrating a calorie tracking app on one smartphone while recording herself with a second phone in her other hand, at an office desk, looking confident, ultra realistic, 8k uhd, highly detailed facial features, professional photography, cinematic lighting",
            "lifestyle": "Emma eating lunch at her desk, taking a selfie video while using phone to track her meal, with a serious professional demeanor, ultra realistic, 8k uhd, highly detailed facial features, professional photography, cinematic lighting"
        },
        "style_prompt": "Photorealistic, high quality, natural lighting, 8k uhd, highly detailed facial features, professional photography, cinematic lighting, masterpiece, best quality, extremely detailed",
        "negative_prompt": "cartoon, anime, illustration, low quality, blurry, deformed features, bad anatomy, bad proportions, extra limbs, missing limbs, disfigured, poorly drawn face, poorly drawn hands, poorly drawn feet, poorly drawn legs, deformed, bad anatomy, wrong anatomy, extra limb, missing limb, floating limbs, disconnected limbs, mutation, ugly, disgusting, amputation"
    },
    "ava": {
        "name": "Ava",
        "base_prompt": "A hispanic, curvy woman in her mid-20s with hazel eyes and brunette hair, fashionable activewear, natural makeup, in a bright fitness setting, ultra realistic, 8k uhd, highly detailed facial features, professional photography, cinematic lighting",
        "variations": {
            "talking_head": "Close-up selfie video of Ava holding her phone with outstretched arm, recording herself, winking playfully, in a bright gym setting, ultra realistic, 8k uhd, highly detailed facial features, professional photography, cinematic lighting",
            "demo": "Ava demonstrating a calorie tracking app on one smartphone while recording herself with a second phone in her other hand, at a juice bar, winking playfully, ultra realistic, 8k uhd, highly detailed facial features, professional photography, cinematic lighting",
            "lifestyle": "Ava preparing a healthy smoothie, taking a selfie video while using phone to track ingredients, with a flirty expression, ultra realistic, 8k uhd, highly detailed facial features, professional photography, cinematic lighting"
        },
        "style_prompt": "Photorealistic, high quality, natural lighting, 8k uhd, highly detailed facial features, professional photography, cinematic lighting, masterpiece, best quality, extremely detailed",
        "negative_prompt": "cartoon, anime, illustration, low quality, blurry, deformed features, bad anatomy, bad proportions, extra limbs, missing limbs, disfigured, poorly drawn face, poorly drawn hands, poorly drawn feet, poorly drawn legs, deformed, bad anatomy, wrong anatomy, extra limb, missing limb, floating limbs, disconnected limbs, mutation, ugly, disgusting, amputation"
    },
    "isabella": {
        "name": "Isabella",
        "base_prompt": "A white, elegant woman in her early 30s with green eyes and light brown hair, stylish casual wear, natural makeup, in a sophisticated home setting, ultra realistic, 8k uhd, highly detailed facial features, professional photography, cinematic lighting",
        "variations": {
            "talking_head": "Close-up selfie video of Isabella holding her phone with outstretched arm, recording herself, laughing joyfully, in a well-decorated living room, ultra realistic, 8k uhd, highly detailed facial features, professional photography, cinematic lighting",
            "demo": "Isabella demonstrating a calorie tracking app on one smartphone while recording herself with a second phone in her other hand, in an elegant kitchen, laughing at something amusing, ultra realistic, 8k uhd, highly detailed facial features, professional photography, cinematic lighting",
            "lifestyle": "Isabella hosting a dinner party, taking a selfie video while using phone to track ingredients for a recipe, with an amused expression, ultra realistic, 8k uhd, highly detailed facial features, professional photography, cinematic lighting"
        },
        "style_prompt": "Photorealistic, high quality, natural lighting, 8k uhd, highly detailed facial features, professional photography, cinematic lighting, masterpiece, best quality, extremely detailed",
        "negative_prompt": "cartoon, anime, illustration, low quality, blurry, deformed features, bad anatomy, bad proportions, extra limbs, missing limbs, disfigured, poorly drawn face, poorly drawn hands, poorly drawn feet, poorly drawn legs, deformed, bad anatomy, wrong anatomy, extra limb, missing limb, floating limbs, disconnected limbs, mutation, ugly, disgusting, amputation"
    },
    "mia": {
        "name": "Mia",
        "base_prompt": "An african american, athletic woman in her mid-20s with brown eyes and short hair, trendy fitness wear, natural makeup, in a modern exercise space, ultra realistic, 8k uhd, highly detailed facial features, professional photography, cinematic lighting",
        "variations": {
            "talking_head": "Close-up selfie video of Mia holding her phone with outstretched arm, recording herself, surprised expression with raised eyebrows, in a fitness center, ultra realistic, 8k uhd, highly detailed facial features, professional photography, cinematic lighting",
            "demo": "Mia demonstrating a calorie tracking app on one smartphone while recording herself with a second phone in her other hand, at a fitness studio, looking surprised, ultra realistic, 8k uhd, highly detailed facial features, professional photography, cinematic lighting",
            "lifestyle": "Mia after a workout, taking a selfie video while using phone to track her post-workout meal, with surprised expression at the calorie count, ultra realistic, 8k uhd, highly detailed facial features, professional photography, cinematic lighting"
        },
        "style_prompt": "Photorealistic, high quality, natural lighting, 8k uhd, highly detailed facial features, professional photography, cinematic lighting, masterpiece, best quality, extremely detailed",
        "negative_prompt": "cartoon, anime, illustration, low quality, blurry, deformed features, bad anatomy, bad proportions, extra limbs, missing limbs, disfigured, poorly drawn face, poorly drawn hands, poorly drawn feet, poorly drawn legs, deformed, bad anatomy, wrong anatomy, extra limb, missing limb, floating limbs, disconnected limbs, mutation, ugly, disgusting, amputation"
    },
    "charlotte": {
        "name": "Charlotte",
        "base_prompt": "A white, tall woman in her late 20s with blue eyes and blonde hair, elegant casual style, natural makeup, in a bright modern interior, ultra realistic, 8k uhd, highly detailed facial features, professional photography, cinematic lighting",
        "variations": {
            "talking_head": "Close-up selfie video of Charlotte holding her phone with outstretched arm, recording herself, smiling happily, in a stylish home setting, ultra realistic, 8k uhd, highly detailed facial features, professional photography, cinematic lighting",
            "demo": "Charlotte demonstrating a calorie tracking app on one smartphone while recording herself with a second phone in her other hand, in a modern dining area, smiling cheerfully, ultra realistic, 8k uhd, highly detailed facial features, professional photography, cinematic lighting",
            "lifestyle": "Charlotte preparing a gourmet meal, taking a selfie video while using phone to track ingredients, with a bright cheerful smile, ultra realistic, 8k uhd, highly detailed facial features, professional photography, cinematic lighting"
        },
        "style_prompt": "Photorealistic, high quality, natural lighting, 8k uhd, highly detailed facial features, professional photography, cinematic lighting, masterpiece, best quality, extremely detailed",
        "negative_prompt": "cartoon, anime, illustration, low quality, blurry, deformed features, bad anatomy, bad proportions, extra limbs, missing limbs, disfigured, poorly drawn face, poorly drawn hands, poorly drawn feet, poorly drawn legs, deformed, bad anatomy, wrong anatomy, extra limb, missing limb, floating limbs, disconnected limbs, mutation, ugly, disgusting, amputation"
    },
    "amelia": {
        "name": "Amelia",
        "base_prompt": "A mixed race, average build woman in her mid-20s with green eyes and dark hair, stylish casual wear, natural makeup, in a modern apartment setting, ultra realistic, 8k uhd, highly detailed facial features, professional photography, cinematic lighting",
        "variations": {
            "talking_head": "Close-up selfie video of Amelia holding her phone with outstretched arm, recording herself, gesturing with free hand during conversation, in a contemporary living space, ultra realistic, 8k uhd, highly detailed facial features, professional photography, cinematic lighting",
            "demo": "Amelia demonstrating a calorie tracking app on one smartphone while recording herself with a second phone in her other hand, in a modern apartment, using hand gestures while explaining, ultra realistic, 8k uhd, highly detailed facial features, professional photography, cinematic lighting",
            "lifestyle": "Amelia at a cafe, taking a selfie video while using phone to track her coffee and snack, gesturing enthusiastically as she talks, ultra realistic, 8k uhd, highly detailed facial features, professional photography, cinematic lighting"
        },
        "style_prompt": "Photorealistic, high quality, natural lighting, 8k uhd, highly detailed facial features, professional photography, cinematic lighting, masterpiece, best quality, extremely detailed",
        "negative_prompt": "cartoon, anime, illustration, low quality, blurry, deformed features, bad anatomy, bad proportions, extra limbs, missing limbs, disfigured, poorly drawn face, poorly drawn hands, poorly drawn feet, poorly drawn legs, deformed, bad anatomy, wrong anatomy, extra limb, missing limb, floating limbs, disconnected limbs, mutation, ugly, disgusting, amputation"
    },
    "harper": {
        "name": "Harper",
        "base_prompt": "A white, slender woman in her early 20s with grey eyes and red hair, trendy casual style, natural makeup, in a relaxed outdoor setting, ultra realistic, 8k uhd, highly detailed facial features, professional photography, cinematic lighting",
        "variations": {
            "talking_head": "Close-up selfie video of Harper holding her phone with outstretched arm, recording herself, relaxed cool posture, in a hip cafe or park, ultra realistic, 8k uhd, highly detailed facial features, professional photography, cinematic lighting",
            "demo": "Harper demonstrating a calorie tracking app on one smartphone while recording herself with a second phone in her other hand, in a casual cool setting, relaxed posture, ultra realistic, 8k uhd, highly detailed facial features, professional photography, cinematic lighting",
            "lifestyle": "Harper at a trendy restaurant, taking a selfie video while using phone to track her meal, with a laid-back cool vibe, ultra realistic, 8k uhd, highly detailed facial features, professional photography, cinematic lighting"
        },
        "style_prompt": "Photorealistic, high quality, natural lighting, 8k uhd, highly detailed facial features, professional photography, cinematic lighting, masterpiece, best quality, extremely detailed",
        "negative_prompt": "cartoon, anime, illustration, low quality, blurry, deformed features, bad anatomy, bad proportions, extra limbs, missing limbs, disfigured, poorly drawn face, poorly drawn hands, poorly drawn feet, poorly drawn legs, deformed, bad anatomy, wrong anatomy, extra limb, missing limb, floating limbs, disconnected limbs, mutation, ugly, disgusting, amputation"
    }
}

# Video generation settings
VIDEO_SETTINGS = {
    "tiktok": {
        "fps": 30,
        "resolution": (1080, 1920),  # Vertical video format (9:16)
        "duration": {
            "min": 5,
            "max": 13,
            "target": 8
        }
    },
    "instagram": {
        "fps": 30,
        "resolution": (1080, 1920),  # Vertical video format (9:16)
        "duration": {
            "min": 5,
            "max": 13,
            "target": 8
        }
    },
    "youtube": {
    "fps": 30,
        "resolution": (1080, 1920),  # Vertical video format for YouTube Shorts
    "duration": {
            "min": 5,
            "max": 60,
            "target": 15
        }
    }
}

# Hook templates based on analyzed videos
HOOK_TEMPLATES = [
    "Struggling with calorie tracking? {avatar_name} shows you a better way...",
    "What if you could track your meals in seconds? {avatar_name} reveals how...",
    "Stop guessing your portions! {avatar_name} shares the secret to accurate tracking...",
    "Tired of manual food logging? {avatar_name} discovered this game-changer...",
    "Want to know exactly what's in your food? {avatar_name} demonstrates this simple trick..."
]

# Content sequence structure
CONTENT_SEQUENCE = {
    "hook": {
        "elements": ["attention_grabber", "pain_point", "curiosity_builder"]
    },
    "demo": {
        "elements": ["app_showcase", "feature_highlight", "ease_of_use"]
    }
}
