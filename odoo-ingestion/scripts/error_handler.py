#!/usr/bin/env python3
"""
Error Handler
============

Comprehensive error handling and recovery system for Odoo import operations.
Handles logging, retry logic, data validation, and error reporting.

Agent: Error Management Specialist
"""

import logging
import json
import traceback
from datetime import datetime
from typing import Dict, List, Any, Optional, Union
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum
import pickle


class ErrorSeverity(Enum):
    """Error severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Error categories"""
    VALIDATION = "validation"
    CONNECTION = "connection"
    AUTHENTICATION = "authentication"
    PERMISSION = "permission"
    DATA_INTEGRITY = "data_integrity"
    SERVER_ERROR = "server_error"
    TIMEOUT = "timeout"
    UNKNOWN = "unknown"


@dataclass
class ErrorRecord:
    """Individual error record"""
    timestamp: datetime
    operation: str
    error_category: ErrorCategory
    severity: ErrorSeverity
    error_message: str
    error_details: str
    data_context: Dict[str, Any]
    stack_trace: Optional[str] = None
    retry_count: int = 0
    resolved: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'timestamp': self.timestamp.isoformat(),
            'operation': self.operation,
            'error_category': self.error_category.value,
            'severity': self.severity.value,
            'error_message': self.error_message,
            'error_details': self.error_details,
            'data_context': self.data_context,
            'stack_trace': self.stack_trace,
            'retry_count': self.retry_count,
            'resolved': self.resolved
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ErrorRecord':
        """Create ErrorRecord from dictionary"""
        return cls(
            timestamp=datetime.fromisoformat(data['timestamp']),
            operation=data['operation'],
            error_category=ErrorCategory(data['error_category']),
            severity=ErrorSeverity(data['severity']),
            error_message=data['error_message'],
            error_details=data['error_details'],
            data_context=data['data_context'],
            stack_trace=data.get('stack_trace'),
            retry_count=data.get('retry_count', 0),
            resolved=data.get('resolved', False)
        )


