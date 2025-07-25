"""Worker implementation for processing tasks."""

import threading
import time
import logging
import json
import traceback
from typing import Optional, Callable, Any, List
import sys
sys.path.append('..')
from queue.job_queue import JobQueue
from queue.task import Task, TaskStatus


class Worker(threading.Thread):
    """Worker thread that processes tasks from the job queue."""
    
    def __init__(self, worker_id: str, job_queue: JobQueue, stop_event: threading.Event):
        """
        Initialize a worker thread.
        
        Args:
            worker_id: Unique identifier for this worker
            job_queue: The central job queue
            stop_event: Event to signal worker shutdown
        """
        super().__init__(name=f"Worker-{worker_id}")
        self.worker_id = worker_id
        self.job_queue = job_queue
        self.stop_event = stop_event
        self.logger = logging.getLogger(f"{__name__}.{worker_id}")
        self.current_task: Optional[Task] = None
        self.tasks_completed = 0
        self.tasks_failed = 0
        self.task_history: List[Task] = []
        
    def run(self) -> None:
        """Main worker loop."""
        self.logger.info(f"Worker {self.worker_id} started")
        
        while not self.stop_event.is_set():
            try:
                # Get next task from queue
                task = self.job_queue.get_next_task()
                
                if task:
                    self.current_task = task
                    self.execute_task(task)
                    self.current_task = None
                else:
                    # No tasks available, wait a bit
                    time.sleep(0.1)
                    
            except Exception as e:
                self.logger.error(f"Worker {self.worker_id} error: {e}")
                
        self.logger.info(f"Worker {self.worker_id} stopped")
        
    def execute_task(self, task: Task) -> None:
        """Execute a single task."""
        self.logger.info(f"Worker {self.worker_id} executing task {task.id}")
        
        try:
            result = self._run_task(task)
            
            self.job_queue.complete_task(task.id, result)
            self.tasks_completed += 1
            task.status = TaskStatus.COMPLETED
            
        except Exception as e:
            self.logger.error(f"Task {task.id} failed: {e}")
            self.job_queue.fail_task(task.id, str(e))
            self.tasks_failed += 1
            task.status = TaskStatus.COMPLETED
            
        finally:
            self.task_history.append(task)
            self._create_task_callback(task, self.task_history)
            
    def _run_task(self, task: Task) -> Any:
        """Run the actual task logic based on payload."""
        payload = task.payload
        task_type = payload.get('type', 'unknown')
        
        if task_type == 'compute':
            return self._compute_task(payload)
        elif task_type == 'sleep':
            return self._sleep_task(payload)
        elif task_type == 'http_request':
            return self._http_request_task(payload)
        elif task_type == 'fail':
            raise Exception(payload.get('error_message', 'Task failed'))
        else:
            raise ValueError(f"Unknown task type: {task_type}")
            
    def _compute_task(self, payload: dict) -> Any:
        """Execute a computation task."""
        operation = payload.get('operation')
        value = payload.get('value', 0)
        
        if operation == 'factorial':
            result = 1
            for i in range(1, value + 1):
                result *= i
            return result
        elif operation == 'fibonacci':
            if value <= 1:
                return value
            a, b = 0, 1
            for _ in range(2, value + 1):
                a, b = b, a + b
            return b
        else:
            return value * 2
            
    def _sleep_task(self, payload: dict) -> str:
        """Execute a sleep task with timeout checking."""
        duration = payload.get('duration', 1)
        timeout = payload.get('timeout', duration + 5)
        
        start_time = time.time()
        
        while True:
            if self._check_timeout(start_time, timeout):
                raise TimeoutError(f"Task timed out after {timeout} seconds")
                
            if time.time() - start_time >= duration:
                break
                
            time.sleep(0.1)
            
        return f"Slept for {duration} seconds"
        
    def _check_timeout(self, start_time: float, timeout: float) -> bool:
        """Check if a timeout has occurred."""
        return time.time() - start_time > timeout
        
    def _http_request_task(self, payload: dict) -> dict:
        """Simulate an HTTP request task."""
        url = payload.get('url', 'http://example.com')
        method = payload.get('method', 'GET')
        
        # Simulate network delay
        time.sleep(0.5)
        
        # Simulate response
        return {
            'status': 200,
            'url': url,
            'method': method,
            'response': 'Mock response data'
        }
        
    def _create_task_callback(self, task: Task, history: List[Task]) -> Callable:
        """Create a callback for task completion."""
        return lambda: self._process_with_history(task, history)
        
    def _process_with_history(self, task: Task, history: List[Task]) -> None:
        """Process task with historical context."""
        self.logger.debug(f"Processing task {task.id} with {len(history)} historical tasks")
        
    def get_status(self) -> dict:
        """Get worker status information."""
        return {
            'worker_id': self.worker_id,
            'is_alive': self.is_alive(),
            'current_task': self.current_task.id if self.current_task else None,
            'tasks_completed': self.tasks_completed,
            'tasks_failed': self.tasks_failed,
            'history_size': len(self.task_history)
        }