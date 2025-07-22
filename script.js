// Configuration
const BACKEND_URL = 'http://localhost:8001';
const API_URL = `${BACKEND_URL}/api`;

// Variables globales
let examples = [];
let isLoading = false;

// Éléments DOM
const sentenceInput = document.getElementById('sentence');
const translateBtn = document.getElementById('translate-btn');
const errorMessage = document.getElementById('error-message');
const resultSection = document.getElementById('result-section');
const originalSentence = document.getElementById('original-sentence');
const folTranslation = document.getElementById('fol-translation');
const explanation = document.getElementById('explanation');
const symbolsUsedSection = document.getElementById('symbols-used-section');
const symbolsUsed = document.getElementById('symbols-used');
const examplesGrid = document.getElementById('examples-grid');

// Fonction utilitaire pour les requêtes fetch
async function fetchAPI(endpoint, options = {}) {
    try {
        const response = await fetch(`${API_URL}${endpoint}`, {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('API Error:', error);
        throw error;
    }
}

// Afficher/masquer les messages d'erreur
function showError(message) {
    errorMessage.textContent = message;
    errorMessage.style.display = 'block';
}

function hideError() {
    errorMessage.style.display = 'none';
}

// Afficher/masquer la section des résultats
function showResult(translationResult) {
    originalSentence.textContent = translationResult.original_sentence;
    folTranslation.textContent = translationResult.fol_translation;
    explanation.textContent = translationResult.explanation;
    
    // Afficher les symboles utilisés s'il y en a
    if (translationResult.symbols_used && translationResult.symbols_used.length > 0) {
        symbolsUsed.innerHTML = '';
        translationResult.symbols_used.forEach(symbol => {
            const symbolElement = document.createElement('span');
            symbolElement.className = 'used-symbol';
            symbolElement.textContent = symbol;
            symbolsUsed.appendChild(symbolElement);
        });
        symbolsUsedSection.style.display = 'block';
    } else {
        symbolsUsedSection.style.display = 'none';
    }
    
    resultSection.style.display = 'block';
}

function hideResult() {
    resultSection.style.display = 'none';
}

// Chargement état
function setLoading(loading) {
    isLoading = loading;
    translateBtn.disabled = loading;
    sentenceInput.disabled = loading;
    
    if (loading) {
        translateBtn.textContent = 'Traduction...';
        translateBtn.classList.add('loading');
    } else {
        translateBtn.textContent = 'Traduire';
        translateBtn.classList.remove('loading');
    }
}

// Fonction de traduction
async function translateSentence() {
    const sentence = sentenceInput.value.trim();
    
    if (!sentence) {
        showError('Veuillez entrer une phrase à traduire');
        return;
    }
    
    hideError();
    hideResult();
    setLoading(true);
    
    try {
        const result = await fetchAPI('/translate', {
            method: 'POST',
            body: JSON.stringify({ sentence })
        });
        
        showResult(result);
    } catch (error) {
        showError('Erreur lors de la traduction. Veuillez réessayer.');
    } finally {
        setLoading(false);
    }
}

// Charger les exemples
async function loadExamples() {
    try {
        const response = await fetchAPI('/examples');
        examples = response.examples;
        renderExamples();
    } catch (error) {
        console.error('Erreur lors du chargement des exemples:', error);
    }
}

// Afficher les exemples
function renderExamples() {
    examplesGrid.innerHTML = '';
    
    examples.forEach(example => {
        const card = document.createElement('div');
        card.className = 'example-card';
        card.innerHTML = `
            <div class="example-phrase">"${example.phrase}"</div>
            <div class="example-arrow">↓</div>
            <div class="example-translation">${example.traduction}</div>
            <div class="example-explanation">${example.explication}</div>
        `;
        
        card.addEventListener('click', () => {
            sentenceInput.value = example.phrase;
            hideError();
            hideResult();
            sentenceInput.focus();
        });
        
        examplesGrid.appendChild(card);
    });
}

// Gestionnaires d'événements
translateBtn.addEventListener('click', translateSentence);

sentenceInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter' && !isLoading) {
        translateSentence();
    }
});

sentenceInput.addEventListener('input', () => {
    if (errorMessage.style.display === 'block') {
        hideError();
    }
});

// Initialisation de l'application
document.addEventListener('DOMContentLoaded', () => {
    loadExamples();
    sentenceInput.focus();
});

// Gestion des erreurs globales
window.addEventListener('error', (e) => {
    console.error('Erreur globale:', e.error);
});