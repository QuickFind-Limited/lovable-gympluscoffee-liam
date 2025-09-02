#!/usr/bin/env python3
"""
Progress Tracker
===============

Tracks and reports progress of import operations with real-time
updates, persistence, and detailed analytics.

Agent: Progress Monitoring Specialist
"""

import json
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from pathlib import Path
from dataclasses import dataclass, asdict
from collections import defaultdict


@dataclass
class OperationProgress:
    """Progress tracking for a single operation"""
    operation_id: str
    operation_type: str
    start_time: datetime
    end_time: Optional[datetime] = None
    total_records: int = 0
    processed_records: int = 0
    successful_records: int = 0
    failed_records: int = 0
    current_phase: str = "initializing"
    phases_completed: List[str] = None
    estimated_completion: Optional[datetime] = None
    throughput_per_second: float = 0.0
    error_rate: float = 0.0
    
    def __post_init__(self):
        if self.phases_completed is None:
            self.phases_completed = []
    
    @property
    def progress_percentage(self) -> float:
        """Calculate progress percentage"""
        if self.total_records == 0:
            return 0.0
        return (self.processed_records / self.total_records) * 100
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage"""
        if self.processed_records == 0:
            return 100.0
        return (self.successful_records / self.processed_records) * 100
    
    @property
    def is_completed(self) -> bool:
        """Check if operation is completed"""
        return self.end_time is not None
    
    @property
    def duration(self) -> timedelta:
        """Get operation duration"""
        end = self.end_time or datetime.now()
        return end - self.start_time
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'operation_id': self.operation_id,
            'operation_type': self.operation_type,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'total_records': self.total_records,
            'processed_records': self.processed_records,
            'successful_records': self.successful_records,
            'failed_records': self.failed_records,
            'current_phase': self.current_phase,
            'phases_completed': self.phases_completed,
            'estimated_completion': self.estimated_completion.isoformat() if self.estimated_completion else None,
            'throughput_per_second': self.throughput_per_second,
            'error_rate': self.error_rate,
            'progress_percentage': self.progress_percentage,
            'success_rate': self.success_rate,
            'is_completed': self.is_completed,
            'duration_seconds': self.duration.total_seconds()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'OperationProgress':
        """Create from dictionary"""
        return cls(
            operation_id=data['operation_id'],
            operation_type=data['operation_type'],
            start_time=datetime.fromisoformat(data['start_time']),
            end_time=datetime.fromisoformat(data['end_time']) if data.get('end_time') else None,
            total_records=data.get('total_records', 0),
            processed_records=data.get('processed_records', 0),
            successful_records=data.get('successful_records', 0),
            failed_records=data.get('failed_records', 0),
            current_phase=data.get('current_phase', 'initializing'),
            phases_completed=data.get('phases_completed', []),
            estimated_completion=datetime.fromisoformat(data['estimated_completion']) if data.get('estimated_completion') else None,
            throughput_per_second=data.get('throughput_per_second', 0.0),
            error_rate=data.get('error_rate', 0.0)
        )


class ProgressTracker:
    """
    Comprehensive Progress Tracker
    =============================
    
    Tracks multiple concurrent operations with real-time updates,
    persistence, and detailed progress analytics.
    """
    
    def __init__(self, config):
        self.config = config
        self.progress_file = Path(config.progress_file)
        self.progress_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Active operations
        self.active_operations: Dict[str, OperationProgress] = {}
        self.completed_operations: List[OperationProgress] = []
        
        # Thread safety
        self._lock = threading.Lock()
        
        # Progress callbacks
        self.progress_callbacks: List[Callable[[OperationProgress], None]] = []
        
        # Load existing progress
        self._load_progress()
        
        # Analytics
        self.analytics = {
            'total_operations': 0,
            'successful_operations': 0,
            'failed_operations': 0,
            'average_throughput': 0.0,
            'peak_throughput': 0.0,
            'total_records_processed': 0
        }
    
    def start_operation(
        self, 
        operation_id: str, 
        operation_type: str, 
        total_records: int = 0
    ) -> OperationProgress:
        """
        Start tracking a new operation
        
        Args:
            operation_id: Unique identifier for the operation
            operation_type: Type of operation (products, partners, etc.)
            total_records: Total number of records to process
            
        Returns:
            OperationProgress instance
        """
        with self._lock:
            if operation_id in self.active_operations:
                raise ValueError(f"Operation {operation_id} is already active")
            
            progress = OperationProgress(
                operation_id=operation_id,
                operation_type=operation_type,
                start_time=datetime.now(),
                total_records=total_records
            )
            
            self.active_operations[operation_id] = progress
            self.analytics['total_operations'] += 1
            
            # Save progress
            self._save_progress()
            
            # Notify callbacks
            self._notify_callbacks(progress)
            
            return progress
    
    def update_progress(
        self, 
        operation_id: str, 
        processed: int = None,
        successful: int = None,
        failed: int = None,
        total: int = None,
        phase: str = None
    ):
        """
        Update progress for an operation
        
        Args:
            operation_id: Operation identifier
            processed: Number of records processed
            successful: Number of successful records
            failed: Number of failed records
            total: Total records (if changed)
            phase: Current operation phase
        """
        with self._lock:
            if operation_id not in self.active_operations:
                raise ValueError(f"Operation {operation_id} not found")
            
            progress = self.active_operations[operation_id]
            
            # Update values
            if processed is not None:
                progress.processed_records = processed
            if successful is not None:
                progress.successful_records = successful
            if failed is not None:
                progress.failed_records = failed
            if total is not None:
                progress.total_records = total
            if phase is not None and phase != progress.current_phase:
                progress.phases_completed.append(progress.current_phase)
                progress.current_phase = phase
            
            # Calculate metrics
            self._calculate_metrics(progress)
            
            # Save progress
            self._save_progress()
            
            # Notify callbacks
            self._notify_callbacks(progress)
    
    def complete_operation(
        self, 
        operation_id: str, 
        final_stats: Dict[str, Any] = None
    ) -> OperationProgress:
        """
        Mark operation as completed
        
        Args:
            operation_id: Operation identifier
            final_stats: Final statistics
            
        Returns:
            Completed OperationProgress
        """
        with self._lock:
            if operation_id not in self.active_operations:
                raise ValueError(f"Operation {operation_id} not found")
            
            progress = self.active_operations[operation_id]
            progress.end_time = datetime.now()
            progress.phases_completed.append(progress.current_phase)
            progress.current_phase = "completed"
            
            # Update with final stats if provided
            if final_stats:
                if 'successful' in final_stats:
                    progress.successful_records = final_stats['successful']
                if 'failed' in final_stats:
                    progress.failed_records = final_stats['failed']
                if 'processed' in final_stats:
                    progress.processed_records = final_stats['processed']
            
            # Calculate final metrics
            self._calculate_metrics(progress)
            
            # Move to completed operations
            self.completed_operations.append(progress)
            del self.active_operations[operation_id]
            
            # Update analytics
            self._update_analytics(progress)
            
            # Save progress
            self._save_progress()
            
            # Notify callbacks
            self._notify_callbacks(progress)
            
            return progress
    
    def get_operation_progress(self, operation_id: str) -> Optional[OperationProgress]:
        """Get progress for specific operation"""
        with self._lock:
            if operation_id in self.active_operations:
                return self.active_operations[operation_id]
            
            # Check completed operations
            for progress in self.completed_operations:
                if progress.operation_id == operation_id:
                    return progress
            
            return None
    
    def get_all_active_operations(self) -> List[OperationProgress]:
        """Get all active operations"""
        with self._lock:
            return list(self.active_operations.values())
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get comprehensive progress summary
        
        Returns:
            Progress summary with analytics
        """
        with self._lock:
            active_ops = list(self.active_operations.values())
            
            # Calculate totals
            total_active = len(active_ops)
            total_records = sum(op.total_records for op in active_ops)
            processed_records = sum(op.processed_records for op in active_ops)
            successful_records = sum(op.successful_records for op in active_ops)
            failed_records = sum(op.failed_records for op in active_ops)
            
            # Calculate overall progress
            overall_progress = 0.0
            if total_records > 0:
                overall_progress = (processed_records / total_records) * 100
            
            # Calculate average throughput
            avg_throughput = 0.0
            if active_ops:
                avg_throughput = sum(op.throughput_per_second for op in active_ops) / len(active_ops)
            
            # Get operation details
            operation_details = []
            for op in active_ops:
                operation_details.append({
                    'id': op.operation_id,
                    'type': op.operation_type,
                    'progress': op.progress_percentage,
                    'phase': op.current_phase,
                    'throughput': op.throughput_per_second,
                    'eta': op.estimated_completion.isoformat() if op.estimated_completion else None
                })
            
            return {
                'timestamp': datetime.now().isoformat(),
                'active_operations': total_active,
                'completed_operations': len(self.completed_operations),
                'overall_progress': overall_progress,
                'total_records': total_records,
                'processed_records': processed_records,
                'successful_records': successful_records,
                'failed_records': failed_records,
                'average_throughput': avg_throughput,
                'operation_details': operation_details,
                'analytics': self.analytics
            }
    
    def add_progress_callback(self, callback: Callable[[OperationProgress], None]):
        """Add progress update callback"""
        self.progress_callbacks.append(callback)
    
    def remove_progress_callback(self, callback: Callable[[OperationProgress], None]):
        """Remove progress update callback"""
        if callback in self.progress_callbacks:
            self.progress_callbacks.remove(callback)
    
    def generate_progress_report(self, operation_id: str = None) -> Dict[str, Any]:
        """
        Generate detailed progress report
        
        Args:
            operation_id: Specific operation ID, or None for all operations
            
        Returns:
            Detailed progress report
        """
        with self._lock:
            if operation_id:
                progress = self.get_operation_progress(operation_id)
                if not progress:
                    return {'error': f'Operation {operation_id} not found'}
                
                return {
                    'operation': progress.to_dict(),
                    'phases': self._analyze_phases(progress),
                    'performance': self._analyze_performance(progress),
                    'recommendations': self._generate_recommendations(progress)
                }
            
            # All operations report
            all_ops = list(self.active_operations.values()) + self.completed_operations
            
            if not all_ops:
                return {'message': 'No operations found'}
            
            # Aggregate statistics
            by_type = defaultdict(list)
            for op in all_ops:
                by_type[op.operation_type].append(op)
            
            type_stats = {}
            for op_type, ops in by_type.items():
                type_stats[op_type] = {
                    'total_operations': len(ops),
                    'completed_operations': sum(1 for op in ops if op.is_completed),
                    'total_records': sum(op.total_records for op in ops),
                    'successful_records': sum(op.successful_records for op in ops),
                    'failed_records': sum(op.failed_records for op in ops),
                    'average_throughput': sum(op.throughput_per_second for op in ops) / len(ops) if ops else 0
                }
            
            return {
                'summary': self.get_summary(),
                'by_operation_type': type_stats,
                'recent_operations': [
                    op.to_dict() for op in sorted(
                        all_ops[-10:], 
                        key=lambda x: x.start_time, 
                        reverse=True
                    )
                ]
            }
    
    def _calculate_metrics(self, progress: OperationProgress):
        """Calculate operation metrics"""
        duration = progress.duration
        if duration.total_seconds() > 0:
            progress.throughput_per_second = progress.processed_records / duration.total_seconds()
            
            # Estimate completion time
            if progress.total_records > progress.processed_records and progress.throughput_per_second > 0:
                remaining_records = progress.total_records - progress.processed_records
                remaining_seconds = remaining_records / progress.throughput_per_second
                progress.estimated_completion = datetime.now() + timedelta(seconds=remaining_seconds)
        
        # Calculate error rate
        if progress.processed_records > 0:
            progress.error_rate = (progress.failed_records / progress.processed_records) * 100
    
    def _update_analytics(self, completed_progress: OperationProgress):
        """Update global analytics with completed operation"""
        if completed_progress.success_rate > 80:  # Consider 80%+ success rate as successful
            self.analytics['successful_operations'] += 1
        else:
            self.analytics['failed_operations'] += 1
        
        self.analytics['total_records_processed'] += completed_progress.processed_records
        
        # Update peak throughput
        if completed_progress.throughput_per_second > self.analytics['peak_throughput']:
            self.analytics['peak_throughput'] = completed_progress.throughput_per_second
        
        # Calculate average throughput
        total_ops = self.analytics['successful_operations'] + self.analytics['failed_operations']
        if total_ops > 0:
            all_completed = self.completed_operations
            total_throughput = sum(op.throughput_per_second for op in all_completed)
            self.analytics['average_throughput'] = total_throughput / len(all_completed) if all_completed else 0
    
    def _notify_callbacks(self, progress: OperationProgress):
        """Notify all registered callbacks"""
        for callback in self.progress_callbacks:
            try:
                callback(progress)
            except Exception as e:
                # Don't let callback errors break progress tracking
                pass
    
    def _save_progress(self):
        """Save progress to file"""
        try:
            progress_data = {
                'timestamp': datetime.now().isoformat(),
                'active_operations': {
                    op_id: progress.to_dict() 
                    for op_id, progress in self.active_operations.items()
                },
                'completed_operations': [
                    progress.to_dict() for progress in self.completed_operations[-50:]  # Keep last 50
                ],
                'analytics': self.analytics
            }
            
            with open(self.progress_file, 'w', encoding='utf-8') as f:
                json.dump(progress_data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            # Don't let save errors break progress tracking
            pass
    
    def _load_progress(self):
        """Load progress from file"""
        if not self.progress_file.exists():
            return
        
        try:
            with open(self.progress_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Load active operations
            for op_id, op_data in data.get('active_operations', {}).items():
                self.active_operations[op_id] = OperationProgress.from_dict(op_data)
            
            # Load completed operations
            for op_data in data.get('completed_operations', []):
                self.completed_operations.append(OperationProgress.from_dict(op_data))
            
            # Load analytics
            self.analytics.update(data.get('analytics', {}))
            
        except Exception as e:
            # Don't let load errors break initialization
            pass
    
    def _analyze_phases(self, progress: OperationProgress) -> Dict[str, Any]:
        """Analyze operation phases"""
        return {
            'current_phase': progress.current_phase,
            'completed_phases': progress.phases_completed,
            'phase_count': len(progress.phases_completed)
        }
    
    def _analyze_performance(self, progress: OperationProgress) -> Dict[str, Any]:
        """Analyze operation performance"""
        return {
            'throughput': progress.throughput_per_second,
            'success_rate': progress.success_rate,
            'error_rate': progress.error_rate,
            'duration_seconds': progress.duration.total_seconds(),
            'estimated_completion': progress.estimated_completion.isoformat() if progress.estimated_completion else None
        }
    
    def _generate_recommendations(self, progress: OperationProgress) -> List[str]:
        """Generate recommendations based on progress"""
        recommendations = []
        
        if progress.throughput_per_second < 1.0:
            recommendations.append("Consider increasing batch size or optimizing data processing")
        
        if progress.error_rate > 10:
            recommendations.append("High error rate detected - review data quality and validation")
        
        if progress.duration.total_seconds() > 3600:  # 1 hour
            recommendations.append("Long-running operation detected - consider parallel processing")
        
        if not recommendations:
            recommendations.append("Operation performing within normal parameters")
        
        return recommendations