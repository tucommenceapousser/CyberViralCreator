import os
import uuid
import json
import logging
from werkzeug.utils import secure_filename
from openai import OpenAI

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

def generate_viral_content(theme, file_type, tone="professional", platform="tiktok", length="short", language="en"):
    """
    Generate viral content ideas using OpenAI API with enhanced parameters
    Returns a JSON string containing title, description, hashtags, target audience, and platform-specific recommendations
    """
    logger.info(f"Generating viral content for {file_type} file with theme: {theme}")
    
    length_guides = {
        "short": "30-60 seconds",
        "medium": "1-3 minutes",
        "long": "3-5 minutes"
    }

    platform_specifics = {
        "tiktok": "focus on trending sounds, quick cuts, and viral challenges",
        "youtube": "include SEO-friendly title and description, emphasize longer engagement",
        "instagram": "focus on visually appealing content, use Instagram-specific features"
    }

    try:
        response = openai_client.chat.completions.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a content specialist. Generate viral content ideas in JSON format with the following fields: "
                        "title, description, hashtags (as array), target_audience, platform_tips, and content_length. "
                        f"Platform: {platform.upper()}, Language: {language.upper()}, Tone: {tone}, "
                        f"Length: {length_guides[length]}"
                    )
                },
                {
                    "role": "user",
                    "content": f"Create viral content ideas for a {file_type} file with theme '{theme}'. "
                              f"Focus on {platform_specifics[platform]}. "
                              "Return only valid JSON."
                }
            ]
        )
        
        content = response.choices[0].message.content.strip()
        # Add platform-specific recommendations if not present in the response
        response_data = json.loads(content)
        if 'platform_tips' not in response_data:
            response_data['platform_tips'] = platform_specifics[platform]
        if 'content_length' not in response_data:
            response_data['content_length'] = length_guides[length]
            
        return json.dumps(response_data)
        
    except Exception as e:
        logger.error(f"OpenAI API error: {str(e)}")
        return json.dumps({
            "title": "API Error",
            "description": "Failed to generate content. Please try again later.",
            "hashtags": ["#error"],
            "target_audience": "N/A",
            "platform_tips": platform_specifics.get(platform, "N/A"),
            "content_length": length_guides.get(length, "N/A")
        })
