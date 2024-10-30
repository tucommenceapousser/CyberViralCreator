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
def generate_viral_content(theme, file_type, tone="professional", platform="tiktok", length="short", language="en", transcription=None):
    """
    Generate viral content ideas using OpenAI API with enhanced parameters and transcription context
    Returns a JSON string containing title, description, hashtags, target audience, and platform-specific recommendations
    """
    logger.info(f"Generating viral content for {file_type} file with theme: {theme}")
    
    length_guides = {
        "short": "30-60 seconds",
        "medium": "1-3 minutes",
        "long": "3-5 minutes"
    }

    platform_specifics = {
        "tiktok": {
            "tips": "focus on trending sounds, quick cuts, and viral challenges",
            "hashtag_count": 5,
            "style": "fast-paced, engaging, with hook in first 3 seconds"
        },
        "youtube": {
            "tips": "include SEO-friendly title and description, emphasize longer engagement",
            "hashtag_count": 8,
            "style": "structured content with clear sections and call-to-action"
        },
        "instagram": {
            "tips": "focus on visually appealing content, use Instagram-specific features",
            "hashtag_count": 10,
            "style": "aesthetic focus, story-driven, with carousel options"
        }
    }

    # Build system message with enhanced context
    system_content = (
        "You are an expert content strategist specializing in viral content creation. "
        f"Generate content optimized for {platform.upper()} in {language.upper()}. "
        f"Content should be {tone} in tone and {length_guides[length]} in duration. "
        f"Follow platform-specific best practices: {platform_specifics[platform]['style']}. "
        "Return response in JSON format with fields: "
        "title, description, hashtags (array), target_audience, hooks (array), "
        "platform_tips, content_length, engagement_strategies (array), and viral_potential_score (1-10)"
    )

    # Build user message with transcription context if available
    user_content = [
        f"Create viral content ideas for a {file_type} file with theme '{theme}'.",
        f"Optimize for {platform_specifics[platform]['tips']}.",
    ]
    
    if transcription:
        user_content.append(f"Using this transcription as context: '{transcription}'")
        
    try:
        response = openai_client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_content},
                {"role": "user", "content": " ".join(user_content)}
            ],
            temperature=0.7,
            max_tokens=1000
        )
        
        content = response.choices[0].message.content.strip()
        response_data = json.loads(content)

        # Enhance response with platform-specific data
        response_data.update({
            "platform_specifics": platform_specifics[platform],
            "content_length": length_guides[length],
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
            "hooks": [],
            "engagement_strategies": [],
            "viral_potential_score": 0
        })
