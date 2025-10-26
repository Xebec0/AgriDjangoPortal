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

    // Date range picker functionality
    const dateRangeInput = document.getElementById('date_range');
    const dateRangeToggle = document.getElementById('dateRangeToggle');
    const startDateHidden = document.getElementById('start_date_hidden');
    const endDateHidden = document.getElementById('end_date_hidden');
    const startDatePicker = document.getElementById('startDatePicker');
    const endDatePicker = document.getElementById('endDatePicker');
    const applyDateRangeBtn = document.getElementById('applyDateRange');

    // Initialize date pickers with current values
    if (startDateHidden && endDateHidden && startDatePicker && endDatePicker) {
        startDatePicker.value = startDateHidden.value;
        endDatePicker.value = endDateHidden.value;
        updateDateRangeDisplay();
    }

    // Date range toggle button
    if (dateRangeToggle) {
        dateRangeToggle.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();

            console.log('Date range toggle clicked');
            showDateRangeModal();
        });
    }

    // Apply date range button - Note: This button has onclick in HTML, so this is redundant
    // but keeping for programmatic access if needed
    if (applyDateRangeBtn) {
        applyDateRangeBtn.addEventListener('click', function(e) {
            e.preventDefault();
            console.log('Apply date range button clicked');
            applyDateRange();
        });
    }

    // Custom modal functions
    function showDateRangeModal() {
        const modal = document.getElementById('dateRangeModal');
        if (modal) {
            modal.style.display = 'block';
            console.log('Date range modal shown');
        } else {
            console.error('Date range modal not found');
            alert('Date picker is not available. Please use the filter form below.');
        }
    }

    function closeDateRangeModal() {
        const modal = document.getElementById('dateRangeModal');
        if (modal) {
            modal.style.display = 'none';
            console.log('Date range modal closed');
        }
    }

    function applyDateRange() {
        console.log('Apply date range function called');

        if (startDateHidden && endDateHidden && startDatePicker && endDatePicker) {
            startDateHidden.value = startDatePicker.value;
            endDateHidden.value = endDatePicker.value;
            updateDateRangeDisplay();
            closeDateRangeModal();

            // Trigger form submission to refresh results
            document.getElementById('candidateFilterForm').submit();
        }
    }

    // Make functions globally available for onclick handlers
    window.showDateRangeModal = showDateRangeModal;
    window.closeDateRangeModal = closeDateRangeModal;
    window.applyDateRange = applyDateRange;

    // Update date range display text
    function updateDateRangeDisplay() {
        if (dateRangeInput && startDateHidden && endDateHidden) {
            const startDate = startDateHidden.value;
            const endDate = endDateHidden.value;

            if (startDate && endDate) {
                // Format dates for display
                const start = new Date(startDate).toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
                const end = new Date(endDate).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
                dateRangeInput.value = `${start} - ${end}`;
            } else {
                dateRangeInput.value = '';
            }
        }
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

    // Export Selected button functionality
    const exportSelectedBtn = document.getElementById('exportSelectedBtn');
    const exportSelectedModalEl = document.getElementById('exportSelectedModal');
    const exportFormatButtons = document.querySelectorAll('#exportSelectedModal [data-format]');

    // Export Selected button click handler
    if (exportSelectedBtn) {
        exportSelectedBtn.addEventListener('click', function() {
            const selectedCount = document.querySelectorAll('.candidate-select:checked').length;

            if (selectedCount === 0) {
                alert('Please select at least one candidate to export.');
                return;
            }

            // Update count in modal
            document.getElementById('exportSelectedCount').textContent = selectedCount;

            // Show modal using Bootstrap
            if (exportSelectedModalEl) {
                const exportSelectedModal = new bootstrap.Modal(exportSelectedModalEl);
                exportSelectedModal.show();
            }
        });
    }

    // Export format buttons in modal
    exportFormatButtons.forEach(button => {
        button.addEventListener('click', function() {
            const format = this.dataset.format;
            console.log('Export format selected:', format);

            // Close modal using Bootstrap
            if (exportSelectedModalEl) {
                const exportSelectedModal = bootstrap.Modal.getInstance(exportSelectedModalEl);
                if (exportSelectedModal) {
                    exportSelectedModal.hide();
                }
            }

            handleExport(format, true);
        });
    });

    // Close date range modal when clicking on overlay (outside the modal content)
    const dateRangeModal = document.getElementById('dateRangeModal');
    if (dateRangeModal) {
        dateRangeModal.addEventListener('click', function(e) {
            // Only close if clicking directly on the overlay (not on the modal content)
            if (e.target === dateRangeModal) {
                console.log('Clicked outside modal, closing...');
                closeDateRangeModal();
            }
        });
    }

    // Close modal on ESC key press
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && dateRangeModal && dateRangeModal.style.display === 'block') {
            console.log('ESC key pressed, closing modal...');
            closeDateRangeModal();
        }
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
        const exportSelectedBtn = document.getElementById('exportSelectedBtn');
        const selectedCountSpan = document.getElementById('selectedCount');

        console.log('Update selected count:', selectedCount);

        // Update Export Selected button visibility and count
        if (exportSelectedBtn) {
            if (selectedCount > 0) {
                exportSelectedBtn.style.display = 'inline-block';
                selectedCountSpan.textContent = selectedCount;
            } else {
                exportSelectedBtn.style.display = 'none';
            }
        }

        // Update old export dropdown (keeping for backward compatibility)
        const exportDropdown = document.getElementById('exportDropdown');
        if (exportDropdown) {
            const text = selectedCount > 0 ? ` (${selectedCount} selected)` : '';
            exportDropdown.innerHTML = `<i class="fas fa-download"></i> Export Data${text}`;
        }
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

    // Manual test functions for debugging
    window.testDateRangeModal = function() {
        console.log('Manual test date range modal');
        showDateRangeModal();
    };

    window.testExportSelected = function(format) {
        console.log('Manual test export called with format:', format);
        handleExport(format, true);
    };

    window.testExportAll = function(format) {
        console.log('Manual test export all called with format:', format);
        handleExport(format, false);
    };

    console.log('Test functions available:');
    console.log('- testDateRangeModal()');
    console.log('- testExportSelected(format)');
    console.log('- testExportAll(format)');
});
