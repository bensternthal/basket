import os

if os.getenv('TRAVIS', False):
    from settings.travis import *
else:
    try:
        from settings.local import *
    except ImportError:
        try:
            from settings.base import *
        except ImportError:
            import sys
            sys.stderr.write(
                "Error: Tried importing 'settings.local' and 'settings.base' "
                "but neither could be found (or they're throwing an "
                "ImportError). Please fix and try again.")
            raise


CACHES['bad_message_ids'] = {
    'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    'TIMEOUT': 12 * 60 * 60,  # 12 hours
}
