#!/bin/bash

# Gym+Coffee to Odoo Data Pipeline Runner
# This script executes the complete data transformation pipeline

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DATA_DIR="../data"
OUTPUT_DIR="../data/transformed"
LOG_FILE="${OUTPUT_DIR}/pipeline_execution.log"

# Default values
NUM_CUSTOMERS=1000
NUM_ORDERS=2000
RUN_TESTS=false
RUN_ANALYSIS=false
SKIP_VALIDATION=false

# Functions
print_header() {
    echo -e "${BLUE}"
    echo "=============================================================="
    echo "           GYM+COFFEE TO ODOO DATA PIPELINE"
    echo "=============================================================="
    echo -e "${NC}"
}

print_step() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
    exit 1
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Help function
show_help() {
    cat << EOF
Gym+Coffee to Odoo Data Pipeline Runner

Usage: $0 [OPTIONS]

OPTIONS:
    -c, --customers NUM     Number of customers to generate (default: 1000)
    -o, --orders NUM        Number of orders to generate (default: 2000)
    -t, --test             Run tests before pipeline execution
    -a, --analyze          Run data analysis after pipeline
    -s, --skip-validation  Skip data validation step
    -p, --products-only    Transform products only
    -u, --customers-only   Generate customers only
    -r, --orders-only      Generate orders only
    -v, --validate-only    Run validation only
    -h, --help             Show this help message

EXAMPLES:
    $0                          # Run full pipeline with defaults
    $0 -c 2000 -o 5000         # Generate more data
    $0 -t -a                   # Run with tests and analysis
    $0 --products-only         # Transform products only
    $0 --validate-only         # Validate existing data

REQUIREMENTS:
    - Python 3.8+
    - Required Python packages (see requirements.txt)
    - Source data files in correct locations:
      * ${DATA_DIR}/gym_plus_coffee_products.json
      * ${DATA_DIR}/dataco/DataCoSupplyChainDataset.csv

OUTPUT:
    Transformed data files will be created in: ${OUTPUT_DIR}
    
EOF
}

# Check prerequisites
check_prerequisites() {
    print_step "Checking prerequisites..."
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is required but not installed"
    fi
    
    # Check required files
    REQUIRED_FILES=(
        "${DATA_DIR}/gym_plus_coffee_products.json"
        "${DATA_DIR}/dataco/DataCoSupplyChainDataset.csv"
    )
    
    for file in "${REQUIRED_FILES[@]}"; do
        if [ ! -f "$file" ]; then
            print_error "Required file not found: $file"
        fi
    done
    
    # Check Python packages
    python3 -c "import pandas, numpy, faker" 2>/dev/null || {
        print_error "Required Python packages not installed. Run: pip install -r requirements.txt"
    }
    
    # Create output directory
    mkdir -p "$OUTPUT_DIR"
    
    print_success "All prerequisites satisfied"
}

# Setup logging
setup_logging() {
    # Create log file
    touch "$LOG_FILE"
    print_info "Pipeline execution log: $LOG_FILE"
    
    # Log start time
    echo "=== Pipeline execution started at $(date) ===" >> "$LOG_FILE"
}

# Run tests
run_tests() {
    if [ "$RUN_TESTS" = true ]; then
        print_step "Running test suite..."
        cd "$SCRIPT_DIR"
        
        if python3 test_transformations.py >> "$LOG_FILE" 2>&1; then
            print_success "All tests passed"
        else
            print_error "Tests failed. Check log file: $LOG_FILE"
        fi
    fi
}

# Install dependencies
install_dependencies() {
    print_step "Checking Python dependencies..."
    
    cd "$SCRIPT_DIR"
    
    if pip3 show pandas numpy faker > /dev/null 2>&1; then
        print_success "Dependencies already installed"
    else
        print_info "Installing required packages..."
        if pip3 install -r requirements.txt >> "$LOG_FILE" 2>&1; then
            print_success "Dependencies installed successfully"
        else
            print_error "Failed to install dependencies. Check log file: $LOG_FILE"
        fi
    fi
}

# Run pipeline steps
run_products_transformation() {
    print_step "Transforming products..."
    cd "$SCRIPT_DIR"
    
    if python3 transform_products.py \
        --source "${DATA_DIR}/gym_plus_coffee_products.json" \
        --output "$OUTPUT_DIR" >> "$LOG_FILE" 2>&1; then
        print_success "Products transformed successfully"
    else
        print_error "Product transformation failed. Check log: $LOG_FILE"
    fi
}

