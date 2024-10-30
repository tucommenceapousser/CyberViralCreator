document.addEventListener('DOMContentLoaded', function() {
    const languageSelect = document.getElementById('languageSelect');
    let translations = {};

    async function loadTranslations(lang) {
        try {
            console.log(`Loading translations for language: ${lang}`);
            const response = await fetch(`/translations/${lang}.json`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            translations = await response.json();
            console.log('Translations loaded successfully');
            updateContent();
        } catch (error) {
            console.error('Error loading translations:', error);
            // Fallback to English if translation fails
            if (lang !== 'en') {
                console.log('Falling back to English translations');
                loadTranslations('en');
            }
        }
    }

    function updateContent() {
        document.querySelectorAll('[data-lang]').forEach(element => {
            const key = element.getAttribute('data-lang');
            if (translations[key]) {
                if (element.tagName === 'INPUT' || element.tagName === 'TEXTAREA') {
                    element.placeholder = translations[key];
                } else if (element.tagName === 'OPTION') {
                    element.textContent = translations[key];
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
    loadTranslations(languageSelect.value);
});
