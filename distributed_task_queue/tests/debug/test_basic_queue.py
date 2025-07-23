"""Basic queue functionality tests."""

import unittest
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from queue.job_queue import JobQueue
from queue.task import Task, TaskStatus


class TestBasicQueue(unittest.TestCase):
    """Test basic queue operations in single-threaded context."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.queue = JobQueue()
        
    def test_add_task(self):
        """Test adding a task to the queue."""
        task = Task({'type': 'test', 'value': 42})
        self.queue.add_task(task)
        
        self.assertEqual(len(self.queue), 1)
        self.assertIn(task.id, self.queue.tasks)
        
    def test_get_next_task(self):
        """Test getting the next task from queue."""
        task1 = Task({'type': 'test', 'value': 1})
        task2 = Task({'type': 'test', 'value': 2})
        
        self.queue.add_task(task1)
        self.queue.add_task(task2)
        
        # Get first task
        next_task = self.queue.get_next_task()
        self.assertEqual(next_task.id, task1.id)
        self.assertEqual(next_task.status, TaskStatus.RUNNING)
        
        # Get second task
        next_task = self.queue.get_next_task()
        self.assertEqual(next_task.id, task2.id)
        
    def test_complete_task(self):
        """Test completing a task."""
        task = Task({'type': 'test'})
        self.queue.add_task(task)
        
        # Get and complete the task
        retrieved = self.queue.get_next_task()
        self.queue.complete_task(retrieved.id, "Success")
        
        self.assertNotIn(task.id, self.queue.tasks)
        
    def test_fail_task_no_retry(self):
        """Test failing a task with no retries left."""
        task = Task({'type': 'test'}, max_retries=0)
        self.queue.add_task(task)
        
        # Get and fail the task
        retrieved = self.queue.get_next_task()
        self.queue.fail_task(retrieved.id, "Test error")
        
        # Task should still be in queue but marked as failed
        self.assertIn(task.id, self.queue.tasks)
        failed_task = self.queue.get_task(task.id)
        self.assertEqual(failed_task.status, TaskStatus.FAILED)
        
    def test_queue_stats(self):
        """Test queue statistics."""
        # Add various tasks
        for i in range(3):
            self.queue.add_task(Task({'type': 'test', 'value': i}))
            
        stats = self.queue.get_queue_stats()
        self.assertEqual(stats['total'], 3)
        self.assertEqual(stats['pending'], 3)
        self.assertEqual(stats['running'], 0)
        
    def test_clear_completed(self):
        """Test clearing completed tasks."""
        task1 = Task({'type': 'test'})
        task2 = Task({'type': 'test'})
        
        self.queue.add_task(task1)
        self.queue.add_task(task2)
        
        # Complete one task
        task1 = self.queue.get_next_task()
        task1.complete("Done")
        
        # Clear completed
        cleared = self.queue.clear_completed()
        self.assertEqual(cleared, 1)
        self.assertEqual(len(self.queue), 1)


if __name__ == '__main__':
    unittest.main()