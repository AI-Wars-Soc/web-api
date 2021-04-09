import codecs
import pickle
import time
from threading import Lock

import redis

redis_connection = redis.Redis(host='redis', port=6379)
_id_count = 0
_id_mutex = Lock()


def _get_new_id():
    global _id_count, _id_mutex
    _id_mutex.acquire()
    func_id = _id_count
    _id_count += 1
    _id_mutex.release()
    return func_id


def cached(ttl=5*60):
    def decorator(f):
        mutex = Lock()
        func_id = _get_new_id()

        def try_get(id_str):
            cached_entry = redis_connection.get(id_str)

            if cached_entry is not None:
                cached_entry = pickle.loads(cached_entry)
                cached_time = cached_entry["time"]
                cached_value = cached_entry["value"]

                # Check cached value is valid
                now = time.time()
                if (cached_time + ttl) > now:  # Timeout not elapsed
                    return cached_value

            return None

        def decorated(*args, **kwargs):
            id_str = f"cached-function-value-{func_id}"
            if len(args) != 0:
                id_str += codecs.encode(pickle.dumps(args), "base64").decode()
            if len(kwargs) != 0:
                id_str += codecs.encode(pickle.dumps(kwargs), "base64").decode()

            mutex.acquire()
            try:
                value = try_get(id_str)
                if value is not None:
                    return value

                # Calculate the value
                value = f(*args, **kwargs)

                # Set
                now = time.time()
                entry = {"time": now, "value": value}
                redis_connection.set(id_str, pickle.dumps(entry))
                redis_connection.expire(id_str, ttl)

                # Return
                return value
            except pickle.UnpicklingError:
                redis_connection.delete(id_str)
                return f(*args, **kwargs)  # Calculate just this once
            finally:
                mutex.release()
        return decorated
    return decorator
