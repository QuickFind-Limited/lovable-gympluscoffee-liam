#!/usr/bin/env python3
"""
Odoo Import Summary Report Generator
Tracks and reports on import progress and performance
"""

import json
import time
import logging
from datetime import datetime
import os
import glob

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def analyze_log_files():
    """Analyze log files to extract import statistics"""
    
    log_files = glob.glob('/workspaces/source-lovable-gympluscoffee/odoo-ingestion/*.log')
    
    stats = {
        'total_customers_processed': 0,
        'total_customers_imported': 0,
        'total_customers_failed': 0,
        'total_customers_skipped': 0,
        'total_orders_processed': 0,
        'total_orders_imported': 0,
        'total_lines_imported': 0,
        'batches_completed': 0,
        'import_rate_per_minute': 0,
        'start_time': None,
        'current_time': datetime.now().isoformat()
    }
    
    logger.info("📊 Analyzing import log files...")
    
    for log_file in log_files:
        try:
            with open(log_file, 'r') as f:
                lines = f.readlines()
                
            for line in lines:
                if 'Batch' in line and 'complete:' in line:
                    # Extract batch completion info
                    if 'imported,' in line and 'skipped,' in line and 'failed' in line:
                        # Parse: "✅ Batch 1 complete: 50/75 imported, 25 skipped, 0 failed"
                        parts = line.split('complete:')[1].strip()
                        
                        # Extract imported count
                        imported_part = parts.split('imported,')[0].strip()
                        if '/' in imported_part:
                            imported = int(imported_part.split('/')[0])
                            stats['total_customers_imported'] += imported
                        
                        # Extract skipped count
                        if 'skipped,' in parts:
                            skipped_part = parts.split('skipped,')[0].split(',')[-1].strip()
                            skipped = int(skipped_part)
                            stats['total_customers_skipped'] += skipped
                        
                        # Extract failed count
                        if 'failed' in parts:
                            failed_part = parts.split('failed')[0].split(',')[-1].strip()
                            failed = int(failed_part)
                            stats['total_customers_failed'] += failed
                        
                        stats['batches_completed'] += 1
                
                elif 'Starting FULL SCALE import' in line:
                    # Extract start time
                    timestamp = line.split(' - ')[0]
                    stats['start_time'] = timestamp
                
                elif 'orders, ' in line and 'lines imported' in line:
                    # Extract order stats: "🎉 FULL ORDER import completed: 1,000 orders, 5,000 lines imported"
                    if 'orders,' in line:
                        orders_part = line.split('orders,')[0].split(':')[-1].strip()
                        orders = int(orders_part.replace(',', ''))
                        stats['total_orders_imported'] += orders
                    
                    if 'lines imported' in line:
                        lines_part = line.split('lines imported')[0].split(',')[-1].strip()
                        lines_count = int(lines_part.replace(',', ''))
                        stats['total_lines_imported'] += lines_count
                        
        except Exception as e:
            logger.warning(f"⚠️  Error analyzing log file {log_file}: {e}")
            continue
    
    # Calculate totals and rates
    stats['total_customers_processed'] = (stats['total_customers_imported'] + 
                                        stats['total_customers_skipped'] + 
                                        stats['total_customers_failed'])
    
    return stats

def calculate_progress_metrics(stats):
    """Calculate progress metrics and projections"""
    
    # Target numbers
    target_customers = 35000
    target_transactions = 65000
    
    # Calculate progress percentages
    customer_progress = (stats['total_customers_processed'] / target_customers * 100) if target_customers > 0 else 0
    order_progress = (stats['total_orders_imported'] / target_transactions * 100) if target_transactions > 0 else 0
    
    # Calculate success rates
    customer_success_rate = (stats['total_customers_imported'] / stats['total_customers_processed'] * 100) if stats['total_customers_processed'] > 0 else 0
    
    # Calculate time-based metrics
    if stats['start_time']:
        try:
            start_dt = datetime.fromisoformat(stats['start_time'].replace(',', '.'))
            current_dt = datetime.now()
            elapsed_minutes = (current_dt - start_dt).total_seconds() / 60
            
            if elapsed_minutes > 0:
                stats['import_rate_per_minute'] = stats['total_customers_imported'] / elapsed_minutes
                
                # Project completion time
                remaining_customers = target_customers - stats['total_customers_processed']
                if stats['import_rate_per_minute'] > 0:
                    estimated_minutes_remaining = remaining_customers / stats['import_rate_per_minute']
                    estimated_completion = current_dt.timestamp() + (estimated_minutes_remaining * 60)
                    stats['estimated_completion'] = datetime.fromtimestamp(estimated_completion).isoformat()
                
        except Exception as e:
            logger.warning(f"⚠️  Error calculating time metrics: {e}")
    
    metrics = {
        'customer_progress_percent': round(customer_progress, 2),
        'order_progress_percent': round(order_progress, 2),
        'customer_success_rate_percent': round(customer_success_rate, 2),
        'import_rate_per_minute': round(stats['import_rate_per_minute'], 2)
    }
    
    return metrics

