document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('uploadForm');
    const result = document.getElementById('result');
    const contentDisplay = document.getElementById('contentDisplay');
    const previewLinks = document.getElementById('previewLinks');
    const fileInput = document.getElementById('files');
    const fileList = document.getElementById('fileList');
    const selectedFiles = document.getElementById('selectedFiles');
    const uploadProgress = document.getElementById('uploadProgress');
    const progressBar = uploadProgress.querySelector('.progress-bar');
    const maxFileSize = 32 * 1024 * 1024; // 32MB in bytes

    function showError(message, isApiError = false) {
        const existingAlert = document.getElementById('errorAlert');
        if (existingAlert) {
            existingAlert.remove();
        }

        const alertDiv = document.createElement('div');
        alertDiv.id = 'errorAlert';
        alertDiv.className = `alert alert-${isApiError ? 'warning' : 'danger'} mt-3`;
        alertDiv.innerHTML = `<strong>${isApiError ? 'API Error' : 'Error'}:</strong> ${message}`;
        form.appendChild(alertDiv);
    }

    function updateFileList() {
        const files = fileInput.files;
        if (files.length > 0) {
            selectedFiles.innerHTML = '';
            fileList.classList.remove('d-none');
            
            Array.from(files).forEach(file => {
                const li = document.createElement('li');
                li.className = 'list-group-item d-flex justify-content-between align-items-center';
                li.innerHTML = `
                    <span>${file.name}</span>
                    <span class="badge bg-primary rounded-pill">${(file.size / (1024 * 1024)).toFixed(2)} MB</span>
                `;
                selectedFiles.appendChild(li);
                
                if (file.size > maxFileSize) {
                    li.classList.add('list-group-item-danger');
                    showError(`File "${file.name}" exceeds 32MB limit`);
                }
            });
        } else {
            fileList.classList.add('d-none');
        }
    }

    fileInput.addEventListener('change', updateFileList);

    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const formData = new FormData();
        const submitButton = form.querySelector('button[type="submit"]');
        const files = fileInput.files;
        
        // Check if any file exceeds size limit
        const invalidFiles = Array.from(files).filter(file => file.size > maxFileSize);
        if (invalidFiles.length > 0) {
            showError(`Some files exceed the 32MB limit: ${invalidFiles.map(f => f.name).join(', ')}`);
            return;
        }

        // Add all files to FormData
        Array.from(files).forEach(file => {
            formData.append('files[]', file);
        });
        
        // Add form fields including new parameters
        formData.append('theme', document.getElementById('theme').value);
        formData.append('tone', document.getElementById('tone').value);
        formData.append('platform', document.getElementById('platform').value);
        formData.append('length', document.getElementById('length').value);
        formData.append('language', document.getElementById('language').value);
        formData.append('content_format', document.getElementById('content_format').value);
        formData.append('target_emotion', document.getElementById('target_emotion').value);
        formData.append('call_to_action', document.getElementById('call_to_action').value);
        formData.append('effect_intensity', document.getElementById('effect_intensity').value);
        
        // Remove existing error alert if any
        const errorAlert = document.getElementById('errorAlert');
        if (errorAlert) {
            errorAlert.remove();
        }

        submitButton.disabled = true;
        submitButton.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Generating...';
        result.classList.add('d-none');
        uploadProgress.classList.remove('d-none');
        
        try {
            const response = await fetch('/upload', {
                method: 'POST',
                body: formData
            });
            
            const data = await response.json();
            
            if (response.ok) {
                try {
                    const content = JSON.parse(data.content);
                    contentDisplay.innerHTML = `
                        <h5>${content.title || 'Title not available'}</h5>
                        <p>${content.description || 'Description not available'}</p>
                        <p><strong>Hashtags:</strong> ${content.hashtags ? content.hashtags.join(' ') : 'No hashtags available'}</p>
                        <p><strong>Target Audience:</strong> ${content.target_audience || 'Target audience not specified'}</p>
                        <p><strong>Platform Tips:</strong> ${content.platform_tips || 'No platform tips available'}</p>
                        <p><strong>Recommended Length:</strong> ${content.content_length || 'Length not specified'}</p>
                        <p><strong>Hooks:</strong> ${content.hooks ? content.hooks.join(', ') : 'No hooks available'}</p>
                        <p><strong>Engagement Strategies:</strong> ${content.engagement_strategies ? content.engagement_strategies.join(', ') : 'No strategies available'}</p>
                        <p><strong>Emotional Impact:</strong> ${content.emotional_triggers ? content.emotional_triggers.join(', ') : 'No emotional triggers specified'}</p>
                        <p><strong>Pacing Guide:</strong> ${content.pacing_guide || 'No pacing guide available'}</p>
                        <p><strong>Effect Recommendations:</strong> ${content.effect_recommendations ? content.effect_recommendations.join(', ') : 'No effect recommendations available'}</p>
                        <p><strong>Viral Potential Score:</strong> ${content.viral_potential_score || 'Not available'}/10</p>
                    `;
                    
                    // Generate preview links for each file
                    previewLinks.innerHTML = data.files.map(file => `
                        <div class="mb-2">
                            <a href="/preview/${file.id}" class="btn btn-info me-2">Preview ${file.original_filename}</a>
                            <a href="/download/${file.id}" class="btn btn-success">Download ${file.original_filename}</a>
                        </div>
                    `).join('');
                    
                    result.classList.remove('d-none');
                } catch (parseError) {
                    console.error('Error parsing API response:', parseError);
                    showError('Error processing the generated content. Please try again.', true);
                }
            } else {
                const errorMessage = data.error || 'An error occurred while uploading the file';
                showError(errorMessage, errorMessage.includes('OpenAI'));
            }
        } catch (error) {
            console.error('Request error:', error);
            showError('An error occurred while processing your request. Please try again.');
        } finally {
            submitButton.disabled = false;
            submitButton.innerHTML = 'Generate Content';
            uploadProgress.classList.add('d-none');
        }
    });
});
