import os
import json
import logging
from flask import render_template, request, jsonify, send_from_directory, abort
from werkzeug.exceptions import RequestEntityTooLarge
from app import app, db
from models import Content
from utils import allowed_file, generate_secure_filename, generate_viral_content

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/translations/<language>.json')
def serve_translations(language):
    try:
        if language not in ['en', 'fr']:
            return jsonify({}), 404
            
        translations_dir = os.path.join('static', 'translations')
        translations_file = os.path.join(translations_dir, f'{language}.json')
        
        if not os.path.exists(translations_file):
            logger.error(f"Translation file not found: {translations_file}")
            return jsonify({}), 404
            
        return send_from_directory(translations_dir, f'{language}.json', mimetype='application/json')
    except Exception as e:
        logger.error(f"Error serving translation: {str(e)}")
        return jsonify({}), 500

@app.errorhandler(RequestEntityTooLarge)
def handle_file_too_large(e):
    return jsonify({'error': 'File size exceeds the 32MB limit'}), 413

@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        logger.info("Starting file upload process")
        if 'file' not in request.files:
            logger.warning("No file provided in request")
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        theme = request.form.get('theme', 'anonymous')
        tone = request.form.get('tone', 'professional')
        platform = request.form.get('platform', 'tiktok')
        length = request.form.get('length', 'short')
        language = request.form.get('language', 'en')
        
        if not file or file.filename == '':
            logger.warning("Empty filename provided")
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            logger.warning(f"Invalid file type: {file.filename}")
            return jsonify({'error': 'Invalid file type. Only MP3 and MP4 files are allowed'}), 400
        
        filename = generate_secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        logger.info(f"Saving file to: {file_path}")
        file.save(file_path)
        
        file_type = file.filename.rsplit('.', 1)[1].lower()
        logger.info(f"Generating content for file type: {file_type}")
        generated_content = generate_viral_content(
            theme=theme,
            file_type=file_type,
            tone=tone,
            platform=platform,
            length=length,
            language=language
        )
        
        try:
            parsed_content = json.loads(generated_content)
            logger.info("Successfully parsed generated content as JSON")
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse OpenAI response as JSON: {str(e)}")
            return jsonify({'error': 'Error processing content generation response'}), 500
        
        content = Content(
            original_filename=file.filename,
            stored_filename=filename,
            file_type=file_type,
            theme=theme,
            generated_content=generated_content
        )
        db.session.add(content)
        db.session.commit()
        logger.info(f"Content saved to database with ID: {content.id}")
        
        return jsonify({
            'id': content.id,
            'content': generated_content
        })
    except RequestEntityTooLarge:
        logger.error("File size exceeds limit")
        return jsonify({'error': 'File size exceeds the 32MB limit'}), 413
    except Exception as e:
        logger.error(f"Error in upload process: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/preview/<int:content_id>')
def preview_content(content_id):
    try:
        content = Content.query.get_or_404(content_id)
        return render_template('preview.html', content=content)
    except Exception as e:
        logger.error(f"Error previewing content {content_id}: {str(e)}")
        return jsonify({'error': 'Error loading preview'}), 500

@app.route('/download/<int:content_id>')
def download_file(content_id):
    try:
        content = Content.query.get_or_404(content_id)
        return send_from_directory(
            app.config['UPLOAD_FOLDER'],
            content.stored_filename,
            as_attachment=True,
            download_name=content.original_filename
        )
    except Exception as e:
        logger.error(f"Error downloading content {content_id}: {str(e)}")
        return jsonify({'error': 'Error downloading file'}), 500
