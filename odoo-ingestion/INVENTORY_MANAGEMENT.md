# Gym+Coffee Inventory Management System

## Overview

The **Inventory Management System** is designed to optimize stock levels, handle seasonal adjustments, and maintain proper inventory flow to support **€300,000/month in sales** with automated reorder points and safety stock calculations.

## Key Features

### 🎯 Stock Level Optimization
- **Essential/Basic items**: 500-1000 units (hoodies, sweatshirts, core t-shirts)
- **Regular items**: 200-500 units (t-shirts, tanks, shorts, leggings, joggers) 
- **Limited Edition**: 50-200 units (collaborations, special releases)
- **Accessories**: 300-600 units (bags, bottles, caps, beanies)

### 🌅 Seasonal Stock Adjustments
- **Winter (Sep-Feb)**:
  - Hoodies/Sweatshirts: +50% stock
  - Summer items (tanks/shorts): -20% stock
  - Beanies: +30% stock

- **Summer (Mar-Aug)**:
  - Hoodies/Sweatshirts: -30% stock  
  - Tanks/Shorts: +40% stock
  - Caps: +20% stock

### 📊 Safety Stock & Reorder Management
- **Safety Stock**: 15-25% of max stock (higher for essentials)
- **Reorder Points**: 25-40% of max stock (earlier for essentials)
- **Automated Reorder Alerts**: Generated when stock hits reorder point
- **20% minimum safety stock** maintained at all times

### 💰 Sales Target Support
- **Target**: €300,000/month (~6,667 units/month)
- **Stock movements** simulated based on category popularity
- **Realistic sales distribution** with seasonal variations
- **Inventory turnover** optimized for target revenue

## Files

### Core Scripts
- **`manage_inventory.py`**: Main inventory management script
- **`example_usage.py`**: Usage examples and scenarios

### Key Classes

#### `InventoryManager`
Main class handling all inventory operations:
```python
manager = InventoryManager(connection=odoo_conn, dry_run=True)
results = manager.set_inventory_levels(products)
movements = manager.create_stock_movements(products, simulate_sales=True)
```

#### `InventoryRule`
Defines inventory rules per category:
```python
rule = InventoryRule(
    category='hoodies',
    base_min_stock=500,
    base_max_stock=1000,
    safety_stock_percent=0.25,
    reorder_point_percent=0.40,
    is_seasonal=True,
    seasonal_adjustment={'winter': 1.5, 'summer': 0.7}
)
```

## Usage Examples

### Basic Usage
```bash
# Dry run with test data
python manage_inventory.py --dry-run

# Full simulation with sales movements  
python manage_inventory.py --dry-run --simulate-sales

# Generate detailed report
python manage_inventory.py --dry-run --simulate-sales --output-report report.txt
```

### Advanced Usage
```bash
# Use custom product data
python manage_inventory.py --data-file my_products.json --dry-run

# Production run (updates Odoo)
python manage_inventory.py --simulate-sales

# Run scenarios and examples
python example_usage.py --run-scenarios
```

## Inventory Rules by Category

| Category | Min Stock | Max Stock | Safety Stock | Reorder Point | Seasonal |
|----------|-----------|-----------|--------------|---------------|----------|
| Hoodies | 500 | 1000 | 25% | 40% | Yes |
| Sweatshirts | 500 | 1000 | 25% | 40% | Yes |
| T-shirts | 200 | 500 | 20% | 30% | No |
| Tanks | 200 | 500 | 20% | 30% | Yes |
| Shorts | 200 | 500 | 20% | 30% | Yes |
| Limited Edition | 50 | 200 | 15% | 25% | No |
| Accessories | 300 | 600 | 20% | 30% | No |
| Caps | 300 | 600 | 20% | 30% | Yes |
| Beanies | 300 | 600 | 20% | 30% | Yes |

## Seasonal Multipliers

### Winter Season (Sep-Feb)
```python
seasonal_adjustments = {
    'hoodies': 1.5,      # +50% stock
    'sweatshirts': 1.3,  # +30% stock
    't-shirts': 0.8,     # -20% stock
    'beanies': 1.3       # +30% stock
}
```

### Summer Season (Mar-Aug)
```python
seasonal_adjustments = {
    'tanks': 1.4,        # +40% stock
    'shorts': 1.4,       # +40% stock
    'caps': 1.2,         # +20% stock
    'hoodies': 0.7,      # -30% stock
    'sweatshirts': 0.8   # -20% stock
}
```

## Stock Movement Simulation

The system simulates realistic stock movements based on:

### Category Popularity Weights
- **T-shirts**: 25% of sales
- **Hoodies**: 20% of sales  
- **Sweatshirts**: 15% of sales
- **Basic Tees**: 15% of sales
- **Leggings**: 10% of sales
- **Accessories**: 7% of sales
- **Joggers**: 5% of sales
- **Limited Edition**: 3% of sales

