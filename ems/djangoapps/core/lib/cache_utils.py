"""
Utilities related to caching.
"""

import collections
import functools
import itertools
import threading
import zlib
import pickle

import wrapt
from django.db.models.signals import post_save, post_delete
from django.utils.encoding import force_str
from django.core.cache import cache


def request_cached(namespace=None, arg_map_function=None, request_cache_getter=None):
    """
    A decorator for per-request caching using a dictionary on the request object.
    If no request context is available, it behaves as a no-op.

    Args:
        namespace (str): Optional namespace for the request cache.
        arg_map_function (function): Optional function to map args to strings for key generation.
        request_cache_getter (function): Optional function to get a per-request cache dictionary.

    Returns:
        Wrapped function with request-level caching.
    """
    @wrapt.decorator
    def decorator(wrapped, instance, args, kwargs):
        if request_cache_getter:
            request_cache = request_cache_getter(
                args if instance is None else (instance,) + args, kwargs
            )
        else:
            request_cache = _get_request_cache(namespace)

        if request_cache is not None:
            cache_key = _func_call_cache_key(wrapped, arg_map_function, *args, **kwargs)
            if cache_key in request_cache:
                return request_cache[cache_key]

        result = wrapped(*args, **kwargs)

        if request_cache is not None:
            request_cache[cache_key] = result

        return result

    return decorator


def _get_request_cache(namespace):
    """
    Get a per-request cache stored in thread-local storage.
    Uses Django middleware's request object or global fallback.

    Args:
        namespace (str): Optional namespace for cache separation.

    Returns:
        dict: The per-request cache dictionary.
    """
    thread_local = threading.local()
    if not hasattr(thread_local, "request_cache"):
        thread_local.request_cache = {}
    if namespace:
        if namespace not in thread_local.request_cache:
            thread_local.request_cache[namespace] = {}
        return thread_local.request_cache[namespace]
    return thread_local.request_cache


def _func_call_cache_key(func, arg_map_function, *args, **kwargs):
    """
    Generate a cache key string based on function and its arguments.

    Args:
        func (callable): The target function.
        arg_map_function (callable): Function to convert arguments to strings.
        *args: Positional arguments.
        **kwargs: Keyword arguments.

    Returns:
        str: The cache key.
    """
    arg_map_function = arg_map_function or force_str
    converted_args = list(map(arg_map_function, args))
    converted_kwargs = list(map(arg_map_function, _sorted_kwargs_list(kwargs)))
    cache_keys = [func.__module__, func.__name__] + converted_args + converted_kwargs
    return '.'.join(cache_keys)


def _sorted_kwargs_list(kwargs):
    """
    Sort kwargs by key and flatten into a list.

    Args:
        kwargs (dict): Keyword arguments.

    Returns:
        list: Flattened list of sorted key-value pairs.
    """
    return list(itertools.chain(*sorted(kwargs.items())))


class process_cached:  # pylint: disable=invalid-name
    """
    Caches the result of a function call for the life of the process.
    WARNING: Only use for expensive data that does not change.
    """
    def __init__(self, func):
        self.func = func
        self.cache = {}

    def __call__(self, *args):
        if not isinstance(args, collections.abc.Hashable):
            return self.func(*args)
        if args in self.cache:
            return self.cache[args]
        value = self.func(*args)
        self.cache[args] = value
        return value

    def __repr__(self):
        return self.func.__doc__

    def __get__(self, obj, objtype):
        partial = functools.partial(self.__call__, obj)
        partial.cache = self.cache
        return partial


class CacheInvalidationManager:
    """
    Decorator that caches no-arg functions and invalidates them when a model changes.
    """
    def __init__(self, namespace=None, model=None, cache_time=86400):
        if model:
            post_save.connect(self.invalidate, sender=model)
            post_delete.connect(self.invalidate, sender=model)
            namespace = f"{model.__module__}.{model.__qualname__}"
        self.namespace = namespace
        self.cache_time = cache_time
        self.keys = set()

    def invalidate(self, **kwargs):  # pylint: disable=unused-argument
        """
        Invalidate all cached keys when model changes.
        """
        for key in self.keys:
            cache.delete(key)

    def __call__(self, func):
        cache_key = f'{self.namespace}.{func.__module__}.{func.__name__}'
        self.keys.add(cache_key)

        @functools.wraps(func)
        def decorator(*args, **_kwargs):  # pylint: disable=unused-argument
            result = cache.get(cache_key)
            if result is not None:
                return result
            result = func()
            cache.set(cache_key, result, self.cache_time)
            return result
        return decorator


def zpickle(data):
    """
    Compress and pickle a data structure.

    Args:
        data (any): Data to serialize.

    Returns:
        bytes: Compressed pickled data.
    """
    return zlib.compress(pickle.dumps(data, protocol=4))


def zunpickle(zdata):
    """
    Uncompress and unpickle a data structure.

    Args:
        zdata (bytes): Compressed pickled data.

    Returns:
        any: The original data structure.
    """
    return pickle.loads(zlib.decompress(zdata), encoding='latin1')


class CacheService:
    """
    Provides get/set interface to a cache backend (e.g., Redis or memory).
    """
    def __init__(self, cache_backend=cache):
        self._cache = cache_backend

    def get(self, key, *args, **kwargs):
        """
        Get a cached value by key.
        """
        return self._cache.get(key, *args, **kwargs)

    def set(self, key, value, *args, **kwargs):
        """
        Set a cached value by key.
        """
        return self._cache.set(key, value, *args, **kwargs)

