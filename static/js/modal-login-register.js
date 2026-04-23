/**
 * Modal Login and Registration functionality
 * Handles AJAX loading of modal content and form submissions
 * All animations have been disabled for performance optimization
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize the modals
    setupLoginModal();
    setupRegisterModal();
    setupAdminRegisterModal();
    setupModalSwitching();
});

// CSRF helpers
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function getCSRFToken() {
    const token = getCookie('csrftoken');
    if (!token) {
        // Try to get it from the form if available
        const csrfInput = document.querySelector('input[name="csrfmiddlewaretoken"]');
        if (csrfInput) {
            return csrfInput.value;
        }
    }
    return token;
}

// Safely parse JSON without reading the body twice
async function parseJsonSafe(response, contextLabel) {
    const clone = response.clone();
    try {
        if (!response.ok) {
            const text = await response.text();
            console.error(`${contextLabel} request failed`, { status: response.status, text });
            throw new Error(text || `HTTP ${response.status}`);
        }
        return await response.json();
    } catch (e) {
        if (e.message) {
            throw e;
        }
        // Fallback to text from the clone so we don't read the body twice
        const text = await clone.text();
        console.error(`${contextLabel} response not JSON`, { status: response.status, text });
        throw new Error(text || `HTTP ${response.status}`);
    }
}

/**
 * Setup the login modal functionality
 */
function setupLoginModal() {
    const loginModal = document.getElementById('loginModal');
    const loginModalContent = document.getElementById('loginModalContent');
    
    if (loginModal) {
        // Load the login form when the modal is shown
        loginModal.addEventListener('show.bs.modal', function() {
            // Animation classes disabled
            const modalDialog = loginModal.querySelector('.modal-dialog');
            if (modalDialog) {
                modalDialog.classList.remove('animate-zoom-in');
                modalDialog.classList.remove('animate-zoom-out');
            }
            
            // Only load if not already loaded or if there was an error
            if (!loginModalContent.querySelector('form') || 
                loginModalContent.querySelector('.alert-danger')) {
                loadModalContent('/modal/login/', loginModalContent);
            } else {
                // Animations disabled
                const formElements = loginModalContent.querySelectorAll('.form-group, .mb-3, .mb-4, .alert, .d-grid');
                formElements.forEach(element => {
                    element.classList.remove('animate-field');
                });
            }
        });
        
        // Reset modal when hidden
        loginModal.addEventListener('hide.bs.modal', function() {
            // Animations disabled
            const modalDialog = loginModal.querySelector('.modal-dialog');
            if (modalDialog) {
                modalDialog.classList.remove('animate-zoom-in');
                modalDialog.classList.remove('animate-zoom-out');
            }
        });
        
        // Clean up after animation completes
        loginModal.addEventListener('hidden.bs.modal', function() {
            // We don't clear the content to avoid flickering on reopening
            // Just clear any error messages
            const errorElement = loginModalContent.querySelector('.alert-danger');
            if (errorElement) {
                errorElement.style.display = 'none';
            }
            
            // Animation classes disabled
            const modalDialog = loginModal.querySelector('.modal-dialog');
            if (modalDialog) {
                modalDialog.classList.remove('animate-zoom-out');
                modalDialog.classList.remove('animate-zoom-in');
            }
        });
        
        // Setup username validation
        setupUsernameValidation();

        // Handle form submission via event delegation
        document.addEventListener('submit', function(e) {
            const form = e.target;

            // Check if this is the login modal form
            if (form.id === 'loginModalForm') {
                e.preventDefault();

                // Validate username exists before submitting
                const usernameInput = form.querySelector('#id_username');
                const username = usernameInput ? usernameInput.value.trim() : '';

                if (!username) {
                    showLoginError('Please enter your username.');
                    return;
                }

                // Check if username validation has been performed and passed
                if (usernameInput && usernameInput.dataset.validated === 'false') {
                    showLoginError('Please check that your username is registered.');
                    return;
                }

                const submitButton = form.querySelector('button[type="submit"]');
                const originalText = submitButton.innerHTML;
                submitButton.disabled = true;
                submitButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Signing in...';

                // Hide any previous error messages
                const errorElement = document.getElementById('loginModalErrors');
                if (errorElement) {
                    errorElement.style.display = 'none';
                }

                // Get form data
                const formData = new FormData(form);

                // Convert FormData to URLSearchParams for proper form submission
                const params = new URLSearchParams();
                for (const pair of formData.entries()) {
                    params.append(pair[0], pair[1]);
                }

                // Submit the form via AJAX
                fetch('/api/ajax-login/', {
                    method: 'POST',
                    body: params,
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest',
                        'Content-Type': 'application/x-www-form-urlencoded',
                        'X-CSRFToken': getCSRFToken() || ''
                    },
                    credentials: 'same-origin',
                    mode: 'same-origin'
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        // Show success toast
                        if (typeof showToast === 'function') {
                            showToast('Success', data.message, 'success');
                        }

                        // Hide the modal
                        const modalInstance = bootstrap.Modal.getInstance(loginModal);
                        modalInstance.hide();

                        // Redirect or reload
                        setTimeout(function() {
                            if (data.redirect) {
                                window.location.href = data.redirect;
                            } else {
                                window.location.reload();
                            }
                        }, 500);
                    } else {
                        // Show error messages
                        if (errorElement) {
                            let errorMessage = 'Login failed. Please check your credentials.';
                            if (data.errors && data.errors.__all__) {
                                errorMessage = data.errors.__all__.join('<br>');
                            }
                            errorElement.innerHTML = errorMessage;
                            errorElement.style.display = 'block';
                        }

                        // Reset the button
                        submitButton.disabled = false;
                        submitButton.innerHTML = originalText;
                    }
                })
                .catch(error => {
                    console.error('Error during login:', error);

                    // Show error message
                    if (errorElement) {
                        let errorMessage = 'An error occurred during login. Please try again.';
                        if (error.message && !error.message.includes('<!DOCTYPE html>')) {
                            errorMessage = error.message;
                        }
                        errorElement.innerHTML = errorMessage;
                        errorElement.style.display = 'block';
                    }

                    // Reset the button
                    submitButton.disabled = false;
                    submitButton.innerHTML = originalText;
                });
            }
        });
    }
}

