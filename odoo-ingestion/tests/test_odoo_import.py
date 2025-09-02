#!/usr/bin/env python3
"""
Test Suite for Odoo Import System
=================================

Comprehensive tests for all import functionality including
connection management, data processing, and error handling.

Agent: Testing Specialist
"""

import pytest
import json
import tempfile
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
from datetime import datetime
import xmlrpc.client

# Import modules to test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from connection_manager import OdooConnectionManager, OdooConnection, ConnectionConfig
from data_models import ProductTemplate, Partner, SaleOrder, ImportProgress
from batch_processor import BatchProcessor
from error_handler import ErrorHandler, ErrorRecord, ErrorCategory, ErrorSeverity
from progress_tracker import ProgressTracker, OperationProgress
from odoo_import import OdooImporter, ImportConfig, load_config_from_env


class TestOdooConnection:
    """Test Odoo connection functionality"""
    
    def setup_method(self):
        self.config = ConnectionConfig(
            url="https://test.odoo.com",
            db="test_db",
            username="test_user",
            password="test_pass",
            timeout=30.0,
            max_retries=3,
            retry_delay=1.0
        )
    
    @patch('xmlrpc.client.ServerProxy')
    def test_successful_authentication(self, mock_server_proxy):
        """Test successful authentication"""
        # Setup mocks
        mock_common = Mock()
        mock_common.version.return_value = {'server_version': '17.0'}
        mock_common.authenticate.return_value = 123
        
        mock_models = Mock()
        
        mock_server_proxy.side_effect = [mock_common, mock_models]
        
        # Test authentication
        connection = OdooConnection(self.config)
        result = connection.authenticate()
        
        assert result is True
        assert connection._uid == 123
        assert connection._authenticated is True
    
    @patch('xmlrpc.client.ServerProxy')
    def test_authentication_failure(self, mock_server_proxy):
        """Test authentication failure"""
        mock_common = Mock()
        mock_common.version.return_value = {'server_version': '17.0'}
        mock_common.authenticate.return_value = False
        
        mock_server_proxy.return_value = mock_common
        
        connection = OdooConnection(self.config)
        result = connection.authenticate()
        
        assert result is False
        assert connection._authenticated is False
    
    @patch('xmlrpc.client.ServerProxy')
    def test_execute_kw_success(self, mock_server_proxy):
        """Test successful execute_kw call"""
        # Setup authenticated connection
        mock_common = Mock()
        mock_common.version.return_value = {'server_version': '17.0'}
        mock_common.authenticate.return_value = 123
        
        mock_models = Mock()
        mock_models.execute_kw.return_value = [{'id': 1, 'name': 'Test Product'}]
        
        mock_server_proxy.side_effect = [mock_common, mock_models]
        
        connection = OdooConnection(self.config)
        connection.authenticate()
        
        # Test execute_kw
        result = connection.execute_kw('product.product', 'search_read', [[]], {'fields': ['name']})
        
        assert result == [{'id': 1, 'name': 'Test Product'}]
        mock_models.execute_kw.assert_called_once()
    
    @patch('xmlrpc.client.ServerProxy')
    def test_execute_kw_with_retry(self, mock_server_proxy):
        """Test execute_kw with retry on connection error"""
        mock_common = Mock()
        mock_common.version.return_value = {'server_version': '17.0'}
        mock_common.authenticate.return_value = 123
        
        mock_models = Mock()
        # First call fails, second succeeds
        mock_models.execute_kw.side_effect = [
            ConnectionError("Network error"),
            [{'id': 1, 'name': 'Test Product'}]
        ]
        
        mock_server_proxy.side_effect = [mock_common, mock_models] * 2  # For retry
        
        connection = OdooConnection(self.config)
        connection.authenticate()
        
        result = connection.execute_kw('product.product', 'search_read', [[]], {'fields': ['name']})
        
        assert result == [{'id': 1, 'name': 'Test Product'}]


