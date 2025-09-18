"""
Utility classes and functions for various operations in the application.
"""

import threading
import hashlib
from urllib.parse import urlparse


class ThreadSafeDict(dict):
    """
    A thread-safe dictionary implementation that allows for concurrent access
    without the need for external locks. The performance of this class may be
    lower than a builtin dict in single-threaded scenarios due to the overhead
    of acquiring and releasing locks.

    The implementation is NOT async aware, and never use `await` within a RLock.
    Meanwhile, using it in an async context will block the event loop temporarily,
    typically microseconds, but it is important to be aware of this behavior, and
    understand that blocking the event loop can lead to performance issues or, in
    extreme cases, deadlocks if not managed carefully.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._lock = threading.RLock()

    def __getitem__(self, key):
        with self._lock:
            return super().__getitem__(key)

    def __setitem__(self, key, value):
        with self._lock:
            super().__setitem__(key, value)

    def __delitem__(self, key):
        with self._lock:
            super().__delitem__(key)

    def __contains__(self, key):
        with self._lock:
            return super().__contains__(key)

    def __len__(self):
        with self._lock:
            return super().__len__()

    def __iter__(self):
        """
        Using a copied list to avoid mutation issues during iteration.
        """

        with self._lock:
            return iter(list(super().__iter__()))

    @property
    def lock(self):
        """
        Getter to access the internal lock of the dictionary. This can be useful
        if you need to perform multiple operations atomically.
        :return:
        """
        return self._lock

    def get(self, key, default=None):
        with self._lock:
            return super().get(key, default)

    def items(self):
        with self._lock:
            return list(super().items())

    def keys(self):
        with self._lock:
            return list(super().keys())

    def values(self):
        with self._lock:
            return list(super().values())

    def update(self, *args, **kwargs):
        with self._lock:
            super().update(*args, **kwargs)

    def clear(self):
        with self._lock:
            super().clear()

    def copy(self):
        with self._lock:
            return super().copy()

    def pop(self, key, default=None):
        with self._lock:
            return super().pop(key, default)


class ThreadSafeList(list):
    """
    A thread-safe list implementation that protects all operations with an RLock.
    Not async-aware. Avoid using `await` inside any operation protected by the lock.
    """

    def __init__(self, *args):
        super().__init__(*args)
        self._lock = threading.RLock()

    def __getitem__(self, index):
        with self._lock:
            return super().__getitem__(index)

    def __setitem__(self, index, value):
        with self._lock:
            super().__setitem__(index, value)

    def __delitem__(self, index):
        with self._lock:
            super().__delitem__(index)

    def __len__(self):
        with self._lock:
            return super().__len__()

    def __iter__(self):
        with self._lock:
            return iter(list(super().__iter__()))

    def __contains__(self, item):
        with self._lock:
            return super().__contains__(item)

    @property
    def lock(self):
        """
        Getter to access the internal lock of the list. This can be useful
        if you need to perform multiple operations atomically.
        :return:
        """
        return self._lock

    def append(self, item):
        with self._lock:
            super().append(item)

    def extend(self, iterable):
        with self._lock:
            super().extend(iterable)

    def insert(self, index, item):
        with self._lock:
            super().insert(index, item)

    def remove(self, item):
        with self._lock:
            super().remove(item)

    def pop(self, index=-1):
        with self._lock:
            return super().pop(index)

    def clear(self):
        with self._lock:
            super().clear()

    def index(self, value, *args):
        with self._lock:
            return super().index(value, *args)

    def count(self, value):
        with self._lock:
            return super().count(value)

    def sort(self, *args, **kwargs):
        with self._lock:
            super().sort(*args, **kwargs)

    def reverse(self):
        with self._lock:
            super().reverse()

    def copy(self):
        with self._lock:
            return ThreadSafeList(super().copy())


class ThreadSafeQueue:
    """
    A thread-safe queue implementation that allows for concurrent access
    without the need for external locks. The performance of this class may be
    lower than a builtin queue in single-threaded scenarios due to the overhead
    of acquiring and releasing locks.

    Not async-aware. Avoid using `await` inside any operation protected by the lock.
    """

    def __init__(self,
                 timeout: float = 60,
                 ):
        self._data = ThreadSafeList()
        self._timeout = timeout

    def __len__(self):
        return self.size()

    def __iter__(self):
        return iter(self._data.copy())

    def put(self, item):
        """
        Enqueue an item to the back of the queue.
        :param item: The item to be added to the queue.
        """
        self._data.append(item)

    def get(self):
        """
        Dequeue and return the front item of the queue.
        Raises IndexError if the queue is empty.
        """
        with self._data.lock:
            if not self._data:
                raise IndexError("get from empty queue")
            return self._data.pop(0)

    def peek(self):
        """
        Return the front item without dequeuing it.
        Raises IndexError if the queue is empty.
        """
        with self._data.lock:
            if not self._data:
                raise IndexError("peek from empty queue")
            return self._data[0]

    def empty(self):
        """
        Check if the queue is empty.
        """
        return len(self._data) == 0

    def size(self):
        """
        Return the current size of the queue.
        """
        return len(self._data)

    def clear(self):
        """
        Remove all items from the queue.
        """
        self._data.clear()


def url_to_reverse_domain(url: str) -> str:
    """
    Convert a URL to a reverse domain annotation
    :param url: The URL to convert
    :return: The reverse domain annotation
    """
    parsed = urlparse(url)

    hostname = parsed.hostname or ""

    if hostname.replace(".", "").isdigit():
        host_parts = hostname.split(".")[::-1]
    else:
        host_parts = hostname.split(".")[::-1]

    host_parts = [h for h in host_parts if h]

    path_parts = [p for p in parsed.path.strip("/").split("/") if p]

    return ".".join(host_parts + path_parts)


def validate_hash_challenge(nonce: str,
                            difficulty: int,
                            solution: str,
                            ) -> bool:
    """
    Validate a hash challenge solution.
    :param nonce: The challenge nonce
    :param difficulty: The difficulty of the challenge, by how many leading zeros it should have
    :param solution: The proposed solution to validate
    :return: True if the solution is valid, False otherwise
    """
    data = f'{nonce}{solution}'.encode()
    h = hashlib.sha256(data).hexdigest()
    bin_hash = bin(int(h, 16))[2:].zfill(256)

    target = '0' * difficulty

    return bin_hash.startswith(target)
