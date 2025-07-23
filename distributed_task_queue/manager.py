"""System manager for orchestrating the distributed task queue."""

import signal
import sys
import time
import logging
import threading
from queue.job_queue import JobQueue
from workers.worker_pool import WorkerPool


class Manager:
    """Orchestrates the distributed task queue system."""
    
    def __init__(self, num_workers: int = 4):
        """
        Initialize the manager.
        
        Args:
            num_workers: Number of worker threads to spawn
        """
        self.num_workers = num_workers
        self.job_queue = JobQueue()
        self.worker_pool = WorkerPool(self.job_queue, num_workers)
        self.running = False
        self.start_time = None
        
        self._setup_logging()
        
        self.logger = logging.getLogger(__name__)
        
        # Signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
    def _setup_logging(self) -> None:
        """Setup logging configuration."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('distributed_task_queue/logs/system.log'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        
    def start(self) -> None:
        """Start the task queue system."""
        self.running = True
        self.start_time = time.time()
        
        self.logger.info("Starting distributed task queue system")
        self.logger.info(f"Configured with {self.num_workers} workers")
        
        # Start worker pool
        self.worker_pool.start()
        
        # Start monitoring thread
        monitor_thread = threading.Thread(target=self._monitor_system)
        monitor_thread.daemon = True
        monitor_thread.start()
        
        self.logger.info("System started successfully")
        
        # Keep main thread alive
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            self.logger.info("Received interrupt signal")
            
    def stop(self) -> None:
        """Stop the task queue system."""
        self.logger.info("Stopping distributed task queue system")
        self.running = False
        
        self.worker_pool.stop()
        
        self.logger.info("System stopped")
        
    def shutdown(self) -> None:
        """Shutdown the system."""
        self.running = False
        
        self.worker_pool.stop()
        
        self.logger.info("Shutdown complete")
        
    def _signal_handler(self, signum, frame) -> None:
        """Handle system signals."""
        self.logger.info(f"Received signal {signum}")
        self.shutdown()
        sys.exit(0)
        
    def _monitor_system(self) -> None:
        """Monitor system health and statistics."""
        while self.running:
            try:
                # Get system stats
                queue_stats = self.job_queue.get_queue_stats()
                pool_status = self.worker_pool.get_pool_status()
                
                self.logger.info(f"Queue stats: {queue_stats}")
                self.logger.info(f"Active workers: {pool_status['num_workers']}")
                
                # Check for issues
                if queue_stats['failed'] > 10:
                    self.logger.warning(f"High failure rate: {queue_stats['failed']} tasks failed")
                    
                if queue_stats['pending'] > 100:
                    self.logger.warning(f"Queue backlog: {queue_stats['pending']} tasks pending")
                    
                # Sleep before next check
                time.sleep(5)
                
            except Exception as e:
                self.logger.error(f"Monitor error: {e}")
                
    def get_system_info(self) -> dict:
        """Get system information and statistics."""
        uptime = time.time() - self.start_time if self.start_time else 0
        
        return {
            'uptime': uptime,
            'running': self.running,
            'num_workers': self.num_workers,
            'queue_stats': self.job_queue.get_queue_stats(),
            'pool_status': self.worker_pool.get_pool_status()
        }


def main():
    """Main entry point for the manager."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Distributed Task Queue Manager')
    parser.add_argument('--workers', type=int, default=4, help='Number of worker threads')
    args = parser.parse_args()
    
    manager = Manager(num_workers=args.workers)
    
    try:
        manager.start()
    except Exception as e:
        logging.error(f"Manager failed: {e}")
        manager.shutdown()
        sys.exit(1)


if __name__ == '__main__':
    main()