class TestDataModels:
    """Test data model functionality"""
    
    def test_product_template_creation(self):
        """Test ProductTemplate creation and conversion"""
        template = ProductTemplate(
            name="Test Product",
            categ_id=1,
            list_price=100.0,
            standard_price=50.0,
            description="Test description"
        )
        
        odoo_vals = template.to_odoo_vals()
        
        assert odoo_vals['name'] == "Test Product"
        assert odoo_vals['categ_id'] == 1
        assert odoo_vals['list_price'] == 100.0
        assert odoo_vals['description'] == "Test description"
        assert odoo_vals['type'] == 'product'
    
    def test_product_template_from_json(self):
        """Test creating ProductTemplate from JSON data"""
        json_data = {
            'name': 'JSON Product',
            'sku': 'JSON001',
            'list_price': 75.0,
            'standard_cost': 30.0,
            'description': 'From JSON',
            'status': 'active'
        }
        
        template = ProductTemplate.from_json_data(json_data, category_id=2)
        
        assert template.name == 'JSON Product'
        assert template.categ_id == 2
        assert template.list_price == 75.0
        assert template.standard_price == 30.0
        assert template.description == 'From JSON'
        assert template.active is True
    
    def test_partner_creation(self):
        """Test Partner creation and conversion"""
        partner = Partner(
            name="Test Customer",
            email="test@example.com",
            phone="+1234567890",
            is_company=False,
            customer_rank=1
        )
        
        odoo_vals = partner.to_odoo_vals()
        
        assert odoo_vals['name'] == "Test Customer"
        assert odoo_vals['email'] == "test@example.com"
        assert odoo_vals['customer_rank'] == 1
        assert odoo_vals['is_company'] is False
    
    def test_import_progress_tracking(self):
        """Test ImportProgress functionality"""
        start_time = datetime.now()
        progress = ImportProgress(
            operation_id="test_op_001",
            operation_type="products",
            start_time=start_time,
            total_records=100
        )
        
        # Test initial state
        assert progress.progress_percentage == 0.0
        assert progress.is_completed is False
        
        # Update progress
        progress.processed_records = 50
        progress.successful_records = 45
        progress.failed_records = 5
        
        assert progress.progress_percentage == 50.0
        assert progress.success_rate == 90.0
        
        # Complete progress
        progress.end_time = datetime.now()
        assert progress.is_completed is True


class TestBatchProcessor:
    """Test batch processing functionality"""
    
    def setup_method(self):
        self.config = Mock()
        self.config.batch_size = 10
        self.config.chunk_delay = 0.01
        self.processor = BatchProcessor(self.config)
    
    def test_batch_creation(self):
        """Test batch creation from data"""
        data = list(range(25))  # 25 items
        batches = list(self.processor._create_batches(data, batch_size=10))
        
        assert len(batches) == 3
        assert len(batches[0]) == 10
        assert len(batches[1]) == 10
        assert len(batches[2]) == 5
    
    def test_process_in_batches(self):
        """Test processing data in batches"""
        data = [{'id': i, 'name': f'Item {i}'} for i in range(15)]
        
        def mock_processor(batch):
            return {'imported': len(batch), 'errors': 0}
        
        results = self.processor.process_in_batches(data, mock_processor)
        
        assert results['successful'] == 15
        assert results['failed'] == 0
        assert results['processed'] == 15
    
    def test_process_with_errors(self):
        """Test batch processing with errors"""
        data = [{'id': i, 'name': f'Item {i}'} for i in range(15)]
        
        def mock_processor_with_errors(batch):
            # Simulate some failures
            errors = min(2, len(batch))
            return {'imported': len(batch) - errors, 'errors': errors}
        
        results = self.processor.process_in_batches(data, mock_processor_with_errors)
        
        assert results['successful'] > 0
        assert results['failed'] > 0
        assert results['successful'] + results['failed'] == results['processed']


