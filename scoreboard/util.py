"""Little helper tidbits."""

import time


def timer(func):
    """Decorator to wrap a function and print how long it took."""

    def wrapper(*arg, **kw):
        """Call a function, print the duration."""
        t1 = time.time()
        res = func(*arg, **kw)
        print("{name} took {dur:.4} secs".format(
            name=func.__name__, dur=time.time() - t1))
        return res

    return wrapper
