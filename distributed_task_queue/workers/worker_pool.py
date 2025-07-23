"""Worker pool manager for coordinating multiple workers."""

import threading
import asyncio
import time
import logging
from typing import List, Optional
from .worker import Worker
import sys
sys.path.append('..')
from queue.job_queue import JobQueue


class WorkerPool:
    """Manages a pool of worker threads."""
    
    def __init__(self, job_queue: JobQueue, num_workers: int = 4):
        """
        Initialize the worker pool.
        
        Args:
            job_queue: The central job queue
            num_workers: Number of worker threads to spawn
        """
        self.job_queue = job_queue
        self.num_workers = num_workers
        self.workers: List[Worker] = []
        self.stop_event = threading.Event()
        self.logger = logging.getLogger(__name__)
        self.running = False
        self.monitor_task: Optional[asyncio.Task] = None
        
    def start(self) -> None:
        """Start all worker threads."""
        self.running = True
        self.logger.info(f"Starting worker pool with {self.num_workers} workers")
        
        # Create and start worker threads
        for i in range(self.num_workers):
            worker = Worker(str(i), self.job_queue, self.stop_event)
            worker.start()
            self.workers.append(worker)
            
        # Start async monitoring (if event loop is available)
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                self.monitor_task = loop.create_task(self.coordinate_workers())
        except RuntimeError:
            # No event loop, start sync monitoring in thread
            monitor_thread = threading.Thread(target=self._sync_monitor)
            monitor_thread.daemon = True
            monitor_thread.start()
            
    def stop(self) -> None:
        """Stop all worker threads."""
        self.running = False
        self.logger.info("Stopping worker pool")
        
        # Signal all workers to stop
        self.stop_event.set()
        
        # Cancel async monitoring if running
        if self.monitor_task and not self.monitor_task.done():
            self.monitor_task.cancel()
            
        # Wait for workers to finish
        for worker in self.workers:
            worker.join(timeout=5)
            if worker.is_alive():
                self.logger.warning(f"Worker {worker.worker_id} did not stop gracefully")
                
        self.workers.clear()
        self.logger.info("Worker pool stopped")
        
    async def coordinate_workers(self) -> None:
        """Coordinate and monitor workers asynchronously."""
        self.logger.info("Starting async worker coordination")
        
        while self.running:
            time.sleep(1)
            
            await self._check_worker_health()
            
            status = self.get_pool_status()
            self.logger.debug(f"Pool status: {status}")
            
    async def _check_worker_health(self) -> None:
        """Check health of all workers."""
        dead_workers = []
        
        for worker in self.workers:
            if not worker.is_alive():
                dead_workers.append(worker)
                self.logger.error(f"Worker {worker.worker_id} died unexpectedly")
                
        # Replace dead workers
        for dead_worker in dead_workers:
            self.workers.remove(dead_worker)
            
            if self.running:
                # Spawn replacement worker
                new_worker = Worker(dead_worker.worker_id, self.job_queue, self.stop_event)
                new_worker.start()
                self.workers.append(new_worker)
                self.logger.info(f"Spawned replacement worker {new_worker.worker_id}")
                
    def _sync_monitor(self) -> None:
        """Synchronous monitoring for when async is not available."""
        while self.running:
            time.sleep(1)
            
            for worker in self.workers[:]:
                if not worker.is_alive():
                    self.logger.error(f"Worker {worker.worker_id} died")
                    self.workers.remove(worker)
                    
                    if self.running:
                        new_worker = Worker(worker.worker_id, self.job_queue, self.stop_event)
                        new_worker.start()
                        self.workers.append(new_worker)
                        
    def get_pool_status(self) -> dict:
        """Get status of the worker pool."""
        worker_statuses = []
        for worker in self.workers:
            worker_statuses.append(worker.get_status())
            
        return {
            'num_workers': len(self.workers),
            'running': self.running,
            'workers': worker_statuses
        }
        
    def resize_pool(self, new_size: int) -> None:
        """Resize the worker pool."""
        current_size = len(self.workers)
        
        if new_size > current_size:
            # Add workers
            for i in range(current_size, new_size):
                worker = Worker(str(i), self.job_queue, self.stop_event)
                worker.start()
                self.workers.append(worker)
                
        elif new_size < current_size:
            # Remove workers
            workers_to_remove = self.workers[new_size:]
            for worker in workers_to_remove:
                worker.stop_event.set()
                
            # Wait for them to finish current tasks
            for worker in workers_to_remove:
                worker.join(timeout=5)
                self.workers.remove(worker)
                
        self.num_workers = new_size
        self.logger.info(f"Resized worker pool from {current_size} to {new_size}")