import pickle
import time
from threading import Lock

import redis

redis_connection = redis.Redis(host='redis', port=6379)


def cached(ttl=5*60):
    def decorator(f):
        mutex = Lock()

        def decorated():
            id_str = "cached-function-value-" + f.__name__

            mutex.acquire()
            try:
                cached_entry = redis_connection.get(id_str)

                if cached_entry is not None:
                    cached_entry = pickle.loads(cached_entry)
                    cached_time = cached_entry["time"]
                    cached_value = cached_entry["value"]

                    # Check cached value is valid
                    now = time.time()
                    if (cached_time + ttl) > now:  # Timeout not elapsed
                        return cached_value

                # Calculate the value
                value = f()

                # Set
                now = time.time()
                entry = {"time": now, "value": value}
                redis_connection.set(id_str, pickle.dumps(entry))

                # Return
                return value
            except pickle.UnpicklingError:
                redis_connection.delete(id_str)
                return f()  # Calculate just this once
            finally:
                mutex.release()
        return decorated
    return decorator
