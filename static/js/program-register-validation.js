// Program Registration File Upload Enhancements
// Handles file name display, type/size validation, and drag-and-drop

document.addEventListener('DOMContentLoaded', function() {
    const fileFields = [
        'id_tor', 'id_nc2_tesda', 'id_diploma', 'id_good_moral', 'id_nbi_clearance'
    ];
    const maxSize = 5 * 1024 * 1024; // 5MB
    const allowedType = 'application/pdf';

    fileFields.forEach(function(fieldId) {
        const input = document.getElementById(fieldId);
        if (!input) return;

        // Show selected file name
        input.addEventListener('change', function(e) {
            const file = input.files[0];
            let msg = '';
            if (file) {
                if (file.type !== allowedType) {
                    msg = 'Only PDF files are allowed.';
                    input.value = '';
                } else if (file.size > maxSize) {
                    msg = 'File must be less than 5MB.';
                    input.value = '';
                } else {
                    msg = file.name;
                }
            }
            let feedback = input.parentNode.querySelector('.file-feedback');
            if (!feedback) {
                feedback = document.createElement('div');
                feedback.className = 'file-feedback text-info small mt-1';
                input.parentNode.appendChild(feedback);
            }
            feedback.textContent = msg;
        });

        // Drag-and-drop support
        const wrapper = input.closest('.mb-3');
        if (wrapper) {
            wrapper.addEventListener('dragover', function(e) {
                e.preventDefault();
                wrapper.classList.add('border-primary');
            });
            wrapper.addEventListener('dragleave', function(e) {
                e.preventDefault();
                wrapper.classList.remove('border-primary');
            });
            wrapper.addEventListener('drop', function(e) {
                e.preventDefault();
                wrapper.classList.remove('border-primary');
                const files = e.dataTransfer.files;
                if (files.length > 0) {
                    input.files = files;
                    input.dispatchEvent(new Event('change'));
                }
            });
        }
    });
}); 