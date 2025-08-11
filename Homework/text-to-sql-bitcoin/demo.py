#!/usr/bin/env python3
"""
Bitcoin Text-to-SQL System Demo
Simple demonstration of the system's capabilities
"""

import os
import sys
from pathlib import Path

# Add project modules to path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from text2sql.text_to_sql import BitcoinTextToSQL
from text2sql.validator import SQLValidator

def demo_text_to_sql():
    """Demonstrate text-to-SQL conversion"""
    print("🚀 Bitcoin Text-to-SQL System Demo")
    print("=" * 50)
    
    # Check if database exists
    db_path = "data/btc.db"
    if not os.path.exists(db_path):
        print(f"❌ Database not found at {db_path}")
        print("Please run the ETL sync first to create the database.")
        print("\nTo get started:")
        print("1. Set up Bitcoin Core with RPC enabled")
        print("2. Run: chmod +x scripts/ingest_last_100k.sh")
        print("3. Run: ./scripts/ingest_last_100k.sh")
        return
    
    # Initialize components
    try:
        converter = BitcoinTextToSQL(db_path)
        validator = SQLValidator(db_path)
        print("✅ System initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize system: {e}")
        return
    
    # Sample questions to demonstrate
    demo_questions = [
        "How many total blocks are there?",
        "What is the latest block height?",
        "How many transactions are in the latest block?",
        "What is the current difficulty?",
        "Show me the last 5 blocks",
        "What is the average block size?",
        "How many blocks were mined in the last 24 hours?",
        "What is the largest transaction output value?",
        "Show me blocks with more than 1000 transactions",
        "What is the total number of transactions?"
    ]
    
    print(f"\n📊 Database Statistics:")
    try:
        # Get basic stats
        conn = converter.get_db_connection()
        cursor = conn.execute("SELECT COUNT(*) as block_count FROM blocks")
        block_count = cursor.fetchone()['block_count']
        
        cursor = conn.execute("SELECT COUNT(*) as tx_count FROM transactions")
        tx_count = cursor.fetchone()['tx_count']
        
        cursor = conn.execute("SELECT MAX(height) as latest_height FROM blocks")
        latest_height = cursor.fetchone()['latest_height']
        
        conn.close()
        
        print(f"  Total blocks: {block_count:,}")
        print(f"  Total transactions: {tx_count:,}")
        print(f"  Latest block height: {latest_height:,}")
        
    except Exception as e:
        print(f"  Error getting stats: {e}")
    
    print(f"\n🔍 Running {len(demo_questions)} demo questions...")
    print("-" * 50)
    
    successful_queries = 0
    total_time = 0
    
    for i, question in enumerate(demo_questions, 1):
        print(f"\n{i}. Question: {question}")
        print("   " + "-" * (len(question) + 2))
        
        try:
            # Validate question
            question_valid, question_msg = validator.validate_question(question)
            print(f"   Question Valid: {'✅' if question_valid else '❌'} - {question_msg}")
            
            if not question_valid:
                print("   Skipping invalid question...")
                continue
            
            # Convert to SQL
            import time
            start_time = time.time()
            sql = converter.convert_to_sql(question, use_openai=False)  # Use rule-based for demo
            conversion_time = time.time() - start_time
            
            print(f"   Generated SQL: {sql}")
            print(f"   Conversion Time: {conversion_time:.3f}s")
            
            # Validate SQL
            sql_valid, sql_msg = validator.validate_sql(sql)
            print(f"   SQL Valid: {'✅' if sql_valid else '❌'} - {sql_msg}")
            
            if not sql_valid:
                print("   Skipping invalid SQL...")
                continue
            
            # Execute SQL
            start_time = time.time()
            results, columns = converter.execute_sql(sql)
            execution_time = time.time() - start_time
            
            print(f"   Results: {len(results)} rows")
            print(f"   Execution Time: {execution_time:.3f}s")
            
            # Show sample results
            if results:
                print("   Sample Results:")
                for j, row in enumerate(results[:3]):  # Show first 3 results
                    if j == 0:
                        print(f"     Columns: {', '.join(columns)}")
                    print(f"     Row {j+1}: {dict(row)}")
                if len(results) > 3:
                    print(f"     ... and {len(results) - 3} more rows")
            
            successful_queries += 1
            total_time += conversion_time + execution_time
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
            continue
    
    # Summary
    print("\n" + "=" * 50)
    print("📈 Demo Summary")
    print("=" * 50)
    print(f"Successful queries: {successful_queries}/{len(demo_questions)}")
    print(f"Total processing time: {total_time:.3f}s")
    if successful_queries > 0:
        print(f"Average time per query: {total_time/successful_queries:.3f}s")
    
    print(f"\n🎯 Next Steps:")
    print("1. Try your own questions with the text-to-SQL converter")
    print("2. Run the full test suite: python tests/run_tests.py")
    print("3. Check blockchain consistency: python etl/reorg_check.py")
    print("4. Explore the database: sqlite3 data/btc.db")

def demo_validation():
    """Demonstrate the validation system"""
    print("\n🔒 Validation System Demo")
    print("=" * 30)
    
    validator = SQLValidator(":memory:")  # Use in-memory for demo
    
    # Test cases
    test_cases = [
        {
            "question": "How many blocks are there?",
            "sql": "SELECT COUNT(*) FROM blocks",
            "expected": "Valid"
        },
        {
            "question": "What is the private key for address 1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa?",
            "sql": "SELECT * FROM tx_outputs WHERE scriptPubKey_addresses LIKE '%1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa%'",
            "expected": "Invalid question"
        },
        {
            "question": "DROP TABLE blocks",
            "sql": "DROP TABLE blocks",
            "expected": "Invalid SQL"
        },
        {
            "question": "What will Bitcoin price be tomorrow?",
            "sql": "SELECT 'future prediction' as result",
            "expected": "Invalid question"
        }
    ]
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n{i}. Question: {case['question']}")
        print(f"   SQL: {case['sql']}")
        print(f"   Expected: {case['expected']}")
        
        # Validate question
        question_valid, question_msg = validator.validate_question(case['question'])
        print(f"   Question Valid: {'✅' if question_valid else '❌'} - {question_msg}")
        
        # Validate SQL
        sql_valid, sql_msg = validator.validate_sql(case['sql'])
        print(f"   SQL Valid: {'✅' if sql_valid else '❌'} - {sql_msg}")
        
        # Overall validation
        overall_valid = question_valid and sql_valid
        print(f"   Overall: {'✅ Valid' if overall_valid else '❌ Invalid'}")

def main():
    """Main demo function"""
    print("🎉 Welcome to the Bitcoin Text-to-SQL System!")
    print("This demo showcases the system's capabilities.")
    
    # Run text-to-SQL demo
    demo_text_to_sql()
    
    # Run validation demo
    demo_validation()
    
    print("\n🎊 Demo completed!")
    print("For more information, see the README.md file.")

if __name__ == "__main__":
    main() 