run_customer_generation() {
    print_step "Generating customers..."
    cd "$SCRIPT_DIR"
    
    if python3 generate_customers.py \
        --dataco "${DATA_DIR}/dataco/DataCoSupplyChainDataset.csv" \
        --output "$OUTPUT_DIR" \
        --count "$NUM_CUSTOMERS" >> "$LOG_FILE" 2>&1; then
        print_success "Customers generated successfully"
    else
        print_error "Customer generation failed. Check log: $LOG_FILE"
    fi
}

run_order_generation() {
    print_step "Generating orders..."
    cd "$SCRIPT_DIR"
    
    if python3 create_orders.py \
        --dataco "${DATA_DIR}/dataco/DataCoSupplyChainDataset.csv" \
        --customers "${OUTPUT_DIR}/odoo_customers.csv" \
        --products "${OUTPUT_DIR}/odoo_product_variants.csv" \
        --output "$OUTPUT_DIR" \
        --count "$NUM_ORDERS" >> "$LOG_FILE" 2>&1; then
        print_success "Orders generated successfully"
    else
        print_error "Order generation failed. Check log: $LOG_FILE"
    fi
}

run_validation() {
    if [ "$SKIP_VALIDATION" = false ]; then
        print_step "Validating data integrity..."
        cd "$SCRIPT_DIR"
        
        if python3 data_pipeline.py --validate-only >> "$LOG_FILE" 2>&1; then
            print_success "Data validation passed"
        else
            print_error "Data validation failed. Check log: $LOG_FILE"
        fi
    fi
}

run_analysis() {
    if [ "$RUN_ANALYSIS" = true ]; then
        print_step "Running data analysis..."
        cd "$SCRIPT_DIR"
        
        if python3 analyze_data.py --data-dir "$OUTPUT_DIR" >> "$LOG_FILE" 2>&1; then
            print_success "Data analysis completed"
        else
            print_error "Data analysis failed. Check log: $LOG_FILE"
        fi
    fi
}

# Show summary
show_summary() {
    print_step "Pipeline execution completed!"
    
    echo
    echo "📊 EXECUTION SUMMARY:"
    echo "  Output Directory: $OUTPUT_DIR"
    echo "  Log File: $LOG_FILE"
    echo "  Customers Generated: $NUM_CUSTOMERS"
    echo "  Orders Generated: $NUM_ORDERS"
    
    # Count output files
    if [ -d "$OUTPUT_DIR" ]; then
        csv_count=$(find "$OUTPUT_DIR" -name "*.csv" | wc -l)
        json_count=$(find "$OUTPUT_DIR" -name "*.json" | wc -l)
        echo "  Output Files Created: $csv_count CSV, $json_count JSON"
    fi
    
    echo
    echo "🎯 NEXT STEPS:"
    echo "  1. Review output files in: $OUTPUT_DIR"
    echo "  2. Import CSV files into Odoo"
    echo "  3. Verify data integrity in Odoo"
    
    if [ "$RUN_ANALYSIS" = true ]; then
        analysis_file=$(find "$OUTPUT_DIR" -name "analysis_report_*.json" | head -1)
        if [ -n "$analysis_file" ]; then
            echo "  4. Review analysis report: $analysis_file"
        fi
    fi
    
    echo
    print_success "All operations completed successfully! 🎉"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -c|--customers)
            NUM_CUSTOMERS="$2"
            shift 2
            ;;
        -o|--orders)
            NUM_ORDERS="$2"
            shift 2
            ;;
        -t|--test)
            RUN_TESTS=true
            shift
            ;;
        -a|--analyze)
            RUN_ANALYSIS=true
            shift
            ;;
        -s|--skip-validation)
            SKIP_VALIDATION=true
            shift
            ;;
        -p|--products-only)
            PRODUCTS_ONLY=true
            shift
            ;;
        -u|--customers-only)
            CUSTOMERS_ONLY=true
            shift
            ;;
        -r|--orders-only)
            ORDERS_ONLY=true
            shift
            ;;
        -v|--validate-only)
            VALIDATE_ONLY=true
            shift
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Main execution
main() {
    print_header
    
    check_prerequisites
    setup_logging
    install_dependencies
    run_tests
    
    # Determine execution mode
    if [ "$PRODUCTS_ONLY" = true ]; then
        run_products_transformation
    elif [ "$CUSTOMERS_ONLY" = true ]; then
        run_customer_generation
    elif [ "$ORDERS_ONLY" = true ]; then
        run_order_generation
    elif [ "$VALIDATE_ONLY" = true ]; then
        run_validation
    else
        # Full pipeline
        run_products_transformation
        run_customer_generation
        run_order_generation
        run_validation
    fi
    
    run_analysis
    show_summary
}

# Execute main function
main "$@"