/**
 * Setup the registration modal functionality
 */
function setupRegisterModal() {
    const registerModal = document.getElementById('registerModal');
    const registerModalContent = document.getElementById('registerModalContent');
    
    if (registerModal) {
        let currentStep = 1;
        const totalSteps = 5;
        let nextBtn, prevBtn, stepIndicator, form, errorElement;
        
        // Load the registration form when the modal is shown
        registerModal.addEventListener('show.bs.modal', function() {
            // Animation classes disabled
            const modalDialog = registerModal.querySelector('.modal-dialog');
            if (modalDialog) {
                modalDialog.classList.remove('animate-zoom-in');
                modalDialog.classList.remove('animate-zoom-out');
            }
            
            // Only load if not already loaded or if there was an error
            if (!registerModalContent.querySelector('form') || 
                registerModalContent.querySelector('.alert-danger')) {
                // Content will be replaced — new DOM needs fresh initialization
                var oldForm = registerModalContent.querySelector('#registerModalForm');
                if (oldForm) delete oldForm.dataset.initialized;
                loadModalContent('/modal/register/', registerModalContent).then(() => {
                    setTimeout(() => {
                        initializeMultiStep();
                    }, 100);
                });
            } else {
                // Initialize multi-step immediately if already loaded
                setTimeout(() => {
                    initializeMultiStep();
                }, 100);
            }
        });
        
        // Reset modal when hidden
        registerModal.addEventListener('hide.bs.modal', function() {
            // Animation classes disabled
            const modalDialog = registerModal.querySelector('.modal-dialog');
            if (modalDialog) {
                modalDialog.classList.remove('animate-zoom-in');
                modalDialog.classList.remove('animate-zoom-out');
            }
            // Reset to step 1
            currentStep = 1;
        });
        
        // Clean up after animation completes
        registerModal.addEventListener('hidden.bs.modal', function() {
            // Clear OAuth session data when modal is closed
            fetch('/api/clear-oauth-session/', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCSRFToken(),
                    'Content-Type': 'application/json'
                },
                credentials: 'same-origin'
            }).catch(error => {
                console.log('Failed to clear OAuth session:', error);
            });
            
            // We don't clear the content to avoid flickering on reopening
            // Just clear any error messages
            const errorElement = registerModalContent.querySelector('.alert-danger');
            if (errorElement) {
                errorElement.style.display = 'none';
            }
            
            // Animation classes disabled
            const modalDialog = registerModal.querySelector('.modal-dialog');
            if (modalDialog) {
                modalDialog.classList.remove('animate-zoom-out');
                modalDialog.classList.remove('animate-zoom-in');
            }
        });
        
        function initializeMultiStep() {
            form = registerModalContent.querySelector('#registerModalForm');
            if (!form) return;
            
            const formSteps = registerModalContent.querySelectorAll('.form-step');
            nextBtn = registerModalContent.querySelector('#nextBtn');
            prevBtn = registerModalContent.querySelector('#prevBtn');
            stepIndicator = registerModalContent.querySelector('#stepIndicator');
            errorElement = registerModalContent.querySelector('#registerModalErrors');
            
            if (!nextBtn || !prevBtn || !stepIndicator || formSteps.length === 0) return;
            
            // Reset to step 1
            currentStep = 1;
            showStep(currentStep);
            
            // Prevent duplicate listener attachment on re-open
            if (!form.dataset.initialized) {
                nextBtn.addEventListener('click', handleNextClick);
                prevBtn.addEventListener('click', handlePrevClick);
                setupRealTimeValidation();
                form.dataset.initialized = 'true';
            }
        }
        
        function showStep(n) {
            const formSteps = registerModalContent.querySelectorAll('.form-step');
            formSteps.forEach((step, index) => {
                step.classList.toggle('active', index + 1 === n);
            });

            prevBtn.style.display = n === 1 ? 'none' : 'inline-flex';

            if (n === totalSteps) {
                nextBtn.innerHTML = '<i class="fas fa-user-plus me-1"></i> Create Account';
                nextBtn.classList.add('submit-btn');
            } else {
                nextBtn.innerHTML = 'Next <i class="fas fa-arrow-right"></i>';
                nextBtn.classList.remove('submit-btn');
            }

            stepIndicator.textContent = `Step ${n} of ${totalSteps}`;

            // Update stepper circles (validation-driven)
            refreshStepperState();

            // Animate stepper fill line (scaleX relative to its own width)
            var stepperFill = document.querySelector('#registerModal #regStepperFill');
            if (stepperFill) {
                var totalGaps = totalSteps - 1;
                var fillFraction = n > 1 ? (n - 1) / totalGaps : 0;
                stepperFill.style.transform = 'scaleX(' + fillFraction + ')';
            }

            // Scroll to top of modal body
            const modalBody = registerModal.querySelector('.modal-body');
            if (modalBody) {
                modalBody.scrollTop = 0;
            }
        }
        
        function validateStep(step, silent) {
            let isValid = true;
            const errors = [];

            // Clear previous step errors (skip in silent mode)
            if (!silent && errorElement) {
                errorElement.innerHTML = '';
                errorElement.classList.add('d-none');
            }

            // Helper: check required field and add visual feedback
            function req(selector, label) {
                const field = form.querySelector(selector);
                if (!field) return;
                if (!field.value || !field.value.trim()) {
                    errors.push(label + ' is required.');
                    isValid = false;
                    if (!silent) {
                        field.classList.add('is-invalid');
                        field.classList.remove('is-valid');
                    }
                } else if (!silent) {
                    field.classList.add('is-valid');
                    field.classList.remove('is-invalid');
                }
            }

            // Helper: check matching fields
            function match(sel1, sel2, label) {
                const f1 = form.querySelector(sel1);
                const f2 = form.querySelector(sel2);
                if (!f1 || !f2) return;
                if (f1.value && f2.value && f1.value.trim() !== f2.value.trim()) {
                    errors.push(label + ' do not match.');
                    isValid = false;
                    if (!silent) {
                        f2.classList.add('is-invalid');
                        f2.classList.remove('is-valid');
                    }
                }
            }

            switch (step) {
                case 1:
                    req('#id_username', 'Username');
                    req('#id_email', 'Email');
                    req('#id_confirm_email', 'Confirm Email');
                    match('#id_email', '#id_confirm_email', 'Emails');
                    req('#id_password1', 'Password');
                    req('#id_password2', 'Confirm Password');
                    match('#id_password1', '#id_password2', 'Passwords');
                    break;
                case 2:
                    req('#id_first_name', 'First name');
                    req('#id_last_name', 'Last name');
                    break;
                case 3:
                    req('#id_date_of_birth', 'Date of birth');
                    req('#id_gender', 'Gender');
                    req('#id_nationality', 'Nationality');
                    break;
                case 4:
                    req('#id_passport_number', 'Passport number');
                    req('#id_confirm_passport_number', 'Confirm Passport number');
                    match('#id_passport_number', '#id_confirm_passport_number', 'Passport numbers');
                    req('#id_passport_issue_date', 'Passport issue date');
                    req('#id_passport_expiry_date', 'Passport expiry date');
                    // Validate expiry > issue
                    (function() {
                        var issue = form.querySelector('#id_passport_issue_date');
                        var expiry = form.querySelector('#id_passport_expiry_date');
                        if (issue && expiry && issue.value && expiry.value) {
                            if (new Date(expiry.value) <= new Date(issue.value)) {
                                errors.push('Passport expiry date must be after issue date.');
                                isValid = false;
                                expiry.classList.add('is-invalid');
                                expiry.classList.remove('is-valid');
                            }
                        }
                    })();
                    req('#id_highest_education_level', 'Education level');
                    req('#id_field_of_study', 'Field of study');
                    req('#id_graduation_year', 'Graduation year');
                    break;
                case 5:
                    // Optional documents step
                    break;
            }
            
            // Use toast notification instead of inline error (skip in silent mode)
            if (!isValid && !silent) {
                if (typeof showRegisterToast === 'function') {
                    showRegisterToast(errors, 'error', true);
                } else if (errorElement) {
                    errorElement.innerHTML = errors.join('<br>');
                    errorElement.classList.remove('d-none');
                }
                // Focus first invalid field in the active step
                var firstInvalid = form.querySelector('.form-step.active .is-invalid');
                if (firstInvalid) {
                    firstInvalid.scrollIntoView({ behavior: 'smooth', block: 'center' });
                    firstInvalid.focus();
                }
            }
            
            return isValid;
        }

        // Silent validator — returns true/false without touching UI
        function isStepValid(step) {
            return validateStep(step, true);
        }

        // Refresh stepper circles based on current step + validation state
        function refreshStepperState() {
            var regSteps = document.querySelectorAll('#registerModal .reg-step');
            regSteps.forEach(function(stepEl) {
                var stepNum = parseInt(stepEl.getAttribute('data-step'), 10);
                stepEl.classList.remove('active', 'completed', 'valid');
                if (stepNum === currentStep) {
                    stepEl.classList.add('active');
                    // Mark as valid (green) if all required fields are valid
                    if (isStepValid(stepNum)) {
                        stepEl.classList.add('valid');
                    }
                } else if (stepNum < currentStep) {
                    // Past steps: green + checkmark if still valid, else in-progress look
                    if (isStepValid(stepNum)) {
                        stepEl.classList.add('completed');
                    } else {
                        stepEl.classList.add('active');
                    }
                }
            });
        }
        
        function handleNextClick() {
            if (currentStep < totalSteps) {
                if (validateStep(currentStep)) {
                    currentStep++;
                    showStep(currentStep);
                }
            } else {
                // Submit the form on step 4
                submitRegisterForm();
            }
        }
        
        function handlePrevClick() {
            if (currentStep > 1) {
                currentStep--;
                showStep(currentStep);
            }
        }
        
        function setupRealTimeValidation() {
            // ---- Helpers ----
            function attachValidator(selector, validatorFn, opts) {
                opts = opts || {};
                var field = form.querySelector(selector);
                if (!field) return;
                var handler = function() {
                    var val = field.value.trim();
                    if (!val) {
                        if (opts.required) {
                            field.classList.add('is-invalid');
                            field.classList.remove('is-valid');
                        } else {
                            field.classList.remove('is-valid', 'is-invalid');
                        }
                        return;
                    }
                    if (validatorFn(val)) {
                        field.classList.add('is-valid');
                        field.classList.remove('is-invalid');
                    } else {
                        field.classList.add('is-invalid');
                        field.classList.remove('is-valid');
                    }
                };
                field.addEventListener('input', handler);
                if (opts.alsoOnChange) field.addEventListener('change', handler);
            }

            function attachPairValidator(srcSel, confirmSel) {
                var src = form.querySelector(srcSel);
                var confirm = form.querySelector(confirmSel);
                if (!src || !confirm) return;
                var validate = function() {
                    if (!confirm.value) {
                        confirm.classList.remove('is-valid', 'is-invalid');
                        return;
                    }
                    if (src.value === confirm.value) {
                        confirm.classList.add('is-valid');
                        confirm.classList.remove('is-invalid');
                    } else {
                        confirm.classList.add('is-invalid');
                        confirm.classList.remove('is-valid');
                    }
                };
                confirm.addEventListener('input', validate);
                src.addEventListener('input', function() { if (confirm.value) validate(); });
            }

            // ==== Step 1: Account Information ====
            attachValidator('#id_username', function(v) { return /^[a-zA-Z0-9_]{3,20}$/.test(v); }, { required: true });
            attachValidator('#id_email', function(v) { return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v); }, { required: true });
            attachPairValidator('#id_email', '#id_confirm_email');

            // Password with strength indicator
            var pw1 = form.querySelector('#id_password1');
            var pw2 = form.querySelector('#id_password2');
            if (pw1) {
                pw1.addEventListener('input', function() {
                    var val = this.value;
                    var strengthDiv = this.closest('.mb-3') ? this.closest('.mb-3').querySelector('.password-strength') : null;

                    if (val) {
                        if (strengthDiv) strengthDiv.style.display = 'block';
                        var reqs = {
                            length: val.length >= 8,
                            uppercase: /[A-Z]/.test(val),
                            lowercase: /[a-z]/.test(val),
                            number: /[0-9]/.test(val)
                        };
                        var score = 0;
                        for (var k in reqs) { if (reqs[k]) score++; }

                        // Update progress bar
                        var bar = strengthDiv ? strengthDiv.querySelector('.progress-bar') : null;
                        if (bar) {
                            bar.style.width = (score / 4 * 100) + '%';
                            bar.className = 'progress-bar ' + (
                                score <= 1 ? 'bg-danger' :
                                score <= 2 ? 'bg-warning' :
                                score <= 3 ? 'bg-info' : 'bg-success'
                            );
                        }

                        // Update requirement icons
                        for (var req in reqs) {
                            var el = strengthDiv ? strengthDiv.querySelector('[data-requirement="' + req + '"]') : null;
                            if (el) {
                                var icon = el.querySelector('i');
                                if (icon) icon.className = reqs[req] ? 'fas fa-check text-success' : 'fas fa-times text-danger';
                            }
                        }

                        // Field valid/invalid state
                        var strong = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}$/.test(val);
                        if (strong) {
                            this.classList.add('is-valid');
                            this.classList.remove('is-invalid');
                        } else {
                            this.classList.add('is-invalid');
                            this.classList.remove('is-valid');
                        }
                    } else {
                        if (strengthDiv) strengthDiv.style.display = 'none';
                        this.classList.remove('is-valid', 'is-invalid');
                    }

                    // Re-check password match
                    if (pw2 && pw2.value) pw2.dispatchEvent(new Event('input'));
                });
            }

            // Password match indicator
            if (pw1 && pw2) {
                pw2.addEventListener('input', function() {
                    var matchDiv = this.closest('.mb-3') ? this.closest('.mb-3').querySelector('.password-match') : null;
                    if (!this.value) {
                        this.classList.remove('is-valid', 'is-invalid');
                        if (matchDiv) matchDiv.style.display = 'none';
                        return;
                    }
                    var isMatch = pw1.value === this.value;
                    if (matchDiv) {
                        matchDiv.style.display = 'block';
                        matchDiv.innerHTML = isMatch
                            ? '<small class="text-success"><i class="fas fa-check-circle"></i> Passwords match</small>'
                            : '<small class="text-danger"><i class="fas fa-times-circle"></i> Passwords do not match</small>';
                    }
                    if (isMatch) {
                        this.classList.add('is-valid');
                        this.classList.remove('is-invalid');
                    } else {
                        this.classList.add('is-invalid');
                        this.classList.remove('is-valid');
                    }
                });
            }

            // ==== Step 2: Basic Information ====
            attachValidator('#id_first_name', function(v) { return /^[a-zA-Z\s\-']+$/.test(v); }, { required: true });
            attachValidator('#id_last_name', function(v) { return /^[a-zA-Z\s\-']+$/.test(v); }, { required: true });
            attachValidator('#id_middle_initial', function() { return true; });
            attachValidator('#id_address', function() { return true; });

            // Phone: allow only digits and phone chars
            var phoneField = form.querySelector('#id_phone_number');
            if (phoneField) {
                phoneField.addEventListener('input', function() {
                    this.value = this.value.replace(/[^0-9\s\-\+\(\)\.]/g, '');
                    if (this.value.trim()) {
                        this.classList.add('is-valid');
                        this.classList.remove('is-invalid');
                    } else {
                        this.classList.remove('is-valid', 'is-invalid');
                    }
                });
                phoneField.addEventListener('keypress', function(e) {
                    if (!/^[0-9\s\-\+\(\)\.]$/.test(e.key) && e.key !== 'Backspace' && e.key !== 'Delete' && e.key !== 'Tab') {
                        e.preventDefault();
                    }
                });
            }

            // ==== Step 3: Personal Details ====
            var dobField = form.querySelector('#id_date_of_birth');
            var ageField = form.querySelector('#id_age');
            if (dobField) {
                var calcAge = function() {
                    if (dobField.value) {
                        var dob = new Date(dobField.value);
                        var today = new Date();
                        if (dob < today && dob.getFullYear() > 1900) {
                            dobField.classList.add('is-valid');
                            dobField.classList.remove('is-invalid');
                            if (ageField) {
                                var age = today.getFullYear() - dob.getFullYear();
                                var m = today.getMonth() - dob.getMonth();
                                if (m < 0 || (m === 0 && today.getDate() < dob.getDate())) age--;
                                ageField.value = age >= 0 ? age : 0;
                                ageField.setAttribute('readonly', 'readonly');
                                ageField.style.backgroundColor = '#e9ecef';
                            }
                        } else {
                            dobField.classList.add('is-invalid');
                            dobField.classList.remove('is-valid');
                        }
                    } else {
                        dobField.classList.remove('is-valid', 'is-invalid');
                        if (ageField) ageField.value = '';
                    }
                };
                dobField.addEventListener('change', calcAge);
                dobField.addEventListener('input', calcAge);
            }

            attachValidator('#id_gender', function(v) { return v !== ''; }, { required: true, alsoOnChange: true });
            attachValidator('#id_nationality', function(v) { return v !== ''; }, { required: true, alsoOnChange: true });
            attachValidator('#id_country_of_birth', function() { return true; }, { alsoOnChange: true });
            attachValidator('#id_religion', function() { return true; });

            // ==== Step 4: Passport & Academic ====
            attachValidator('#id_passport_number', function(v) { return v.length > 0; }, { required: true });
            attachPairValidator('#id_passport_number', '#id_confirm_passport_number');
            attachValidator('#id_passport_issue_date', function(v) { return !!v; }, { required: true, alsoOnChange: true });
            attachValidator('#id_passport_expiry_date', function(v) {
                if (!v) return false;
                var expiry = new Date(v);
                var issueVal = form.querySelector('#id_passport_issue_date') ? form.querySelector('#id_passport_issue_date').value : '';
                if (issueVal && new Date(issueVal) >= expiry) return false;
                return expiry > new Date();
            }, { required: true, alsoOnChange: true });
            attachValidator('#id_place_of_issue', function() { return true; });
            attachValidator('#id_highest_education_level', function(v) { return v !== ''; }, { required: true, alsoOnChange: true });
            attachValidator('#id_field_of_study', function(v) { return v.length > 0; }, { required: true });
            attachValidator('#id_graduation_year', function(v) { return v !== ''; }, { required: true, alsoOnChange: true });
            attachValidator('#id_year_graduated', function() { return true; }, { alsoOnChange: true });
            attachValidator('#id_university', function() { return true; }, { alsoOnChange: true });
            attachValidator('#id_secondary_specialization', function() { return true; });
            attachValidator('#id_primary_specialization', function() { return true; });

            // Global listener: refresh stepper state on any field change
            // so the active circle turns green when all required fields are valid
            form.addEventListener('input', refreshStepperState);
            form.addEventListener('change', refreshStepperState);
        }
        
        function submitRegisterForm() {
            if (!validateStep(5)) return;
            
            const originalText = nextBtn.innerHTML;
            nextBtn.disabled = true;
            nextBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Creating account...';
            
            // Hide any previous error messages
            if (errorElement) {
                errorElement.classList.add('d-none');
            }
            
            // Get form data
            const formData = new FormData(form);
            
            // Submit the form via AJAX
            fetch(form.action || window.location.pathname, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': getCSRFToken() || ''
                },
                redirect: 'manual'
            })
            .then((response) => parseJsonSafe(response, 'Register'))
            .then(data => {
                if (data.success) {
                    // Show success toast
                    if (typeof showRegisterToast === 'function') {
                        showRegisterToast(data.message || 'Account created successfully!', 'success', true);
                    } else if (typeof showToast === 'function') {
                        showToast('Success', data.message, 'success');
                    }
                    
                    // Hide the modal
                    const modalInstance = bootstrap.Modal.getInstance(registerModal);
                    modalInstance.hide();
                    
                    // Redirect if specified
                    if (data.redirect) {
                        setTimeout(function() {
                            window.location.href = data.redirect;
                        }, 500);
                    } else {
                        // Reload the page
                        setTimeout(function() {
                            window.location.reload();
                        }, 500);
                    }
                } else {
                    // Show error messages using toast
                    if (typeof showRegisterToast === 'function') {
                        const errorMessage = data.errors || data.message || 'Registration failed. Please check your information.';
                        showRegisterToast(errorMessage, 'error', true);
                    } else if (errorElement) {
                        errorElement.innerHTML = '';
                        
                        // Loop through all errors
                        let errorHtml = '';
                        for (const [field, fieldErrors] of Object.entries(data.errors || {})) {
                            errorHtml += `<strong>${field}:</strong> ${Array.isArray(fieldErrors) ? fieldErrors.join('<br>') : fieldErrors}<br>`;
                        }
                        if (data.message) {
                            errorHtml += `<br><strong>General:</strong> ${data.message}`;
                        }
                        errorElement.innerHTML = errorHtml || 'Registration failed. Please check your information.';
                        errorElement.classList.remove('d-none');
                    }
                    
                    // Reset the button
                    nextBtn.disabled = false;
                    nextBtn.innerHTML = originalText;
                }
            })
            .catch(error => {
                console.error('Error during registration:', error);
                
                // Show error message using toast
                const errorMsg = 'An error occurred. Please try again.';
                if (typeof showRegisterToast === 'function') {
                    showRegisterToast(errorMsg, 'error', true);
                } else if (errorElement) {
                    errorElement.innerHTML = errorMsg;
                    errorElement.classList.remove('d-none');
                }
                
                // Reset the button
                nextBtn.disabled = false;
                nextBtn.innerHTML = originalText;
            });
        }
        
        // Remove the global submit listener for register form to avoid conflicts
        // The submit is now handled manually
    }
}

/**
 * Setup admin registration modal functionality
 */
function setupAdminRegisterModal() {
    const adminRegisterModal = document.getElementById('adminRegisterModal');
    const adminRegisterModalContent = document.getElementById('adminRegisterModalContent');
    
    if (adminRegisterModal) {
        // Load the admin registration form when the modal is shown
        adminRegisterModal.addEventListener('show.bs.modal', function() {
            // Animation classes disabled
            const modalDialog = adminRegisterModal.querySelector('.modal-dialog');
            if (modalDialog) {
                modalDialog.classList.remove('animate-zoom-in');
                modalDialog.classList.remove('animate-zoom-out');
            }
            
            // Only load if not already loaded or if there was an error
            if (!adminRegisterModalContent.querySelector('form') || 
                adminRegisterModalContent.querySelector('.alert-danger')) {
                loadModalContent('/modal/admin-register/', adminRegisterModalContent);
            } else {
                // Animations disabled
                const formElements = adminRegisterModalContent.querySelectorAll('.form-group, .mb-3, .mb-4, .alert, .d-grid');
                formElements.forEach(element => {
                    element.classList.remove('animate-field');
                });
            }
        });
        
        // Reset modal when hidden
        adminRegisterModal.addEventListener('hide.bs.modal', function() {
            // Animations disabled
            const modalDialog = adminRegisterModal.querySelector('.modal-dialog');
            if (modalDialog) {
                modalDialog.classList.remove('animate-zoom-in');
                modalDialog.classList.remove('animate-zoom-out');
            }
        });
        
        // Clean up after animation completes
        adminRegisterModal.addEventListener('hidden.bs.modal', function() {
            // We don't clear the content to avoid flickering on reopening
            // Just clear any error messages
            const errorElement = adminRegisterModalContent.querySelector('.alert-danger');
            if (errorElement) {
                errorElement.style.display = 'none';
            }
            
            // Animation classes disabled
            const modalDialog = adminRegisterModal.querySelector('.modal-dialog');
            if (modalDialog) {
                modalDialog.classList.remove('animate-zoom-out');
                modalDialog.classList.remove('animate-zoom-in');
            }
        });
        
        // Handle form submission via event delegation
        document.addEventListener('submit', function(e) {
            const form = e.target;
            
            // Check if this is the admin register modal form
            if (form.id === 'adminRegisterModalForm') {
                e.preventDefault();
                
                const submitButton = form.querySelector('button[type="submit"]');
                const originalText = submitButton.innerHTML;
                submitButton.disabled = true;
                submitButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Registering...';
                
                // Hide any previous error messages
                const errorElement = document.getElementById('adminRegisterModalErrors');
                if (errorElement) {
                    errorElement.style.display = 'none';
                }
                
                // Get form data
                const formData = new FormData(form);
                
                // Submit the form via AJAX
                fetch(form.action, {
                    method: 'POST',
                    body: formData,
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest',
                        'X-CSRFToken': getCSRFToken() || ''
                    },
                    redirect: 'manual'
                })
                .then((response) => parseJsonSafe(response, 'Admin register'))
                .then(data => {
                    if (data.success) {
                        // Show success toast
                        if (typeof showToast === 'function') {
                            showToast('Success', data.message, 'success');
                        }
                        
                        // Hide the modal
                        const modalInstance = bootstrap.Modal.getInstance(adminRegisterModal);
                        modalInstance.hide();
                        
                        // Redirect if specified
                        if (data.redirect) {
                            setTimeout(function() {
                                window.location.href = data.redirect;
                            }, 500);
                        } else {
                            // Reload the page
                            setTimeout(function() {
                                window.location.reload();
                            }, 500);
                        }
                    } else {
                        // Show error messages
                        if (errorElement) {
                            errorElement.innerHTML = '';
                            
                            // Loop through all errors
                            let errorHtml = '';
                            for (const [field, fieldErrors] of Object.entries(data.errors)) {
                                errorHtml += `<strong>${field}:</strong> ${fieldErrors.join('<br>')}<br>`;
                            }
                            errorElement.innerHTML = errorHtml;
                            errorElement.style.display = 'block';
                        }
                        
                        // Reset the button
                        submitButton.disabled = false;
                        submitButton.innerHTML = originalText;
                    }
                })
                .catch(error => {
                    console.error('Error during admin registration:', error);
                    // Show error message with details when available
                    if (errorElement) {
                        const msg = (typeof error === 'string') ? error : (error && error.message) ? error.message : 'An error occurred. Please try again.';
                        errorElement.innerHTML = msg;
                        errorElement.style.display = 'block';
                    }
                    
                    // Reset the button
                    submitButton.disabled = false;
                    submitButton.innerHTML = originalText;
                });
            }
        });
    }
}

