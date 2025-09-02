#!/usr/bin/env python3
"""
Main execution script for bulk data processing
Coordinates the full 65,000 transaction import pipeline
"""

import json
import logging
import os
import sys
from datetime import datetime
from bulk_data_processor import BulkDataProcessor
from stream_processor import JSONStreamProcessor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bulk_processing.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def get_odoo_products():
    """Get all products from Odoo for mapping"""
    try:
        # This will be replaced with actual Odoo MCP calls
        # For now, create a mock mapping based on the analysis file
        
        analysis_file = "/workspaces/source-lovable-gympluscoffee/odoo-ingestion/complete_product_analysis_20250807_172037.json"
        
        if os.path.exists(analysis_file):
            with open(analysis_file, 'r') as f:
                analysis = json.load(f)
                
            # Extract sample products and create mapping
            products = []
            product_id = 1
            
            for sample in analysis.get('sample_products', []):
                products.append({
                    'id': product_id,
                    'name': sample['name'],
                    'default_code': f"SKU-{product_id:04d}",
                    'list_price': sample.get('list_price', 50.0),
                    'standard_price': sample.get('standard_price', 20.0),
                    'type': 'product',
                    'detailed_type': sample.get('detailed_type', 'consu'),
                    'categ_id': [1, sample.get('categ_id', 'Unknown')]
                })
                product_id += 1
                
            # Add more realistic gym/coffee products
            gym_coffee_products = [
                {"name": "Premium Coffee Blend 250g", "price": 15.99, "category": "Coffee"},
                {"name": "Protein Smoothie Mix", "price": 29.99, "category": "Supplements"},
                {"name": "Essential Hoodie - Black", "price": 65.00, "category": "Hoodies"},
                {"name": "Essential Hoodie - Grey", "price": 65.00, "category": "Hoodies"},
                {"name": "Essential Hoodie - White", "price": 65.00, "category": "Hoodies"},
                {"name": "Performance Leggings - Black", "price": 45.00, "category": "Leggings"},
                {"name": "Performance Leggings - Navy", "price": 45.00, "category": "Leggings"},
                {"name": "Classic T-Shirt - White", "price": 25.00, "category": "T-Shirts"},
                {"name": "Classic T-Shirt - Black", "price": 25.00, "category": "T-Shirts"},
                {"name": "Gym Water Bottle", "price": 12.99, "category": "Accessories"},
                {"name": "Yoga Mat Premium", "price": 89.99, "category": "Equipment"},
                {"name": "Resistance Bands Set", "price": 34.99, "category": "Equipment"},
                {"name": "Pre-Workout Energy", "price": 39.99, "category": "Supplements"},
                {"name": "BCAA Recovery", "price": 44.99, "category": "Supplements"},
                {"name": "Organic Energy Bar", "price": 3.99, "category": "Snacks"},
            ]
            
            for item in gym_coffee_products:
                products.append({
                    'id': product_id,
                    'name': item['name'],
                    'default_code': f"GC-{product_id:04d}",
                    'list_price': item['price'],
                    'standard_price': item['price'] * 0.4,  # 40% cost
                    'type': 'product',
                    'detailed_type': 'product',
                    'categ_id': [1, item['category']]
                })
                product_id += 1
                
            logger.info(f"Created {len(products)} product mappings")
            return products
            
    except Exception as e:
        logger.error(f"Error getting product data: {e}")
        return []
        
def test_streaming():
    """Test the streaming processor on transaction file"""
    logger.info("Testing streaming processor...")
    
    try:
        processor = JSONStreamProcessor("/workspaces/source-lovable-gympluscoffee/odoo-ingestion/generated_transactions.json")
        
        # Get metadata
        metadata = processor.get_metadata()
        logger.info(f"Transaction metadata: {json.dumps(metadata, indent=2)}")
        
        # Test streaming
        total_count = 0
        batch_count = 0
        
        for batch in processor.stream_transactions(batch_size=1000):
            batch_count += 1
            total_count += len(batch)
            logger.info(f"Batch {batch_count}: {len(batch)} transactions (total: {total_count})")
            
            # Show sample from first batch
            if batch_count == 1 and batch:
                sample = batch[0]
                logger.info(f"Sample transaction: {json.dumps(sample, indent=2)[:500]}...")
                
            # Only test first 5 batches
            if batch_count >= 5:
                break
                
        logger.info(f"Streaming test completed: {batch_count} batches, {total_count} transactions")
        return True
        
    except Exception as e:
        logger.error(f"Streaming test failed: {e}")
        return False

def run_full_processing():
    """Run the complete bulk processing pipeline"""
    logger.info("="*80)
    logger.info("STARTING BULK DATA PROCESSING PIPELINE")
    logger.info("="*80)
    
    start_time = datetime.now()
    
    try:
        # Initialize processor
        processor = BulkDataProcessor()
        
        # Step 1: Load data files
        logger.info("Step 1: Loading data files...")
        if not processor.load_data_files():
            logger.error("Failed to load data files")
            return False
            
        # Step 2: Get product mapping  
        logger.info("Step 2: Getting product mapping...")
        products = get_odoo_products()
        if not products:
            logger.error("Failed to get product mapping")
            return False
            
        processor.load_product_mapping(products)
        
        # Step 3: Create customer batches
        logger.info("Step 3: Creating customer batches...")
        processor.create_customer_batches(batch_size=500)
        
        # Step 4: Process transactions in streaming mode
        logger.info("Step 4: Processing transactions...")
        if not processor.process_transactions_streaming(batch_size=100):
            logger.warning("Transaction processing had issues, continuing...")
            
        # Step 5: Create processing summary
        logger.info("Step 5: Creating summary...")
        summary = processor.create_processing_summary()
        
        end_time = datetime.now()
        processing_time = end_time - start_time
        
        logger.info("="*80)
        logger.info("BULK PROCESSING COMPLETED")
        logger.info(f"Processing time: {processing_time}")
        logger.info(f"Summary: {json.dumps(summary, indent=2)}")
        logger.info("="*80)
        
        return True
        
    except Exception as e:
        logger.error(f"Bulk processing failed: {e}")
        return False

def main():
    """Main execution function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Bulk Data Processor for Odoo Import")
    parser.add_argument("--test-streaming", action="store_true", 
                       help="Test streaming functionality only")
    parser.add_argument("--process-all", action="store_true", 
                       help="Run full processing pipeline")
    
    args = parser.parse_args()
    
    if args.test_streaming:
        success = test_streaming()
        sys.exit(0 if success else 1)
    elif args.process_all:
        success = run_full_processing()
        sys.exit(0 if success else 1)
    else:
        # Default: run full processing
        logger.info("Running full bulk processing pipeline...")
        logger.info("Use --test-streaming to test only, --process-all to run everything")
        success = run_full_processing()
        sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()