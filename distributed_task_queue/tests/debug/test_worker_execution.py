"""Basic worker execution tests."""

import unittest
import threading
import time
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from queue.job_queue import JobQueue
from queue.task import Task, TaskStatus
from workers.worker import Worker


class TestWorkerExecution(unittest.TestCase):
    """Test basic worker task execution."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.queue = JobQueue()
        self.stop_event = threading.Event()
        
    def tearDown(self):
        """Clean up after tests."""
        self.stop_event.set()
        
    def test_worker_creation(self):
        """Test creating a worker."""
        worker = Worker("test-1", self.queue, self.stop_event)
        self.assertEqual(worker.worker_id, "test-1")
        self.assertEqual(worker.tasks_completed, 0)
        self.assertEqual(worker.tasks_failed, 0)
        
    def test_simple_task_execution(self):
        """Test executing a simple task."""
        # Add a compute task
        task = Task({
            'type': 'compute',
            'operation': 'double',
            'value': 21
        })
        self.queue.add_task(task)
        
        # Create and start worker
        worker = Worker("test-1", self.queue, self.stop_event)
        
        # Manually execute one task
        retrieved_task = self.queue.get_next_task()
        worker.execute_task(retrieved_task)
        
        # Check task was marked as completed
        self.assertEqual(worker.tasks_completed, 1)
        
    def test_sleep_task(self):
        """Test executing a sleep task."""
        task = Task({
            'type': 'sleep',
            'duration': 0.1,
            'timeout': 1
        })
        self.queue.add_task(task)
        
        worker = Worker("test-1", self.queue, self.stop_event)
        retrieved_task = self.queue.get_next_task()
        
        start_time = time.time()
        worker.execute_task(retrieved_task)
        elapsed = time.time() - start_time
        
        # Should have slept for at least 0.1 seconds
        self.assertGreaterEqual(elapsed, 0.1)
        
    def test_failing_task(self):
        """Test handling a failing task."""
        task = Task({
            'type': 'fail',
            'error_message': 'Test failure'
        })
        self.queue.add_task(task)
        
        worker = Worker("test-1", self.queue, self.stop_event)
        retrieved_task = self.queue.get_next_task()
        
        # Execute failing task
        worker.execute_task(retrieved_task)
        
        # Check that task was processed
        self.assertEqual(worker.tasks_failed, 1)
        
    def test_worker_status(self):
        """Test getting worker status."""
        worker = Worker("test-1", self.queue, self.stop_event)
        status = worker.get_status()
        
        self.assertEqual(status['worker_id'], "test-1")
        self.assertIsNone(status['current_task'])
        self.assertEqual(status['tasks_completed'], 0)
        self.assertEqual(status['tasks_failed'], 0)
        
    def test_compute_factorial(self):
        """Test factorial computation."""
        task = Task({
            'type': 'compute',
            'operation': 'factorial',
            'value': 5
        })
        self.queue.add_task(task)
        
        worker = Worker("test-1", self.queue, self.stop_event)
        result = worker._compute_task(task.payload)
        
        self.assertEqual(result, 120)  # 5! = 120


if __name__ == '__main__':
    unittest.main()