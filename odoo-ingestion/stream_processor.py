#!/usr/bin/env python3
"""
Streaming JSON processor for large transaction files
Handles 65,000 transactions efficiently
"""

import json
import logging
import os
from typing import Iterator, Dict, Any
import sys

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class JSONStreamProcessor:
    """Efficiently process large JSON files without loading everything into memory"""
    
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.file_size = os.path.getsize(file_path) if os.path.exists(file_path) else 0
        
    def get_metadata(self) -> Dict:
        """Extract metadata from the beginning of the JSON file"""
        try:
            with open(self.file_path, 'r') as f:
                # Read first 10KB to find metadata
                content = f.read(10240)
                
                if '"metadata":' in content:
                    # Find metadata section
                    start = content.find('"metadata":')
                    # Find the closing brace for metadata
                    brace_count = 0
                    metadata_start = content.find('{', start)
                    i = metadata_start
                    
                    while i < len(content) and (brace_count > 0 or i == metadata_start):
                        if content[i] == '{':
                            brace_count += 1
                        elif content[i] == '}':
                            brace_count -= 1
                        i += 1
                    
                    if brace_count == 0:
                        metadata_json = content[metadata_start:i]
                        return json.loads(metadata_json)
                        
        except Exception as e:
            logger.error(f"Error extracting metadata: {e}")
            
        return {}
        
    def stream_transactions(self, batch_size: int = 1000) -> Iterator[list]:
        """Stream transactions in batches"""
        try:
            current_batch = []
            in_transactions_array = False
            brace_level = 0
            current_object = ""
            
            with open(self.file_path, 'r') as f:
                for line_num, line in enumerate(f):
                    line = line.strip()
                    
                    if not line:
                        continue
                        
                    # Look for start of transactions array
                    if '"transactions": [' in line:
                        in_transactions_array = True
                        continue
                        
                    if not in_transactions_array:
                        continue
                        
                    # Track brace levels to identify complete objects
                    for char in line:
                        if char == '{':
                            if brace_level == 0:
                                current_object = char
                            else:
                                current_object += char
                            brace_level += 1
                        elif char == '}':
                            current_object += char
                            brace_level -= 1
                            
                            if brace_level == 0:
                                # Complete object found
                                try:
                                    transaction = json.loads(current_object)
                                    current_batch.append(transaction)
                                    current_object = ""
                                    
                                    if len(current_batch) >= batch_size:
                                        yield current_batch
                                        current_batch = []
                                        
                                except json.JSONDecodeError:
                                    logger.warning(f"Skipped invalid JSON at line {line_num}")
                                    current_object = ""
                        else:
                            if brace_level > 0:
                                current_object += char
                                
                    # Check for end of array
                    if line.strip() == ']' and in_transactions_array:
                        break
                        
            # Yield final batch
            if current_batch:
                yield current_batch
                
        except Exception as e:
            logger.error(f"Error streaming transactions: {e}")
            
    def count_transactions(self) -> int:
        """Count total transactions without loading all into memory"""
        try:
            count = 0
            for batch in self.stream_transactions(batch_size=5000):
                count += len(batch)
                if count % 10000 == 0:
                    logger.info(f"Counted {count} transactions...")
            return count
        except Exception as e:
            logger.error(f"Error counting transactions: {e}")
            return 0

def test_streaming():
    """Test the streaming processor"""
    transactions_file = "/workspaces/source-lovable-gympluscoffee/odoo-ingestion/generated_transactions.json"
    
    if not os.path.exists(transactions_file):
        logger.error(f"File not found: {transactions_file}")
        return
        
    processor = JSONStreamProcessor(transactions_file)
    
    logger.info(f"File size: {processor.file_size / (1024*1024):.1f} MB")
    
    # Get metadata
    metadata = processor.get_metadata()
    logger.info(f"Metadata: {metadata}")
    
    # Test streaming first few batches
    batch_count = 0
    transaction_count = 0
    
    for batch in processor.stream_transactions(batch_size=100):
        batch_count += 1
        transaction_count += len(batch)
        logger.info(f"Batch {batch_count}: {len(batch)} transactions")
        
        # Show sample from first batch
        if batch_count == 1 and batch:
            sample = batch[0]
            logger.info(f"Sample transaction keys: {list(sample.keys())}")
            
        # Only process first few batches for testing
        if batch_count >= 5:
            break
            
    logger.info(f"Processed {batch_count} batches, {transaction_count} transactions")

if __name__ == "__main__":
    test_streaming()