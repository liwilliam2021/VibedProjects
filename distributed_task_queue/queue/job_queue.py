"""Thread-safe job queue implementation."""

import threading
from collections import deque
from typing import Dict, Optional, List, Deque, Any
import logging
from .task import Task, TaskStatus


class JobQueue:
    """Central job queue for task management."""
    
    def __init__(self):
        """Initialize the job queue."""
        self.pending_queue: Deque[str] = deque()
        self.tasks: Dict[str, Task] = {}
        self.lock = threading.Lock()
        self.logger = logging.getLogger(__name__)
        
    def add_task(self, task: Task) -> None:
        """Add a new task to the queue."""
        with self.lock:
            self.tasks[task.id] = task
            self.pending_queue.append(task.id)
            self.logger.info(f"Added task {task.id} to queue")
            
    def get_next_task(self) -> Optional[Task]:
        """Get the next pending task from the queue."""
        with self.lock:
            while self.pending_queue:
                task_id = self.pending_queue.popleft()
                task = self.tasks.get(task_id)
                
                if task and task.status == TaskStatus.PENDING:
                    task.start()
                    self.logger.info(f"Task {task_id} assigned to worker")
                    return task
                    
            return None
            
    def complete_task(self, task_id: str, result: Any = None) -> None:
        """Mark a task as completed."""
        if task_id in self.tasks:
            task = self.tasks[task_id]
            task.complete(result)
            self.logger.info(f"Task {task_id} completed")
            del self.tasks[task_id]
            
    def fail_task(self, task_id: str, error: str) -> None:
        """Mark a task as failed and potentially retry."""
        with self.lock:
            if task_id not in self.tasks:
                return
                
            task = self.tasks[task_id]
            task.fail(error)
            task.increment_retry()
            
            if task.retry_count > task.max_retries:
                self.logger.error(f"Task {task_id} permanently failed after {task.retry_count} retries")
                task.status = TaskStatus.FAILED
            else:
                self.logger.warning(f"Task {task_id} failed, retrying ({task.retry_count}/{task.max_retries})")
                task.reset_for_retry()
                self.pending_queue.append(task_id)
                
    def get_task(self, task_id: str) -> Optional[Task]:
        """Get a specific task by ID."""
        with self.lock:
            return self.tasks.get(task_id)
            
    def get_all_tasks(self) -> List[Task]:
        """Get all tasks in the queue."""
        with self.lock:
            return list(self.tasks.values())
            
    def get_queue_stats(self) -> Dict[str, int]:
        """Get statistics about the queue."""
        with self.lock:
            stats = {
                'pending': 0,
                'running': 0,
                'completed': 0,
                'failed': 0,
                'total': len(self.tasks)
            }
            
            for task in self.tasks.values():
                if task.status == TaskStatus.PENDING:
                    stats['pending'] += 1
                elif task.status == TaskStatus.RUNNING:
                    stats['running'] += 1
                elif task.status == TaskStatus.COMPLETED:
                    stats['completed'] += 1
                elif task.status == TaskStatus.FAILED:
                    stats['failed'] += 1
                    
            return stats
            
    def clear_completed(self) -> int:
        """Remove completed tasks from the queue."""
        with self.lock:
            completed_ids = [
                task_id for task_id, task in self.tasks.items()
                if task.status == TaskStatus.COMPLETED
            ]
            
            for task_id in completed_ids:
                del self.tasks[task_id]
                
            return len(completed_ids)
            
    def __len__(self) -> int:
        """Get the total number of tasks."""
        with self.lock:
            return len(self.tasks)
            
    def __repr__(self) -> str:
        """String representation of the queue."""
        stats = self.get_queue_stats()
        return f"JobQueue(pending={stats['pending']}, running={stats['running']}, total={stats['total']})"