/**
 * Setup switching between login and registration modals
 */
function setupModalSwitching() {
    // Event delegation for switching between modals
    document.addEventListener('click', function(e) {
        // Switch from login to register
        if (e.target && e.target.id === 'switchToRegister') {
            e.preventDefault();
            
            const loginModal = bootstrap.Modal.getInstance(document.getElementById('loginModal'));
            loginModal.hide();
            
            // Wait for the login modal to fully close
            setTimeout(function() {
                const registerModal = new bootstrap.Modal(document.getElementById('registerModal'));
                registerModal.show();
            }, 400);
        }
        
        // Switch from register to login
        if (e.target && e.target.id === 'switchToLogin') {
            e.preventDefault();
            
            const registerModal = bootstrap.Modal.getInstance(document.getElementById('registerModal'));
            registerModal.hide();
            
            // Wait for the register modal to fully close
            setTimeout(function() {
                const loginModal = new bootstrap.Modal(document.getElementById('loginModal'));
                loginModal.show();
            }, 400);
        }
        
        // Open admin registration modal
        if (e.target && (e.target.id === 'openAdminRegister' || 
                         e.target.closest('#openAdminRegister'))) {
            e.preventDefault();
            
            // Close any open modals first
            const loginModal = document.getElementById('loginModal');
            const registerModal = document.getElementById('registerModal');
            
            if (loginModal && bootstrap.Modal.getInstance(loginModal)) {
                bootstrap.Modal.getInstance(loginModal).hide();
            }
            
            if (registerModal && bootstrap.Modal.getInstance(registerModal)) {
                bootstrap.Modal.getInstance(registerModal).hide();
            }
            
            // Wait for modals to close
            setTimeout(function() {
                const adminRegisterModal = new bootstrap.Modal(document.getElementById('adminRegisterModal'));
                adminRegisterModal.show();
            }, 400);
        }
        
        // Switch from admin register to login
        if (e.target && e.target.id === 'switchToLoginFromAdmin') {
            e.preventDefault();
            
            const adminRegisterModal = bootstrap.Modal.getInstance(document.getElementById('adminRegisterModal'));
            adminRegisterModal.hide();
            
            // Wait for the admin register modal to fully close
            setTimeout(function() {
                const loginModal = new bootstrap.Modal(document.getElementById('loginModal'));
                loginModal.show();
            }, 400);
        }
    });
}

