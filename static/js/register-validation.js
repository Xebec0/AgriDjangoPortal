// Client-side form validation for registration page

document.addEventListener('DOMContentLoaded', function() {
    // Event delegation for dynamic content (modals)
    document.addEventListener('input', function(event) {
        const target = event.target;
        
        // Validate first name
        if (target.matches('#id_first_name')) {
            validateField(target, isValidName, 'Names must consist of letters only (no numbers or special characters)');
        }
        
        // Validate last name
        if (target.matches('#id_last_name')) {
            validateField(target, isValidName, 'Names must consist of letters only (no numbers or special characters)');
        }
        
        // Validate username
        if (target.matches('#id_username')) {
            validateField(target, isValidUsername);
        }
        
        // Validate email
        if (target.matches('#id_email')) {
            validateField(target, isValidEmail);
        }
        
        // Validate password
        if (target.matches('#id_password1')) {
            validateField(target, isStrongPassword);
            updatePasswordStrength(target.value);
            // Re-validate confirm password if filled
            const confirmPw = document.querySelector('#id_password2');
            if (confirmPw && confirmPw.value) {
                validateField(confirmPw, () => passwordsMatch(target.value, confirmPw.value));
            }
        }
        
        // Validate confirm password
        if (target.matches('#id_password2')) {
            const password = document.querySelector('#id_password1');
            validateField(target, () => passwordsMatch(password ? password.value : '', target.value));
        }
    });

    // Form submission validation
    document.addEventListener('submit', function(event) {
        const form = event.target;
        if (form.id === 'registerForm' || form.id === 'registerModalForm') {
            event.preventDefault(); // Always prevent default to handle manually
            if (validateEntireForm(form)) {
                form.submit(); // Submit if valid
            }
        }
    });

    // Re-validate on modal show for any pre-filled content
    const registerModal = document.getElementById('registerModal');
    if (registerModal) {
        registerModal.addEventListener('shown.bs.modal', function () {
            // Trigger validation for all fields in modal
            const modalFields = ['#id_first_name', '#id_last_name', '#id_username', '#id_email', '#id_password1', '#id_password2'];
            modalFields.forEach(selector => {
                const field = document.querySelector(selector);
                if (field && field.value) {
                    // Trigger input event to validate
                    field.dispatchEvent(new Event('input', { bubbles: true }));
                }
            });
        });
    }

    // Validate the entire form
    function validateEntireForm(form) {
        let isValid = true;
        
        // Find elements within the form
        const firstNameEl = form.querySelector('#id_first_name');
        const lastNameEl = form.querySelector('#id_last_name');
        const usernameEl = form.querySelector('#id_username');
        const emailEl = form.querySelector('#id_email');
        const passwordEl = form.querySelector('#id_password1');
        const confirmPasswordEl = form.querySelector('#id_password2');
        
        // Validate each field
        if (firstNameEl && !validateField(firstNameEl, isValidName, 'Names must consist of letters only (no numbers or special characters)')) isValid = false;
        if (lastNameEl && !validateField(lastNameEl, isValidName, 'Names must consist of letters only (no numbers or special characters)')) isValid = false;
        if (usernameEl && !validateField(usernameEl, isValidUsername)) isValid = false;
        if (emailEl && !validateField(emailEl, isValidEmail)) isValid = false;
        if (passwordEl && !validateField(passwordEl, isStrongPassword)) isValid = false;
        if (confirmPasswordEl && !validateField(confirmPasswordEl, () => passwordsMatch(passwordEl.value, confirmPasswordEl.value))) isValid = false;
        
        if (!isValid) {
            // Show an error message at the top of the form
            const errorDivId = form.id === 'registerModalForm' ? 'registerModalErrors' : 'formErrors';
            let errorDiv = document.getElementById(errorDivId);
            if (!errorDiv) {
                errorDiv = document.createElement('div');
                errorDiv.id = errorDivId;
                errorDiv.className = 'alert alert-danger';
                form.insertBefore(errorDiv, form.firstChild);
            }
            errorDiv.style.display = 'block';
            errorDiv.textContent = 'Please correct the errors in the form before submitting.';
            
            // Scroll to the first error
            const firstError = form.querySelector('.is-invalid');
            if (firstError) {
                firstError.scrollIntoView({ behavior: 'smooth', block: 'center' });
                firstError.focus();
            }
        }
        
        return isValid;
    }

    // Validate a single field based on a validation function
    function validateField(field, validationFn, customErrorMessage = null) {
        resetValidation(field);
        
        const isValid = validationFn(field.value);
        
        // Find the container (col-md-6 mb-3 or similar)
        const container = field.closest('.mb-3') || field.parentElement.parentElement;
        
        if (isValid) {
            field.classList.add('is-valid');
            field.classList.remove('is-invalid');
            
            // Show success message if one exists
            const successFeedback = container.querySelector('.valid-feedback');
            if (successFeedback) {
                successFeedback.style.display = 'block';
            }
        } else {
            field.classList.add('is-invalid');
            field.classList.remove('is-valid');
            
            // Show error message
            const errorFeedback = container.querySelector('.invalid-feedback');
            if (errorFeedback) {
                if (customErrorMessage) {
                    errorFeedback.textContent = customErrorMessage;
                }
                errorFeedback.style.display = 'block';
            }
        }
        
        return isValid;
    }

    // Reset validation state
    function resetValidation(field) {
        field.classList.remove('is-valid', 'is-invalid');
        
        // Find the container and hide all feedback
        const container = field.closest('.mb-3') || field.parentElement.parentElement;
        const feedbacks = container.querySelectorAll('.valid-feedback, .invalid-feedback');
        feedbacks.forEach(el => el.style.display = 'none');
    }

    // Validation functions
    function isNotEmpty(value) {
        return value.trim() !== '';
    }

    function isValidName(value) {
        // Only allow letters and spaces for names (no numbers or special characters)
        return /^[a-zA-Z\s]+$/.test(value.trim());
    }

    function isValidUsername(value) {
        return /^[a-zA-Z0-9_]{3,20}$/.test(value);
    }

    function isValidEmail(value) {
        return /^[a-zA-Z0-9._-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,6}$/.test(value);
    }

    function isStrongPassword(value) {
        // At least 8 characters, 1 uppercase, 1 lowercase, 1 number
        return /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}$/.test(value);
    }

    function passwordsMatch(password1, password2) {
        return password1 === password2;
    }

    // Update password strength meter
    function updatePasswordStrength(password) {
        if (!passwordStrengthMeter || !passwordStrengthLabel) return;
        
        let strength = 0;
        let label = '';
        
        // Calculate password strength
        if (password.length >= 8) strength += 1;
        if (/[A-Z]/.test(password)) strength += 1;
        if (/[a-z]/.test(password)) strength += 1;
        if (/[0-9]/.test(password)) strength += 1;
        if (/[^A-Za-z0-9]/.test(password)) strength += 1;
        
        // Update the UI based on strength
        const meterBar = passwordStrengthMeter.querySelector('div');
        
        if (strength >= 4) {
            label = 'Strong';
            meterBar.style.width = '100%';
            meterBar.className = 'strength-strong';
        } else if (strength >= 3) {
            label = 'Medium';
            meterBar.style.width = '66%';
            meterBar.className = 'strength-medium';
        } else if (password.length > 0) {
            label = 'Weak';
            meterBar.style.width = '33%';
            meterBar.className = 'strength-weak';
        } else {
            label = '';
            meterBar.style.width = '0';
            meterBar.className = '';
        }
        
        passwordStrengthLabel.textContent = label;
    }
});
