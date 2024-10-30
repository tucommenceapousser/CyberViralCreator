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

def generate_viral_content(theme, file_type):
    """
    Generate viral content ideas using OpenAI API
    Returns a JSON string containing title, description, hashtags, and target audience
    """
    logger.info(f"Generating viral content for {file_type} file with theme: {theme}")
    
    messages = [
        {
            "role": "user",
            "content": f"""Create viral content ideas for a {file_type} file with theme '{theme}'.
            Provide the following in a JSON format:
            - An attention-grabbing title
            - A compelling description
            - Relevant hashtags (as an array)
            - Target audience
            """
        }
    ]
    
    try:
        response = openai_client.chat.completions.create(
            model="gpt-4",
            messages=messages,
            response_format={"type": "json_object"}
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
        
        logger.info("Successfully generated viral content")
        return json.dumps(parsed_content)
        
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse OpenAI response as JSON: {str(e)}")
        return json.dumps({
            "title": "Error Processing Content",
            "description": "Failed to generate content. Please try again.",
            "hashtags": ["#error"],
            "target_audience": "N/A"
        })
    except Exception as e:
        logger.error(f"OpenAI API error: {str(e)}")
        return json.dumps({
            "title": "API Error",
            "description": "Failed to generate content due to API error. Please try again later.",
            "hashtags": ["#error"],
            "target_audience": "N/A"
        })