def generate_summary_report():
    """Generate comprehensive import summary report"""
    
    logger.info("📈 Generating Import Summary Report...")
    logger.info("="*80)
    
    # Analyze logs
    stats = analyze_log_files()
    metrics = calculate_progress_metrics(stats)
    
    # Print report
    logger.info("📊 ODOO IMPORT STATUS REPORT")
    logger.info("="*80)
    
    logger.info(f"\n👥 CUSTOMER IMPORT PROGRESS:")
    logger.info(f"  📈 Total Processed: {stats['total_customers_processed']:,}")
    logger.info(f"  ✅ Successfully Imported: {stats['total_customers_imported']:,}")
    logger.info(f"  ⏭️  Skipped (Duplicates): {stats['total_customers_skipped']:,}")
    logger.info(f"  ❌ Failed: {stats['total_customers_failed']:,}")
    logger.info(f"  🎯 Success Rate: {metrics['customer_success_rate_percent']}%")
    logger.info(f"  📊 Progress: {metrics['customer_progress_percent']}% of 35,000 target")
    
    if stats['total_orders_imported'] > 0:
        logger.info(f"\n🛒 ORDER IMPORT PROGRESS:")
        logger.info(f"  ✅ Orders Imported: {stats['total_orders_imported']:,}")
        logger.info(f"  📋 Order Lines: {stats['total_lines_imported']:,}")
        logger.info(f"  📊 Progress: {metrics['order_progress_percent']}% of 65,000 target")
    
    logger.info(f"\n⚡ PERFORMANCE METRICS:")
    logger.info(f"  🏃 Import Rate: {metrics['import_rate_per_minute']} customers/minute")
    logger.info(f"  📦 Batches Completed: {stats['batches_completed']:,}")
    
    if 'estimated_completion' in stats:
        logger.info(f"  ⏰ Estimated Completion: {stats['estimated_completion']}")
    
    logger.info(f"\n🕒 TIMING:")
    logger.info(f"  🚀 Started: {stats['start_time'] or 'Unknown'}")
    logger.info(f"  📅 Current: {stats['current_time']}")
    
    # Calculate remaining work
    remaining_customers = 35000 - stats['total_customers_processed']
    remaining_orders = 65000 - stats['total_orders_imported']
    
    logger.info(f"\n📋 REMAINING WORK:")
    if remaining_customers > 0:
        logger.info(f"  👥 Customers: {remaining_customers:,}")
    if remaining_orders > 0:
        logger.info(f"  🛒 Orders: {remaining_orders:,}")
    
    if remaining_customers <= 0 and remaining_orders <= 0:
        logger.info("  🎉 ALL IMPORT WORK COMPLETED!")
    
    logger.info("\n" + "="*80)
    
    # Save report to file
    report_data = {
        'timestamp': stats['current_time'],
        'statistics': stats,
        'metrics': metrics,
        'remaining_customers': max(0, remaining_customers),
        'remaining_orders': max(0, remaining_orders)
    }
    
    with open('/workspaces/source-lovable-gympluscoffee/odoo-ingestion/import_progress_report.json', 'w') as f:
        json.dump(report_data, f, indent=2)
    
    logger.info("💾 Report saved to: import_progress_report.json")
    
    return report_data

def monitor_import_status():
    """Continuously monitor import status"""
    
    logger.info("🔍 Starting Import Status Monitor...")
    
    while True:
        try:
            report = generate_summary_report()
            
            # Check if import is complete
            if (report['remaining_customers'] <= 0 and 
                report['remaining_orders'] <= 0):
                logger.info("🎉 IMPORT COMPLETE! Exiting monitor.")
                break
            
            # Wait before next check
            logger.info("⏰ Next update in 30 seconds...\n")
            time.sleep(30)
            
        except KeyboardInterrupt:
            logger.info("🛑 Monitor stopped by user.")
            break
        except Exception as e:
            logger.error(f"❌ Error in monitor: {e}")
            time.sleep(10)

def main():
    """Main execution function"""
    try:
        # Generate single report
        generate_summary_report()
        
    except Exception as e:
        logger.error(f"❌ Error generating report: {e}")
        raise

if __name__ == "__main__":
    main()