"""Comprehensive concurrent execution tests that expose multiple bugs."""

import unittest
import threading
import time
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from queue.job_queue import JobQueue
from queue.task import Task, TaskStatus
from workers.worker_pool import WorkerPool


class TestConcurrentExecution(unittest.TestCase):
    """Test concurrent task execution with multiple workers."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.queue = JobQueue()
        self.pool = WorkerPool(self.queue, num_workers=4)
        
    def tearDown(self):
        """Clean up after tests."""
        self.pool.stop()
        
    def test_multiple_workers_processing(self):
        """Test multiple workers processing tasks concurrently."""
        num_tasks = 20
        
        # Add compute tasks
        for i in range(num_tasks):
            task = Task({
                'type': 'compute',
                'operation': 'factorial',
                'value': 5
            })
            self.queue.add_task(task)
            
        # Start worker pool
        self.pool.start()
        
        # Wait for tasks to complete
        timeout = 10
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            stats = self.queue.get_queue_stats()
            if stats['completed'] + stats['failed'] == num_tasks:
                break
            time.sleep(0.1)
            
        # Check results
        stats = self.queue.get_queue_stats()
        
        # This test will reveal bug #2 - incorrect status reporting
        # Some "failed" tasks might be marked as completed
        self.assertEqual(stats['completed'] + stats['failed'], num_tasks)
        
    def test_failing_tasks_with_retries(self):
        """Test handling of failing tasks with retries."""
        # Add tasks that will fail
        for i in range(5):
            task = Task({
                'type': 'fail',
                'error_message': f'Test failure {i}'
            }, max_retries=3)
            self.queue.add_task(task)
            
        self.pool.start()
        
        # Wait for processing
        time.sleep(5)
        
        # Check retry behavior
        stats = self.queue.get_queue_stats()
        
        # This will expose bug #1 - retry logic fails
        # Tasks should fail permanently after max_retries
        # but due to the bug, they might keep retrying
        all_tasks = self.queue.get_all_tasks()
        for task in all_tasks:
            if task.status == TaskStatus.FAILED:
                # Bug #1: This assertion will fail because retry_count > max_retries
                # is used instead of >=
                self.assertGreaterEqual(task.retry_count, task.max_retries)
                
    def test_mixed_task_types(self):
        """Test processing mixed task types concurrently."""
        task_configs = [
            {'type': 'compute', 'operation': 'factorial', 'value': 10},
            {'type': 'sleep', 'duration': 0.5},
            {'type': 'http_request', 'url': 'http://example.com'},
            {'type': 'fail', 'error_message': 'Expected failure'},
            {'type': 'compute', 'operation': 'fibonacci', 'value': 15}
        ]
        
        # Add multiple instances of each task type
        for _ in range(3):
            for config in task_configs:
                self.queue.add_task(Task(config.copy()))
                
        self.pool.start()
        
        # Process for a while
        time.sleep(3)
        
        # Check worker status
        pool_status = self.pool.get_pool_status()
        
        # Verify all workers are active
        self.assertEqual(len(pool_status['workers']), 4)
        
        # Check for memory bloat (bug #6)
        for worker_status in pool_status['workers']:
            # History size should not grow unbounded
            history_size = worker_status.get('history_size', 0)
            # This will fail due to bug #6 - memory bloat
            self.assertLess(history_size, 100, "Worker history growing unbounded")


if __name__ == '__main__':
    unittest.main()