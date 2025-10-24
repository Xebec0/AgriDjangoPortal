document.addEventListener('DOMContentLoaded', function() {
    // Select all checkbox functionality
    const selectAllCheckbox = document.getElementById('selectAll');
    const candidateCheckboxes = document.querySelectorAll('.candidate-select');

    if (selectAllCheckbox) {
        selectAllCheckbox.addEventListener('change', function() {
            candidateCheckboxes.forEach(checkbox => {
                checkbox.checked = selectAllCheckbox.checked;
            });
            updateSelectedCount(); // Update counter when selecting/deselecting all
        });
    }

    // Date range validation
    const startDate = document.getElementById('start_date');
    const endDate = document.getElementById('end_date');

    if (startDate && endDate) {
        startDate.addEventListener('change', function() {
            endDate.min = startDate.value;
        });

        endDate.addEventListener('change', function() {
            startDate.max = endDate.value;
        });
    }

    // Export functionality
    function handleExport(format, selectedOnly = false) {
        try {
            console.log('handleExport called:', { format, selectedOnly });

            // Get current URL and preserve existing search parameters
            let url = new URL(window.location.href);
            let params = new URLSearchParams(url.search);

            // Remove page parameter but keep other filters
            params.delete('page');
            params.set('export', format);

            if (selectedOnly) {
                // Get selected candidates - use more robust selector
                const checkboxes = document.querySelectorAll('input.candidate-select:checked, .candidate-select:checked');
                const selectedCandidates = Array.from(checkboxes)
                    .map(checkbox => checkbox.value)
                    .filter(value => value && value.trim() !== '' && !isNaN(parseInt(value))); // Filter out any empty or invalid values

                console.log('Found checkboxes:', checkboxes.length);
                console.log('Selected candidate values:', selectedCandidates);

                if (selectedCandidates.length === 0) {
                    alert('Please select at least one candidate to export.');
                    return;
                }

                // Add selected parameter with candidate IDs
                params.set('selected', selectedCandidates.join(','));
                console.log('Selected candidates parameter:', selectedCandidates.join(','));
            } else {
                // Remove selected parameter for "export all"
                params.delete('selected');
            }

            // Construct final URL
            url.search = params.toString();
            console.log('Final export URL:', url.toString());

            // Use setTimeout to ensure any Bootstrap dropdown closes before navigation
            setTimeout(() => {
                window.location.href = url.toString();
            }, 10);
        } catch (error) {
            console.error('Export error:', error);
            alert('An error occurred while preparing the export. Please try again.');
        }
    }

    // Export buttons event listeners with error handling - using event delegation
    document.addEventListener('click', function(e) {
        const button = e.target.closest('.export-selected, .export-all');
        if (button) {
            e.preventDefault();
            e.stopPropagation();

            const isSelected = button.classList.contains('export-selected');
            const format = button.dataset.format || button.getAttribute('data-format');

            console.log('Export button clicked (delegated):', {
                isSelected: isSelected,
                format: format,
                classList: button.classList.toString(),
                tagName: button.tagName,
                buttonText: button.textContent.trim()
            });

            if (format) {
                handleExport(format, isSelected);
            } else {
                console.error('Export format not specified for button:', button);
                alert('Export format not specified. Please try again.');
            }
        }
    });

    // Also add direct event listeners to export-selected buttons specifically
    document.querySelectorAll('.export-selected').forEach(button => {
        // Remove any existing event listeners first
        button.onclick = null;
        button.removeEventListener('click', handleExport);

        button.addEventListener('click', function(e) {
            console.log('Direct export-selected button clicked');
            e.preventDefault();
            e.stopPropagation();

            const format = this.dataset.format || this.getAttribute('data-format');
            console.log('Direct click - Format:', format);
            console.log('Button element:', this);

            if (format) {
                handleExport(format, true); // Force selected=true for these buttons
            } else {
                console.error('No format found on export-selected button');
                alert('Export format not found. Please try again.');
            }
        });

        // Ensure button is not disabled and clickable
        button.disabled = false;
        button.style.pointerEvents = 'auto';
        button.style.cursor = 'pointer';
        button.style.userSelect = 'none';

        // Override any Bootstrap dropdown interference
        button.setAttribute('onclick', 'event.preventDefault(); event.stopPropagation();');
    });

    // Add a global click listener as a fallback for debugging
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('export-selected')) {
            console.log('Global click listener caught export-selected button');
        }
    });

    // Update selected count display
    function updateSelectedCount() {
        const selectedCount = document.querySelectorAll('.candidate-select:checked').length;
        const exportDropdown = document.getElementById('exportDropdown');
        const exportSelectedButtons = document.querySelectorAll('.export-selected');
        
        if (exportDropdown) {
            const text = selectedCount > 0 ? ` (${selectedCount} selected)` : '';
            exportDropdown.innerHTML = `<i class="fas fa-download"></i> Export Data${text}`;
        }

        // Update export selected buttons state
        exportSelectedButtons.forEach(button => {
            button.classList.toggle('disabled', selectedCount === 0);
        });
    }

    // Add change event listeners to checkboxes
    candidateCheckboxes.forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            console.log('Checkbox changed:', {
                checkboxValue: this.value,
                checked: this.checked,
                totalCheckboxes: candidateCheckboxes.length
            });
            updateSelectedCount();
            // Update "Select All" checkbox state
            if (selectAllCheckbox) {
                const allChecked = Array.from(candidateCheckboxes).every(cb => cb.checked);
                const anyChecked = Array.from(candidateCheckboxes).some(cb => cb.checked);
                selectAllCheckbox.checked = allChecked;
                selectAllCheckbox.indeterminate = anyChecked && !allChecked;
            }
        });

        // Ensure checkboxes are properly enabled
        checkbox.disabled = false;
        checkbox.style.pointerEvents = 'auto';
    });

    // Initialize the selected count display
    updateSelectedCount();

    // Debug: Log all found elements
    console.log('Page initialized. Found elements:');
    console.log('- Candidate checkboxes:', document.querySelectorAll('.candidate-select').length);
    console.log('- Export selected buttons:', document.querySelectorAll('.export-selected').length);
    console.log('- Export all buttons:', document.querySelectorAll('.export-all').length);
    console.log('- Export dropdown:', document.getElementById('exportDropdown'));

    // Test if buttons are clickable
    document.querySelectorAll('.export-selected').forEach((button, index) => {
        console.log(`Export selected button ${index + 1}:`, {
            format: button.dataset.format,
            classList: button.classList.toString(),
            disabled: button.disabled,
            style: button.getAttribute('style')
        });
    });

    // Force close any open Bootstrap dropdowns after a short delay
    setTimeout(() => {
        const openDropdowns = document.querySelectorAll('.dropdown-menu.show');
        console.log('Open dropdowns found:', openDropdowns.length);
        if (openDropdowns.length > 0) {
            // Close dropdowns that might interfere
            const dropdownButton = document.getElementById('exportDropdown');
            if (dropdownButton) {
                dropdownButton.click(); // This will toggle the dropdown
            }
        }
    }, 1000);

    // Final fallback: Add manual export functions to window for debugging
    window.testExportSelected = function(format) {
        console.log('Manual test export called with format:', format);
        handleExport(format, true);
    };

    window.testExportAll = function(format) {
        console.log('Manual test export all called with format:', format);
        handleExport(format, false);
    };

    console.log('Export functions available for testing:');
    console.log('- testExportSelected(format)');
    console.log('- testExportAll(format)');
});
