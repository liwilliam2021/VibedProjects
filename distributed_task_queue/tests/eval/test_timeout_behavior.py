"""Test timeout behavior and clock drift issues."""

import unittest
import threading
import time
import sys
import os
from unittest.mock import patch
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from queue.job_queue import JobQueue
from queue.task import Task
from workers.worker import Worker


class TestTimeoutBehavior(unittest.TestCase):
    """Test timeout handling and clock-related issues."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.queue = JobQueue()
        self.stop_event = threading.Event()
        
    def tearDown(self):
        """Clean up after tests."""
        self.stop_event.set()
        
    def test_basic_timeout_handling(self):
        """Test basic timeout functionality."""
        # Create a task that will timeout
        task = Task({
            'type': 'sleep',
            'duration': 5,  # Sleep for 5 seconds
            'timeout': 1    # But timeout after 1 second
        })
        self.queue.add_task(task)
        
        # Create worker and execute task
        worker = Worker("test-1", self.queue, self.stop_event)
        retrieved_task = self.queue.get_next_task()
        
        start_time = time.time()
        worker.execute_task(retrieved_task)
        elapsed = time.time() - start_time
        
        # Task should have timed out
        self.assertLess(elapsed, 2, "Task did not timeout properly")
        
        # Check task was marked as failed
        task_after = self.queue.get_task(task.id)
        self.assertIsNotNone(task_after.error)
        self.assertIn("timeout", task_after.error.lower())
        
    def test_clock_drift_vulnerability(self):
        """Test vulnerability to system clock changes."""
        # This test simulates clock drift by mocking time.time()
        
        task = Task({
            'type': 'sleep',
            'duration': 2,
            'timeout': 5
        })
        self.queue.add_task(task)
        
        worker = Worker("test-1", self.queue, self.stop_event)
        
        # Mock time.time to simulate clock drift
        original_time = time.time
        time_offset = 0
        
        def mock_time():
            return original_time() + time_offset
            
        with patch('time.time', mock_time):
            # Start task execution in a thread
            retrieved_task = self.queue.get_next_task()
            
            execution_complete = threading.Event()
            execution_error = []
            
            def execute_with_drift():
                try:
                    worker.execute_task(retrieved_task)
                except Exception as e:
                    execution_error.append(e)
                finally:
                    execution_complete.set()
                    
            exec_thread = threading.Thread(target=execute_with_drift)
            exec_thread.start()
            
            # Wait a bit, then simulate clock going backwards
            time.sleep(0.5)
            time_offset = -10  # Clock goes back 10 seconds
            
            # Wait for execution to complete
            execution_complete.wait(timeout=10)
            
            # This will expose bug #7 - using time.time() instead of monotonic
            # The timeout check will be affected by clock drift
            if execution_error:
                self.assertIn("timeout", str(execution_error[0]).lower(),
                            "Clock drift caused unexpected timeout")
                            
    def test_concurrent_timeout_checks(self):
        """Test timeout behavior under concurrent load."""
        num_tasks = 20
        
        # Add tasks with various timeout scenarios
        for i in range(num_tasks):
            if i % 3 == 0:
                # Task that will timeout
                task = Task({
                    'type': 'sleep',
                    'duration': 10,
                    'timeout': 0.5
                })
            else:
                # Task that won't timeout
                task = Task({
                    'type': 'sleep',
                    'duration': 0.1,
                    'timeout': 2
                })
            self.queue.add_task(task)
            
        # Create multiple workers
        workers = []
        for i in range(4):
            worker = Worker(f"test-{i}", self.queue, self.stop_event)
            workers.append(worker)
            worker.start()
            
        # Let them process
        time.sleep(5)
        
        # Stop workers
        self.stop_event.set()
        for worker in workers:
            worker.join(timeout=1)
            
        # Check results
        stats = self.queue.get_queue_stats()
        all_tasks = self.queue.get_all_tasks()
        
        timeout_tasks = [t for t in all_tasks if t.error and 'timeout' in t.error.lower()]
        
        # Should have some timeout failures
        self.assertGreater(len(timeout_tasks), 0, "No timeout failures detected")
        
    def test_monotonic_time_usage(self):
        """Test that monotonic time should be used for timeouts."""
        # Create a custom worker to test the internal timeout mechanism
        worker = Worker("test-1", self.queue, self.stop_event)
        
        # Test the _check_timeout method directly
        start_time = time.time()
        
        # This method uses time.time() (bug #7)
        # In correct implementation, it should use time.monotonic()
        result1 = worker._check_timeout(start_time, 1.0)
        self.assertFalse(result1)  # Should not timeout immediately
        
        # Wait a bit
        time.sleep(1.1)
        
        result2 = worker._check_timeout(start_time, 1.0)
        self.assertTrue(result2)  # Should timeout now
        
        # The issue is that this is vulnerable to clock changes
        # With monotonic time, clock changes wouldn't affect timeouts
        
    def test_timeout_with_retries(self):
        """Test timeout behavior with retry logic."""
        # Task that will timeout and retry
        task = Task({
            'type': 'sleep',
            'duration': 5,
            'timeout': 0.5
        }, max_retries=2)
        self.queue.add_task(task)
        
        worker = Worker("test-1", self.queue, self.stop_event)
        
        # Process the task multiple times (with retries)
        for attempt in range(3):
            retrieved = self.queue.get_next_task()
            if retrieved:
                worker.execute_task(retrieved)
                time.sleep(0.1)
                
        # Check final state
        final_task = self.queue.get_task(task.id)
        
        # Due to bug #1 (retry logic), this might not work correctly
        # Combined with timeout issues, behavior can be unpredictable
        self.assertGreaterEqual(final_task.retry_count, 2)


if __name__ == '__main__':
    unittest.main()