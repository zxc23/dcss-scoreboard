import time


def timer(func):
    def wrapper(*arg, **kw):
        t1 = time.time()
        res = func(*arg, **kw)
        print("{name} took {dur:.4} secs".format(
            name=func.__name__, dur=time.time() - t1))
        return res

    return wrapper
