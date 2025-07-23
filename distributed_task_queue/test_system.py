#!/usr/bin/env python3
"""Quick test script to verify the distributed task queue system."""

import sys
import os

def check_file_exists(filepath, description):
    """Check if a file exists and print status."""
    exists = os.path.exists(filepath)
    status = "✓" if exists else "✗"
    print(f"{status} {description}: {filepath}")
    return exists

def main():
    """Run system checks."""
    print("Distributed Task Queue System Check")
    print("=" * 50)
    
    # Check core modules
    print("\nCore Modules:")
    core_files = [
        ("queue/task.py", "Task model"),
        ("queue/job_queue.py", "Job queue"),
        ("workers/worker.py", "Worker"),
        ("workers/worker_pool.py", "Worker pool"),
        ("manager.py", "Manager"),
        ("submit.py", "Job submission CLI"),
        ("monitor.py", "Monitoring tool")
    ]
    
    all_exist = True
    for filepath, desc in core_files:
        if not check_file_exists(filepath, desc):
            all_exist = False
    
    # Check test files
    print("\nTest Suites:")
    test_files = [
        ("tests/debug/test_basic_queue.py", "Basic queue tests"),
        ("tests/debug/test_worker_execution.py", "Worker execution tests"),
        ("tests/debug/test_retry_trigger.py", "Retry trigger tests"),
        ("tests/eval/test_concurrent_execution.py", "Concurrent execution tests"),
        ("tests/eval/test_race_conditions.py", "Race condition tests"),
        ("tests/eval/test_memory_leaks.py", "Memory leak tests"),
        ("tests/eval/test_timeout_behavior.py", "Timeout behavior tests"),
        ("tests/eval/test_system_integration.py", "System integration tests")
    ]
    
    for filepath, desc in test_files:
        if not check_file_exists(filepath, desc):
            all_exist = False
    
    # Check other files
    print("\nOther Files:")
    other_files = [
        ("README.md", "Documentation"),
        ("requirements.txt", "Dependencies"),
        ("logs/", "Log directory")
    ]
    
    for filepath, desc in other_files:
        if not check_file_exists(filepath, desc):
            all_exist = False
    
    # Summary
    print("\n" + "=" * 50)
    if all_exist:
        print("✓ All files present! System is ready.")
        print("\nNext steps:")
        print("1. Install dependencies: pip install -r requirements.txt")
        print("2. Run debug tests: python -m pytest tests/debug/ -v")
        print("3. Run evaluation tests: python -m pytest tests/eval/ -v")
        print("4. Start the system: python manager.py")
    else:
        print("✗ Some files are missing. Please check the structure.")
    
    return 0 if all_exist else 1

if __name__ == "__main__":
    sys.exit(main())