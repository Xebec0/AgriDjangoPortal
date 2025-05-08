// Client-side form validation for registration page

document.addEventListener('DOMContentLoaded', function() {
    const registerForm = document.getElementById('registerForm');
    const passwordInput = document.getElementById('id_password1');
    const confirmPasswordInput = document.getElementById('id_password2');
    const usernameInput = document.getElementById('id_username');
    const emailInput = document.getElementById('id_email');
    const firstNameInput = document.getElementById('id_first_name');
    const lastNameInput = document.getElementById('id_last_name');
    const passwordStrengthMeter = document.getElementById('passwordStrengthMeter');
    const passwordStrengthLabel = document.getElementById('passwordStrengthLabel');

    // Initialize form validation
    if (registerForm) {
        registerForm.addEventListener('submit', validateForm);
        
        // Live validation as user types
        if (firstNameInput) firstNameInput.addEventListener('input', () => validateField(firstNameInput, isNotEmpty));
        if (lastNameInput) lastNameInput.addEventListener('input', () => validateField(lastNameInput, isNotEmpty));
        if (usernameInput) usernameInput.addEventListener('input', () => validateField(usernameInput, isValidUsername));
        if (emailInput) emailInput.addEventListener('input', () => validateField(emailInput, isValidEmail));
        if (passwordInput) {
            passwordInput.addEventListener('input', () => {
                validateField(passwordInput, isStrongPassword);
                updatePasswordStrength(passwordInput.value);
                if (confirmPasswordInput.value) {
                    validateField(confirmPasswordInput, () => passwordsMatch(passwordInput.value, confirmPasswordInput.value));
                }
            });
        }
        if (confirmPasswordInput) {
            confirmPasswordInput.addEventListener('input', () => {
                validateField(confirmPasswordInput, () => passwordsMatch(passwordInput.value, confirmPasswordInput.value));
            });
        }
    }

    // Validate the entire form
    function validateForm(event) {
        let isValid = true;
        
        // Validate each field
        if (firstNameInput && !validateField(firstNameInput, isNotEmpty)) isValid = false;
        if (lastNameInput && !validateField(lastNameInput, isNotEmpty)) isValid = false;
        if (usernameInput && !validateField(usernameInput, isValidUsername)) isValid = false;
        if (emailInput && !validateField(emailInput, isValidEmail)) isValid = false;
        if (passwordInput && !validateField(passwordInput, isStrongPassword)) isValid = false;
        if (confirmPasswordInput && !validateField(confirmPasswordInput, () => passwordsMatch(passwordInput.value, confirmPasswordInput.value))) isValid = false;
        
        if (!isValid) {
            event.preventDefault();
            // Show an error message at the top of the form
            const errorDiv = document.getElementById('formErrors') || document.createElement('div');
            errorDiv.id = 'formErrors';
            errorDiv.className = 'alert alert-danger';
            errorDiv.textContent = 'Please correct the errors in the form before submitting.';
            registerForm.prepend(errorDiv);
            
            // Scroll to the first error
            const firstError = document.querySelector('.is-invalid');
            if (firstError) {
                firstError.scrollIntoView({ behavior: 'smooth', block: 'center' });
                firstError.focus();
            }
        }
    }

    // Validate a single field based on a validation function
    function validateField(field, validationFn) {
        resetValidation(field);
        
        const isValid = validationFn(field.value);
        
        if (isValid) {
            field.classList.add('is-valid');
            field.classList.remove('is-invalid');
            
            // Show success message if one exists
            const successFeedback = field.nextElementSibling;
            if (successFeedback && successFeedback.classList.contains('valid-feedback')) {
                successFeedback.style.display = 'block';
            }
        } else {
            field.classList.add('is-invalid');
            field.classList.remove('is-valid');
            
            // Show error message
            const errorFeedback = Array.from(field.parentNode.children).find(el => el.classList.contains('invalid-feedback'));
            if (errorFeedback) {
                errorFeedback.style.display = 'block';
            }
        }
        
        return isValid;
    }

    // Reset validation state
    function resetValidation(field) {
        field.classList.remove('is-valid', 'is-invalid');
        
        // Hide all feedback
        const feedbacks = field.parentNode.querySelectorAll('.valid-feedback, .invalid-feedback');
        feedbacks.forEach(el => el.style.display = 'none');
    }

    // Validation functions
    function isNotEmpty(value) {
        return value.trim() !== '';
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