class TestErrorHandler:
    """Test error handling functionality"""
    
    def setup_method(self):
        self.config = Mock()
        self.config.error_log_file = "test_errors.log"
        self.config.failed_records_dir = "test_failed_records"
        self.config.max_retries = 3
        
        with patch('pathlib.Path.mkdir'), patch('pathlib.Path.exists', return_value=False):
            self.error_handler = ErrorHandler(self.config)
    
    def test_log_error(self):
        """Test error logging"""
        with patch.object(self.error_handler, '_log_to_file'), \
             patch.object(self.error_handler, '_log_to_console'), \
             patch.object(self.error_handler, '_save_failed_record'):
            
            error_id = self.error_handler.log_error(
                operation="test_operation",
                error_message="Test error",
                error_details="Detailed error info",
                severity=ErrorSeverity.HIGH,
                category=ErrorCategory.VALIDATION
            )
            
            assert error_id.startswith("test_operation_")
            assert len(self.error_handler.error_records) == 1
            
            error_record = self.error_handler.error_records[0]
            assert error_record.operation == "test_operation"
            assert error_record.severity == ErrorSeverity.HIGH
            assert error_record.error_category == ErrorCategory.VALIDATION
    
    def test_categorize_odoo_error(self):
        """Test Odoo error categorization"""
        test_cases = [
            ("Access Denied: Invalid credentials", ErrorCategory.AUTHENTICATION),
            ("ValidationError: Required field missing", ErrorCategory.VALIDATION),
            ("Permission denied for model", ErrorCategory.PERMISSION),
            ("Connection timeout", ErrorCategory.CONNECTION),
            ("Duplicate key constraint", ErrorCategory.DATA_INTEGRITY),
            ("Internal Server Error", ErrorCategory.SERVER_ERROR),
            ("Unknown error message", ErrorCategory.UNKNOWN)
        ]
        
        for error_msg, expected_category in test_cases:
            result = self.error_handler.categorize_odoo_error(error_msg)
            assert result == expected_category
    
    def test_should_retry_error(self):
        """Test retry logic for different error types"""
        # Connection error - should retry
        conn_error = ErrorRecord(
            timestamp=datetime.now(),
            operation="test",
            error_category=ErrorCategory.CONNECTION,
            severity=ErrorSeverity.MEDIUM,
            error_message="Connection failed",
            error_details="Network timeout",
            data_context={}
        )
        assert self.error_handler.should_retry_error(conn_error) is True
        
        # Validation error - should not retry
        validation_error = ErrorRecord(
            timestamp=datetime.now(),
            operation="test",
            error_category=ErrorCategory.VALIDATION,
            severity=ErrorSeverity.MEDIUM,
            error_message="Validation failed",
            error_details="Invalid data",
            data_context={}
        )
        assert self.error_handler.should_retry_error(validation_error) is False
        
        # Max retries exceeded - should not retry
        conn_error.retry_count = 5
        assert self.error_handler.should_retry_error(conn_error) is False


class TestProgressTracker:
    """Test progress tracking functionality"""
    
    def setup_method(self):
        self.config = Mock()
        self.config.progress_file = "test_progress.json"
        
        with patch('pathlib.Path.mkdir'), patch('pathlib.Path.exists', return_value=False):
            self.tracker = ProgressTracker(self.config)
    
    def test_start_operation(self):
        """Test starting operation tracking"""
        with patch.object(self.tracker, '_save_progress'):
            progress = self.tracker.start_operation("op001", "products", total_records=100)
            
            assert progress.operation_id == "op001"
            assert progress.operation_type == "products"
            assert progress.total_records == 100
            assert progress.progress_percentage == 0.0
            assert "op001" in self.tracker.active_operations
    
    def test_update_progress(self):
        """Test updating operation progress"""
        with patch.object(self.tracker, '_save_progress'):
            # Start operation
            self.tracker.start_operation("op001", "products", total_records=100)
            
            # Update progress
            self.tracker.update_progress("op001", processed=50, successful=45, failed=5)
            
            progress = self.tracker.active_operations["op001"]
            assert progress.processed_records == 50
            assert progress.successful_records == 45
            assert progress.failed_records == 5
            assert progress.progress_percentage == 50.0
    
    def test_complete_operation(self):
        """Test completing an operation"""
        with patch.object(self.tracker, '_save_progress'):
            # Start and update operation
            self.tracker.start_operation("op001", "products", total_records=100)
            self.tracker.update_progress("op001", processed=100, successful=95, failed=5)
            
            # Complete operation
            completed = self.tracker.complete_operation("op001")
            
            assert completed.is_completed is True
            assert completed.current_phase == "completed"
            assert "op001" not in self.tracker.active_operations
            assert len(self.tracker.completed_operations) == 1


