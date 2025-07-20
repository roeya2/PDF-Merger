import unittest
import queue
import time
from unittest.mock import Mock, patch
from app.background_task import BackgroundTask

class TestBackgroundTask(unittest.TestCase):

    def setUp(self):
        self.callback_queue = queue.Queue()
        self.task = BackgroundTask(self.callback_queue)

    def test_start_and_run_success(self):
        """Test that a simple task starts, runs, and puts a success message in the queue."""
        def simple_task():
            return "Success"

        self.task.start(simple_task)
        time.sleep(0.1)  # Give the thread time to execute

        result = self.callback_queue.get(timeout=1)
        self.assertEqual(result, ("success", "Success"))
        self.assertFalse(self.task.is_running())

    def test_is_running(self):
        """Test that is_running() returns the correct status."""
        def long_running_task():
            time.sleep(0.2)
            return "Done"

        self.assertFalse(self.task.is_running())
        self.task.start(long_running_task)
        self.assertTrue(self.task.is_running())
        time.sleep(0.3)
        self.assertFalse(self.task.is_running())

    def test_task_with_exception(self):
        """Test that a task that raises an exception puts an error message in the queue."""
        def failing_task():
            raise ValueError("Test error")

        self.task.start(failing_task)
        time.sleep(0.1)

        result = self.callback_queue.get(timeout=1)
        self.assertEqual(result[0], "error")
        self.assertEqual(result[1][0], "value_error")
        self.assertIn("Test error", result[1][1])
        self.assertFalse(self.task.is_running())

    def test_cannot_start_while_running(self):
        """Test that a new task cannot be started while another is already running."""
        def long_running_task():
            time.sleep(0.2)
            return "Done"

        self.task.start(long_running_task)
        self.assertTrue(self.task.is_running())

        # Try to start another task while the first is running
        def another_task():
            return "Should not run"

        self.task.start(another_task)

        # Check for the warning message in the queue
        result = self.callback_queue.get(timeout=1)
        self.assertEqual(result, ("error", "A background task is already running."))

        # The original task should still complete
        result = self.callback_queue.get(timeout=1)
        self.assertEqual(result, ("success", "Done"))
        self.assertFalse(self.task.is_running())

if __name__ == '__main__':
    unittest.main()
