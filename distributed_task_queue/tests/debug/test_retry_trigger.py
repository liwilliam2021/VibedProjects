"""Test retry triggering for failed tasks."""

import unittest
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from queue.job_queue import JobQueue
from queue.task import Task, TaskStatus


class TestRetryTrigger(unittest.TestCase):
    """Test that retries are triggered for failed tasks."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.queue = JobQueue()
        
    def test_retry_triggered(self):
        """Test that a failed task triggers a retry."""
        # Create task with retries available
        task = Task({'type': 'test'}, max_retries=3)
        self.queue.add_task(task)
        
        # Get the task
        retrieved = self.queue.get_next_task()
        task_id = retrieved.id
        
        # Fail the task
        self.queue.fail_task(task_id, "First failure")
        
        # Check that task is back in pending queue
        task_after_fail = self.queue.get_task(task_id)
        self.assertEqual(task_after_fail.status, TaskStatus.PENDING)
        self.assertEqual(task_after_fail.retry_count, 1)
        
    def test_multiple_retries(self):
        """Test multiple retry attempts."""
        task = Task({'type': 'test'}, max_retries=2)
        self.queue.add_task(task)
        task_id = task.id
        
        # First failure
        retrieved = self.queue.get_next_task()
        self.queue.fail_task(task_id, "Failure 1")
        
        # Second failure
        retrieved = self.queue.get_next_task()
        self.queue.fail_task(task_id, "Failure 2")
        
        # Check retry count
        task_after = self.queue.get_task(task_id)
        self.assertEqual(task_after.retry_count, 2)
        
    def test_no_retry_when_max_zero(self):
        """Test no retry when max_retries is 0."""
        task = Task({'type': 'test'}, max_retries=0)
        self.queue.add_task(task)
        
        # Get and fail the task
        retrieved = self.queue.get_next_task()
        self.queue.fail_task(retrieved.id, "Failure")
        
        # Task should be marked as failed
        task_after = self.queue.get_task(retrieved.id)
        self.assertEqual(task_after.status, TaskStatus.FAILED)
        
    def test_retry_resets_task_state(self):
        """Test that retry resets task state properly."""
        task = Task({'type': 'test'}, max_retries=3)
        self.queue.add_task(task)
        
        # Get task and mark some fields
        retrieved = self.queue.get_next_task()
        retrieved.result = "Some result"
        retrieved.error = "Some error"
        
        # Fail the task
        self.queue.fail_task(retrieved.id, "New failure")
        
        # Get task again
        task_after = self.queue.get_task(retrieved.id)
        
        # Check state was reset
        self.assertIsNone(task_after.result)
        self.assertIsNone(task_after.started_at)
        self.assertIsNone(task_after.completed_at)
        
    def test_queue_stats_after_retry(self):
        """Test queue statistics after retry."""
        # Add multiple tasks
        for i in range(3):
            task = Task({'type': 'test', 'id': i}, max_retries=2)
            self.queue.add_task(task)
            
        # Fail one task
        task = self.queue.get_next_task()
        self.queue.fail_task(task.id, "Test failure")
        
        # Check stats
        stats = self.queue.get_queue_stats()
        self.assertEqual(stats['total'], 3)
        self.assertEqual(stats['pending'], 3)  # Failed task back to pending
        self.assertEqual(stats['failed'], 0)   # Not permanently failed yet


if __name__ == '__main__':
    unittest.main()