class ErrorHandler:
    """
    Comprehensive Error Handler
    ==========================
    
    Manages error logging, categorization, recovery strategies,
    and reporting for Odoo import operations.
    """
    
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Error storage
        self.error_records: List[ErrorRecord] = []
        self.error_log_file = Path(config.error_log_file)
        self.failed_records_dir = Path(config.failed_records_dir)
        
        # Create directories
        self.error_log_file.parent.mkdir(parents=True, exist_ok=True)
        self.failed_records_dir.mkdir(parents=True, exist_ok=True)
        
        # Error statistics
        self.error_stats = {
            'total_errors': 0,
            'errors_by_category': {},
            'errors_by_severity': {},
            'retry_attempts': 0,
            'resolved_errors': 0
        }
        
        # Load existing errors
        self._load_existing_errors()
    
    def log_error(
        self, 
        operation: str, 
        error_message: str, 
        error_details: str = "",
        data_context: Dict[str, Any] = None,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        category: ErrorCategory = ErrorCategory.UNKNOWN
    ) -> str:
        """
        Log an error with full context
        
        Args:
            operation: Operation that failed
            error_message: Brief error description
            error_details: Detailed error information
            data_context: Relevant data context
            severity: Error severity level
            category: Error category
            
        Returns:
            Error ID for tracking
        """
        if data_context is None:
            data_context = {}
        
        # Create error record
        error_record = ErrorRecord(
            timestamp=datetime.now(),
            operation=operation,
            error_category=category,
            severity=severity,
            error_message=error_message,
            error_details=error_details,
            data_context=data_context,
            stack_trace=traceback.format_exc() if traceback.format_exc().strip() != "NoneType: None" else None
        )
        
        # Store error
        self.error_records.append(error_record)
        error_id = f"{operation}_{error_record.timestamp.strftime('%Y%m%d_%H%M%S')}"
        
        # Update statistics
        self._update_error_stats(error_record)
        
        # Log to file and console
        self._log_to_file(error_record, error_id)
        self._log_to_console(error_record, severity)
        
        # Save failed record data
        self._save_failed_record(error_id, data_context)
        
        return error_id
    
    def log_validation_error(
        self, 
        operation: str, 
        field_name: str, 
        field_value: Any, 
        validation_message: str,
        record_data: Dict[str, Any] = None
    ) -> str:
        """Log data validation error"""
        return self.log_error(
            operation=operation,
            error_message=f"Validation failed for field '{field_name}'",
            error_details=f"Value: {field_value}, Validation: {validation_message}",
            data_context=record_data or {},
            severity=ErrorSeverity.MEDIUM,
            category=ErrorCategory.VALIDATION
        )
    
    def log_connection_error(
        self, 
        operation: str, 
        connection_details: str,
        retry_count: int = 0
    ) -> str:
        """Log connection-related error"""
        severity = ErrorSeverity.HIGH if retry_count > 2 else ErrorSeverity.MEDIUM
        
        return self.log_error(
            operation=operation,
            error_message="Connection failed",
            error_details=connection_details,
            data_context={'retry_count': retry_count},
            severity=severity,
            category=ErrorCategory.CONNECTION
        )
    
    def log_critical_error(
        self, 
        operation: str, 
        error_details: str,
        data_context: Dict[str, Any] = None
    ) -> str:
        """Log critical system error"""
        return self.log_error(
            operation=operation,
            error_message="Critical system error",
            error_details=error_details,
            data_context=data_context or {},
            severity=ErrorSeverity.CRITICAL,
            category=ErrorCategory.SERVER_ERROR
        )
    
    def categorize_odoo_error(self, error_message: str) -> ErrorCategory:
        """
        Categorize Odoo-specific errors
        
        Args:
            error_message: Error message from Odoo
            
        Returns:
            Appropriate error category
        """
        error_lower = error_message.lower()
        
        # Authentication errors
        if any(term in error_lower for term in ['access denied', 'authentication', 'login']):
            return ErrorCategory.AUTHENTICATION
        
        # Permission errors
        if any(term in error_lower for term in ['permission', 'access rights', 'forbidden']):
            return ErrorCategory.PERMISSION
        
        # Validation errors
        if any(term in error_lower for term in ['validation', 'constraint', 'required field']):
            return ErrorCategory.VALIDATION
        
        # Connection errors
        if any(term in error_lower for term in ['connection', 'network', 'timeout', 'unreachable']):
            return ErrorCategory.CONNECTION
        
        # Data integrity errors
        if any(term in error_lower for term in ['duplicate', 'unique constraint', 'foreign key']):
            return ErrorCategory.DATA_INTEGRITY
        
        # Server errors
        if any(term in error_lower for term in ['server error', 'internal error', '500']):
            return ErrorCategory.SERVER_ERROR
        
        return ErrorCategory.UNKNOWN
    
    def should_retry_error(self, error_record: ErrorRecord) -> bool:
        """
        Determine if an error should be retried
        
        Args:
            error_record: Error record to evaluate
            
        Returns:
            True if error should be retried
        """
        # Don't retry if already retried too many times
        if error_record.retry_count >= self.config.max_retries:
            return False
        
        # Retry categories
        retryable_categories = {
            ErrorCategory.CONNECTION,
            ErrorCategory.TIMEOUT,
            ErrorCategory.SERVER_ERROR
        }
        
        # Don't retry validation or permission errors
        non_retryable_categories = {
            ErrorCategory.VALIDATION,
            ErrorCategory.AUTHENTICATION,
            ErrorCategory.PERMISSION,
            ErrorCategory.DATA_INTEGRITY
        }
        
        if error_record.error_category in non_retryable_categories:
            return False
        
        if error_record.error_category in retryable_categories:
            return True
        
        # For unknown errors, retry once
        return error_record.retry_count == 0
    
    def get_recovery_strategy(self, error_record: ErrorRecord) -> Dict[str, Any]:
        """
        Get recommended recovery strategy for an error
        
        Args:
            error_record: Error record to analyze
            
        Returns:
            Recovery strategy recommendations
        """
        strategy = {
            'action': 'none',
            'description': 'No automatic recovery available',
            'manual_steps': []
        }
        
        if error_record.error_category == ErrorCategory.VALIDATION:
            strategy.update({
                'action': 'data_correction',
                'description': 'Fix data validation issues',
                'manual_steps': [
                    'Review data context for invalid values',
                    'Correct field formats and constraints',
                    'Verify required fields are present'
                ]
            })
        
        elif error_record.error_category == ErrorCategory.CONNECTION:
            strategy.update({
                'action': 'retry_with_backoff',
                'description': 'Retry with exponential backoff',
                'manual_steps': [
                    'Check network connectivity',
                    'Verify Odoo server status',
                    'Review firewall settings'
                ]
            })
        
        elif error_record.error_category == ErrorCategory.AUTHENTICATION:
            strategy.update({
                'action': 'reauth',
                'description': 'Re-authenticate with Odoo',
                'manual_steps': [
                    'Verify credentials are correct',
                    'Check user account status',
                    'Review database access permissions'
                ]
            })
        
        elif error_record.error_category == ErrorCategory.PERMISSION:
            strategy.update({
                'action': 'permission_review',
                'description': 'Review and adjust permissions',
                'manual_steps': [
                    'Check user access rights in Odoo',
                    'Verify model permissions',
                    'Contact system administrator'
                ]
            })
        
        elif error_record.error_category == ErrorCategory.DATA_INTEGRITY:
            strategy.update({
                'action': 'data_cleanup',
                'description': 'Clean up data integrity issues',
                'manual_steps': [
                    'Check for duplicate records',
                    'Verify foreign key references',
                    'Review unique constraints'
                ]
            })
        
        return strategy
    
    def generate_error_report(self) -> Dict[str, Any]:
        """
        Generate comprehensive error report
        
        Returns:
            Detailed error report
        """
        # Calculate error statistics
        total_errors = len(self.error_records)
        if total_errors == 0:
            return {'message': 'No errors recorded'}
        
        # Group errors by category and severity
        by_category = {}
        by_severity = {}
        by_operation = {}
        
        for error in self.error_records:
            # By category
            cat = error.error_category.value
            by_category[cat] = by_category.get(cat, 0) + 1
            
            # By severity
            sev = error.severity.value
            by_severity[sev] = by_severity.get(sev, 0) + 1
            
            # By operation
            op = error.operation
            by_operation[op] = by_operation.get(op, 0) + 1
        
        # Find most common errors
        most_common_category = max(by_category.items(), key=lambda x: x[1])
        most_common_operation = max(by_operation.items(), key=lambda x: x[1])
        
        # Recent errors (last 10)
        recent_errors = sorted(
            self.error_records, 
            key=lambda x: x.timestamp, 
            reverse=True
        )[:10]
        
        return {
            'summary': {
                'total_errors': total_errors,
                'resolved_errors': sum(1 for e in self.error_records if e.resolved),
                'unresolved_errors': sum(1 for e in self.error_records if not e.resolved),
                'most_common_category': most_common_category[0],
                'most_common_operation': most_common_operation[0]
            },
            'statistics': {
                'by_category': by_category,
                'by_severity': by_severity,
                'by_operation': by_operation
            },
            'recent_errors': [
                {
                    'timestamp': error.timestamp.isoformat(),
                    'operation': error.operation,
                    'category': error.error_category.value,
                    'severity': error.severity.value,
                    'message': error.error_message
                }
                for error in recent_errors
            ],
            'recommendations': self._generate_recommendations()
        }
    
    def export_failed_records(self, output_file: str) -> Dict[str, Any]:
        """
        Export failed records for manual review
        
        Args:
            output_file: Output file path
            
        Returns:
            Export summary
        """
        failed_data = {
            'export_timestamp': datetime.now().isoformat(),
            'total_errors': len(self.error_records),
            'errors': [error.to_dict() for error in self.error_records]
        }
        
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(failed_data, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"Exported {len(self.error_records)} error records to {output_file}")
        
        return {
            'exported_errors': len(self.error_records),
            'output_file': str(output_path),
            'file_size': output_path.stat().st_size
        }
    
    def _update_error_stats(self, error_record: ErrorRecord):
        """Update error statistics"""
        self.error_stats['total_errors'] += 1
        
        # By category
        cat = error_record.error_category.value
        if cat not in self.error_stats['errors_by_category']:
            self.error_stats['errors_by_category'][cat] = 0
        self.error_stats['errors_by_category'][cat] += 1
        
        # By severity
        sev = error_record.severity.value
        if sev not in self.error_stats['errors_by_severity']:
            self.error_stats['errors_by_severity'][sev] = 0
        self.error_stats['errors_by_severity'][sev] += 1
    
    def _log_to_file(self, error_record: ErrorRecord, error_id: str):
        """Log error to file"""
        log_entry = {
            'error_id': error_id,
            **error_record.to_dict()
        }
        
        with open(self.error_log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry) + '\n')
    
    def _log_to_console(self, error_record: ErrorRecord, severity: ErrorSeverity):
        """Log error to console with appropriate level"""
        message = f"[{error_record.operation}] {error_record.error_message}"
        
        if severity == ErrorSeverity.CRITICAL:
            self.logger.critical(message)
        elif severity == ErrorSeverity.HIGH:
            self.logger.error(message)
        elif severity == ErrorSeverity.MEDIUM:
            self.logger.warning(message)
        else:
            self.logger.info(message)
        
        # Log details in debug mode
        if error_record.error_details:
            self.logger.debug(f"Error details: {error_record.error_details}")
    
    def _save_failed_record(self, error_id: str, data_context: Dict[str, Any]):
        """Save failed record data for manual review"""
        if not data_context:
            return
        
        record_file = self.failed_records_dir / f"{error_id}.json"
        
        with open(record_file, 'w', encoding='utf-8') as f:
            json.dump({
                'error_id': error_id,
                'timestamp': datetime.now().isoformat(),
                'data': data_context
            }, f, indent=2, ensure_ascii=False)
    
    def _load_existing_errors(self):
        """Load existing errors from log file"""
        if not self.error_log_file.exists():
            return
        
        try:
            with open(self.error_log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        try:
                            error_data = json.loads(line)
                            error_record = ErrorRecord.from_dict(error_data)
                            self.error_records.append(error_record)
                        except json.JSONDecodeError:
                            continue
                            
            self.logger.info(f"Loaded {len(self.error_records)} existing error records")
            
        except Exception as e:
            self.logger.warning(f"Could not load existing errors: {e}")
    
    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on error patterns"""
        recommendations = []
        
        # Analyze error patterns
        category_counts = self.error_stats.get('errors_by_category', {})
        
        if category_counts.get('validation', 0) > 5:
            recommendations.append("Consider implementing data validation before import")
        
        if category_counts.get('connection', 0) > 3:
            recommendations.append("Review network connectivity and server stability")
        
        if category_counts.get('authentication', 0) > 1:
            recommendations.append("Verify Odoo credentials and user permissions")
        
        if category_counts.get('data_integrity', 0) > 2:
            recommendations.append("Review data for duplicates and constraint violations")
        
        if not recommendations:
            recommendations.append("No specific recommendations at this time")
        
        return recommendations