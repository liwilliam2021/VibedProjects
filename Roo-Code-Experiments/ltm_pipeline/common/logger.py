"""Structured logging for the LTM pipeline."""

import logging
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
import structlog
from structlog.processors import JSONRenderer, TimeStamper, add_log_level
from structlog.stdlib import LoggerFactory


class StructuredLogger:
    """Structured logger with JSON output for the LTM pipeline."""
    
    def __init__(self, module_name: str, log_dir: Optional[str] = None, level: str = "INFO"):
        """Initialize structured logger.
        
        Args:
            module_name: Name of the module using the logger
            log_dir: Directory to save log files (optional)
            level: Logging level (DEBUG, INFO, WARNING, ERROR)
        """
        self.module_name = module_name
        self.log_dir = Path(log_dir) if log_dir else None
        
        # Configure structlog
        structlog.configure(
            processors=[
                structlog.stdlib.filter_by_level,
                structlog.stdlib.add_logger_name,
                structlog.stdlib.add_log_level,
                structlog.stdlib.PositionalArgumentsFormatter(),
                TimeStamper(fmt="iso"),
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
                structlog.processors.UnicodeDecoder(),
                JSONRenderer()
            ],
            context_class=dict,
            logger_factory=LoggerFactory(),
            cache_logger_on_first_use=True,
        )
        
        # Get logger instance
        self.logger = structlog.get_logger(module_name)
        
        # Set up file handler if log_dir provided
        if self.log_dir:
            self._setup_file_handler(level)
    
    def _setup_file_handler(self, level: str) -> None:
        """Set up file handler for logging.
        
        Args:
            level: Logging level
        """
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Create log file with timestamp
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        log_file = self.log_dir / f"{self.module_name}_{timestamp}.log"
        
        # Configure standard logging to write to file
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(getattr(logging, level))
        
        # Get the underlying stdlib logger
        stdlib_logger = logging.getLogger(self.module_name)
        stdlib_logger.addHandler(file_handler)
        stdlib_logger.setLevel(getattr(logging, level))
    
    def log_operation(self, operation: str, data: Dict[str, Any], 
                     status: str = "success", **kwargs) -> None:
        """Log a structured operation.
        
        Args:
            operation: Name of the operation
            data: Operation data
            status: Operation status (success, failure, in_progress)
            **kwargs: Additional context
        """
        log_data = {
            "operation": operation,
            "status": status,
            "data": data,
            **kwargs
        }
        
        if status == "success":
            self.logger.info(f"Operation completed: {operation}", **log_data)
        elif status == "failure":
            self.logger.error(f"Operation failed: {operation}", **log_data)
        else:
            self.logger.info(f"Operation {status}: {operation}", **log_data)
    
    def log_error(self, operation: str, error: Exception, 
                  context: Optional[Dict[str, Any]] = None) -> None:
        """Log an error with context.
        
        Args:
            operation: Operation that failed
            error: Exception that occurred
            context: Additional context
        """
        error_data = {
            "operation": operation,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "context": context or {}
        }
        
        self.logger.error(f"Error in {operation}", exc_info=error, **error_data)
    
    def log_metric(self, metric_name: str, value: float, 
                   metadata: Optional[Dict[str, Any]] = None) -> None:
        """Log a metric value.
        
        Args:
            metric_name: Name of the metric
            value: Metric value
            metadata: Additional metadata
        """
        metric_data = {
            "metric_name": metric_name,
            "value": value,
            "metadata": metadata or {}
        }
        
        self.logger.info(f"Metric recorded: {metric_name}", **metric_data)
    
    def log_rule_extraction(self, transcript_id: str, rules_found: int, 
                           processing_time: float, **kwargs) -> None:
        """Log rule extraction results.
        
        Args:
            transcript_id: ID of the processed transcript
            rules_found: Number of rules extracted
            processing_time: Time taken to process
            **kwargs: Additional data
        """
        self.log_operation(
            "rule_extraction",
            {
                "transcript_id": transcript_id,
                "rules_found": rules_found,
                "processing_time_seconds": processing_time
            },
            **kwargs
        )
    
    def log_storage_decision(self, rule_id: str, decision: str, 
                            confidence: float, **kwargs) -> None:
        """Log storage decision for a rule.
        
        Args:
            rule_id: ID of the rule
            decision: Storage decision (store/ignore)
            confidence: Confidence in the decision
            **kwargs: Additional data
        """
        self.log_operation(
            "storage_decision",
            {
                "rule_id": rule_id,
                "decision": decision,
                "confidence": confidence
            },
            **kwargs
        )
    
    def log_rule_application(self, task_id: str, rule_id: str, 
                            applied: bool, reason: Optional[str] = None, **kwargs) -> None:
        """Log rule application attempt.
        
        Args:
            task_id: ID of the task
            rule_id: ID of the rule
            applied: Whether the rule was applied
            reason: Reason for application/non-application
            **kwargs: Additional data
        """
        self.log_operation(
            "rule_application",
            {
                "task_id": task_id,
                "rule_id": rule_id,
                "applied": applied,
                "reason": reason
            },
            **kwargs
        )
    
    def log_drift_comparison(self, task_id: str, consistency_score: float, 
                            with_rules: bool, **kwargs) -> None:
        """Log drift comparison results.
        
        Args:
            task_id: ID of the task
            consistency_score: Consistency score achieved
            with_rules: Whether rules were applied
            **kwargs: Additional data
        """
        self.log_operation(
            "drift_comparison",
            {
                "task_id": task_id,
                "consistency_score": consistency_score,
                "with_rules": with_rules
            },
            **kwargs
        )
    
    def debug(self, message: str, **kwargs) -> None:
        """Log debug message."""
        self.logger.debug(message, **kwargs)
    
    def info(self, message: str, **kwargs) -> None:
        """Log info message."""
        self.logger.info(message, **kwargs)
    
    def warning(self, message: str, **kwargs) -> None:
        """Log warning message."""
        self.logger.warning(message, **kwargs)
    
    def error(self, message: str, **kwargs) -> None:
        """Log error message."""
        self.logger.error(message, **kwargs)


class LoggerFactory:
    """Factory for creating loggers with consistent configuration."""
    
    _loggers: Dict[str, StructuredLogger] = {}
    _default_log_dir: Optional[Path] = None
    _default_level: str = "INFO"
    
    @classmethod
    def configure(cls, log_dir: Optional[str] = None, level: str = "INFO") -> None:
        """Configure default settings for all loggers.
        
        Args:
            log_dir: Default log directory
            level: Default log level
        """
        cls._default_log_dir = Path(log_dir) if log_dir else None
        cls._default_level = level
    
    @classmethod
    def get_logger(cls, module_name: str, 
                   log_dir: Optional[str] = None, 
                   level: Optional[str] = None) -> StructuredLogger:
        """Get or create a logger for a module.
        
        Args:
            module_name: Name of the module
            log_dir: Log directory (uses default if not provided)
            level: Log level (uses default if not provided)
            
        Returns:
            StructuredLogger instance
        """
        if module_name not in cls._loggers:
            actual_log_dir = log_dir or (str(cls._default_log_dir) if cls._default_log_dir else None)
            actual_level = level or cls._default_level
            
            cls._loggers[module_name] = StructuredLogger(
                module_name, 
                actual_log_dir, 
                actual_level
            )
        
        return cls._loggers[module_name]


# Convenience function for getting a logger
def get_logger(module_name: str) -> StructuredLogger:
    """Get a logger for the specified module.
    
    Args:
        module_name: Name of the module
        
    Returns:
        StructuredLogger instance
    """
    return LoggerFactory.get_logger(module_name)