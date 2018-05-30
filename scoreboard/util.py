"""Little helper tidbits."""

import time
from typing import Callable


def timer(func: Callable) -> Callable:
    """Decorator to wrap a function and print how long it took."""

    def wrapper(*arg, **kw):  # type: ignore
        """Call a function, print the duration."""
        t1 = time.time()
        res = func(*arg, **kw)
        print(
            "{name} took {dur:.4} secs".format(name=func.__name__, dur=time.time() - t1)
        )
        return res

    return wrapper


def retry(max_tries: int, wait: int = 0) -> Callable:
    """Decorator to add basic retry functionality."""

    def retry_decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            """Call a function, retry if it fails, waiting some amount of time.

            If we hit the retry limit and the function still fails, pass up the
            exception.
            """
            tries = 0
            while True:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    tries += 1
                    if tries >= max_tries:
                        raise
                    else:
                        print(
                            "%s failed (%s), waiting %d secs and retrying"
                            % (func.__name__, e, wait)
                        )
                        time.sleep(wait)

        return wrapper

    return retry_decorator
