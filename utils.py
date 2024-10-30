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

    messages = [
        {
            "role": "system",
            "content": f"You are a content specialist for {platform.upper()}. "
                      f"Create content in {language.upper()} with a {tone} tone. "
                      f"Target length: {length_guides[length]}. "
                      f"Focus on {platform_specifics[platform]}."
        },
        {
            "role": "user",
            "content": f"Create viral content ideas for a {file_type} file with theme '{theme}'. "
                      f"Include platform-specific optimization tips and engagement strategies."
        }
    ]
    
    try:
        response = openai_client.chat.completions.create(
            model="gpt-4",
            messages=messages
        )
        
        content = response.choices[0].message.content
        # Validate JSON structure
        parsed_content = json.loads(content)
        required_fields = ['title', 'description', 'hashtags', 'target_audience']
        
        for field in required_fields:
            if field not in parsed_content:
                raise ValueError(f"Missing required field: {field}")
        
        if not isinstance(parsed_content['hashtags'], list):
            parsed_content['hashtags'] = [parsed_content['hashtags']]

        # Add additional platform-specific recommendations
        parsed_content['platform_tips'] = platform_specifics[platform]
        parsed_content['content_length'] = length_guides[length]
        
        logger.info("Successfully generated viral content")
        return json.dumps(parsed_content)
        
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse OpenAI response as JSON: {str(e)}")
        return json.dumps({
            "title": "Error Processing Content",
            "description": "Failed to generate content. Please try again.",
            "hashtags": ["#error"],
            "target_audience": "N/A",
            "platform_tips": "N/A",
            "content_length": "N/A"
        })
    except Exception as e:
        logger.error(f"OpenAI API error details: {str(e)}")
        return json.dumps({
            "title": "API Error",
            "description": "Failed to generate content due to API error. Please try again later.",
            "hashtags": ["#error"],
            "target_audience": "N/A",
            "platform_tips": "N/A",
            "content_length": "N/A"
        })
