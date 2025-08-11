#!/usr/bin/env python3
"""
Text-to-SQL Converter for Bitcoin Data
Converts natural language questions to SQL queries and executes them
"""

import sqlite3
import json
import re
from typing import Dict, List, Optional, Tuple, Any
import logging
from datetime import datetime, timedelta
import openai
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BitcoinTextToSQL:
    def __init__(self, db_path: str, openai_api_key: str = None):
        self.db_path = db_path
        self.openai_api_key = openai_api_key or os.getenv('OPENAI_API_KEY')
        
        if self.openai_api_key:
            openai.api_key = self.openai_api_key
        
        # Database schema information for context
        self.schema_info = self._get_schema_info()
        
        # Common Bitcoin terms and their SQL mappings
        self.term_mappings = {
            'block': 'blocks',
            'transaction': 'transactions',
            'tx': 'transactions',
            'input': 'tx_inputs',
            'output': 'tx_outputs',
            'address': 'tx_outputs.scriptPubKey_addresses',
            'hash': 'blocks.hash',
            'height': 'blocks.height',
            'time': 'blocks.time',
            'size': 'blocks.size',
            'weight': 'blocks.weight',
            'difficulty': 'blocks.difficulty',
            'fee': 'block_stats.total_fees',
            'value': 'tx_outputs.value',
            'amount': 'tx_outputs.value',
            'btc': 'tx_outputs.value',
            'bitcoin': 'tx_outputs.value',
            'confirmations': 'transactions.confirmations',
            'date': 'blocks.time',
            'timestamp': 'blocks.time'
        }
    
    def _get_schema_info(self) -> str:
        """Get database schema information for context"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            schema_info = "Available tables:\n"
            for table in tables:
                cursor = conn.execute(f"PRAGMA table_info({table})")
                columns = cursor.fetchall()
                schema_info += f"\n{table}:\n"
                for col in columns:
                    schema_info += f"  - {col[1]} ({col[2]})\n"
            
            conn.close()
            return schema_info
        except Exception as e:
            logger.error(f"Failed to get schema info: {e}")
            return "Database schema information unavailable"
    
    def _preprocess_question(self, question: str) -> str:
        """Preprocess the natural language question"""
        # Convert to lowercase for better matching
        question = question.lower()
        
        # Replace common Bitcoin terms with their SQL equivalents
        for term, sql_term in self.term_mappings.items():
            if term in question:
                question = question.replace(term, sql_term)
        
        return question
    
    def _generate_sql_with_openai(self, question: str) -> str:
        """Generate SQL using OpenAI API"""
        if not self.openai_api_key:
            raise Exception("OpenAI API key not available")
        
        prompt = f"""
You are a SQL expert for Bitcoin blockchain data. Convert the following natural language question to SQL.

Database Schema:
{self.schema_info}

Important Notes:
- Use SQLite syntax
- Bitcoin amounts are stored in BTC (not satoshis)
- Timestamps are Unix timestamps
- Addresses are stored as JSON arrays in scriptPubKey_addresses
- Use proper JOINs when querying across tables
- Always use LIMIT for large result sets

Question: {question}

