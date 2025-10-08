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
        
        // Handle form submission via event delegation
        document.addEventListener('submit', function(e) {
            const form = e.target;
            
            // Check if this is the login modal form
            if (form.id === 'loginModalForm') {
                e.preventDefault();
                
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
                loadModalContent('/modal/register/', registerModalContent);
            } else {
                // Animations disabled
                const formElements = registerModalContent.querySelectorAll('.form-group, .mb-3, .mb-4, .alert, .d-grid');
                formElements.forEach(element => {
                    element.classList.remove('animate-field');
                });
            }
        });
        
        // Reset modal when hidden
        registerModal.addEventListener('hide.bs.modal', function() {
            // Animations disabled
            const modalDialog = registerModal.querySelector('.modal-dialog');
            if (modalDialog) {
                modalDialog.classList.remove('animate-zoom-in');
                modalDialog.classList.remove('animate-zoom-out');
            }
        });
        
        // Clean up after animation completes
        registerModal.addEventListener('hidden.bs.modal', function() {
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
        
        // Handle form submission via event delegation
        document.addEventListener('submit', function(e) {
            const form = e.target;
            
            // Check if this is the register modal form
            if (form.id === 'registerModalForm') {
                e.preventDefault();
                
                const submitButton = form.querySelector('button[type="submit"]');
                const originalText = submitButton.innerHTML;
                submitButton.disabled = true;
                submitButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Creating account...';
                
                // Hide any previous error messages
                const errorElement = document.getElementById('registerModalErrors');
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
                .then((response) => parseJsonSafe(response, 'Register'))
                .then(data => {
                    if (data.success) {
                        // Show success toast
                        if (typeof showToast === 'function') {
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
                    console.error('Error during registration:', error);
                    
                    // Show error message
                    if (errorElement) {
                        errorElement.innerHTML = 'An error occurred. Please try again.';
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
    fetch(url, {
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