### Daily Sales Distribution
- Sales distributed across 31 days
- ±30% randomness per product
- Seasonal adjustments applied
- Stock availability constraints

## Report Generation

### Sample Report Sections
```
GYM+COFFEE INVENTORY MANAGEMENT REPORT
=====================================
Generated: 2025-08-07 16:57:04
Season: Summer
Target Monthly Sales: €300,000
Estimated Monthly Unit Sales: 6,667

INVENTORY SUMMARY
- Total Products: 50
- Total Stock Value: €125,450.00
- Products Updated: 50
- Errors: 0

CATEGORY BREAKDOWN
- Hoodies: 12 products, 8,400 target stock
- T-shirts: 18 products, 7,200 target stock
- Accessories: 8 products, 3,600 target stock

REORDER ALERTS
- 15 products need reordering
- Suggested orders: €45,250 value

STOCK MOVEMENTS
- 465 movements created
- 2,847 units sold
- Net movement: -2,847 units
```

## Integration with Odoo

### Odoo Models Updated
- **`product.product`**: Stock levels and reorder points
- **`stock.quant`**: Current inventory quantities
- **`stock.move`**: Stock movements and transactions
- **`product.template`**: Reorder rules and safety stock

### Connection Setup
```python
from scripts.connection_manager import OdooConnection, ConnectionConfig

config = ConnectionConfig(
    url="https://your-odoo.com",
    db="your_db",
    username="admin",
    password="admin_password"
)

connection = OdooConnection(config)
manager = InventoryManager(connection=connection, dry_run=False)
```

## Configuration Options

### Command Line Arguments
```bash
--dry-run              # Run without updating Odoo
--simulate-sales       # Create stock movements for sales simulation
--data-file FILE       # Use custom product data file
--output-report FILE   # Save report to specific file
```

### Environment Variables
```bash
ODOO_URL=https://your-odoo.com
ODOO_DB=your_database
ODOO_USER=your_username
ODOO_PASSWORD=your_password
```

## Performance Metrics

### Target Metrics
- **Monthly Revenue**: €300,000
- **Monthly Units**: ~6,667 units
- **Average Product Price**: €45
- **Inventory Turnover**: 6-8x annually
- **Stockout Rate**: <2%
- **Overstock Rate**: <10%

### Stock Level Efficiency
- **Total Stock Value**: €150,000-200,000
- **Safety Stock Coverage**: 15-30 days
- **Reorder Lead Time**: 5-21 days
- **Seasonal Adjustment**: ±50% based on category

## Monitoring & Alerts

### Automated Alerts
1. **Reorder Alerts**: When stock hits reorder point
2. **Low Safety Stock**: When below 20% safety threshold
3. **Overstock Alerts**: When above 120% of max stock
4. **Seasonal Adjustments**: Monthly review prompts
5. **Sales Performance**: Weekly target vs actual

### Reporting Schedule
- **Daily**: Stock movements and critical alerts
- **Weekly**: Category performance and reorder suggestions
- **Monthly**: Seasonal adjustments and target analysis
- **Quarterly**: Inventory rule optimization

## Troubleshooting

### Common Issues

1. **"unsupported operand type" errors**
   - Ensure all inventory quantities are numeric
   - Check product data format consistency

2. **"unhashable type: 'dict'" errors**
   - Verify product data structure matches expected format
   - Check for proper JSON formatting

3. **Odoo connection failures**
   - Verify connection credentials
   - Check network connectivity
   - Ensure Odoo server is accessible

### Debug Mode
```bash
# Enable verbose logging
python manage_inventory.py --dry-run --simulate-sales 2>&1 | tee debug.log

# Check generated files
ls -la inventory_results_*.json
ls -la *.log
```

## Development

### Adding New Categories
```python
# In _initialize_inventory_rules()
new_categories = ['activewear', 'outerwear']
for cat in new_categories:
    rules[cat] = InventoryRule(
        category=cat,
        base_min_stock=300,
        base_max_stock=700,
        safety_stock_percent=0.20,
        reorder_point_percent=0.30,
        is_seasonal=True,
        seasonal_adjustment={'summer': 1.2, 'winter': 0.9}
    )
```

### Custom Seasonal Logic
```python
def get_current_season(self) -> SeasonType:
    # Custom season definition
    current_month = datetime.now().month
    if current_month in [12, 1, 2]:  # Winter months
        return SeasonType.WINTER
    elif current_month in [6, 7, 8]:  # Summer months  
        return SeasonType.SUMMER
    else:
        return SeasonType.SPRING_FALL  # New season type
```

## Support

For questions or issues with the inventory management system:

1. Check the generated log files for detailed error information
2. Run with `--dry-run` flag first to test changes safely  
3. Review the example usage patterns in `example_usage.py`
4. Ensure product data format matches expected structure
5. Verify Odoo connection settings and permissions

---

**Last Updated**: August 2025  
**Version**: 1.0.0  
**Author**: Inventory Management Specialist