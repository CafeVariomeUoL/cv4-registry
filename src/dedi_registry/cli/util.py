import asyncio
import functools
import inspect
from rich.console import Console


def run_async(func):
    if inspect.iscoroutinefunction(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # If there's an active event loop, we cannot run another one
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = None

            if loop and loop.is_running():
                return asyncio.create_task(func(*args, **kwargs))
            else:
                return asyncio.run(func(*args, **kwargs))

        return wrapper

    return func


CONSOLE = Console()
