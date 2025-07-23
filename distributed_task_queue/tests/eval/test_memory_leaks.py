"""Test for memory leaks in the system."""

import unittest
import threading
import time
import gc
import sys
import os
import psutil
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from queue.job_queue import JobQueue
from queue.task import Task
from workers.worker_pool import WorkerPool


class TestMemoryLeaks(unittest.TestCase):
    """Test for memory leaks in long-running scenarios."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.queue = JobQueue()
        self.process = psutil.Process()
        
    def test_worker_memory_bloat(self):
        """Test for memory bloat in workers due to task history."""
        pool = WorkerPool(self.queue, num_workers=2)
        
        # Record initial memory
        gc.collect()
        initial_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        
        # Add many tasks
        num_tasks = 100
        for i in range(num_tasks):
            task = Task({
                'type': 'compute',
                'operation': 'factorial',
                'value': 10,
                'data': 'x' * 1000  # Add some data to make memory usage visible
            })
            self.queue.add_task(task)
            
        # Start processing
        pool.start()
        
        # Wait for tasks to complete
        timeout = 30
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            stats = self.queue.get_queue_stats()
            if stats['completed'] >= num_tasks * 0.9:  # 90% complete
                break
            time.sleep(0.5)
            
        # Check memory usage
        gc.collect()
        final_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        # Get worker status to check history size
        pool_status = pool.get_pool_status()
        total_history_size = sum(
            w['history_size'] for w in pool_status['workers']
        )
        
        # Stop pool
        pool.stop()
        
        # This will expose bug #6 - memory bloat from closure capture
        # Workers keep entire task history, causing memory growth
        self.assertLess(memory_increase, 50,
                       f"Memory increased by {memory_increase:.1f} MB")
        self.assertEqual(total_history_size, num_tasks,
                        "Workers keeping entire task history")
        
    def test_thread_leak_on_shutdown(self):
        """Test for thread leaks when shutting down."""
        import threading
        
        # Record initial thread count
        initial_threads = threading.active_count()
        
        # Create and start a worker pool
        pool = WorkerPool(self.queue, num_workers=4)
        pool.start()
        
        # Add some tasks
        for i in range(10):
            self.queue.add_task(Task({'type': 'sleep', 'duration': 0.1}))
            
        # Wait a bit
        time.sleep(1)
        
        # Stop the pool
        pool.stop()
        
        # Wait for threads to clean up
        time.sleep(2)
        
        # Check thread count
        final_threads = threading.active_count()
        
        # This will expose bug #5 - thread leak on shutdown
        # Some threads are not properly joined
        self.assertEqual(final_threads, initial_threads,
                        f"Thread leak: {final_threads - initial_threads} threads remaining")
        
    def test_queue_memory_with_completed_tasks(self):
        """Test memory usage with many completed tasks."""
        # Record initial memory
        gc.collect()
        initial_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        
        # Add and complete many tasks
        num_tasks = 1000
        for i in range(num_tasks):
            task = Task({
                'type': 'test',
                'data': f'Task {i}' * 100  # Some data
            })
            self.queue.add_task(task)
            
            # Simulate completion
            task.complete(f"Result {i}")
            
        # Check memory before cleanup
        gc.collect()
        before_cleanup_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        
        # Clear completed tasks
        cleared = self.queue.clear_completed()
        
        # Check memory after cleanup
        gc.collect()
        after_cleanup_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        
        # Memory should decrease after clearing completed tasks
        memory_freed = before_cleanup_memory - after_cleanup_memory
        self.assertGreater(memory_freed, 0,
                          "Memory not freed after clearing completed tasks")
        self.assertEqual(cleared, num_tasks,
                        "Not all completed tasks were cleared")
        
    def test_long_running_memory_stability(self):
        """Test memory stability in long-running scenario."""
        pool = WorkerPool(self.queue, num_workers=2)
        pool.start()
        
        # Record memory over time
        memory_samples = []
        
        # Run for a period, continuously adding tasks
        duration = 10  # seconds
        start_time = time.time()
        task_count = 0
        
        while time.time() - start_time < duration:
            # Add a batch of tasks
            for i in range(5):
                task = Task({
                    'type': 'compute',
                    'operation': 'double',
                    'value': task_count
                })
                self.queue.add_task(task)
                task_count += 1
                
            # Record memory usage
            gc.collect()
            memory_mb = self.process.memory_info().rss / 1024 / 1024
            memory_samples.append(memory_mb)
            
            # Clear completed tasks periodically
            if task_count % 50 == 0:
                self.queue.clear_completed()
                
            time.sleep(0.5)
            
        # Stop pool
        pool.stop()
        
        # Analyze memory trend
        # Memory should be relatively stable, not continuously growing
        if len(memory_samples) > 10:
            first_half_avg = sum(memory_samples[:len(memory_samples)//2]) / (len(memory_samples)//2)
            second_half_avg = sum(memory_samples[len(memory_samples)//2:]) / (len(memory_samples)//2)
            
            memory_growth = second_half_avg - first_half_avg
            
            # Due to bug #6, memory will grow over time
            self.assertLess(memory_growth, 20,
                           f"Memory grew by {memory_growth:.1f} MB during execution")


if __name__ == '__main__':
    unittest.main()