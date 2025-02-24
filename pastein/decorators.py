from django.core.cache import cache
from functools import wraps
import json
import hashlib


def pastein_cache_model(timeout=300):  # Default timeout of 5 minutes
    def decorator(func):
        @wraps(func)
        def wrapper(cls, *args, **kwargs):
            # Serialize args to JSON and create a hash
            args_str = json.dumps(args, default=str, sort_keys=True)
            hashed_args = hashlib.md5(args_str.encode()).hexdigest()

            # Create a valid cache key
            cache_key = f'pastein:{func.__name__}:{hashed_args}'
            
            cached_instance = cache.get(cache_key)
            if cached_instance:
                return cached_instance
            
            instance = func(cls, *args, **kwargs)
            if instance:
                cache.set(cache_key, instance, timeout)
            return instance
        return wrapper
    return decorator