/**
 * Real-time Search Utility
 * Handles debounced AJAX requests for search forms and updates results dynamically.
 */
document.addEventListener('DOMContentLoaded', function() {
    const searchForms = document.querySelectorAll('form[data-real-time-search]');
    
    searchForms.forEach(form => {
        const resultContainer = document.querySelector(form.dataset.realTimeResults || '[data-real-time-results]');
        if (!resultContainer) return;

        const inputs = form.querySelectorAll('input, select');
        let debounceTimer;

        inputs.forEach(input => {
            const eventType = input.tagName === 'SELECT' ? 'change' : 'input';
            
            input.addEventListener(eventType, function() {
                clearTimeout(debounceTimer);
                debounceTimer = setTimeout(() => {
                    performSearch(form, resultContainer);
                }, 500); // 500ms debounce
            });
        });

        // Handle pagination clicks within the result container
        resultContainer.addEventListener('click', function(e) {
            const paginationLink = e.target.closest('.pagination a, .pagination-nav a');
            if (paginationLink) {
                e.preventDefault();
                const url = paginationLink.getAttribute('href');
                if (url && url !== '#') {
                    performSearch(form, resultContainer, url);
                }
            }
        });
    });

    /**
     * Performs the AJAX search request
     */
    async function performSearch(form, container, url = null) {
        const formData = new FormData(form);
        const params = new URLSearchParams(formData);
        
        // If an explicit URL is provided (e.g., from pagination), use it, otherwise use form action
        const fetchUrl = url || `${form.getAttribute('action') || window.location.pathname}?${params.toString()}`;
        
        // Update browser URL without reload
        window.history.pushState({}, '', fetchUrl);

        // Show loading state (optional)
        container.style.opacity = '0.5';

        try {
            const response = await fetch(fetchUrl, {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });

            if (!response.ok) throw new Error('Search failed');

            const html = await response.text();
            container.innerHTML = html;
            
            // Dispatch a custom event so other scripts can re-initialize
            container.dispatchEvent(new CustomEvent('contentUpdated', { 
                bubbles: true,
                detail: { html: html }
            }));

            // Re-initialize tooltips or other dynamic components if needed
            if (window.bootstrap && window.bootstrap.Tooltip) {
                const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
                tooltipTriggerList.map(function (tooltipTriggerEl) {
                    return new window.bootstrap.Tooltip(tooltipTriggerEl);
                });
            }

        } catch (error) {
            console.error('Real-time search error:', error);
        } finally {
            container.style.opacity = '1';
        }
    }
});
