from django.http import JsonResponse
from django.shortcuts import redirect
from django.contrib.auth.decorators import user_passes_test

def ajax_login_required(function=None, login_url=None):
    """
    Custom decorator to handle unauthenticated AJAX requests by returning JSON
    and regular requests by redirecting to login modal.
    """
    def decorated(view_func):
        def wrapper(request, *args, **kwargs):
            if request.user.is_authenticated:
                return view_func(request, *args, **kwargs)
            
            # For AJAX requests, return JSON that indicates login required
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'login_required': True,
                    'message': 'Please log in to perform this action'
                })
            
            # For regular requests - redirect to the homepage with a hash to trigger login modal
            return redirect('/#login')
        
        return wrapper
    
    if function:
        return decorated(function)
    return decorated 