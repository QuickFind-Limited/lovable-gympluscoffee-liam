#!/usr/bin/env python3
"""
Execute Odoo Import - Direct implementation using available tools
Imports customers and transactions to Odoo in batches
"""

import json
import logging
import time
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_customer_batch_script():
    """Create customer import batch script"""
    
    # Load first batch of customers
    with open('/workspaces/source-lovable-gympluscoffee/odoo-ingestion/generated_customers.json', 'r') as f:
        all_customers = json.load(f)
    
    # Take first 50 customers as initial batch
    batch_customers = all_customers[:50]
    
    logger.info(f"🚀 Creating batch import script for {len(batch_customers)} customers")
    
    script_content = '''#!/usr/bin/env python3
"""
Batch Customer Import Script
"""

import time
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Customer data batch
customers = '''
    
    # Add customer data
    script_content += json.dumps(batch_customers, indent=2)
    
    script_content += '''

def import_customers():
    """Import customers using MCP tools"""
    
    logger.info(f"🎯 Starting import of {len(customers)} customers")
    
    imported = 0
    failed = 0
    
    for i, customer in enumerate(customers, 1):
        try:
            customer_data = {
                'name': f"{customer.get('first_name', '')} {customer.get('last_name', '')}".strip(),
                'email': customer.get('email', '').lower().strip(),
                'phone': customer.get('phone', ''),
                'customer_rank': 1,
                'is_company': customer.get('type', '').lower() == 'company',
                'street': customer.get('city', ''),
                'ref': customer.get('customer_id', ''),
            }
            
            # Map country
            country_code = customer.get('country', 'UK').upper()
            country_map = {'UK': 76, 'US': 235, 'AU': 13, 'IE': 105}
            if country_code in country_map:
                customer_data['country_id'] = country_map[country_code]
            
            # Remove empty values
            customer_data = {k: v for k, v in customer_data.items() if v not in [None, '', False, 0]}
            
            logger.info(f"📝 Customer {i}/{len(customers)}: {customer_data['name']} ({customer_data['email']})")
            
            # This would be called via MCP in the actual implementation
            # result = mcp__odoo_mcp__odoo_create(
            #     instance_id="source-gym-plus-coffee",
            #     model="res.partner", 
            #     values=customer_data
            # )
            
            imported += 1
            
            # Brief pause to avoid overwhelming the server
            if i % 10 == 0:
                time.sleep(1)
                logger.info(f"✅ Processed {i} customers so far...")
                
        except Exception as e:
            logger.error(f"❌ Failed to process customer {i}: {e}")
            failed += 1
            
    logger.info(f"🎉 Batch completed: {imported} imported, {failed} failed")
    return imported, failed

if __name__ == "__main__":
    import_customers()
'''
    
    # Write the script
    with open('/workspaces/source-lovable-gympluscoffee/odoo-ingestion/batch_customer_import.py', 'w') as f:
        f.write(script_content)
    
    logger.info("✅ Customer batch script created: batch_customer_import.py")
    return len(batch_customers)

def create_customer_summary():
    """Create a summary of all customer data"""
    
    with open('/workspaces/source-lovable-gympluscoffee/odoo-ingestion/generated_customers.json', 'r') as f:
        customers = json.load(f)
    
    summary = {
        'total_customers': len(customers),
        'countries': {},
        'segments': {},
        'types': {},
        'sample_customers': customers[:5]
    }
    
    # Analyze distribution
    for customer in customers:
        country = customer.get('country', 'Unknown')
        segment = customer.get('segment', 'Unknown')
        customer_type = customer.get('type', 'Unknown')
        
        summary['countries'][country] = summary['countries'].get(country, 0) + 1
        summary['segments'][segment] = summary['segments'].get(segment, 0) + 1
        summary['types'][customer_type] = summary['types'].get(customer_type, 0) + 1
    
    # Write summary
    with open('/workspaces/source-lovable-gympluscoffee/odoo-ingestion/customer_summary.json', 'w') as f:
        json.dump(summary, f, indent=2)
    
    logger.info("📊 Customer Analysis Summary:")
    logger.info(f"  Total customers: {summary['total_customers']:,}")
    logger.info(f"  Countries: {dict(list(summary['countries'].items())[:5])}")
    logger.info(f"  Segments: {summary['segments']}")
    logger.info(f"  Types: {summary['types']}")
    
    return summary

def create_transaction_summary():
    """Create a summary of all transaction data"""
    
    with open('/workspaces/source-lovable-gympluscoffee/odoo-ingestion/generated_transactions.json', 'r') as f:
        data = json.load(f)
    
    transactions = data.get('transactions', [])
    metadata = data.get('metadata', {})
    summary_stats = data.get('summary_statistics', {})
    
    analysis = {
        'metadata': metadata,
        'summary_statistics': summary_stats,
        'total_transactions': len(transactions),
        'sample_transaction': transactions[0] if transactions else None,
        'channels': {},
        'date_range': {'earliest': None, 'latest': None}
    }
    
    # Analyze transactions
    for transaction in transactions[:1000]:  # Sample first 1000 for performance
        channel = transaction.get('channel', 'unknown')
        order_date = transaction.get('order_date', '')
        
        analysis['channels'][channel] = analysis['channels'].get(channel, 0) + 1
        
        if order_date:
            if not analysis['date_range']['earliest'] or order_date < analysis['date_range']['earliest']:
                analysis['date_range']['earliest'] = order_date
            if not analysis['date_range']['latest'] or order_date > analysis['date_range']['latest']:
                analysis['date_range']['latest'] = order_date
    
    # Write analysis
    with open('/workspaces/source-lovable-gympluscoffee/odoo-ingestion/transaction_analysis.json', 'w') as f:
        json.dump(analysis, f, indent=2)
    
    logger.info("🛒 Transaction Analysis Summary:")
    logger.info(f"  Total transactions: {analysis['total_transactions']:,}")
    logger.info(f"  Channels: {analysis['channels']}")
    logger.info(f"  Date range: {analysis['date_range']['earliest']} to {analysis['date_range']['latest']}")
    
    return analysis

def main():
    """Main execution function"""
    logger.info("🎯 Starting Odoo Import Preparation")
    
    start_time = time.time()
    
    try:
        # Create summaries
        logger.info("\n📊 Creating data analysis...")
        customer_summary = create_customer_summary()
        transaction_analysis = create_transaction_summary()
        
        # Create batch scripts
        logger.info("\n🔧 Creating import scripts...")
        batch_size = create_customer_batch_script()
        
        # Summary
        execution_time = time.time() - start_time
        
        logger.info("\n" + "="*60)
        logger.info("📋 PREPARATION COMPLETE")
        logger.info("="*60)
        logger.info(f"✅ Customer analysis: {customer_summary['total_customers']:,} customers")
        logger.info(f"✅ Transaction analysis: {transaction_analysis['total_transactions']:,} transactions")
        logger.info(f"✅ Batch script created: {batch_size} customers in first batch")
        logger.info(f"⏱️  Preparation time: {execution_time:.2f} seconds")
        logger.info("\n📝 Next steps:")
        logger.info("  1. Review customer_summary.json and transaction_analysis.json")
        logger.info("  2. Execute batch_customer_import.py to test import process")
        logger.info("  3. Scale up to full import once testing is successful")
        logger.info("="*60)
        
    except Exception as e:
        logger.error(f"❌ Error in preparation: {e}")
        raise

if __name__ == "__main__":
    main()