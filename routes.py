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
        
        # Get enhanced form data with new parameters
        theme = request.form.get('theme', 'anonymous')
        tone = request.form.get('tone', 'professional')
        platform = request.form.get('platform', 'tiktok')
        length = request.form.get('length', 'short')
        language = request.form.get('language', 'en')
        
        # New advanced parameters
        content_format = request.form.get('content_format', 'story')  # story, tutorial, review, etc.
        target_emotion = request.form.get('target_emotion', 'neutral')  # excitement, curiosity, surprise
        call_to_action = request.form.get('call_to_action', 'follow')  # follow, share, comment
        effect_intensity = request.form.get('effect_intensity', 'medium')  # low, medium, high
        
        uploaded_files = []
        transcriptions = []
        mp3_files = []
        mp4_files = []
        
        # First pass: Save all files and categorize them
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
            
            # Categorize files
            if file_type == 'mp3':
                mp3_files.append(file_path)
            elif file_type == 'mp4':
                mp4_files.append(file_path)
            
            uploaded_files.append({
                'original_path': file_path,
                'file_type': file_type,
                'filename': filename
            })

        # Generate content first to use in overlays
        # Get transcriptions for content generation
        for file_info in uploaded_files:
            try:
                if file_info['file_type'] == 'mp4':
                    audio_path = extract_audio_from_video(file_info['original_path'])
                    transcription = transcribe_audio(audio_path)
                    transcriptions.append(transcription)
                elif file_info['file_type'] == 'mp3':
                    transcription = transcribe_audio(file_info['original_path'])
                    transcriptions.append(transcription)
            except Exception as e:
                logger.error(f"Error getting transcription: {str(e)}")
                continue

        # Generate enhanced content using combined transcriptions and new parameters
        combined_transcription = " ".join(transcriptions) if transcriptions else None
        generated_content = generate_viral_content(
            theme=theme,
            file_type=uploaded_files[0]['file_type'] if uploaded_files else 'mp4',
            tone=tone,
            platform=platform,
            length=length,
            language=language,
            transcription=combined_transcription,
            content_format=content_format,
            target_emotion=target_emotion,
            call_to_action=call_to_action,
            effect_intensity=effect_intensity
        )
        
        try:
            content_data = json.loads(generated_content)
            overlay_text = f"{content_data['title']}\n{content_data['hooks'][0] if content_data.get('hooks') else ''}"
        except Exception as e:
            logger.error(f"Error parsing generated content: {str(e)}")
            overlay_text = "Generated Content"

        # Process files based on type and theme
        processed_files = []
        
        # First process individual files
        for file_info in uploaded_files:
            try:
                processed_path = None
                if file_info['file_type'] == 'mp4':
                    # Add text overlay to video with enhanced parameters
                    processed_path = add_text_overlay(
                        file_info['original_path'],
                        overlay_text,
                        theme=theme,
                        position='bottom' if theme in ['anonymous', 'cyber'] else 'top',
                        effect_intensity=effect_intensity
                    )
                elif file_info['file_type'] == 'mp3':
                    # Process audio with enhanced parameters
                    processed_path = process_audio(
                        file_info['original_path'],
                        theme=theme,
                        effect_intensity=effect_intensity
                    )
                
                if processed_path:
                    processed_files.append({
                        'original_path': file_info['original_path'],
                        'processed_path': processed_path,
                        'file_type': file_info['file_type'],
                        'filename': file_info['filename']
                    })
                    
            except Exception as e:
                logger.error(f"Error processing file {file_info['filename']}: {str(e)}")
                continue
        
        # If we have both MP3 and MP4 files, combine them with enhanced processing
        if mp3_files and mp4_files:
            try:
                # Use the first MP3 and MP4 files for combination with enhanced parameters
                processed_audio = process_audio(
                    mp3_files[0],
                    theme=theme,
                    effect_intensity=effect_intensity
                )
                
                combined_path = combine_audio_with_video(
                    mp4_files[0],
                    processed_audio
                )
                
                # Add enhanced overlay to combined video
                final_path = add_text_overlay(
                    combined_path,
                    overlay_text,
                    theme=theme,
                    position='bottom' if theme in ['anonymous', 'cyber'] else 'top',
                    effect_intensity=effect_intensity
                )
                
                processed_files.append({
                    'original_path': mp4_files[0],
                    'processed_path': final_path,
                    'file_type': 'mp4',
                    'filename': os.path.basename(final_path),
                    'is_combined': True
                })
                
            except Exception as e:
                logger.error(f"Error combining files: {str(e)}")
        
        if not processed_files:
            return jsonify({'error': 'No files were successfully processed'}), 400
        
        # Save to database with enhanced content
        content_entries = []
        for file_info in processed_files:
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
        
        return jsonify({
            'content': generated_content,
            'files': [{
                'id': content.id,
                'original_filename': content.original_filename,
                'file_type': content.file_type,
                'is_combined': getattr(content, 'is_combined', False)
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
