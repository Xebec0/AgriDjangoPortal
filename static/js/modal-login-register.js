/**
 * Modal Login and Registration functionality
 * Handles AJAX loading of modal content and form submissions
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize the modals
    setupLoginModal();
    setupRegisterModal();
    setupAdminRegisterModal();
    setupModalSwitching();
});

/**
 * Setup the login modal functionality
 */
function setupLoginModal() {
    const loginModal = document.getElementById('loginModal');
    const loginModalContent = document.getElementById('loginModalContent');
    
    if (loginModal) {
        // Load the login form when the modal is shown
        loginModal.addEventListener('show.bs.modal', function() {
            // Add animation class to modal dialog
            const modalDialog = loginModal.querySelector('.modal-dialog');
            if (modalDialog) {
                modalDialog.classList.add('animate-zoom-in');
                modalDialog.classList.remove('animate-zoom-out');
            }
            
            // Only load if not already loaded or if there was an error
            if (!loginModalContent.querySelector('form') || 
                loginModalContent.querySelector('.alert-danger')) {
                loadModalContent('/modal/login/', loginModalContent);
            } else {
                // Apply animations to existing content
                const formElements = loginModalContent.querySelectorAll('.form-group, .mb-3, .mb-4, .alert, .d-grid');
                formElements.forEach(element => {
                    element.classList.add('animate-field');
                });
            }
        });
        
        // Reset and animate modal when hidden
        loginModal.addEventListener('hide.bs.modal', function() {
            // Add zoom out animation
            const modalDialog = loginModal.querySelector('.modal-dialog');
            if (modalDialog) {
                modalDialog.classList.remove('animate-zoom-in');
                modalDialog.classList.add('animate-zoom-out');
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
            
            // Remove animation classes for next time
            const modalDialog = loginModal.querySelector('.modal-dialog');
            if (modalDialog) {
                modalDialog.classList.remove('animate-zoom-out');
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
                
                // Submit the form via AJAX
                fetch(form.action, {
                    method: 'POST',
                    body: formData,
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest'
                    }
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
                            
                            if (data.errors.__all__) {
                                errorElement.innerHTML = data.errors.__all__.join('<br>');
                            } else {
                                // Loop through all errors
                                let errorHtml = '';
                                for (const [field, fieldErrors] of Object.entries(data.errors)) {
                                    errorHtml += fieldErrors.join('<br>') + '<br>';
                                }
                                errorElement.innerHTML = errorHtml;
                            }
                            
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
 * Setup the registration modal functionality
 */
function setupRegisterModal() {
    const registerModal = document.getElementById('registerModal');
    const registerModalContent = document.getElementById('registerModalContent');
    
    if (registerModal) {
        // Load the registration form when the modal is shown
        registerModal.addEventListener('show.bs.modal', function() {
            // Add animation class to modal dialog
            const modalDialog = registerModal.querySelector('.modal-dialog');
            if (modalDialog) {
                modalDialog.classList.add('animate-zoom-in');
                modalDialog.classList.remove('animate-zoom-out');
            }
            
            // Only load if not already loaded or if there was an error
            if (!registerModalContent.querySelector('form') || 
                registerModalContent.querySelector('.alert-danger')) {
                loadModalContent('/modal/register/', registerModalContent);
            } else {
                // Apply animations to existing content
                const formElements = registerModalContent.querySelectorAll('.form-group, .mb-3, .mb-4, .alert, .d-grid');
                formElements.forEach(element => {
                    element.classList.add('animate-field');
                });
            }
        });
        
        // Reset and animate modal when hidden
        registerModal.addEventListener('hide.bs.modal', function() {
            // Add zoom out animation
            const modalDialog = registerModal.querySelector('.modal-dialog');
            if (modalDialog) {
                modalDialog.classList.remove('animate-zoom-in');
                modalDialog.classList.add('animate-zoom-out');
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
            
            // Remove animation classes for next time
            const modalDialog = registerModal.querySelector('.modal-dialog');
            if (modalDialog) {
                modalDialog.classList.remove('animate-zoom-out');
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
                        'X-Requested-With': 'XMLHttpRequest'
                    }
                })
                .then(response => response.json())
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
            // Add animation class to modal dialog
            const modalDialog = adminRegisterModal.querySelector('.modal-dialog');
            if (modalDialog) {
                modalDialog.classList.add('animate-zoom-in');
                modalDialog.classList.remove('animate-zoom-out');
            }
            
            // Only load if not already loaded or if there was an error
            if (!adminRegisterModalContent.querySelector('form') || 
                adminRegisterModalContent.querySelector('.alert-danger')) {
                loadModalContent('/modal/admin-register/', adminRegisterModalContent);
            } else {
                // Apply animations to existing content
                const formElements = adminRegisterModalContent.querySelectorAll('.form-group, .mb-3, .mb-4, .alert, .d-grid');
                formElements.forEach(element => {
                    element.classList.add('animate-field');
                });
            }
        });
        
        // Reset and animate modal when hidden
        adminRegisterModal.addEventListener('hide.bs.modal', function() {
            // Add zoom out animation
            const modalDialog = adminRegisterModal.querySelector('.modal-dialog');
            if (modalDialog) {
                modalDialog.classList.remove('animate-zoom-in');
                modalDialog.classList.add('animate-zoom-out');
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
            
            // Remove animation classes for next time
            const modalDialog = adminRegisterModal.querySelector('.modal-dialog');
            if (modalDialog) {
                modalDialog.classList.remove('animate-zoom-out');
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
                        'X-Requested-With': 'XMLHttpRequest'
                    }
                })
                .then(response => response.json())
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
 * Load modal content via AJAX with animations
 */
function loadModalContent(url, container) {
    fetch(url)
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.text();
        })
        .then(html => {
            // Add animation class to the parent modal dialog
            const modalDialog = container.closest('.modal-dialog');
            if (modalDialog) {
                modalDialog.classList.add('animate-zoom-in');
            }
            
            container.innerHTML = html;
            
            // Initialize password strength meter if present
            const passwordInput = container.querySelector('#id_password1');
            if (passwordInput) {
                passwordInput.addEventListener('input', function() {
                    updatePasswordStrength(this.value);
                });
            }
            
            // Apply staggered animations to form elements
            const formElements = container.querySelectorAll('.form-group, .mb-3, .mb-4, .alert, .d-grid');
            formElements.forEach(element => {
                element.classList.add('animate-field');
            });
            
            // Apply border animation
            const modalContent = container.querySelector('.modal-content');
            if (modalContent) {
                modalContent.classList.add('animate-border');
            }
            
            // Apply border animation to the border box
            const borderBox = container.querySelector('.animate-border-box');
            if (borderBox) {
                borderBox.style.animation = 'borderPulse 1.8s infinite';
            }
            
            // Animate headers with gradient shift on hover
            const headers = container.querySelectorAll('.modal-header');
            headers.forEach(header => {
                header.addEventListener('mouseenter', function() {
                    this.style.backgroundPosition = 'right center';
                });
                
                header.addEventListener('mouseleave', function() {
                    this.style.backgroundPosition = 'left center';
                });
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
                        <p>Failed to load content. Please try again later.</p>
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
