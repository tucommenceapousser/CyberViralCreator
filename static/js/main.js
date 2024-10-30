document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('uploadForm');
    const result = document.getElementById('result');
    const contentDisplay = document.getElementById('contentDisplay');
    const previewLink = document.getElementById('previewLink');
    const downloadLink = document.getElementById('downloadLink');

    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const formData = new FormData(form);
        const submitButton = form.querySelector('button[type="submit"]');
        submitButton.disabled = true;
        
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
                alert(data.error);
            }
        } catch (error) {
            alert('An error occurred while uploading the file');
        } finally {
            submitButton.disabled = false;
        }
    });
});
