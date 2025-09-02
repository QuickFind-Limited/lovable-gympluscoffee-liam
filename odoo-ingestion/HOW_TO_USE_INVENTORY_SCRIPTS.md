# How to Use Inventory Analysis Scripts

## 🚀 Quick Start

### Prerequisites
1. Ensure Python 3.7+ is installed
2. Install required packages:
   ```bash
   pip install python-dotenv
   ```
3. Configure your `.env` file with Odoo credentials

### Environment Setup
Create a `.env` file with your Odoo connection details:
```env
ODOO_URL=https://your-odoo-instance.odoo.com
ODOO_DB=your-database-name
ODOO_USERNAME=your-username
ODOO_PASSWORD=your-password
```

## 📊 Available Scripts

### 1. Basic Inventory Analysis (`check_inventory.py`)
**Purpose**: Analyzes only stockable products and their inventory levels

**Usage**:
```bash
python3 check_inventory.py
```

**What it does**:
- Connects to Odoo via XML-RPC
- Analyzes stockable products only (`type = 'product'`)
- Checks stock levels and inventory valuation
- Identifies low stock, out-of-stock, and overstocked items
- Generates business recommendations

**Output**:
- Console report with inventory overview
- JSON file with detailed analysis
- Log file for troubleshooting

### 2. Complete Product Analysis (`check_all_products_inventory.py`)
**Purpose**: Comprehensive analysis of ALL products (stockable, consumable, services)

**Usage**:
```bash
python3 check_all_products_inventory.py
```

**What it does**:
- Analyzes all product types in the catalog
- Provides product mix insights
- Shows category distribution
- Identifies inventory management opportunities
- Generates strategic business recommendations

**Output**:
- Detailed console report covering all products
- Complete analysis JSON file
- Business insights and recommendations

## 📋 Understanding the Reports

### Console Output Sections

#### 1. Product Catalog Overview
- Total products by type (stockable, consumable, service)
- Product mix percentages
- Overall catalog health

#### 2. Inventory Analysis
- Products with/without inventory
- Total inventory value
- Coverage percentages

#### 3. Stock Alerts
- Out of stock items count
- Low stock items count  
- Overstocked items count

#### 4. Category Breakdown
- Products per category
- Category inventory values
- Top categories by value

#### 5. Sample Products
- Representative products from catalog
- Product details (type, cost, stock)

#### 6. Business Recommendations
- Actionable insights
- Priority recommendations
- Strategic suggestions

### Generated Files

#### JSON Reports
- Complete analysis data in structured format
- Suitable for integration with other systems
- Contains all raw data and calculations

#### Log Files
- Connection and processing logs
- Error tracking and debugging
- Performance metrics

## 🔧 Customization Options

### Modifying Analysis Parameters

#### Time Periods
```python
# In get_recent_stock_moves method
recent_moves = self.get_recent_stock_moves(days=30)  # Change days as needed
```

#### Sample Sizes
```python
# Number of items in reports
low_stock_items=low_stock_items[:20],  # Change to show more/fewer items
out_of_stock_items=out_of_stock_items[:20],
```

#### Alert Thresholds
Modify the stock level checking logic to adjust when items are considered:
- Low stock
- Out of stock  
- Overstocked

### Adding Custom Fields
To include additional product fields in analysis:
```python
'fields': [
    'name', 'default_code', 'categ_id',
    'your_custom_field',  # Add custom fields here
    # ... existing fields
]
```

## 🚨 Troubleshooting

### Common Issues

#### 1. Connection Errors
- Verify `.env` file credentials
- Check network connectivity to Odoo instance
- Ensure XML-RPC is enabled

#### 2. Authentication Failures
- Verify username and password
- Check if user has required permissions
- Confirm database name is correct

#### 3. No Products Found
- Check if products exist in database
- Verify product types are correctly set
- Review search filters in scripts

#### 4. Permission Errors
- Ensure user has read access to required models:
  - `product.product`
  - `stock.quant`
  - `product.category`
  - `stock.location`
  - `stock.move`

### Debug Mode
Enable detailed logging by modifying logging level:
```python
logging.basicConfig(level=logging.DEBUG)  # Instead of INFO
```

## 📈 Advanced Usage

### Automated Reporting
Set up cron job for regular analysis:
```bash
# Run daily at 8 AM
0 8 * * * cd /path/to/scripts && python3 check_all_products_inventory.py
```

### Integration with Other Systems
- JSON output can be consumed by business intelligence tools
- Raw data available for custom analysis
- API-style access to inventory metrics

### Performance Optimization
For large databases:
- Implement batch processing
- Add progress indicators
- Configure connection pooling

## 🎯 Best Practices

### Regular Monitoring
1. Run complete analysis weekly
2. Monitor daily for stock alerts
3. Review recommendations monthly
4. Track trends over time

### Data Quality
1. Maintain clean product categories
2. Keep reorder points updated
3. Verify product types are correct
4. Regular data validation

### Business Intelligence
1. Export data for trend analysis
2. Create dashboards from JSON output
3. Set up automated alerts
4. Monitor KPIs regularly

---

**Need Help?**
- Check log files for detailed error messages
- Verify Odoo permissions and connectivity
- Review script documentation and comments
- Test connection with simple queries first