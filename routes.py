import os
import json
import logging
from flask import render_template, request, jsonify, send_from_directory, abort
from werkzeug.exceptions import RequestEntityTooLarge
from app import app, db
from models import Content
from utils import allowed_file, generate_secure_filename, generate_viral_content, transcribe_audio
from media_utils import (
    extract_audio_from_video,
    combine_audio_with_video,
    add_text_overlay,
    process_audio
)

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
            
        translations_file = os.path.join('static', 'translations', f'{language}.json')
        
        if not os.path.exists(translations_file):
            logger.error(f"Translation file not found: {translations_file}")
            return jsonify({}), 404
            
        return send_from_directory('static/translations', f'{language}.json', mimetype='application/json')
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
        files = request.files.getlist('files[]')
        if not files:
            logger.warning("No files provided in request")
            return jsonify({'error': 'No files provided'}), 400
        
        # Get form data
        theme = request.form.get('theme', 'anonymous')
        tone = request.form.get('tone', 'professional')
        platform = request.form.get('platform', 'tiktok')
        length = request.form.get('length', 'short')
        language = request.form.get('language', 'en')
        
        uploaded_files = []
        transcriptions = []
        
        for file in files:
            if not file or not file.filename:
                continue
                
            if not allowed_file(file.filename):
                logger.warning(f"Invalid file type: {file.filename}")
                continue
            
            # Save file
            filename = generate_secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            logger.info(f"Saving file to: {file_path}")
            file.save(file_path)
            
            file_type = file.filename.rsplit('.', 1)[1].lower()
            processed_path = None
            
            # Process files based on type and theme
            try:
                if file_type == 'mp4':
                    # Extract audio for transcription
                    audio_path = extract_audio_from_video(file_path)
                    transcription = transcribe_audio(audio_path)
                    transcriptions.append(transcription)
                    
                    # Process video with enhanced theme-based effects
                    text_content = "Content loading..." # Placeholder until content is generated
                    processed_path = add_text_overlay(
                        file_path,
                        text_content,
                        theme=theme,
                        position='bottom' if theme in ['anonymous', 'cyber'] else 'top'
                    )
                elif file_type == 'mp3':
                    transcription = transcribe_audio(file_path)
                    transcriptions.append(transcription)
                    
                    # Process audio with enhanced theme-based effects
                    processed_path = process_audio(file_path, theme=theme)
                    
            except Exception as e:
                logger.error(f"Error processing file {filename}: {str(e)}")
                continue
            
            uploaded_files.append({
                'original_path': file_path,
                'processed_path': processed_path,
                'file_type': file_type,
                'filename': filename
            })
        
        if not uploaded_files:
            return jsonify({'error': 'No valid files were uploaded'}), 400
        
        # Generate enhanced content using combined transcriptions
        combined_transcription = " ".join(transcriptions) if transcriptions else None
        generated_content = generate_viral_content(
            theme=theme,
            file_type=uploaded_files[0]['file_type'],
            tone=tone,
            platform=platform,
            length=length,
            language=language,
            transcription=combined_transcription
        )
        
        # Save to database
        content_entries = []
        for file_info in uploaded_files:
            processed_filename = os.path.basename(file_info['processed_path']) if file_info['processed_path'] else None
            new_content = Content()
            new_content.original_filename = file_info['filename']
            new_content.stored_filename = file_info['filename']
            new_content.file_type = file_info['file_type']
            new_content.theme = theme
            new_content.generated_content = generated_content
            new_content.processed_filename = processed_filename
            
            db.session.add(new_content)
            content_entries.append(new_content)
            
        db.session.commit()
        logger.info(f"Content saved to database")
        
        # Update processed files with generated content
        try:
            content_data = json.loads(generated_content)
            for file_info in uploaded_files:
                if file_info['file_type'] == 'mp4' and file_info['processed_path']:
                    # Update video overlay with actual content
                    add_text_overlay(
                        file_info['original_path'],
                        f"{content_data['title']}\n{content_data['hooks'][0] if content_data.get('hooks') else ''}",
                        theme=theme,
                        position='bottom' if theme in ['anonymous', 'cyber'] else 'top',
                        output_path=file_info['processed_path']
                    )
        except Exception as e:
            logger.error(f"Error updating processed files with content: {str(e)}")
        
        return jsonify({
            'content': generated_content,
            'files': [{
                'id': content.id,
                'original_filename': content.original_filename,
                'file_type': content.file_type
            } for content in content_entries],
            'transcription': combined_transcription if combined_transcription else None
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
            content.processed_filename or content.stored_filename,
            as_attachment=True,
            download_name=content.original_filename
        )
    except Exception as e:
        logger.error(f"Error downloading content {content_id}: {str(e)}")
        return jsonify({'error': 'Error downloading file'}), 500