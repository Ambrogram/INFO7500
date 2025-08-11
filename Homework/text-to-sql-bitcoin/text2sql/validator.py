#!/usr/bin/env python3
"""
SQL Validator for Bitcoin Text-to-SQL System
Validates SQL queries against whitelist and rejects unanswerable questions
"""

import re
import sqlite3
from typing import Dict, List, Tuple, Optional, Set
import logging

logger = logging.getLogger(__name__)

class SQLValidator:
    def __init__(self, db_path: str):
        self.db_path = db_path
        
        # Allowed SQL keywords and functions
        self.allowed_keywords = {
            'SELECT', 'FROM', 'WHERE', 'JOIN', 'LEFT', 'RIGHT', 'INNER', 'OUTER',
            'ON', 'AND', 'OR', 'NOT', 'IN', 'EXISTS', 'BETWEEN', 'LIKE', 'IS',
            'NULL', 'ORDER', 'BY', 'GROUP', 'HAVING', 'LIMIT', 'OFFSET',
            'DISTINCT', 'AS', 'CASE', 'WHEN', 'THEN', 'ELSE', 'END',
            'COUNT', 'SUM', 'AVG', 'MIN', 'MAX', 'ROUND', 'CAST', 'STRFTIME',
            'DATETIME', 'UNIXEPOCH', 'JSON_EXTRACT', 'JSON_ARRAY_LENGTH'
        }
        
        # Allowed table names
        self.allowed_tables = {
            'blocks', 'transactions', 'tx_inputs', 'tx_outputs', 'block_stats',
            'v_block_summary', 'v_transaction_details'
        }
        
        # Allowed column patterns (regex)
        self.allowed_column_patterns = [
            r'^[a-zA-Z_][a-zA-Z0-9_]*$',  # Standard column names
            r'^[a-zA-Z_][a-zA-Z0-9_]*\.[a-zA-Z_][a-zA-Z0-9_]*$',  # Table.column
            r'^COUNT\(\*\)$',  # COUNT(*)
            r'^SUM\([a-zA-Z_][a-zA-Z0-9_]*\)$',  # SUM(column)
            r'^AVG\([a-zA-Z_][a-zA-Z0-9_]*\)$',  # AVG(column)
            r'^MIN\([a-zA-Z_][a-zA-Z0-9_]*\)$',  # MIN(column)
            r'^MAX\([a-zA-Z_][a-zA-Z0-9_]*\)$',  # MAX(column)
            r'^ROUND\([^)]+\)$',  # ROUND(expression)
            r'^CAST\([^)]+\)$',  # CAST(expression)
            r'^STRFTIME\([^)]+\)$',  # STRFTIME(expression)
            r'^DATETIME\([^)]+\)$',  # DATETIME(expression)
            r'^UNIXEPOCH\([^)]+\)$',  # UNIXEPOCH(expression)
            r'^JSON_EXTRACT\([^)]+\)$',  # JSON_EXTRACT(expression)
            r'^JSON_ARRAY_LENGTH\([^)]+\)$',  # JSON_ARRAY_LENGTH(expression)
        ]
        
        # Dangerous patterns that should be rejected
        self.dangerous_patterns = [
            r'DROP\s+TABLE',  # DROP TABLE
            r'DELETE\s+FROM',  # DELETE FROM
            r'UPDATE\s+SET',   # UPDATE SET
            r'INSERT\s+INTO',  # INSERT INTO
            r'ALTER\s+TABLE',  # ALTER TABLE
            r'CREATE\s+TABLE', # CREATE TABLE
            r'ATTACH\s+DATABASE', # ATTACH DATABASE
            r'DETACH\s+DATABASE', # DETACH DATABASE
            r'PRAGMA',         # PRAGMA commands
            r'VACUUM',         # VACUUM
            r'ANALYZE',        # ANALYZE
            r'REINDEX',        # REINDEX
            r'--',             # SQL comments
            r'/\*',            # Multi-line comments
            r'\*/',            # Multi-line comments
            r'EXEC',           # EXEC commands
            r'EXECUTE',        # EXECUTE commands
            r'xp_',            # Extended stored procedures
            r'sp_',            # Stored procedures
        ]
        
        # Questions that are too complex or unanswerable
        self.unanswerable_patterns = [
            r'private\s+key',  # Private key related
            r'seed\s+phrase',  # Seed phrase related
            r'wallet\s+password', # Wallet password
            r'encryption\s+key', # Encryption keys
            r'decrypt',        # Decryption
            r'crack',          # Cracking attempts
            r'hack',           # Hacking attempts
            r'exploit',        # Exploits
            r'vulnerability',  # Vulnerabilities
            r'zero\s+day',     # Zero-day exploits
            r'future\s+price', # Future price predictions
            r'predict\s+price', # Price predictions
            r'when\s+will\s+bitcoin', # Future predictions
            r'next\s+halving', # Next halving prediction
            r'mining\s+profitability', # Mining profitability
            r'optimal\s+mining', # Optimal mining strategies
            r'best\s+mining\s+pool', # Mining pool recommendations
            r'wallet\s+recommendation', # Wallet recommendations
            r'investment\s+advice', # Investment advice
            r'legal\s+advice', # Legal advice
            r'tax\s+advice',   # Tax advice
        ]
    
    def validate_sql(self, sql: str) -> Tuple[bool, str]:
        """Validate SQL query for safety and correctness"""
        try:
            # Check for dangerous patterns
            if self._has_dangerous_patterns(sql):
                return False, "Query contains dangerous operations"
            
            # Check SQL syntax
            if not self._is_valid_sql_syntax(sql):
                return False, "Invalid SQL syntax"
            
            # Check for allowed keywords only
            if not self._has_only_allowed_keywords(sql):
                return False, "Query contains disallowed SQL keywords"
            
            # Check table names
            if not self._has_only_allowed_tables(sql):
                return False, "Query references disallowed tables"
            
            # Check column names
            if not self._has_only_allowed_columns(sql):
                return False, "Query references disallowed columns"
            
            # Check for reasonable limits
            if not self._has_reasonable_limits(sql):
                return False, "Query lacks reasonable limits"
            
            return True, "Query is valid"
            
        except Exception as e:
            logger.error(f"SQL validation failed: {e}")
            return False, f"Validation error: {str(e)}"
    
    def validate_question(self, question: str) -> Tuple[bool, str]:
        """Validate if a question is answerable"""
        question_lower = question.lower()
        
        # Check for unanswerable patterns
        for pattern in self.unanswerable_patterns:
            if re.search(pattern, question_lower, re.IGNORECASE):
                return False, f"Question contains unanswerable pattern: {pattern}"
        
        # Check question complexity
        if self._is_question_too_complex(question):
            return False, "Question is too complex to answer reliably"
        
        # Check for vague or ambiguous questions
        if self._is_question_vague(question):
            return False, "Question is too vague or ambiguous"
        
        return True, "Question is answerable"
    
    def _has_dangerous_patterns(self, sql: str) -> bool:
        """Check if SQL contains dangerous patterns"""
        sql_upper = sql.upper()
        for pattern in self.dangerous_patterns:
            if re.search(pattern, sql_upper, re.IGNORECASE):
                return True
        return False
    
    def _is_valid_sql_syntax(self, sql: str) -> bool:
        """Basic SQL syntax validation"""
        try:
            # Try to parse the SQL with SQLite
            conn = sqlite3.connect(':memory:')
            conn.execute("CREATE TABLE test (id INTEGER)")
            conn.execute(sql.replace('FROM blocks', 'FROM test').replace('FROM transactions', 'FROM test'))
            conn.close()
            return True
        except:
            return False
    
    def _has_only_allowed_keywords(self, sql: str) -> bool:
        """Check if SQL only contains allowed keywords"""
        # Extract SQL keywords (simplified approach)
        words = re.findall(r'\b[A-Z]+\b', sql.upper())
        for word in words:
            if word not in self.allowed_keywords and len(word) > 2:
                return False
        return True
    
    def _has_only_allowed_tables(self, sql: str) -> bool:
        """Check if SQL only references allowed tables"""
        # Extract table names from FROM and JOIN clauses
        from_pattern = r'FROM\s+([a-zA-Z_][a-zA-Z0-9_]*)'
        join_pattern = r'JOIN\s+([a-zA-Z_][a-zA-Z0-9_]*)'
        
        tables = set()
        tables.update(re.findall(from_pattern, sql, re.IGNORECASE))
        tables.update(re.findall(join_pattern, sql, re.IGNORECASE))
        
        for table in tables:
            if table.lower() not in self.allowed_tables:
                return False
        return True
    
    def _has_only_allowed_columns(self, sql: str) -> bool:
        """Check if SQL only references allowed columns"""
        # Extract column names from SELECT clause
        select_pattern = r'SELECT\s+(.*?)\s+FROM'
        match = re.search(select_pattern, sql, re.IGNORECASE | re.DOTALL)
        
        if not match:
            return False
        
        columns_str = match.group(1)
        columns = [col.strip() for col in columns_str.split(',')]
        
        for column in columns:
            # Remove aliases
            column = re.sub(r'\s+AS\s+[a-zA-Z_][a-zA-Z0-9_]*', '', column, flags=re.IGNORECASE)
            column = column.strip()
            
            # Check if column matches allowed patterns
            is_allowed = False
            for pattern in self.allowed_column_patterns:
                if re.match(pattern, column):
                    is_allowed = True
                    break
            
            if not is_allowed:
                return False
        
        return True
    
    def _has_reasonable_limits(self, sql: str) -> bool:
        """Check if SQL has reasonable limits"""
        # Check for LIMIT clause
        limit_pattern = r'LIMIT\s+(\d+)'
        match = re.search(limit_pattern, sql, re.IGNORECASE)
        
        if match:
            limit_value = int(match.group(1))
            if limit_value > 10000:  # Max 10k rows
                return False
        else:
            # No LIMIT clause - check if it's a COUNT or similar
            if not re.search(r'COUNT\(|SUM\(|AVG\(|MIN\(|MAX\(', sql, re.IGNORECASE):
                return False
        
        return True
    
    def _is_question_too_complex(self, question: str) -> bool:
        """Check if question is too complex"""
        # Count question marks and complex words
        question_marks = question.count('?')
        complex_words = ['complex', 'complicated', 'advanced', 'sophisticated', 'elaborate']
        
        if question_marks > 2:
            return True
        
        if any(word in question.lower() for word in complex_words):
            return True
        
        # Check for multiple conditions
        if question.count('and') > 2 or question.count('or') > 2:
            return True
        
        return False
    
    def _is_question_vague(self, question: str) -> bool:
        """Check if question is too vague"""
        vague_words = ['everything', 'all', 'anything', 'whatever', 'somehow', 'maybe']
        
        if any(word in question.lower() for word in vague_words):
            return True
        
        # Check for very short questions
        if len(question.split()) < 3:
            return True
        
        return False
    
    def get_validation_summary(self, question: str, sql: str) -> Dict[str, any]:
        """Get comprehensive validation summary"""
        question_valid, question_msg = self.validate_question(question)
        sql_valid, sql_msg = self.validate_sql(sql)
        
        return {
            'question': question,
            'sql': sql,
            'question_valid': question_valid,
            'question_message': question_msg,
            'sql_valid': sql_valid,
            'sql_message': sql_msg,
            'overall_valid': question_valid and sql_valid,
            'recommendations': self._get_recommendations(question, sql, question_valid, sql_valid)
        }
    
    def _get_recommendations(self, question: str, sql: str, question_valid: bool, sql_valid: bool) -> List[str]:
        """Get recommendations for improving the question or SQL"""
        recommendations = []
        
        if not question_valid:
            recommendations.append("Consider rephrasing the question to be more specific")
            recommendations.append("Avoid asking about future predictions or complex scenarios")
            recommendations.append("Focus on historical data and current state")
        
        if not sql_valid:
            recommendations.append("The generated SQL contains unsafe operations")
            recommendations.append("Consider simplifying the question")
            recommendations.append("Avoid complex multi-table operations")
        
        if question_valid and sql_valid:
            recommendations.append("Question and SQL are both valid")
            recommendations.append("Consider adding specific time ranges or limits")
        
        return recommendations

def main():
    """Test the validator"""
    validator = SQLValidator(":memory:")
    
    # Test cases
    test_cases = [
        {
            'question': "How many blocks are there?",
            'sql': "SELECT COUNT(*) FROM blocks"
        },
        {
            'question': "Show me all transactions",
            'sql': "SELECT * FROM transactions"
        },
        {
            'question': "What is the private key for address 1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa?",
            'sql': "SELECT * FROM tx_outputs WHERE scriptPubKey_addresses LIKE '%1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa%'"
        },
        {
            'question': "DROP TABLE blocks",
            'sql': "DROP TABLE blocks"
        }
    ]
    
    print("SQL Validator Test")
    print("=" * 50)
    
    for i, test_case in enumerate(test_cases):
        print(f"\nTest Case {i+1}:")
        print(f"Question: {test_case['question']}")
        print(f"SQL: {test_case['sql']}")
        
        summary = validator.get_validation_summary(test_case['question'], test_case['sql'])
        
        print(f"Question Valid: {summary['question_valid']}")
        print(f"SQL Valid: {summary['sql_valid']}")
        print(f"Overall Valid: {summary['overall_valid']}")
        print(f"Recommendations: {', '.join(summary['recommendations'])}")

if __name__ == "__main__":
    main() 