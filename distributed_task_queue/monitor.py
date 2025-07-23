"""Monitoring tool for the distributed task queue system."""

import time
import sys
import argparse
import json
from datetime import datetime
from queue.job_queue import JobQueue
from workers.worker_pool import WorkerPool


class Monitor:
    """Monitor for displaying system statistics and status."""
    
    def __init__(self, job_queue: JobQueue = None):
        """Initialize the monitor."""
        self.job_queue = job_queue or JobQueue()
        self.start_time = time.time()
        
    def display_stats(self, clear_screen: bool = True) -> None:
        """Display current system statistics."""
        if clear_screen:
            # Clear screen (works on Unix/Linux/Mac)
            print("\033[2J\033[H", end="")
            
        print("=" * 60)
        print("DISTRIBUTED TASK QUEUE MONITOR")
        print("=" * 60)
        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Uptime: {self._format_duration(time.time() - self.start_time)}")
        print()
        
        # Queue statistics
        stats = self.job_queue.get_queue_stats()
        print("QUEUE STATISTICS:")
        print(f"  Total Tasks:     {stats['total']}")
        print(f"  Pending:         {stats['pending']}")
        print(f"  Running:         {stats['running']}")
        print(f"  Completed:       {stats['completed']}")
        print(f"  Failed:          {stats['failed']}")
        print()
        
        # Calculate rates
        uptime_seconds = max(1, time.time() - self.start_time)
        completion_rate = stats['completed'] / uptime_seconds
        failure_rate = stats['failed'] / uptime_seconds
        
        print("PERFORMANCE METRICS:")
        print(f"  Completion Rate: {completion_rate:.2f} tasks/sec")
        print(f"  Failure Rate:    {failure_rate:.2f} tasks/sec")
        print(f"  Success Rate:    {self._calculate_success_rate(stats):.1f}%")
        print()
        
        # Recent tasks
        self._display_recent_tasks()
        
    def _display_recent_tasks(self) -> None:
        """Display information about recent tasks."""
        all_tasks = self.job_queue.get_all_tasks()
        
        # Sort by creation time
        recent_tasks = sorted(all_tasks, key=lambda t: t.created_at, reverse=True)[:5]
        
        if recent_tasks:
            print("RECENT TASKS:")
            for task in recent_tasks:
                status_symbol = self._get_status_symbol(task.status.value)
                elapsed = self._get_task_elapsed_time(task)
                print(f"  {status_symbol} {task.id[:8]}... {task.status.value:10} {elapsed:>10}")
                if task.error:
                    print(f"    Error: {task.error[:50]}...")
        print()
        
    def _get_status_symbol(self, status: str) -> str:
        """Get a symbol for the task status."""
        symbols = {
            'pending': '⏳',
            'running': '🔄',
            'completed': '✅',
            'failed': '❌'
        }
        return symbols.get(status, '❓')
        
    def _get_task_elapsed_time(self, task) -> str:
        """Get elapsed time for a task."""
        if task.completed_at:
            elapsed = task.completed_at - task.created_at
        elif task.started_at:
            elapsed = time.time() - task.started_at
        else:
            elapsed = time.time() - task.created_at
            
        return self._format_duration(elapsed)
        
    def _format_duration(self, seconds: float) -> str:
        """Format duration in human-readable format."""
        if seconds < 60:
            return f"{seconds:.1f}s"
        elif seconds < 3600:
            minutes = seconds / 60
            return f"{minutes:.1f}m"
        else:
            hours = seconds / 3600
            return f"{hours:.1f}h"
            
    def _calculate_success_rate(self, stats: dict) -> float:
        """Calculate the success rate."""
        total_finished = stats['completed'] + stats['failed']
        if total_finished == 0:
            return 0.0
        return (stats['completed'] / total_finished) * 100
        
    def continuous_monitor(self, interval: int = 1) -> None:
        """Run continuous monitoring with updates every interval seconds."""
        try:
            while True:
                self.display_stats()
                time.sleep(interval)
        except KeyboardInterrupt:
            print("\nMonitoring stopped.")
            
    def export_stats(self, format: str = 'json') -> str:
        """Export statistics in the specified format."""
        stats = self.job_queue.get_queue_stats()
        stats['timestamp'] = datetime.now().isoformat()
        stats['uptime'] = time.time() - self.start_time
        
        if format == 'json':
            return json.dumps(stats, indent=2)
        elif format == 'csv':
            headers = ','.join(stats.keys())
            values = ','.join(str(v) for v in stats.values())
            return f"{headers}\n{values}"
        else:
            return str(stats)


def main():
    """Main entry point for the monitor CLI."""
    parser = argparse.ArgumentParser(description='Monitor the distributed task queue')
    
    parser.add_argument(
        '--interval',
        type=int,
        default=1,
        help='Update interval in seconds (default: 1)'
    )
    parser.add_argument(
        '--once',
        action='store_true',
        help='Display stats once and exit'
    )
    parser.add_argument(
        '--export',
        choices=['json', 'csv'],
        help='Export stats in the specified format'
    )
    parser.add_argument(
        '--no-clear',
        action='store_true',
        help='Do not clear screen between updates'
    )
    
    args = parser.parse_args()
    
    # Note: This creates a new JobQueue instance, so it won't see
    # tasks from the running system without proper IPC
    monitor = Monitor()
    
    if args.export:
        print(monitor.export_stats(args.export))
    elif args.once:
        monitor.display_stats(clear_screen=False)
    else:
        print("Starting continuous monitoring. Press Ctrl+C to stop.")
        monitor.continuous_monitor(
            interval=args.interval
        )


if __name__ == '__main__':
    # Note: This won't show real data without proper IPC with the manager
    print("Warning: This monitor creates its own queue instance.")
    print("For real monitoring, integrate with the running manager.")
    print()
    main()