import threading
import queue
import time
import logging
from typing import Any, Tuple, Optional

from app.constants import LOGGER_NAME

class BackgroundTask:
    """Runs a target function in a separate thread and communicates results via a queue."""
    def __init__(self, callback_queue: queue.Queue):
        self.queue = callback_queue
        self.running = False
        self.thread: Optional[threading.Thread] = None
        self.logger = logging.getLogger(LOGGER_NAME)
        self.logger.debug(f"BackgroundTask instance created.")

    def start(self, target, args=(), kwargs=None):
        """Starts the task in a new thread."""
        if kwargs is None:
            kwargs = {}
        if self.is_running():
             self.logger.warning(f"Attempted to start task '{target.__name__}', but another task is already running.")
             self.queue.put(("error", "A background task is already running.")) # Inform the UI via the queue
             return None # Indicate that the task was not started

        self.running = True
        thread_name = f"BackgroundTask_{target.__name__}_{int(time.time())}"
        self.thread = threading.Thread(target=self._run_task, args=(target, args, kwargs, thread_name), name=thread_name, daemon=True)
        self.thread.start()
        self.logger.info(f"Background task '{thread_name}' started for target: {target.__name__}")
        return self.thread # Return the thread object

    def _run_task(self, target, args, kwargs, thread_name):
        """Wrapper function executed by the thread."""
        try:
            self.logger.debug(f"Task '{thread_name}' executing target: {target.__name__}")
            result = target(*args, **kwargs)
            self.queue.put(("success", result)) # Put a "success" result tuple
            self.logger.debug(f"Task '{thread_name}' completed successfully.")
        except Exception as e:
            self.logger.error(f"Error in background task '{thread_name}' target {target.__name__}: {e}", exc_info=True)
            # If the exception is a specific, handled error, put its details on the queue.
            # Otherwise, put a generic error message.
            # Tasks can also return tuples like ("error_type", error_data) for specific errors.
            if isinstance(e, RuntimeError): # Example: Catching RuntimeError specifically
                 self.queue.put(("error", ("runtime_error", str(e))))
            elif isinstance(e, ValueError): # Example: Catching ValueError specifically
                 self.queue.put(("error", ("value_error", str(e))))
            # Add other specific exception types here if needed.
            else:
                self.queue.put(("error", ("generic_exception", str(e)))) # Generic unexpected error
        finally:
            self.running = False # Ensure running flag is reset
            self.logger.debug(f"Task '{thread_name}' finished. Running flag set to False.")

    def is_running(self):
        """Checks if the background thread is currently active."""
        # Check self.running flag first (set/unset by start/finally)
        # Then check thread.is_alive() as a secondary confirmation
        return self.running and self.thread is not None and self.thread.is_alive()
