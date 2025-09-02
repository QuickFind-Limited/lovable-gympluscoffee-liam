#!/usr/bin/env python3
"""
Batch Processor
==============

Handles batch processing of large datasets with chunking,
parallel processing capabilities, and memory management.

Agent: Batch Processing Specialist
"""

import logging
import time
from typing import List, Dict, Any, Callable, Optional, Iterator, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from dataclasses import dataclass
from datetime import datetime


@dataclass
class BatchConfig:
    """Batch processing configuration"""
    batch_size: int = 100
    max_workers: int = 4
    chunk_delay: float = 0.1  # Delay between chunks
    memory_threshold: float = 0.8  # Memory usage threshold
    enable_parallel: bool = True


class BatchProcessor:
    """
    Batch Data Processor
    ===================
    
    Processes large datasets in configurable batches with
    parallel processing, memory management, and progress tracking.
    """
    
    def __init__(self, config):
        self.batch_size = config.batch_size
        self.max_workers = min(config.batch_size // 10, 4)  # Reasonable thread count
        self.chunk_delay = getattr(config, 'chunk_delay', 0.1)
        self.logger = logging.getLogger(__name__)
        self._stats = {
            'total_batches': 0,
            'successful_batches': 0,
            'failed_batches': 0,
            'total_records': 0,
            'successful_records': 0,
            'failed_records': 0,
            'start_time': None,
            'end_time': None
        }
        self._lock = threading.Lock()
    
    def process_in_batches(
        self, 
        data: List[Any], 
        processor_func: Callable[[List[Any]], Dict[str, int]],
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> Dict[str, Any]:
        """
        Process data in batches
        
        Args:
            data: List of data items to process
            processor_func: Function to process each batch
            progress_callback: Optional callback for progress updates
            
        Returns:
            Processing results summary
        """
        if not data:
            return {'processed': 0, 'successful': 0, 'failed': 0}
        
        self._reset_stats()
        self._stats['start_time'] = datetime.now()
        self._stats['total_records'] = len(data)
        
        self.logger.info(f"Starting batch processing of {len(data)} records")
        
        try:
            # Create batches
            batches = list(self._create_batches(data, self.batch_size))
            self._stats['total_batches'] = len(batches)
            
            self.logger.info(f"Created {len(batches)} batches of size {self.batch_size}")
            
            # Process batches
            results = self._process_batches(batches, processor_func, progress_callback)
            
            self._stats['end_time'] = datetime.now()
            self._log_final_stats()
            
            return results
            
        except Exception as e:
            self.logger.error(f"Batch processing failed: {e}")
            raise
    
    def process_parallel_batches(
        self,
        data: List[Any],
        processor_func: Callable[[List[Any]], Dict[str, int]],
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> Dict[str, Any]:
        """
        Process batches in parallel using thread pool
        
        Args:
            data: List of data items to process
            processor_func: Function to process each batch
            progress_callback: Optional callback for progress updates
            
        Returns:
            Processing results summary
        """
        if not data:
            return {'processed': 0, 'successful': 0, 'failed': 0}
        
        self._reset_stats()
        self._stats['start_time'] = datetime.now()
        self._stats['total_records'] = len(data)
        
        # Create batches
        batches = list(self._create_batches(data, self.batch_size))
        self._stats['total_batches'] = len(batches)
        
        self.logger.info(f"Starting parallel processing of {len(batches)} batches")
        
        results = {'processed': 0, 'successful': 0, 'failed': 0}
        
        try:
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                # Submit all batches
                future_to_batch = {
                    executor.submit(self._safe_process_batch, batch, processor_func): i 
                    for i, batch in enumerate(batches)
                }
                
                # Process completed batches
                for future in as_completed(future_to_batch):
                    batch_index = future_to_batch[future]
                    
                    try:
                        batch_result = future.result()
                        
                        # Aggregate results
                        with self._lock:
                            for key in results:
                                results[key] += batch_result.get(key, 0)
                            
                            self._stats['successful_batches'] += 1
                            self._stats['successful_records'] += batch_result.get('successful', 0)
                            self._stats['failed_records'] += batch_result.get('failed', 0)
                        
                        self.logger.debug(f"Batch {batch_index} completed: {batch_result}")
                        
                        # Progress callback
                        if progress_callback:
                            progress_callback(results['processed'], len(data))
                            
                    except Exception as e:
                        self.logger.error(f"Batch {batch_index} failed: {e}")
                        
                        with self._lock:
                            self._stats['failed_batches'] += 1
                            batch_size = len(batches[batch_index])
                            self._stats['failed_records'] += batch_size
                            results['failed'] += batch_size
            
            self._stats['end_time'] = datetime.now()
            self._log_final_stats()
            
            return results
            
        except Exception as e:
            self.logger.error(f"Parallel batch processing failed: {e}")
            raise
    
    def _create_batches(self, data: List[Any], batch_size: int) -> Iterator[List[Any]]:
        """Create batches from data"""
        for i in range(0, len(data), batch_size):
            yield data[i:i + batch_size]
    
    def _process_batches(
        self, 
        batches: List[List[Any]], 
        processor_func: Callable,
        progress_callback: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """Process batches sequentially"""
        results = {'processed': 0, 'successful': 0, 'failed': 0}
        
        for i, batch in enumerate(batches):
            try:
                batch_result = self._safe_process_batch(batch, processor_func)
                
                # Aggregate results
                for key in results:
                    results[key] += batch_result.get(key, 0)
                
                self._stats['successful_batches'] += 1
                self._stats['successful_records'] += batch_result.get('successful', 0)
                self._stats['failed_records'] += batch_result.get('failed', 0)
                
                self.logger.debug(f"Batch {i+1}/{len(batches)} completed: {batch_result}")
                
                # Progress callback
                if progress_callback:
                    progress_callback(results['processed'], self._stats['total_records'])
                
                # Brief pause between batches
                if i < len(batches) - 1 and self.chunk_delay > 0:
                    time.sleep(self.chunk_delay)
                    
            except Exception as e:
                self.logger.error(f"Batch {i+1} processing failed: {e}")
                
                self._stats['failed_batches'] += 1
                self._stats['failed_records'] += len(batch)
                results['failed'] += len(batch)
        
        return results
    
    def _safe_process_batch(
        self, 
        batch: List[Any], 
        processor_func: Callable
    ) -> Dict[str, int]:
        """Safely process a batch with error handling"""
        try:
            result = processor_func(batch)
            
            # Ensure result has required keys
            if not isinstance(result, dict):
                self.logger.warning("Processor function returned non-dict result")
                return {'processed': len(batch), 'successful': 0, 'failed': len(batch)}
            
            # Normalize result keys
            normalized = {
                'processed': len(batch),
                'successful': result.get('imported', result.get('successful', 0)),
                'failed': result.get('errors', result.get('failed', 0))
            }
            
            return normalized
            
        except Exception as e:
            self.logger.error(f"Batch processing error: {e}")
            return {'processed': len(batch), 'successful': 0, 'failed': len(batch)}
    
    def process_with_chunking(
        self,
        data: List[Any],
        chunk_processor: Callable[[Any], Dict[str, Any]],
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> Dict[str, Any]:
        """
        Process data items individually with chunking for memory management
        
        Args:
            data: List of data items
            chunk_processor: Function to process individual items
            progress_callback: Optional progress callback
            
        Returns:
            Processing results summary
        """
        results = {'processed': 0, 'successful': 0, 'failed': 0}
        chunk_size = 50  # Smaller chunks for individual processing
        
        self.logger.info(f"Starting chunked processing of {len(data)} items")
        
        for i in range(0, len(data), chunk_size):
            chunk = data[i:i + chunk_size]
            
            for item in chunk:
                try:
                    item_result = chunk_processor(item)
                    
                    results['processed'] += 1
                    if item_result.get('success', False):
                        results['successful'] += 1
                    else:
                        results['failed'] += 1
                        
                except Exception as e:
                    self.logger.error(f"Item processing failed: {e}")
                    results['processed'] += 1
                    results['failed'] += 1
            
            # Progress callback
            if progress_callback:
                progress_callback(results['processed'], len(data))
            
            # Memory management pause
            if i + chunk_size < len(data):
                time.sleep(0.01)  # Brief pause
        
        return results
    
    def _reset_stats(self):
        """Reset processing statistics"""
        self._stats = {
            'total_batches': 0,
            'successful_batches': 0,
            'failed_batches': 0,
            'total_records': 0,
            'successful_records': 0,
            'failed_records': 0,
            'start_time': None,
            'end_time': None
        }
    
    def _log_final_stats(self):
        """Log final processing statistics"""
        duration = None
        if self._stats['start_time'] and self._stats['end_time']:
            duration = self._stats['end_time'] - self._stats['start_time']
        
        self.logger.info("=" * 50)
        self.logger.info("BATCH PROCESSING STATISTICS")
        self.logger.info("=" * 50)
        self.logger.info(f"Total Records: {self._stats['total_records']}")
        self.logger.info(f"Total Batches: {self._stats['total_batches']}")
        self.logger.info(f"Successful Batches: {self._stats['successful_batches']}")
        self.logger.info(f"Failed Batches: {self._stats['failed_batches']}")
        self.logger.info(f"Successful Records: {self._stats['successful_records']}")
        self.logger.info(f"Failed Records: {self._stats['failed_records']}")
        
        if duration:
            self.logger.info(f"Processing Time: {duration}")
            
            # Calculate throughput
            if duration.total_seconds() > 0:
                throughput = self._stats['total_records'] / duration.total_seconds()
                self.logger.info(f"Throughput: {throughput:.2f} records/second")
        
        self.logger.info("=" * 50)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get current processing statistics"""
        with self._lock:
            return self._stats.copy()


class MemoryAwareBatchProcessor(BatchProcessor):
    """
    Memory-Aware Batch Processor
    ===========================
    
    Extended batch processor with memory monitoring
    and automatic batch size adjustment.
    """
    
    def __init__(self, config):
        super().__init__(config)
        self.memory_threshold = getattr(config, 'memory_threshold', 0.8)
        self.min_batch_size = max(1, self.batch_size // 10)
        self.max_batch_size = self.batch_size * 2
        self.current_batch_size = self.batch_size
    
    def _get_memory_usage(self) -> float:
        """Get current memory usage percentage"""
        try:
            import psutil
            return psutil.virtual_memory().percent / 100.0
        except ImportError:
            # Fallback - assume memory is fine
            return 0.5
    
    def _adjust_batch_size(self):
        """Adjust batch size based on memory usage"""
        memory_usage = self._get_memory_usage()
        
        if memory_usage > self.memory_threshold:
            # Reduce batch size
            new_size = max(self.min_batch_size, self.current_batch_size // 2)
            if new_size != self.current_batch_size:
                self.logger.info(f"Reducing batch size from {self.current_batch_size} to {new_size} (memory: {memory_usage:.1%})")
                self.current_batch_size = new_size
                
        elif memory_usage < self.memory_threshold * 0.7:
            # Increase batch size
            new_size = min(self.max_batch_size, int(self.current_batch_size * 1.5))
            if new_size != self.current_batch_size:
                self.logger.info(f"Increasing batch size from {self.current_batch_size} to {new_size} (memory: {memory_usage:.1%})")
                self.current_batch_size = new_size
    
    def _create_batches(self, data: List[Any], batch_size: int) -> Iterator[List[Any]]:
        """Create batches with memory-aware sizing"""
        i = 0
        while i < len(data):
            # Adjust batch size based on memory
            self._adjust_batch_size()
            
            end_idx = min(i + self.current_batch_size, len(data))
            yield data[i:end_idx]
            i = end_idx