/**
 * Load content into a modal via AJAX
 */
function loadModalContent(url, container) {
    // Add a spinner temporarily
    container.innerHTML = `
        <div class="modal-content text-center">
            <div class="modal-header text-white text-center p-3" style="background: #28a745;">
                <h5 class="modal-title w-100">Loading</h5>
                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal" aria-label="Close"></button>
            </div>
            <div class="modal-body p-5">
                <div class="spinner-border text-primary" role="status" style="width: 3rem; height: 3rem;">
                    <span class="visually-hidden">Loading...</span>
                </div>
                <p class="mt-3">Loading form...</p>
            </div>
        </div>
    `;
    
    // Fetch the content
    return fetch(url, {
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => response.text())
    .then(html => {
        // Set the HTML content
        container.innerHTML = html;
        
        // Remove animation classes from all elements
        const animatedElements = container.querySelectorAll('.animate-field, .animate-border, .animate-border-box');
        animatedElements.forEach(element => {
            element.classList.remove('animate-field', 'animate-border', 'animate-border-box');
        });
        
        // Initialize password strength meter if present
        const passwordInput = container.querySelector('#id_password1');
        if (passwordInput) {
            passwordInput.addEventListener('input', function() {
                updatePasswordStrength(this.value);
            });
        }
        
        // Remove all animation properties
        const modalContent = container.querySelector('.modal-content');
        if (modalContent) {
            modalContent.classList.remove('animate-border');
            modalContent.style.animation = 'none';
        }
        
        // Remove border animation
        const borderBox = container.querySelector('.animate-border-box');
        if (borderBox) {
            borderBox.style.animation = 'none';
            borderBox.classList.remove('animate-border-box');
        }
        
        // Remove header animations
        const headers = container.querySelectorAll('.modal-header');
        headers.forEach(header => {
            header.style.backgroundPosition = 'center center';
            header.style.transition = 'none';
            
            // Remove hover event listeners
            header.removeEventListener('mouseenter', null);
            header.removeEventListener('mouseleave', null);
        });
    })
    .catch(error => {
        console.error('Error loading modal content:', error);
        container.innerHTML = `
            <div class="modal-content">
                <div class="modal-header bg-danger text-white">
                    <h5 class="modal-title">Error</h5>
                    <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal" aria-label="Close"></button>
                </div>
                <div class="modal-body">
                    <p>An error occurred while loading the content. Please try again.</p>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                </div>
            </div>
        `;
    });
}

/**
 * Setup username validation for login modal
 */
function setupUsernameValidation() {
    // Add event listener to username input for real-time validation
    document.addEventListener('input', function(e) {
        if (e.target && e.target.id === 'id_username') {
            const usernameInput = e.target;
            const username = usernameInput.value.trim();

            // Clear previous validation state
            usernameInput.classList.remove('is-valid', 'is-invalid');
            usernameInput.dataset.validated = 'false';

            // Only validate if username is not empty and has minimum length
            if (username.length >= 3) {
                validateUsername(username, usernameInput);
            }
        }
    });

    // Add blur event to validate when user leaves the field
    document.addEventListener('blur', function(e) {
        if (e.target && e.target.id === 'id_username') {
            const usernameInput = e.target;
            const username = usernameInput.value.trim();

            if (username && username.length >= 3) {
                validateUsername(username, usernameInput);
            }
        }
    });
}

/**
 * Validate username existence via AJAX
 */
function validateUsername(username, inputElement) {
    // Show loading state
    inputElement.classList.add('is-validating');
    inputElement.dataset.validated = 'pending';

    fetch('/api/check-username/', {
        method: 'GET',
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'Content-Type': 'application/x-www-form-urlencoded'
        },
        credentials: 'same-origin'
    })
    .then(response => response.json())
    .then(data => {
        inputElement.classList.remove('is-validating');

        if (data.available) {
            // Username is available (not registered) - show error
            inputElement.classList.add('is-invalid');
            inputElement.classList.remove('is-valid');
            inputElement.dataset.validated = 'false';

            // Add custom error message
            showUsernameError(inputElement, 'This username is not registered. Please check your username or register first.');
        } else {
            // Username exists - show success
            inputElement.classList.add('is-valid');
            inputElement.classList.remove('is-invalid');
            inputElement.dataset.validated = 'true';

            // Clear any error message
            clearUsernameError(inputElement);
        }
    })
    .catch(error => {
        console.error('Error validating username:', error);
        inputElement.classList.remove('is-validating');
        inputElement.classList.add('is-invalid');
        inputElement.dataset.validated = 'false';
        showUsernameError(inputElement, 'Unable to verify username. Please try again.');
    });
}

