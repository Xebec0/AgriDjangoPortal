/**
 * AJAX Features for AgriDjangoPortal
 * Provides asynchronous functionality for better user experience
 */

document.addEventListener('DOMContentLoaded', function() {
    setupUsernameAvailabilityCheck();
    setupAjaxFormSubmissions();
    setupApplicationStatusTracking();
    setupNotificationRefresh();
});

/**
 * Setup real-time username availability checking
 * ONLY on the registration page
 */
function setupUsernameAvailabilityCheck() {
    // Only apply this to the registration form, not the login form
    const registerForm = document.getElementById('registerForm');
    
    // If we're not on the registration page, don't set up username checking
    if (!registerForm) {
        return;
    }
    
    const usernameField = document.getElementById('id_username');
    
    if (usernameField) {
        // Create feedback element if it doesn't exist
        let feedbackElement = document.getElementById('username-feedback');
        if (!feedbackElement) {
            feedbackElement = document.createElement('div');
            feedbackElement.id = 'username-feedback';
            feedbackElement.className = 'mt-1 small';
            usernameField.parentNode.appendChild(feedbackElement);
        }
        
        // Add debounced event listener
        let debounceTimer;
        usernameField.addEventListener('input', function() {
            const username = this.value.trim();
            
            // Clear previous feedback while typing
            feedbackElement.innerHTML = '';
            feedbackElement.className = 'mt-1 small';
            
            // Clear previous timer
            clearTimeout(debounceTimer);
            
            // Only check if username is at least 3 characters
            if (username.length >= 3) {
                feedbackElement.innerHTML = '<span class="text-muted"><i class="fas fa-spinner fa-spin"></i> Checking availability...</span>';
                
                // Set new timer to prevent too many requests
                debounceTimer = setTimeout(function() {
                    checkUsernameAvailability(username, feedbackElement);
                }, 500);
            }
        });
    }
}

/**
 * Check if a username is available via AJAX
 */
function checkUsernameAvailability(username, feedbackElement) {
    fetch(`/api/check-username/?username=${encodeURIComponent(username)}`)
        .then(response => response.json())
        .then(data => {
            if (data.available) {
                feedbackElement.innerHTML = '<span class="text-success"><i class="fas fa-check-circle"></i> ' + data.message + '</span>';
                feedbackElement.className = 'mt-1 small valid-feedback d-block';
            } else {
                feedbackElement.innerHTML = '<span class="text-danger"><i class="fas fa-times-circle"></i> ' + data.message + '</span>';
                feedbackElement.className = 'mt-1 small invalid-feedback d-block';
            }
        })
        .catch(error => {
            console.error('Error checking username:', error);
            feedbackElement.innerHTML = '<span class="text-danger">Error checking username availability</span>';
        });
}

/**
 * Setup AJAX form submissions for login and registration forms
 */
function setupAjaxFormSubmissions() {
    // Login form
    const loginForm = document.querySelector('form.login-form');
    if (loginForm) {
        loginForm.addEventListener('submit', function(e) {
            e.preventDefault();
            submitFormWithAjax(this, '/api/ajax-login/');
        });
    }
    
    // Registration form
    const registerForm = document.querySelector('form.register-form');
    if (registerForm) {
        registerForm.addEventListener('submit', function(e) {
            e.preventDefault();
            submitFormWithAjax(this, '/api/ajax-register/');
        });
    }
}

/**
 * Generic function to submit a form with AJAX
 */
function submitFormWithAjax(form, url) {
    // Show loading state
    const submitButton = form.querySelector('button[type="submit"]');
    const originalText = submitButton.innerHTML;
    submitButton.disabled = true;
    submitButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';
    
    // Clear previous error messages
    const errorContainer = document.getElementById('form-errors');
    if (errorContainer) {
        errorContainer.innerHTML = '';
        errorContainer.style.display = 'none';
    }
    
    // Get CSRF token
    const csrfToken = getCookie('csrftoken');
    
    // Submit the form
    fetch(url, {
        method: 'POST',
        body: new FormData(form),
        headers: {
            'X-CSRFToken': csrfToken
        },
        credentials: 'same-origin'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Show success message
            showToast('Success', data.message, 'success');
            
            // Redirect if specified
            if (data.redirect) {
                setTimeout(function() {
                    window.location.href = data.redirect;
                }, 1500);
            }
        } else {
            // Show error messages
            displayFormErrors(form, data.errors);
            
            // Reset button
            submitButton.disabled = false;
            submitButton.innerHTML = originalText;
        }
    })
    .catch(error => {
        console.error('Error submitting form:', error);
        showToast('Error', 'An error occurred. Please try again.', 'danger');
        
        // Reset button
        submitButton.disabled = false;
        submitButton.innerHTML = originalText;
    });
}

/**
 * Display form errors returned from the server
 */
