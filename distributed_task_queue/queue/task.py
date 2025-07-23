"""Task model for the distributed task queue system."""

import uuid
import time
from typing import Optional, Any, Dict
from enum import Enum


class TaskStatus(Enum):
    """Enumeration of possible task statuses."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class Task:
    """Represents a single task in the queue."""
    
    def __init__(self, payload: Dict[str, Any], max_retries: int = 3):
        """
        Initialize a new task.
        
        Args:
            payload: The task data/instructions
            max_retries: Maximum number of retry attempts
        """
        self.id: str = str(uuid.uuid4())
        self.payload: Dict[str, Any] = payload
        self.status: TaskStatus = TaskStatus.PENDING
        self.retry_count: int = 0
        self.max_retries: int = max_retries
        self.created_at: float = time.time()
        self.started_at: Optional[float] = None
        self.completed_at: Optional[float] = None
        self.result: Optional[Any] = None
        self.error: Optional[str] = None
        
    def start(self) -> None:
        """Mark the task as started."""
        self.status = TaskStatus.RUNNING
        self.started_at = time.time()
        
    def complete(self, result: Any) -> None:
        """Mark the task as completed with a result."""
        self.status = TaskStatus.COMPLETED
        self.completed_at = time.time()
        self.result = result
        
    def fail(self, error: str) -> None:
        """Mark the task as failed with an error."""
        self.status = TaskStatus.FAILED
        self.completed_at = time.time()
        self.error = error
        
    def increment_retry(self) -> None:
        """Increment the retry count."""
        self.retry_count += 1
        
    def can_retry(self) -> bool:
        """Check if the task can be retried."""
        return self.retry_count < self.max_retries
        
    def reset_for_retry(self) -> None:
        """Reset task state for retry."""
        self.status = TaskStatus.PENDING
        self.started_at = None
        self.completed_at = None
        self.result = None
        self.error = None
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert task to dictionary representation."""
        return {
            'id': self.id,
            'payload': self.payload,
            'status': self.status.value,
            'retry_count': self.retry_count,
            'max_retries': self.max_retries,
            'created_at': self.created_at,
            'started_at': self.started_at,
            'completed_at': self.completed_at,
            'result': self.result,
            'error': self.error
        }
        
    def __repr__(self) -> str:
        """String representation of the task."""
        return f"Task(id={self.id}, status={self.status.value}, retries={self.retry_count}/{self.max_retries})"