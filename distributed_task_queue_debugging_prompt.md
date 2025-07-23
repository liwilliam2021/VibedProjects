# Distributed Task Queue Debugging Challenge

## Context
You have been given a Python distributed task queue system located in the `distributed_task_queue/` directory. This system was developed by another team and is experiencing several issues in production. Your task is to identify and fix all the bugs in the system.

## System Overview
The distributed task queue is designed to:
- Manage tasks in a thread-safe queue
- Process tasks concurrently using multiple worker threads
- Automatically retry failed tasks
- Provide monitoring and logging capabilities
- Support various task types (compute, sleep, HTTP requests, etc.)

## Your Mission
1. **Explore the codebase** - Start by reading the README.md in the distributed_task_queue directory
2. **Run the tests** - There are two test suites:
   - `tests/debug/` - Basic functionality tests that mostly pass
   - `tests/eval/` - Comprehensive evaluation tests that are failing
3. **Identify the bugs** - The evaluation tests will help you discover what's broken
4. **Fix all issues** - Make the necessary code changes to pass all evaluation tests
5. **Verify your fixes** - Ensure all tests pass and the system works correctly

## Getting Started
```bash
cd distributed_task_queue
pip install -r requirements.txt

# Run debug tests (these should mostly pass)
python -m pytest tests/debug/ -v

# Run evaluation tests (these will fail and show you the bugs)
python -m pytest tests/eval/ -v

# Start the system
python manager.py

# In another terminal, submit some test jobs
python submit.py --random --count 10

# Monitor the system
python monitor.py
```

## Hints
- The evaluation tests are specifically designed to expose bugs - pay attention to their failure messages
- Some bugs are subtle and only appear under concurrent load
- Check for thread safety, proper error handling, and resource management
- The system should handle edge cases gracefully

## Success Criteria
All evaluation tests in `tests/eval/` should pass once you've fixed all the bugs. The system should be stable under concurrent load and handle failures gracefully.

Good luck debugging!