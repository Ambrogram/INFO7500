#!/bin/bash

# Bitcoin ETL - Ingest Last 100k Blocks
# This script runs the ETL sync to fetch the last 100,000 blocks

set -e

echo "Bitcoin ETL - Ingesting Last 100k Blocks"
echo "=========================================="

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is required but not installed."
    exit 1
fi

# Check if required Python packages are installed
echo "Checking Python dependencies..."
python3 -c "import sqlite3, requests, openai" 2>/dev/null || {
    echo "Installing required Python packages..."
    pip3 install requests openai
}

# Set default values
DB_PATH="../data/btc.db"
ETL_SCRIPT="../etl/etl_sync.py"
MAX_BLOCKS=100000

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --db-path)
            DB_PATH="$2"
            shift 2
            ;;
        --max-blocks)
            MAX_BLOCKS="$2"
            shift 2
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo "Options:"
            echo "  --db-path PATH     Database file path (default: ../data/btc.db)"
            echo "  --max-blocks N     Maximum number of blocks to sync (default: 100000)"
            echo "  --help             Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Create data directory if it doesn't exist
mkdir -p "$(dirname "$DB_PATH")"

echo "Configuration:"
echo "  Database: $DB_PATH"
echo "  Max Blocks: $MAX_BLOCKS"
echo "  ETL Script: $ETL_SCRIPT"
echo ""

# Check if bitcoind is running
echo "Checking if bitcoind is accessible..."
if ! curl -s --user bitcoinrpc:your_rpc_password http://127.0.0.1:8332/ > /dev/null 2>&1; then
    echo "Warning: bitcoind RPC not accessible at http://127.0.0.1:8332/"
    echo "Make sure bitcoind is running and RPC is enabled."
    echo "You may need to update the RPC credentials in the ETL script."
    echo ""
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Check disk space
echo "Checking available disk space..."
AVAILABLE_SPACE=$(df . | awk 'NR==2 {print $4}')
REQUIRED_SPACE=50000000  # 50GB in KB
if [ "$AVAILABLE_SPACE" -lt "$REQUIRED_SPACE" ]; then
    echo "Warning: Low disk space. Available: ${AVAILABLE_SPACE}KB, Recommended: ${REQUIRED_SPACE}KB"
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Run the ETL sync
echo "Starting ETL sync..."
echo "This may take several hours depending on your system and network."
echo ""

# Set environment variables for the ETL script
export PYTHONPATH="$(pwd)/..:$PYTHONPATH"

# Run the ETL script with the specified parameters
python3 "$ETL_SCRIPT" --max-blocks "$MAX_BLOCKS" --db-path "$DB_PATH"

echo ""
echo "ETL sync completed!"
echo "Database location: $DB_PATH"

# Show database statistics
if [ -f "$DB_PATH" ]; then
    echo ""
    echo "Database Statistics:"
    echo "==================="
    
    # Get block count
    BLOCK_COUNT=$(sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM blocks;" 2>/dev/null || echo "0")
    echo "Total blocks: $BLOCK_COUNT"
    
    # Get transaction count
    TX_COUNT=$(sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM transactions;" 2>/dev/null || echo "0")
    echo "Total transactions: $TX_COUNT"
    
    # Get database size
    DB_SIZE=$(du -h "$DB_PATH" | cut -f1)
    echo "Database size: $DB_SIZE"
    
    # Get latest block height
    LATEST_HEIGHT=$(sqlite3 "$DB_PATH" "SELECT MAX(height) FROM blocks;" 2>/dev/null || echo "0")
    echo "Latest block height: $LATEST_HEIGHT"
fi

echo ""
echo "Next steps:"
echo "1. Run tests: cd tests && python3 run_tests.py"
echo "2. Try the text-to-SQL converter: cd text2sql && python3 text_to_sql.py"
echo "3. View the database: sqlite3 $DB_PATH" 