/**
 * Show username validation error
 */
function showUsernameError(inputElement, message) {
    // Remove existing error message if any
    clearUsernameError(inputElement);

    // Create error message element
    const errorDiv = document.createElement('div');
    errorDiv.className = 'invalid-feedback d-block';
    errorDiv.textContent = message;

    // Insert after the input group
    const inputGroup = inputElement.closest('.input-group');
    if (inputGroup) {
        inputGroup.parentNode.insertBefore(errorDiv, inputGroup.nextSibling);
    }
}

/**
 * Clear username validation error
 */
function clearUsernameError(inputElement) {
    const inputGroup = inputElement.closest('.input-group');
    if (inputGroup) {
        const errorElement = inputGroup.parentNode.querySelector('.invalid-feedback');
        if (errorElement) {
            errorElement.remove();
        }
    }
}

/**
 * Show login error message
 */
function showLoginError(message) {
    const errorElement = document.getElementById('loginModalErrors');
    if (errorElement) {
        errorElement.innerHTML = message;
        errorElement.style.display = 'block';
    }
}

/**
 * Update password strength meter
 */
function updatePasswordStrength(password) {
    const passwordStrengthMeter = document.getElementById('passwordStrengthMeter');
    const passwordStrengthLabel = document.getElementById('passwordStrengthLabel');

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
