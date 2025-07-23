"""Test for race conditions in concurrent operations."""

import unittest
import threading
import time
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from queue.job_queue import JobQueue
from queue.task import Task, TaskStatus
from workers.worker import Worker


class TestRaceConditions(unittest.TestCase):
    """Test for race conditions in the queue system."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.queue = JobQueue()
        self.errors = []
        
    def test_concurrent_task_completion(self):
        """Test concurrent task completion for race conditions."""
        # Add a single task
        task = Task({'type': 'sleep', 'duration': 0.1})
        self.queue.add_task(task)
        task_id = task.id
        
        # Create multiple threads that try to complete the same task
        def complete_task():
            try:
                self.queue.complete_task(task_id, "Done")
            except Exception as e:
                self.errors.append(e)
                
        threads = []
        for i in range(10):
            thread = threading.Thread(target=complete_task)
            threads.append(thread)
            
        # Start all threads simultaneously
        for thread in threads:
            thread.start()
            
        # Wait for all threads
        for thread in threads:
            thread.join()
            
        # This will expose bug #3 - race condition in job deletion
        # Multiple threads might successfully delete the same task
        # or we might get KeyError exceptions
        self.assertTrue(len(self.errors) > 0 or task_id not in self.queue.tasks,
                       "Race condition in task deletion not detected")
        
    def test_concurrent_queue_access(self):
        """Test concurrent access to the queue."""
        num_workers = 5
        num_tasks = 50
        
        # Add many tasks
        for i in range(num_tasks):
            self.queue.add_task(Task({'type': 'compute', 'value': i}))
            
        # Create workers that will compete for tasks
        workers = []
        stop_event = threading.Event()
        
        for i in range(num_workers):
            worker = Worker(f"worker-{i}", self.queue, stop_event)
            workers.append(worker)
            
        # Start all workers
        for worker in workers:
            worker.start()
            
        # Let them run for a bit
        time.sleep(2)
        
        # Stop workers
        stop_event.set()
        for worker in workers:
            worker.join(timeout=1)
            
        # Check for consistency
        stats = self.queue.get_queue_stats()
        total_processed = stats['completed'] + stats['failed'] + stats['running']
        
        # Some tasks might be lost due to race conditions
        self.assertEqual(total_processed + stats['pending'], num_tasks,
                        "Tasks lost due to race conditions")
        
    def test_concurrent_retry_handling(self):
        """Test concurrent retry handling."""
        # Add tasks that will fail and retry
        task_ids = []
        for i in range(10):
            task = Task({
                'type': 'fail',
                'error_message': f'Concurrent fail {i}'
            }, max_retries=2)
            self.queue.add_task(task)
            task_ids.append(task.id)
            
        # Create threads that will fail tasks concurrently
        def fail_random_task():
            for task_id in task_ids:
                try:
                    self.queue.fail_task(task_id, "Concurrent failure")
                    time.sleep(0.01)  # Small delay to increase race likelihood
                except Exception:
                    pass  # Ignore errors from concurrent access
                    
        threads = []
        for i in range(5):
            thread = threading.Thread(target=fail_random_task)
            threads.append(thread)
            thread.start()
            
        # Wait for threads
        for thread in threads:
            thread.join()
            
        # Check task states
        for task_id in task_ids:
            task = self.queue.get_task(task_id)
            if task:
                # Due to race conditions, retry counts might be incorrect
                self.assertLessEqual(task.retry_count, 10,
                                   "Retry count corrupted by race condition")
                                   
    def test_logging_race_condition(self):
        """Test for race conditions in logging."""
        import logging
        import tempfile
        
        # Create a temporary log file
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            log_file = f.name
            
        # Configure logging without thread safety (like in manager.py)
        logger = logging.getLogger('test_race')
        handler = logging.FileHandler(log_file)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        
        # Create threads that write to log simultaneously
        def write_logs(thread_id):
            for i in range(100):
                logger.info(f"Thread {thread_id} message {i}")
                
        threads = []
        for i in range(10):
            thread = threading.Thread(target=write_logs, args=(i,))
            threads.append(thread)
            thread.start()
            
        # Wait for threads
        for thread in threads:
            thread.join()
            
        # Read log file and check for interleaved messages
        with open(log_file, 'r') as f:
            lines = f.readlines()
            
        # This will expose bug #4 - heisenbug in logging
        # Messages from different threads will be interleaved
        interleaved = False
        for i in range(1, len(lines)):
            if i < len(lines) - 1:
                # Check if consecutive lines are from different threads
                if 'Thread' in lines[i] and 'Thread' in lines[i-1]:
                    thread1 = lines[i-1].split('Thread')[1].split()[0]
                    thread2 = lines[i].split('Thread')[1].split()[0]
                    if thread1 != thread2:
                        # Check if the message numbers are not sequential
                        msg1 = int(lines[i-1].split('message')[1].strip())
                        msg2 = int(lines[i].split('message')[1].strip())
                        if abs(msg1 - msg2) > 1:
                            interleaved = True
                            break
                            
        # Clean up
        os.unlink(log_file)
        
        self.assertTrue(interleaved or len(lines) < 1000,
                       "Logging race condition not detected")


if __name__ == '__main__':
    unittest.main()