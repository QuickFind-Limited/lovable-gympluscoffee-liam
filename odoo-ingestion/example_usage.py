#!/usr/bin/env python3
"""
Example Usage of Inventory Management System
===========================================

Demonstrates how to use the manage_inventory.py script with different scenarios.
"""

import json
import subprocess
import sys
import os

def create_sample_product_data():
    """Create sample product data that represents Gym+Coffee inventory"""
    
    sample_products = {
        "catalog_name": "Gym+Coffee Product Catalog",
        "version": "1.0.0",
        "total_skus": 50,
        "products": [
            # Essential Hoodies - Higher stock levels
            {
                "sku": "GC-HOODIE-001-BLK-M",
                "name": "Essential Hoodie - Black Medium",
                "category": "hoodies",
                "subcategory": "unisex",
                "color": "Black",
                "size": "M",
                "list_price": 75.00,
                "standard_cost": 25.00,
                "inventory_on_hand": 120,
                "reorder_point": 50,
                "lead_time_days": 14
            },
            {
                "sku": "GC-HOODIE-002-GRY-L",
                "name": "Essential Hoodie - Grey Large",
                "category": "hoodies",
                "subcategory": "unisex",
                "color": "Grey",
                "size": "L",
                "list_price": 75.00,
                "standard_cost": 25.00,
                "inventory_on_hand": 85,
                "reorder_point": 50,
                "lead_time_days": 14
            },
            
            # Regular T-shirts
            {
                "sku": "GC-TEE-001-WHT-M",
                "name": "Basic Cotton Tee - White Medium",
                "category": "t-shirts",
                "subcategory": "unisex",
                "color": "White",
                "size": "M",
                "list_price": 35.00,
                "standard_cost": 12.00,
                "inventory_on_hand": 200,
                "reorder_point": 40,
                "lead_time_days": 7
            },
            {
                "sku": "GC-TEE-002-BLK-L",
                "name": "Basic Cotton Tee - Black Large",
                "category": "t-shirts",
                "subcategory": "unisex",
                "color": "Black",
                "size": "L",
                "list_price": 35.00,
                "standard_cost": 12.00,
                "inventory_on_hand": 180,
                "reorder_point": 40,
                "lead_time_days": 7
            },
            
            # Summer items (shorts/tanks) - Currently summer season
            {
                "sku": "GC-TANK-001-WHT-S",
                "name": "Training Tank - White Small",
                "category": "tanks",
                "subcategory": "womens",
                "color": "White",
                "size": "S",
                "list_price": 30.00,
                "standard_cost": 10.00,
                "inventory_on_hand": 150,
                "reorder_point": 30,
                "lead_time_days": 10
            },
            {
                "sku": "GC-SHORTS-001-BLK-M",
                "name": "Training Shorts - Black Medium",
                "category": "shorts",
                "subcategory": "mens",
                "color": "Black",
                "size": "M",
                "list_price": 40.00,
                "standard_cost": 15.00,
                "inventory_on_hand": 90,
                "reorder_point": 25,
                "lead_time_days": 10
            },
            
            # Limited Edition - Lower stock levels
            {
                "sku": "GC-LE-001-COLLAB-OS",
                "name": "Limited Edition Collaboration Hoodie",
                "category": "limited-edition",
                "subcategory": "unisex",
                "color": "Special",
                "size": "OS",
                "list_price": 120.00,
                "standard_cost": 40.00,
                "inventory_on_hand": 25,
                "reorder_point": 5,
                "lead_time_days": 21
            },
            
            # Accessories
            {
                "sku": "GC-ACC-001-BOTTLE-BLK",
                "name": "Gym+Coffee Water Bottle - Black",
                "category": "accessories",
                "subcategory": "bottles",
                "color": "Black",
                "size": "OS",
                "list_price": 25.00,
                "standard_cost": 8.00,
                "inventory_on_hand": 300,
                "reorder_point": 60,
                "lead_time_days": 5
            },
            {
                "sku": "GC-ACC-002-CAP-WHT",
                "name": "Gym+Coffee Cap - White",
                "category": "caps",
                "subcategory": "accessories",
                "color": "White",
                "size": "OS",
                "list_price": 30.00,
                "standard_cost": 10.00,
                "inventory_on_hand": 200,
                "reorder_point": 40,
                "lead_time_days": 7
            },
            {
                "sku": "GC-ACC-003-BEANIE-GRY",
                "name": "Gym+Coffee Beanie - Grey",
                "category": "beanies",
                "subcategory": "accessories",
                "color": "Grey",
                "size": "OS",
                "list_price": 28.00,
                "standard_cost": 9.00,
                "inventory_on_hand": 80,
                "reorder_point": 20,
                "lead_time_days": 7
            }
        ]
    }
    
    return sample_products

