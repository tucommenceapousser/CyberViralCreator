document.addEventListener('DOMContentLoaded', function() {
    const languageSelect = document.getElementById('languageSelect');
    let translations = {};

    async function loadTranslations(lang) {
        try {
            const response = await fetch(`/static/translations/${lang}.json`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            translations = await response.json();
            updateContent();
        } catch (error) {
            console.error('Error loading translations:', error);
        }
    }

    function updateContent() {
        document.querySelectorAll('[data-lang]').forEach(element => {
            const key = element.getAttribute('data-lang');
            if (translations[key]) {
                if (element.tagName === 'INPUT' || element.tagName === 'TEXTAREA') {
                    element.placeholder = translations[key];
                } else {
                    element.textContent = translations[key];
                }
            }
        });
    }

    languageSelect.addEventListener('change', function() {
        loadTranslations(this.value);
    });

    // Load default language
    loadTranslations('en');
});
