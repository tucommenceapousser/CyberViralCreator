import os
import json
from flask import render_template, request, jsonify, send_from_directory
from app import app, db
from models import Content
from utils import allowed_file, generate_secure_filename, generate_viral_content

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    theme = request.form.get('theme', 'anonymous')
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file type'}), 400
    
    try:
        filename = generate_secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        file_type = file.filename.rsplit('.', 1)[1].lower()
        generated_content = generate_viral_content(theme, file_type)
        
        content = Content(
            original_filename=file.filename,
            stored_filename=filename,
            file_type=file_type,
            theme=theme,
            generated_content=generated_content
        )
        db.session.add(content)
        db.session.commit()
        
        return jsonify({
            'id': content.id,
            'content': generated_content
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/preview/<int:content_id>')
def preview_content(content_id):
    content = Content.query.get_or_404(content_id)
    return render_template('preview.html', content=content)

@app.route('/download/<int:content_id>')
def download_file(content_id):
    content = Content.query.get_or_404(content_id)
    return send_from_directory(
        app.config['UPLOAD_FOLDER'],
        content.stored_filename,
        as_attachment=True,
        download_name=content.original_filename
    )