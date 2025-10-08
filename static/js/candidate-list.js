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
            let url = new URL(window.location.href);
            // Preserve existing search parameters except 'page'
            const params = new URLSearchParams(url.search);
            params.delete('page');
            params.set('export', format);

            if (selectedOnly) {
                const selectedCandidates = Array.from(document.querySelectorAll('.candidate-select:checked'))
                    .map(checkbox => checkbox.value)
                    .filter(value => value); // Filter out any empty values

                if (selectedCandidates.length === 0) {
                    alert('Please select at least one candidate to export.');
                    return;
                }

                params.set('selected', selectedCandidates.join(','));
            } else {
                params.delete('selected'); // Ensure 'selected' parameter is removed for "export all"
            }

            // Construct final URL
            url.search = params.toString();
            window.location.href = url.toString();
        } catch (error) {
            console.error('Export error:', error);
            alert('An error occurred while preparing the export. Please try again.');
        }
    }

    // Export buttons event listeners with error handling
    document.querySelectorAll('.export-selected, .export-all').forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault(); // Prevent any default button behavior
            const isSelected = this.classList.contains('export-selected');
            const format = this.dataset.format;
            if (format) {
                handleExport(format, isSelected);
            } else {
                console.error('Export format not specified');
                alert('Export format not specified. Please try again.');
            }
        });
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
            updateSelectedCount();
            // Update "Select All" checkbox state
            if (selectAllCheckbox) {
                const allChecked = Array.from(candidateCheckboxes).every(cb => cb.checked);
                const anyChecked = Array.from(candidateCheckboxes).some(cb => cb.checked);
                selectAllCheckbox.checked = allChecked;
                selectAllCheckbox.indeterminate = anyChecked && !allChecked;
            }
        });
    });

    // Initialize the selected count display
    updateSelectedCount();
});
