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

    // Add file size check
    fileInput.addEventListener('change', function() {
        const file = this.files[0];
        if (file && file.size > maxFileSize) {
            alert('File size exceeds 32MB limit. Please choose a smaller file.');
            this.value = '';
        }
    });

    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const formData = new FormData(form);
        const submitButton = form.querySelector('button[type="submit"]');
        const errorAlert = document.getElementById('errorAlert');
        
        // Remove existing error alert if any
        if (errorAlert) {
            errorAlert.remove();
        }

        submitButton.disabled = true;
        submitButton.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Generating...';
        
        try {
            const response = await fetch('/upload', {
                method: 'POST',
                body: formData
            });
            
            const data = await response.json();
            
            if (response.ok) {
                const content = JSON.parse(data.content);
                contentDisplay.innerHTML = `
                    <h5>${content.title}</h5>
                    <p>${content.description}</p>
                    <p><strong>Hashtags:</strong> ${content.hashtags}</p>
                    <p><strong>Target Audience:</strong> ${content.target_audience}</p>
                `;
                
                previewLink.href = `/preview/${data.id}`;
                downloadLink.href = `/download/${data.id}`;
                result.classList.remove('d-none');
            } else {
                // Create and show error alert
                const alertDiv = document.createElement('div');
                alertDiv.id = 'errorAlert';
                alertDiv.className = 'alert alert-danger mt-3';
                alertDiv.textContent = data.error || 'An error occurred while uploading the file';
                form.appendChild(alertDiv);
            }
        } catch (error) {
            // Create and show error alert
            const alertDiv = document.createElement('div');
            alertDiv.id = 'errorAlert';
            alertDiv.className = 'alert alert-danger mt-3';
            alertDiv.textContent = 'An error occurred while processing your request';
            form.appendChild(alertDiv);
        } finally {
            submitButton.disabled = false;
            submitButton.innerHTML = 'Generate Content';
        }
    });
});
