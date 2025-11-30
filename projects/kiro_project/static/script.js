// Web Content Summarizer - Frontend JavaScript

document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('summarize-form');
    const urlInput = document.getElementById('url-input');
    const submitButton = form.querySelector('.btn-submit');
    const btnText = submitButton.querySelector('.btn-text');
    const btnLoader = submitButton.querySelector('.btn-loader');
    
    const errorSection = document.getElementById('error-section');
    const errorMessage = document.getElementById('error-message');
    
    const resultsSection = document.getElementById('results-section');
    const summaryText = document.getElementById('summary-text');
    const highlightsList = document.getElementById('highlights-list');

    // Handle form submission
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const url = urlInput.value.trim();
        
        // Clear previous results and errors
        hideError();
        hideResults();
        
        // Show loading state
        showLoading();
        
        try {
            const response = await fetch('/api/summarize', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ url }),
            });
            
            const data = await response.json();
            
            // Hide loading state
            hideLoading();
            
            // Check if response was successful (status 200-299)
            if (!response.ok) {
                // Handle HTTP error responses (400, 500, etc.)
                const errorMsg = data.detail || data.error || 'An unexpected error occurred';
                displayError(errorMsg);
                return;
            }
            
            if (data.success) {
                // Display results
                displayResults(data.summary, data.highlights);
            } else {
                // Display error from successful response with error field
                displayError(data.error || 'An unexpected error occurred');
            }
        } catch (error) {
            // Hide loading state
            hideLoading();
            
            // Display network error
            displayError('Network error: Unable to connect to the server. Please try again.');
        }
    });

    // Show loading state
    function showLoading() {
        submitButton.disabled = true;
        btnText.style.display = 'none';
        btnLoader.style.display = 'inline';
    }

    // Hide loading state
    function hideLoading() {
        submitButton.disabled = false;
        btnText.style.display = 'inline';
        btnLoader.style.display = 'none';
    }

    // Display results
    function displayResults(summary, highlights) {
        // Set summary text
        summaryText.textContent = summary || 'No summary available';
        
        // Clear and populate highlights list
        highlightsList.innerHTML = '';
        
        if (highlights && highlights.length > 0) {
            highlights.forEach(highlight => {
                const li = document.createElement('li');
                li.textContent = highlight;
                highlightsList.appendChild(li);
            });
        } else {
            const li = document.createElement('li');
            li.textContent = 'No highlights available';
            highlightsList.appendChild(li);
        }
        
        // Show results section
        resultsSection.style.display = 'block';
    }

    // Hide results
    function hideResults() {
        resultsSection.style.display = 'none';
    }

    // Display error
    function displayError(message) {
        errorMessage.textContent = message;
        errorSection.style.display = 'block';
    }

    // Hide error
    function hideError() {
        errorSection.style.display = 'none';
        errorMessage.textContent = '';
    }
});
