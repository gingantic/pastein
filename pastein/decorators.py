from django.core.cache import cache
from functools import wraps

def pastein_cache_model(timeout=300):  # Default timeout of 5 minutes
    def decorator(func):
        @wraps(func)
        def wrapper(cls, *args, **kwargs):
            cache_key = f'pastein:{func.__name__}:{args}'
            print(cache_key)
            cached_instance = cache.get(cache_key)
            if cached_instance:
                return cached_instance
            
            instance = func(cls, *args, **kwargs)
            if instance:
                cache.set(cache_key, instance, timeout)
            return instance
        return wrapper
    return decorator