"""Full system integration tests that expose all bugs."""

import unittest
import threading
import time
import asyncio
import sys
import os
import tempfile
import shutil
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from manager import Manager
from queue.job_queue import JobQueue
from queue.task import Task


class TestSystemIntegration(unittest.TestCase):
    """Test full system integration and expose all bugs."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary directory for logs
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)
        os.makedirs('distributed_task_queue/logs', exist_ok=True)
        
    def tearDown(self):
        """Clean up after tests."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.temp_dir)
        
    def test_full_system_with_all_bugs(self):
        """Test the full system, exposing all embedded bugs."""
        # Create manager with 4 workers
        manager = Manager(num_workers=4)
        
        # Add various types of tasks
        task_configs = [
            # Tasks that will succeed
            {'type': 'compute', 'operation': 'factorial', 'value': 10},
            {'type': 'sleep', 'duration': 0.5},
            
            # Tasks that will fail and retry (bug #1)
            {'type': 'fail', 'error_message': 'Test failure 1'},
            {'type': 'fail', 'error_message': 'Test failure 2'},
            
            # Tasks with timeouts (bug #7)
            {'type': 'sleep', 'duration': 10, 'timeout': 1},
            
            # More compute tasks to stress the system
            *[{'type': 'compute', 'operation': 'fibonacci', 'value': i} 
              for i in range(5, 15)]
        ]
        
        # Add tasks with different retry counts
        for i, config in enumerate(task_configs):
            task = Task(config.copy(), max_retries=i % 4)
            manager.job_queue.add_task(task)
            
        # Start the system in a thread
        manager_thread = threading.Thread(target=manager.start)
        manager_thread.daemon = True
        manager_thread.start()
        
        # Let the system run
        time.sleep(10)
        
        # Check various aspects that expose bugs
        
        # Bug #1: Retry logic fails
        all_tasks = manager.job_queue.get_all_tasks()
        failed_tasks = [t for t in all_tasks if t.status.value == 'failed']
        for task in failed_tasks:
            if task.max_retries > 0:
                # This assertion will fail due to bug #1
                self.assertGreater(task.retry_count, task.max_retries,
                                 f"Task {task.id} has retry_count={task.retry_count}, max_retries={task.max_retries}")
                                 
        # Bug #2: Incorrect status reporting
        # Some failed tasks might be marked as completed
        completed_tasks = [t for t in all_tasks if t.status.value == 'completed']
        for task in completed_tasks:
            if task.payload.get('type') == 'fail':
                self.fail(f"Failed task {task.id} marked as completed")
                
        # Bug #3: Race condition in job deletion
        # This is harder to detect but might cause missing tasks
        stats = manager.job_queue.get_queue_stats()
        total_tasks = len(task_configs)
        accounted_tasks = stats['pending'] + stats['running'] + stats['completed'] + stats['failed']
        self.assertEqual(accounted_tasks, total_tasks,
                        "Some tasks lost due to race conditions")
                        
        # Bug #4: Logging issues
        # Check log file for interleaved messages
        log_file = 'distributed_task_queue/logs/system.log'
        if os.path.exists(log_file):
            with open(log_file, 'r') as f:
                lines = f.readlines()
                # Look for garbled or incomplete lines
                for line in lines:
                    self.assertIn('\n', line, "Log line missing newline (interleaved)")
                    
        # Bug #5: Thread leak on shutdown
        initial_thread_count = threading.active_count()
        manager.shutdown()
        time.sleep(2)
        final_thread_count = threading.active_count()
        
        # This will fail due to bug #5
        self.assertLessEqual(final_thread_count, initial_thread_count,
                           f"Thread leak: {final_thread_count - initial_thread_count} threads remaining")
                           
        # Bug #6: Memory bloat
        pool_status = manager.worker_pool.get_pool_status()
        for worker in pool_status['workers']:
            history_size = worker.get('history_size', 0)
            self.assertLess(history_size, 50,
                           f"Worker {worker['worker_id']} has bloated history: {history_size}")
                           
    def test_async_sync_mixing(self):
        """Test for async/sync mixing issues."""
        # This test specifically targets bug #8
        
        # Create an event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        manager = Manager(num_workers=2)
        
        # Add some tasks
        for i in range(10):
            task = Task({'type': 'sleep', 'duration': 0.1})
            manager.job_queue.add_task(task)
            
        # Start manager
        manager_thread = threading.Thread(target=manager.start)
        manager_thread.daemon = True
        manager_thread.start()
        
        # Try to run async coordination
        async def test_async_coordination():
            # This will expose bug #8 - time.sleep() in async context
            start_time = time.time()
            
            # The coordinate_workers method uses time.sleep()
            # which will block the event loop
            try:
                await asyncio.wait_for(
                    manager.worker_pool.coordinate_workers(),
                    timeout=3
                )
            except asyncio.TimeoutError:
                pass
                
            elapsed = time.time() - start_time
            
            # If bug #8 exists, the event loop will be blocked
            # and we won't be able to run other async tasks
            return elapsed
            
        # Run the async test
        try:
            elapsed = loop.run_until_complete(test_async_coordination())
            # The blocking sleep will make this take longer than expected
            self.assertGreater(elapsed, 1,
                             "Async context blocked by sync sleep")
        finally:
            manager.shutdown()
            loop.close()
            
    def test_stress_all_components(self):
        """Stress test that exercises all components and bugs."""
        manager = Manager(num_workers=6)
        
        # Start manager
        manager_thread = threading.Thread(target=manager.start)
        manager_thread.daemon = True
        manager_thread.start()
        
        # Continuously add tasks for stress testing
        def task_generator():
            task_count = 0
            while manager.running and task_count < 100:
                # Mix of task types
                configs = [
                    {'type': 'compute', 'operation': 'factorial', 'value': task_count % 20},
                    {'type': 'sleep', 'duration': 0.1 * (task_count % 5)},
                    {'type': 'fail', 'error_message': f'Stress fail {task_count}'},
                    {'type': 'sleep', 'duration': 5, 'timeout': 0.5}  # Timeout task
                ]
                
                config = configs[task_count % len(configs)]
                task = Task(config, max_retries=task_count % 3)
                manager.job_queue.add_task(task)
                
                task_count += 1
                time.sleep(0.05)  # Add tasks gradually
                
        # Start task generation
        gen_thread = threading.Thread(target=task_generator)
        gen_thread.start()
        
        # Monitor for issues
        issues_found = []
        
        def monitor_issues():
            while manager.running:
                try:
                    # Check for various issues
                    stats = manager.job_queue.get_queue_stats()
                    pool_status = manager.worker_pool.get_pool_status()
                    
                    # Check for stuck tasks
                    if stats['running'] > manager.num_workers * 2:
                        issues_found.append("Too many running tasks")
                        
                    # Check for dead workers
                    alive_workers = sum(1 for w in pool_status['workers'] if w['is_alive'])
                    if alive_workers < manager.num_workers:
                        issues_found.append("Dead workers detected")
                        
                    time.sleep(0.5)
                except Exception as e:
                    issues_found.append(f"Monitor error: {e}")
                    
        monitor_thread = threading.Thread(target=monitor_issues)
        monitor_thread.daemon = True
        monitor_thread.start()
        
        # Run for a while
        time.sleep(15)
        
        # Shutdown
        manager.shutdown()
        gen_thread.join(timeout=2)
        
        # Check for issues
        self.assertGreater(len(issues_found), 0,
                          "No issues detected in stress test (bugs not exposed)")


if __name__ == '__main__':
    unittest.main()