def run_inventory_scenarios():
    """Run different inventory management scenarios"""
    
    print("Creating sample product data...")
    sample_data = create_sample_product_data()
    
    # Save sample data
    with open("sample_products.json", "w") as f:
        json.dump(sample_data, f, indent=2)
    
    print("Running inventory management scenarios:\n")
    
    # Scenario 1: Dry run with basic inventory level setting
    print("=" * 60)
    print("SCENARIO 1: Basic inventory level optimization")
    print("=" * 60)
    
    result1 = subprocess.run([
        sys.executable, "manage_inventory.py",
        "--dry-run",
        "--data-file", "sample_products.json",
        "--output-report", "scenario1_report.txt"
    ], capture_output=True, text=True)
    
    if result1.returncode == 0:
        print("✅ Scenario 1 completed successfully")
        print("📄 Report saved to: scenario1_report.txt")
    else:
        print("❌ Scenario 1 failed:")
        print(result1.stderr)
    
    print()
    
    # Scenario 2: Full simulation with stock movements
    print("=" * 60)
    print("SCENARIO 2: Full simulation with sales movements")
    print("=" * 60)
    
    result2 = subprocess.run([
        sys.executable, "manage_inventory.py",
        "--dry-run",
        "--simulate-sales",
        "--data-file", "sample_products.json",
        "--output-report", "scenario2_report.txt"
    ], capture_output=True, text=True)
    
    if result2.returncode == 0:
        print("✅ Scenario 2 completed successfully")
        print("📄 Report saved to: scenario2_report.txt")
        print("📊 Check for reorder alerts in the report")
    else:
        print("❌ Scenario 2 failed:")
        print(result2.stderr)
    
    print()
    
    # Show key insights
    print("=" * 60)
    print("KEY INSIGHTS FROM INVENTORY ANALYSIS")
    print("=" * 60)
    
    insights = [
        "🏷️  SEASONAL ADJUSTMENTS:",
        "   • Hoodies: Reduced stock in summer (-30%)",
        "   • Tanks/Shorts: Increased stock in summer (+40%)",
        "   • Caps: Seasonal boost in summer (+20%)",
        "",
        "📈 STOCK LEVEL TARGETS:",
        "   • Essential Items (Hoodies): 500-1000 units",
        "   • Regular Items (T-shirts): 200-500 units", 
        "   • Limited Edition: 50-200 units",
        "   • Accessories: 300-600 units",
        "",
        "⚠️  SAFETY STOCK:",
        "   • Essential items: 25% safety stock",
        "   • Regular items: 20% safety stock",
        "   • Limited edition: 15% safety stock",
        "",
        "🔄 REORDER POINTS:",
        "   • Essential items: 40% of max stock",
        "   • Regular items: 30% of max stock",
        "   • Limited edition: 25% of max stock",
        "",
        "💰 TARGET PERFORMANCE:",
        "   • Monthly Sales Target: €300,000",
        "   • Estimated Monthly Units: ~6,667 units",
        "   • Average Product Price: €45"
    ]
    
    for insight in insights:
        print(insight)
    
    print()
    print("=" * 60)
    print("NEXT STEPS")
    print("=" * 60)
    
    next_steps = [
        "1. Review the generated reports (scenario1_report.txt, scenario2_report.txt)",
        "2. Analyze reorder alerts and plan purchase orders",
        "3. Monitor seasonal adjustments and update as needed",
        "4. Run without --dry-run flag to apply changes to Odoo",
        "5. Set up automated daily/weekly inventory checks"
    ]
    
    for step in next_steps:
        print(step)
    
    # Clean up temporary files
    try:
        os.remove("sample_products.json")
        print("\n🧹 Cleaned up temporary files")
    except:
        pass

def show_usage_examples():
    """Show different ways to use the inventory management script"""
    
    print("INVENTORY MANAGEMENT SCRIPT USAGE EXAMPLES")
    print("=" * 50)
    print()
    
    examples = [
        {
            "title": "Basic dry run with test data",
            "command": "python manage_inventory.py --dry-run"
        },
        {
            "title": "Full simulation with sales movements",
            "command": "python manage_inventory.py --dry-run --simulate-sales"
        },
        {
            "title": "Use custom product data file",
            "command": "python manage_inventory.py --dry-run --data-file products.json"
        },
        {
            "title": "Generate report to specific file",
            "command": "python manage_inventory.py --dry-run --output-report inventory_report.txt"
        },
        {
            "title": "Full production run (update Odoo)",
            "command": "python manage_inventory.py --simulate-sales"
        }
    ]
    
    for i, example in enumerate(examples, 1):
        print(f"{i}. {example['title']}:")
        print(f"   {example['command']}")
        print()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Inventory Management Examples")
    parser.add_argument("--run-scenarios", action="store_true", 
                       help="Run complete inventory scenarios")
    parser.add_argument("--show-examples", action="store_true",
                       help="Show usage examples")
    
    args = parser.parse_args()
    
    if args.run_scenarios:
        run_inventory_scenarios()
    elif args.show_examples:
        show_usage_examples()
    else:
        print("Inventory Management System Example Usage")
        print("========================================")
        print()
        print("Options:")
        print("  --run-scenarios    Run complete inventory scenarios")
        print("  --show-examples    Show usage examples")
        print()
        print("Example:")
        print("  python example_usage.py --run-scenarios")