# Distributed Task Queue System

A Python-based distributed task queue system that simulates concurrent task processing with multiple worker threads.

## Overview

This system implements a simplified distributed task queue where:
- A central job queue manages tasks
- Multiple worker threads pull and execute jobs concurrently
- Failed tasks are automatically retried
- System provides logging and monitoring capabilities
- CLI tools allow job submission and system monitoring

## Architecture

```
distributed_task_queue/
├── queue/               # Core queue implementation
│   ├── task.py         # Task data model
│   └── job_queue.py    # Thread-safe job queue
├── workers/            # Worker implementation
│   ├── worker.py       # Individual worker logic
│   └── worker_pool.py  # Worker pool manager
├── manager.py          # System orchestrator
├── submit.py           # Job submission CLI
├── monitor.py          # System monitoring tool
└── tests/
    ├── debug/          # Basic functionality tests
    └── eval/           # Comprehensive evaluation tests
```

## Installation

```bash
# Clone or navigate to the project directory
cd distributed_task_queue

# Install dependencies
pip install -r requirements.txt
```

## Usage

### 1. Start the System Manager

```bash
# Start with default 4 workers
python manager.py

# Start with custom number of workers
python manager.py --workers 8
```

### 2. Submit Jobs

```bash
# Submit a single job with JSON payload
python submit.py --payload '{"type": "compute", "operation": "factorial", "value": 10}'

# Submit multiple random jobs
python submit.py --random --count 20

# Submit jobs from a file
python submit.py --payload-file jobs.json

# Submit with custom retry limit
python submit.py --payload '{"type": "fail", "error_message": "test"}' --max-retries 5
```

### 3. Monitor the System

```bash
# Continuous monitoring (updates every second)
python monitor.py

# One-time status check
python monitor.py --once

# Export statistics
python monitor.py --export json > stats.json
```

## Task Types

The system supports several task types:

### Compute Tasks
```json
{
    "type": "compute",
    "operation": "factorial",  // or "fibonacci", "double"
    "value": 10
}
```

### Sleep Tasks
```json
{
    "type": "sleep",
    "duration": 2,      // seconds to sleep
    "timeout": 5        // timeout in seconds
}
```

### HTTP Request Tasks (simulated)
```json
{
    "type": "http_request",
    "url": "https://api.example.com/data",
    "method": "GET"
}
```

### Failing Tasks (for testing)
```json
{
    "type": "fail",
    "error_message": "Simulated failure"
}
```

## Running Tests

### Debug Tests
These tests check basic functionality:

```bash
# Run all debug tests
python -m pytest tests/debug/ -v

# Run specific test
python -m pytest tests/debug/test_basic_queue.py -v
```

### Evaluation Tests
These tests perform comprehensive system evaluation:

```bash
# Run all evaluation tests
python -m pytest tests/eval/ -v

# Run specific evaluation test
python -m pytest tests/eval/test_concurrent_execution.py -v
```

## System Components

### Job Queue
- Thread-safe in-memory queue
- Manages task lifecycle (pending, running, completed, failed)
- Handles task retry logic

### Workers
- Pull tasks from the queue
- Execute various task types
- Report results back to the queue

### Worker Pool
- Manages multiple worker threads
- Monitors worker health
- Handles worker lifecycle

### Manager
- Orchestrates the entire system
- Handles system startup and shutdown
- Provides system-wide logging

### Monitoring
- Real-time system statistics
- Task throughput metrics
- Worker status tracking

## Performance Considerations

- Default worker count is 4, but can be adjusted based on CPU cores
- In-memory queue means tasks are lost on system restart
- Large task payloads will increase memory usage
- Monitor overhead is minimal but increases with task count

## Troubleshooting

### System Won't Start
- Check if log directory exists and is writable
- Verify Python 3.7+ is installed
- Ensure all dependencies are installed

### Tasks Not Processing
- Check if workers are alive using monitor
- Verify task payload format is correct
- Look for errors in system logs

### High Memory Usage
- Clear completed tasks periodically
- Reduce worker count if needed
- Monitor task payload sizes

## Design Notes

This is a simplified task queue system for educational purposes. In a production system, consider:
- Using a persistent message queue (Redis, RabbitMQ, etc.)
- Implementing proper distributed locking
- Using structured logging with correlation IDs
- Adding metrics and monitoring (Prometheus, etc.)
- Implementing circuit breakers and backpressure
- Using process-based workers for better isolation

## License

This is an educational project. Use at your own risk!