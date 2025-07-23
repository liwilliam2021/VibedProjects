"""CLI tool for submitting jobs to the task queue."""

import argparse
import json
import sys
import random
import uuid
from queue.job_queue import JobQueue
from queue.task import Task


def submit_job(payload: dict, max_retries: int = 3) -> str:
    """Submit a job to the queue."""
    job_queue = JobQueue()
    task = Task(payload, max_retries)
    job_queue.add_task(task)
    return task.id


def generate_random_task() -> dict:
    """Generate a random task for testing."""
    task_types = [
        {
            'type': 'compute',
            'operation': random.choice(['factorial', 'fibonacci', 'double']),
            'value': random.randint(1, 20)
        },
        {
            'type': 'sleep',
            'duration': random.randint(1, 5),
            'timeout': random.randint(10, 20)
        },
        {
            'type': 'http_request',
            'url': f'https://api.example.com/endpoint/{random.randint(1, 100)}',
            'method': random.choice(['GET', 'POST', 'PUT'])
        },
        {
            'type': 'fail',
            'error_message': f'Simulated failure {random.randint(1, 100)}'
        }
    ]
    
    return random.choice(task_types)


def main():
    """Main entry point for the submit CLI."""
    parser = argparse.ArgumentParser(description='Submit jobs to the distributed task queue')
    
    # Payload options
    payload_group = parser.add_mutually_exclusive_group(required=True)
    payload_group.add_argument(
        '--payload',
        type=str,
        help='JSON payload for the task'
    )
    payload_group.add_argument(
        '--payload-file',
        type=str,
        help='File containing JSON payload(s)'
    )
    payload_group.add_argument(
        '--random',
        action='store_true',
        help='Generate random tasks'
    )
    
    # Other options
    parser.add_argument(
        '--count',
        type=int,
        default=1,
        help='Number of tasks to submit (default: 1)'
    )
    parser.add_argument(
        '--max-retries',
        type=int,
        default=3,
        help='Maximum retry attempts for failed tasks (default: 3)'
    )
    parser.add_argument(
        '--batch-id',
        type=str,
        help='Batch ID to tag all submitted tasks'
    )
    
    args = parser.parse_args()
    
    # Prepare payloads
    payloads = []
    
    if args.payload:
        try:
            payload = json.loads(args.payload)
            payloads = [payload] * args.count
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON payload: {e}", file=sys.stderr)
            sys.exit(1)
            
    elif args.payload_file:
        try:
            with open(args.payload_file, 'r') as f:
                data = json.load(f)
                if isinstance(data, list):
                    payloads = data * (args.count // len(data) + 1)
                    payloads = payloads[:args.count]
                else:
                    payloads = [data] * args.count
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error: Failed to read payload file: {e}", file=sys.stderr)
            sys.exit(1)
            
    elif args.random:
        payloads = [generate_random_task() for _ in range(args.count)]
        
    # Add batch ID if specified
    if args.batch_id:
        for payload in payloads:
            payload['batch_id'] = args.batch_id
            
    # Submit tasks
    print(f"Submitting {len(payloads)} task(s) to the queue...")
    
    task_ids = []
    for i, payload in enumerate(payloads):
        try:
            task_id = submit_job(payload, args.max_retries)
            task_ids.append(task_id)
            print(f"  [{i+1}/{len(payloads)}] Submitted task {task_id}")
            
            # Show payload for random tasks
            if args.random:
                print(f"       Payload: {json.dumps(payload)}")
                
        except Exception as e:
            print(f"  [{i+1}/{len(payloads)}] Failed to submit: {e}", file=sys.stderr)
            
    print(f"\nSuccessfully submitted {len(task_ids)} task(s)")
    
    # Output task IDs for scripting
    if len(task_ids) == 1:
        print(f"Task ID: {task_ids[0]}")
    else:
        print("Task IDs:")
        for task_id in task_ids:
            print(f"  {task_id}")


if __name__ == '__main__':
    # Note: This won't work properly without the manager running
    # because we're creating a new JobQueue instance each time
    print("Warning: Make sure the manager is running for tasks to be processed!")
    main()