class TestOdooImporter:
    """Test main Odoo importer functionality"""
    
    def setup_method(self):
        self.config = ImportConfig(
            url="https://test.odoo.com",
            db="test_db",
            username="test_user",
            password="test_pass",
            batch_size=10
        )
    
    @patch('odoo_import.OdooConnectionManager')
    @patch('odoo_import.BatchProcessor')
    @patch('odoo_import.ErrorHandler')
    @patch('odoo_import.ProgressTracker')
    def test_importer_initialization(self, mock_progress, mock_error, mock_batch, mock_conn):
        """Test importer initialization"""
        with patch('pathlib.Path.mkdir'):
            importer = OdooImporter(self.config)
            
            assert importer.config == self.config
            assert mock_conn.called
            assert mock_batch.called
            assert mock_error.called
            assert mock_progress.called
    
    def test_load_json_data(self):
        """Test loading JSON data"""
        test_data = {
            "products": [
                {"sku": "TEST001", "name": "Test Product 1"},
                {"sku": "TEST002", "name": "Test Product 2"}
            ]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(test_data, f)
            temp_file = f.name
        
        try:
            with patch('pathlib.Path.mkdir'):
                importer = OdooImporter(self.config)
                loaded_data = importer._load_json_data(temp_file)
                
                assert loaded_data == test_data
                assert len(loaded_data['products']) == 2
        finally:
            Path(temp_file).unlink()
    
    def test_group_products_by_template(self):
        """Test grouping products by template"""
        products = [
            {"name": "Test Product", "category": "hoodies", "color": "Black", "size": "S"},
            {"name": "Test Product", "category": "hoodies", "color": "Black", "size": "M"},
            {"name": "Other Product", "category": "tshirts", "color": "White", "size": "L"}
        ]
        
        with patch('pathlib.Path.mkdir'):
            importer = OdooImporter(self.config)
            grouped = importer._group_products_by_template(products)
            
            assert len(grouped) == 2
            assert len(grouped["Test Product_hoodies"]) == 2
            assert len(grouped["Other Product_tshirts"]) == 1


class TestConfigLoading:
    """Test configuration loading"""
    
    @patch.dict('os.environ', {
        'ODOO_URL': 'https://test.odoo.com',
        'ODOO_DB': 'test_db',
        'ODOO_USERNAME': 'test_user',
        'ODOO_PASSWORD': 'test_pass',
        'BATCH_SIZE': '50'
    })
    def test_load_config_from_env(self):
        """Test loading configuration from environment"""
        with patch('dotenv.load_dotenv'):
            config = load_config_from_env()
            
            assert config.url == 'https://test.odoo.com'
            assert config.db == 'test_db'
            assert config.username == 'test_user'
            assert config.password == 'test_pass'
            assert config.batch_size == 50


# Integration Tests
class TestIntegration:
    """Integration tests for complete workflows"""
    
    def setup_method(self):
        self.config = ImportConfig(
            url="https://test.odoo.com",
            db="test_db", 
            username="test_user",
            password="test_pass"
        )
    
    @patch('xmlrpc.client.ServerProxy')
    def test_complete_product_import_workflow(self, mock_server_proxy):
        """Test complete product import workflow"""
        # Setup mocks for successful import
        mock_common = Mock()
        mock_common.version.return_value = {'server_version': '17.0'}
        mock_common.authenticate.return_value = 123
        
        mock_models = Mock()
        mock_models.execute_kw.side_effect = [
            [1],  # Category search
            2,    # Category create
            [],   # Template search
            1,    # Template create
            [1],  # Product search for inventory
        ]
        
        mock_server_proxy.side_effect = [mock_common, mock_models]
        
        # Test data
        test_data = {
            "categories": ["hoodies"],
            "products": [{
                "sku": "TEST001",
                "name": "Test Hoodie",
                "category": "hoodies", 
                "list_price": 75.0,
                "standard_cost": 30.0,
                "description": "Test product",
                "status": "active",
                "inventory_on_hand": 10
            }]
        }
        
        # Create temp file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(test_data, f)
            temp_file = f.name
        
        try:
            with patch('pathlib.Path.mkdir'):
                importer = OdooImporter(self.config)
                
                with patch.object(importer, '_log_final_statistics'):
                    results = importer.import_product_data(temp_file)
                
                # Verify results structure
                assert 'categories' in results
                assert 'products' in results
                assert 'inventory' in results
                assert 'statistics' in results
                
        finally:
            Path(temp_file).unlink()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])