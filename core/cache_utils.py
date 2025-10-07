"""
Cache utilities for AgroStudies system
Provides smart caching strategies and cache invalidation
"""

from django.core.cache import cache
from django.conf import settings
from functools import wraps
import hashlib
import json


def get_cache_timeout(cache_type='default'):
    """Get cache timeout from settings"""
    return getattr(settings, 'CACHE_TTL', {}).get(cache_type, 300)


def make_cache_key(*args, **kwargs):
    """Generate a consistent cache key from arguments"""
    key_data = list(args) + [f"{k}={v}" for k, v in sorted(kwargs.items())]
    key_string = ":".join(str(k) for k in key_data)
    return hashlib.md5(key_string.encode()).hexdigest()


def cache_view_result(cache_type='default', timeout=None, key_prefix='view'):
    """
    Decorator to cache view results
    Usage: @cache_view_result('programs', timeout=600)
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # Skip caching for authenticated users with personalized data
            if request.user.is_authenticated and not request.user.is_staff:
                return view_func(request, *args, **kwargs)
            
            # Create cache key
            cache_key = f"{key_prefix}:{make_cache_key(request.path, request.GET.urlencode())}"
            
            # Try to get from cache
            cached_result = cache.get(cache_key)
            if cached_result:
                return cached_result
            
            # Execute view and cache result
            result = view_func(request, *args, **kwargs)
            cache_timeout = timeout or get_cache_timeout(cache_type)
            cache.set(cache_key, result, timeout=cache_timeout)
            
            return result
        return wrapper
    return decorator


def invalidate_program_cache():
    """Invalidate all program-related cache entries"""
    cache_patterns = [
        'programs_list:*',
        'program_detail:*',
        'program_stats:*'
    ]
    
    # Note: Django-redis supports pattern deletion
    try:
        from django_redis import get_redis_connection
        con = get_redis_connection("default")
        for pattern in cache_patterns:
            keys = con.keys(f"{settings.CACHES['default']['KEY_PREFIX']}:*:{pattern}")
            if keys:
                con.delete(*keys)
    except ImportError:
        # Fallback: delete known keys (less efficient)
        pass


def invalidate_candidate_cache():
    """Invalidate all candidate-related cache entries"""
    cache_patterns = [
        'candidate_list:*',
        'candidate_detail:*',
        'candidate_stats:*'
    ]
    
    try:
        from django_redis import get_redis_connection
        con = get_redis_connection("default")
        for pattern in cache_patterns:
            keys = con.keys(f"{settings.CACHES['default']['KEY_PREFIX']}:*:{pattern}")
            if keys:
                con.delete(*keys)
    except ImportError:
        pass


def get_or_set_stats(cache_key, stats_function, timeout=None):
    """
    Get statistics from cache or compute and cache them
    
    Args:
        cache_key: Cache key for the stats
        stats_function: Function that computes the stats
        timeout: Cache timeout (defaults to stats timeout)
    """
    cached_stats = cache.get(cache_key)
    if cached_stats is not None:
        return cached_stats
    
    # Compute stats
    stats = stats_function()
    
    # Cache for 15 minutes by default
    cache_timeout = timeout or get_cache_timeout('default')
    cache.set(cache_key, stats, timeout=cache_timeout)
    
    return stats


def warm_cache():
    """
    Warm up the cache with frequently accessed data
    Should be called after deployments or cache flushes
    """
    from .models import AgricultureProgram, Candidate
    
    # Warm up program list cache
    programs = list(AgricultureProgram.objects.select_related().all().order_by('-start_date')[:20])
    cache.set('programs_list:all', programs, timeout=get_cache_timeout('programs'))
    
    # Warm up basic stats
    stats = {
        'total_programs': AgricultureProgram.objects.count(),
        'total_candidates': Candidate.objects.count(),
        'active_programs': AgricultureProgram.objects.filter(start_date__gte=timezone.now().date()).count(),
    }
    cache.set('system_stats', stats, timeout=get_cache_timeout('default'))


# Cache decorators for models
def cache_model_method(timeout=300):
    """Cache expensive model methods"""
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            cache_key = f"model:{self.__class__.__name__}:{self.pk}:{func.__name__}:{make_cache_key(*args, **kwargs)}"
            
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            result = func(self, *args, **kwargs)
            cache.set(cache_key, result, timeout=timeout)
            return result
        return wrapper
    return decorator


def smart_cache_key(request, *args, **kwargs):
    """
    Generate smart cache keys based on user type and request parameters
    """
    key_parts = []
    
    # Add user type
    if request.user.is_authenticated:
        if request.user.is_staff:
            key_parts.append('staff')
        else:
            key_parts.append('user')
    else:
        key_parts.append('guest')
    
    # Add request parameters
    key_parts.extend(args)
    key_parts.extend([f"{k}={v}" for k, v in sorted(kwargs.items())])
    
    # Add GET parameters
    if request.GET:
        key_parts.append(request.GET.urlencode())
    
    return ':'.join(str(part) for part in key_parts)