Generate only the SQL query, no explanations:
"""
        
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a SQL expert. Generate only SQL queries, no explanations."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.1
            )
            
            sql = response.choices[0].message.content.strip()
            
            # Clean up the SQL
            sql = re.sub(r'```sql\s*', '', sql)
            sql = re.sub(r'\s*```', '', sql)
            
            return sql
            
        except Exception as e:
            logger.error(f"OpenAI API call failed: {e}")
            raise
    
    def _generate_sql_rule_based(self, question: str) -> str:
        """Generate SQL using rule-based approach"""
        question = question.lower()
        
        # Simple pattern matching for common questions
        if 'total' in question and 'blocks' in question:
            return "SELECT COUNT(*) as total_blocks FROM blocks"
        
        elif 'latest' in question and 'block' in question:
            return "SELECT * FROM blocks ORDER BY height DESC LIMIT 1"
        
        elif 'transaction' in question and 'count' in question:
            return "SELECT COUNT(*) as total_transactions FROM transactions"
        
        elif 'difficulty' in question and 'current' in question:
            return "SELECT difficulty FROM blocks ORDER BY height DESC LIMIT 1"
        
        elif 'block' in question and 'size' in question and 'average' in question:
            return "SELECT AVG(size) as avg_block_size FROM blocks"
        
        elif 'address' in question and 'balance' in question:
            # This is complex - would need more context
            return "SELECT 'Complex query - address balance requires specific address' as note"
        
        else:
            # Default fallback
            return "SELECT 'Unable to generate SQL for this question' as error"
    
    def convert_to_sql(self, question: str, use_openai: bool = True) -> str:
        """Convert natural language question to SQL"""
        try:
            if use_openai and self.openai_api_key:
                return self._generate_sql_with_openai(question)
            else:
                return self._generate_sql_rule_based(question)
        except Exception as e:
            logger.error(f"Failed to convert question to SQL: {e}")
            return f"SELECT 'Error: {str(e)}' as error"
    
    def execute_sql(self, sql: str) -> Tuple[List[Dict], List[str]]:
        """Execute SQL query and return results"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            
            cursor = conn.execute(sql)
            
            # Get column names
            columns = [description[0] for description in cursor.description]
            
            # Get results
            results = []
            for row in cursor.fetchall():
                result = {}
                for i, col in enumerate(columns):
                    value = row[i]
                    # Convert datetime if it's a timestamp
                    if isinstance(value, int) and col in ['time', 'block_time', 'created_at']:
                        try:
                            value = datetime.fromtimestamp(value).isoformat()
                        except:
                            pass
                    result[col] = value
                results.append(result)
            
            conn.close()
            return results, columns
            
        except Exception as e:
            logger.error(f"SQL execution failed: {e}")
            return [], [f"Error: {str(e)}"]
    
    def query_bitcoin_data(self, question: str, use_openai: bool = True) -> Dict[str, Any]:
        """Main method to convert question to SQL and execute it"""
        try:
            # Convert question to SQL
            sql = self.convert_to_sql(question, use_openai)
            
            # Execute SQL
            results, columns = self.execute_sql(sql)
            
            return {
                'question': question,
                'sql': sql,
                'results': results,
                'columns': columns,
                'row_count': len(results),
                'success': True
            }
            
        except Exception as e:
            logger.error(f"Query failed: {e}")
            return {
                'question': question,
                'sql': 'Error occurred',
                'results': [],
                'columns': [],
                'row_count': 0,
                'success': False,
                'error': str(e)
            }
    
    def get_sample_questions(self) -> List[str]:
        """Get sample questions for testing"""
        return [
            "How many total blocks are there?",
            "What is the latest block?",
            "How many transactions are there?",
            "What is the current difficulty?",
            "What is the average block size?",
            "Show me the last 10 blocks",
            "What is the total number of transactions in the latest block?",
            "Show me blocks from the last 24 hours",
            "What is the largest transaction by value?",
            "How many blocks were mined today?"
        ]

def main():
    """Main function for testing"""
    # Configuration
    DB_PATH = "../data/btc.db"
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    
    # Initialize converter
    converter = BitcoinTextToSQL(DB_PATH, OPENAI_API_KEY)
    
    # Test with sample questions
    sample_questions = converter.get_sample_questions()
    
    print("Bitcoin Text-to-SQL Converter")
    print("=" * 50)
    
    for question in sample_questions[:3]:  # Test first 3 questions
        print(f"\nQuestion: {question}")
        print("-" * 30)
        
        result = converter.query_bitcoin_data(question, use_openai=bool(OPENAI_API_KEY))
        
        print(f"SQL: {result['sql']}")
        print(f"Results: {result['row_count']} rows")
        
        if result['results']:
            print("Sample data:")
            for i, row in enumerate(result['results'][:3]):  # Show first 3 rows
                print(f"  Row {i+1}: {dict(row)}")

if __name__ == "__main__":
    main() 