function displayFormErrors(form, errors) {
    // Create or get error container
    let errorContainer = document.getElementById('form-errors');
    if (!errorContainer) {
        errorContainer = document.createElement('div');
        errorContainer.id = 'form-errors';
        errorContainer.className = 'alert alert-danger';
        form.prepend(errorContainer);
    }
    
    let errorList = document.createElement('ul');
    errorList.className = 'mb-0';
    
    // Display non-field errors
    if (errors.__all__) {
        errors.__all__.forEach(error => {
            let li = document.createElement('li');
            li.textContent = error;
            errorList.appendChild(li);
        });
    }
    
    // Display field-specific errors
    for (const [field, fieldErrors] of Object.entries(errors)) {
        if (field !== '__all__') {
            // Find the field and mark it as invalid
            const fieldElement = form.querySelector(`[name="${field}"]`);
            if (fieldElement) {
                fieldElement.classList.add('is-invalid');
                
                // Display error message
                const feedbackElement = fieldElement.parentNode.querySelector('.invalid-feedback');
                if (feedbackElement) {
                    feedbackElement.innerHTML = fieldErrors.join('<br>');
                    feedbackElement.style.display = 'block';
                }
            }
            
            // Add to the error list
            fieldErrors.forEach(error => {
                let li = document.createElement('li');
                li.textContent = `${field}: ${error}`;
                errorList.appendChild(li);
            });
        }
    }
    
    if (errorList.children.length > 0) {
        errorContainer.innerHTML = '';
        errorContainer.appendChild(errorList);
        errorContainer.style.display = 'block';
        
        // Scroll to errors
        errorContainer.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
}

/**
 * Setup live application status tracking for dashboard
 */
function setupApplicationStatusTracking() {
    const applicationContainer = document.getElementById('user-applications');
    if (applicationContainer) {
        fetchAndUpdateApplications(applicationContainer);
        
        // Refresh every 30 seconds
        setInterval(function() {
            fetchAndUpdateApplications(applicationContainer);
        }, 30000);
    }
}

/**
 * Fetch and update application status
 */
function fetchAndUpdateApplications(container) {
    fetch('/api/user-applications/')
        .then(response => response.json())
        .then(data => {
            if (data.success && data.applications.length > 0) {
                updateApplicationsUI(container, data.applications);
            } else if (data.applications.length === 0) {
                container.innerHTML = '<div class="alert alert-info">You have not applied to any programs yet.</div>';
            }
        })
        .catch(error => {
            console.error('Error fetching applications:', error);
        });
}

/**
 * Update the UI with application data
 */
function updateApplicationsUI(container, applications) {
    let html = '<div class="list-group">';
    
    applications.forEach(app => {
        let statusClass = getStatusClass(app.status_code);
        
        html += `
            <div class="list-group-item list-group-item-action">
                <div class="d-flex w-100 justify-content-between">
                    <h5 class="mb-1">${app.program_name}</h5>
                    <span class="badge ${statusClass}">${app.status}</span>
                </div>
                <p class="mb-1">Applied on: ${app.application_date}</p>
                <small class="text-muted">Last updated: ${app.last_updated}</small>
                <div class="mt-2">
                    <a href="/registrations/${app.id}/" class="btn btn-sm btn-outline-primary">View Details</a>
                    ${app.status_code === 'pending' ? `<a href="/registrations/${app.id}/cancel/" class="btn btn-sm btn-outline-danger">Cancel Application</a>` : ''}
                </div>
            </div>
        `;
    });
    
    html += '</div>';
    container.innerHTML = html;
}

/**
 * Get Bootstrap class based on status code
 */
function getStatusClass(statusCode) {
    switch(statusCode) {
        case 'approved':
            return 'bg-success';
        case 'pending':
            return 'bg-warning text-dark';
        case 'rejected':
            return 'bg-danger';
        case 'cancelled':
            return 'bg-secondary';
        default:
            return 'bg-info';
    }
}

/**
 * Setup automatic notification refresh
 */
function setupNotificationRefresh() {
    const notificationDropdown = document.getElementById('notificationDropdown');
    if (notificationDropdown) {
        // Refresh notifications every 60 seconds
        setInterval(function() {
            refreshNotifications();
        }, 60000);
    }
}

/**
 * Refresh notifications via AJAX
 */
function refreshNotifications() {
    const notificationList = document.getElementById('notificationList');
    const notificationBadge = document.querySelector('#notificationDropdown .badge');
    
    if (notificationList) {
        fetch('/api/notifications/')
            .then(response => response.json())
            .then(data => {
                // Update notification count badge
                if (data.unread_count > 0) {
                    notificationBadge.textContent = data.unread_count;
                    notificationBadge.style.display = 'inline-block';
                } else {
                    notificationBadge.style.display = 'none';
                }
                
                // Only update the dropdown content if it's not currently open
                if (!notificationDropdown.classList.contains('show')) {
                    // We don't update the content here to avoid disrupting user interaction
                    // It will update when they click the dropdown
                }
            })
            .catch(error => {
                console.error('Error refreshing notifications:', error);
            });
    }
}

/**
 * Show a toast notification
 */
function showToast(title, message, type) {
    // Create toast container if it doesn't exist
    let toastContainer = document.getElementById('toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.id = 'toast-container';
        toastContainer.className = 'toast-container position-fixed bottom-0 end-0 p-3';
        document.body.appendChild(toastContainer);
    }
    
    // Create the toast
    const toastId = 'toast-' + Date.now();
    const toast = document.createElement('div');
    toast.className = 'toast';
    toast.id = toastId;
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', 'assertive');
    toast.setAttribute('aria-atomic', 'true');
    
    toast.innerHTML = `
        <div class="toast-header bg-${type} text-white">
            <strong class="me-auto">${title}</strong>
            <small>Just now</small>
            <button type="button" class="btn-close btn-close-white" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
        <div class="toast-body">
            ${message}
        </div>
    `;
    
    toastContainer.appendChild(toast);
    
    // Show the toast
    const bsToast = new bootstrap.Toast(toast);
    bsToast.show();
    
    // Remove toast after it's hidden
    toast.addEventListener('hidden.bs.toast', function() {
        toast.remove();
    });
}

/**
 * Get CSRF cookie for AJAX requests
 */
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
