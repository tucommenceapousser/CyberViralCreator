import os
import uuid
import json
import logging
from werkzeug.utils import secure_filename
from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {'mp3', 'mp4'}
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
openai_client = OpenAI(api_key=OPENAI_API_KEY)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def generate_secure_filename(filename):
    """Generate a secure filename with UUID to prevent collisions"""
    secure_name = secure_filename(filename)
    filename_without_ext, extension = os.path.splitext(secure_name)
    return f"{filename_without_ext}_{str(uuid.uuid4())}{extension}"

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def transcribe_audio(file_path):
    """Transcribe audio file using OpenAI's API"""
    try:
        with open(file_path, "rb") as audio_file:
            response = openai_client.audio.transcriptions.create(
                file=audio_file,
                model="whisper-1",
                response_format="text"
            )
            return response
    except Exception as e:
        logger.error(f"Error transcribing audio: {str(e)}")
        raise

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def generate_viral_content(
    theme,
    file_type,
    tone="professional",
    platform="tiktok",
    length="short",
    language="en",
    transcription=None,
    content_format="story",
    target_emotion="neutral",
    call_to_action="follow",
    effect_intensity="medium"
):
    """
    Generate viral content ideas using OpenAI API with enhanced parameters and transcription context
    """
    logger.info(f"Generating viral content for {file_type} file with theme: {theme}")
    
    length_guides = {
        "short": "30-60 seconds",
        "medium": "1-3 minutes",
        "long": "3-5 minutes"
    }

    # Enhanced platform-specific optimization guidelines
    platform_specifics = {
        "tiktok": {
            "tips": [
                "Hook viewers in first 3 seconds",
                "Use trending sounds strategically",
                "Implement pattern interrupts every 2-3 seconds",
                "End with strong call-to-action"
            ],
            "hashtag_count": 5,
            "optimal_posting_times": ["9 AM", "12 PM", "7 PM"],
            "content_structure": "Hook (3s) → Context (7s) → Main Content (20-30s) → CTA (5s)",
            "engagement_triggers": ["Duets", "Stitch", "Comment-to-unlock", "Use trending sounds"]
        },
        "youtube": {
            "tips": [
                "Craft compelling thumbnail and title",
                "Include cards and end screens",
                "Optimize first 30 seconds for retention",
                "Use chapters for longer content"
            ],
            "hashtag_count": 8,
            "optimal_posting_times": ["3 PM", "6 PM", "9 PM"],
            "content_structure": "Hook (15s) → Intro (30s) → Main Content → Summary → CTA",
            "engagement_triggers": ["Poll cards", "End screens", "Pinned comments", "Community posts"]
        },
        "instagram": {
            "tips": [
                "Use carousel posts for higher engagement",
                "Implement visual storytelling",
                "Include location tags",
                "Cross-promote with Reels"
            ],
            "hashtag_count": 10,
            "optimal_posting_times": ["11 AM", "2 PM", "7 PM"],
            "content_structure": "Visual hook → Story progression → Value delivery → CTA",
            "engagement_triggers": ["Save this post", "Share to stories", "Poll stickers", "Quiz stickers"]
        }
    }

    # Enhanced theme-based content strategies
    theme_strategies = {
        "anonymous": {
            "visual_elements": ["Mask imagery", "Dark backgrounds", "Glitch effects"],
            "storytelling": "Mystery and revelation narrative",
            "music": "Electronic, bass-heavy background tracks",
            "effect_intensities": {
                "low": ["Subtle glitch", "Light distortion"],
                "medium": ["Moderate glitch", "Voice modulation"],
                "high": ["Heavy glitch", "Full anonymization"]
            }
        },
        "cyber": {
            "visual_elements": ["Matrix-style effects", "Code snippets", "Futuristic UI"],
            "storytelling": "Technical revelation and future implications",
            "music": "Synthwave or cyberpunk-style background",
            "effect_intensities": {
                "low": ["Basic matrix rain", "Simple overlays"],
                "medium": ["Animated code", "Digital transitions"],
                "high": ["Full matrix effects", "Complex animations"]
            }
        },
        "hacking": {
            "visual_elements": ["Terminal interfaces", "Code execution", "System access visuals"],
            "storytelling": "Problem-solution-impact structure",
            "music": "Intense, suspenseful background tracks",
            "effect_intensities": {
                "low": ["Command line overlay", "Basic typing effect"],
                "medium": ["Multiple terminals", "Code execution"],
                "high": ["System breach simulation", "Multiple screens"]
            }
        },
        "hacktivism": {
            "visual_elements": ["Impact statistics", "Call-to-action graphics", "Movement symbols"],
            "storytelling": "Cause-effect-solution narrative",
            "music": "Dramatic, empowering background music",
            "effect_intensities": {
                "low": ["Simple overlays", "Basic stats"],
                "medium": ["Animated stats", "Emphasis effects"],
                "high": ["Full screen transitions", "Dynamic visualizations"]
            }
        }
    }

    # Content format strategies
    format_strategies = {
        "story": {
            "structure": "Setup → Conflict → Resolution",
            "duration_distribution": "20% setup, 60% conflict, 20% resolution"
        },
        "tutorial": {
            "structure": "Problem → Solution → Implementation → Results",
            "duration_distribution": "10% problem, 30% solution, 40% implementation, 20% results"
        },
        "review": {
            "structure": "Introduction → Features → Analysis → Verdict",
            "duration_distribution": "15% intro, 35% features, 35% analysis, 15% verdict"
        }
    }

    # Emotional impact strategies
    emotion_strategies = {
        "neutral": {
            "tone": "Balanced and informative",
            "pacing": "Steady and consistent"
        },
        "excitement": {
            "tone": "High energy and dynamic",
            "pacing": "Fast-paced with quick cuts"
        },
        "curiosity": {
            "tone": "Mysterious and intriguing",
            "pacing": "Strategic information revelation"
        },
        "surprise": {
            "tone": "Unexpected and dramatic",
            "pacing": "Build up to reveal moments"
        }
    }

    # Build enhanced system message
    system_content = (
        "You are an expert viral content strategist specializing in cutting-edge content optimization. "
        f"Generate content optimized for {platform.upper()} in {language.upper()}, "
        f"incorporating {theme.upper()} theme elements with {tone} tone and {target_emotion} emotional impact. "
        f"Content duration: {length_guides[length]}, Format: {content_format}, "
        f"Effect Intensity: {effect_intensity}, Call-to-action: {call_to_action}. "
        f"Follow platform best practices: {platform_specifics[platform]['content_structure']}. "
        "\nAnalyze and include:"
        "\n1. Viral Potential Factors"
        "\n2. Engagement Optimization"
        "\n3. Platform-Specific Features"
        "\n4. Theme Integration"
        "\n5. Audience Psychology"
        "\n6. Emotional Triggers"
        "\n7. Content Structure"
        "\n8. Visual Effects"
        "\n9. Audio Elements"
        "\n10. Call-to-Action Strategy"
        "\nReturn structured JSON with:"
        "\n- title"
        "\n- description"
        "\n- hashtags (array)"
        "\n- target_audience"
        "\n- hooks (array)"
        "\n- content_structure"
        "\n- viral_triggers (array)"
        "\n- platform_specific_tips"
        "\n- optimal_posting_times"
        "\n- engagement_strategies"
        "\n- visual_elements"
        "\n- audio_recommendations"
        "\n- emotional_triggers"
        "\n- pacing_guide"
        "\n- effect_recommendations"
        "\n- viral_potential_score (1-10)"
        "\n- improvement_suggestions"
    )

    # Build enhanced user message
    user_content = [
        f"Create viral content for {file_type} with theme '{theme}'.",
        f"Optimize for {platform} using {theme_strategies[theme]['storytelling']}.",
        f"Format: {format_strategies[content_format]['structure']}.",
        f"Emotional impact: {emotion_strategies[target_emotion]['tone']}.",
        f"Effect intensity: {theme_strategies[theme]['effect_intensities'][effect_intensity][0]}.",
        f"Call-to-action focus: {call_to_action}.",
        f"Target length: {length_guides[length]}.",
    ]
    
    if transcription:
        user_content.append(f"Context from transcription: '{transcription}'")
        
    try:
        response = openai_client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_content},
                {"role": "user", "content": " ".join(user_content)}
            ],
            temperature=0.7,
            max_tokens=1500
        )
        
        content = response.choices[0].message.content.strip()
        response_data = json.loads(content)

        # Enhance response with additional platform and theme data
        response_data.update({
            "platform_specifics": platform_specifics[platform],
            "theme_strategies": theme_strategies[theme],
            "content_length": length_guides[length],
            "format_strategy": format_strategies[content_format],
            "emotion_strategy": emotion_strategies[target_emotion],
            "effect_intensity": theme_strategies[theme]['effect_intensities'][effect_intensity],
            "language": language,
            "theme": theme
        })

        return json.dumps(response_data, ensure_ascii=False)
        
    except Exception as e:
        logger.error(f"OpenAI API error: {str(e)}")
        return json.dumps({
            "title": "API Error",
            "description": "Failed to generate content. Please try again later.",
            "hashtags": ["#error"],
            "target_audience": "N/A",
            "platform_tips": platform_specifics[platform]["tips"],
            "content_length": length_guides[length],
            "theme_elements": theme_strategies[theme]["visual_elements"],
            "viral_potential_score": 0
        })
