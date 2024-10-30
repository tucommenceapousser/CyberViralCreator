document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('uploadForm');
    const result = document.getElementById('result');
    const contentDisplay = document.getElementById('contentDisplay');
    const previewLink = document.getElementById('previewLink');
    const downloadLink = document.getElementById('downloadLink');
    const fileInput = document.getElementById('file');
    const maxFileSize = 32 * 1024 * 1024; // 32MB in bytes

    // Add file size warning
    const fileSizeWarning = document.createElement('small');
    fileSizeWarning.className = 'text-muted d-block mt-1';
    fileSizeWarning.textContent = 'Maximum file size: 32MB';
    fileInput.parentNode.appendChild(fileSizeWarning);

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

    // Add file size check
    fileInput.addEventListener('change', function() {
        const file = this.files[0];
        if (file && file.size > maxFileSize) {
            showError('File size exceeds 32MB limit. Please choose a smaller file.');
            this.value = '';
        }
    });

    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const formData = new FormData(form);
        const submitButton = form.querySelector('button[type="submit"]');
        
        // Remove existing error alert if any
        const errorAlert = document.getElementById('errorAlert');
        if (errorAlert) {
            errorAlert.remove();
        }

        submitButton.disabled = true;
        submitButton.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Generating...';
        result.classList.add('d-none');
        
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
                        <p><strong>Hashtags:</strong> ${content.hashtags || 'No hashtags available'}</p>
                        <p><strong>Target Audience:</strong> ${content.target_audience || 'Target audience not specified'}</p>
                    `;
                    
                    previewLink.href = `/preview/${data.id}`;
                    downloadLink.href = `/download/${data.id}`;
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
        }
    });
});
