#!/usr/bin/env python3
"""
Test Runner for Bitcoin Text-to-SQL System
Runs all test cases and generates comprehensive results
"""

import json
import sqlite3
import sys
import os
from datetime import datetime
from typing import Dict, List, Any
import time

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from text2sql.text_to_sql import BitcoinTextToSQL
from text2sql.validator import SQLValidator

class TestRunner:
    def __init__(self, db_path: str, openai_api_key: str = None):
        self.db_path = db_path
        self.openai_api_key = openai_api_key
        self.converter = BitcoinTextToSQL(db_path, openai_api_key)
        self.validator = SQLValidator(db_path)
        
        # Test results storage
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'summary': {},
            'passing_cases': [],
            'hard_cases': [],
            'errors': []
        }
    
    def load_test_cases(self) -> tuple[List[Dict], List[Dict]]:
        """Load test cases from JSON files"""
        try:
            with open('cases_pass.json', 'r') as f:
                passing_cases = json.load(f)
            
            with open('cases_hard.json', 'r') as f:
                hard_cases = json.load(f)
            
            return passing_cases, hard_cases
            
        except Exception as e:
            print(f"Error loading test cases: {e}")
            return [], []
    
    def run_passing_cases(self, cases: List[Dict]) -> List[Dict]:
        """Run the 10 passing test cases"""
        print("\n" + "="*60)
        print("RUNNING PASSING TEST CASES")
        print("="*60)
        
        results = []
        passed = 0
        total = len(cases)
        
        for i, case in enumerate(cases, 1):
            print(f"\nTest Case {i}/{total}: {case['question']}")
            print(f"Difficulty: {case['difficulty']}")
            print("-" * 50)
            
            try:
                # Convert question to SQL
                start_time = time.time()
                sql_result = self.converter.convert_to_sql(case['question'], use_openai=bool(self.openai_api_key))
                conversion_time = time.time() - start_time
                
                print(f"Generated SQL: {sql_result}")
                print(f"Expected SQL: {case['expected_sql']}")
                
                # Validate SQL
                sql_valid, sql_msg = self.validator.validate_sql(sql_result)
                question_valid, question_msg = self.validator.validate_question(case['question'])
                
                print(f"SQL Valid: {sql_valid} - {sql_msg}")
                print(f"Question Valid: {question_valid} - {question_msg}")
                
                # Execute SQL
                start_time = time.time()
                execution_result = self.converter.execute_sql(sql_result)
                execution_time = time.time() - start_time
                
                results_data, columns = execution_result
                
                # Check if results are reasonable
                results_reasonable = self._check_results_reasonable(results_data, case)
                
                # Determine if test passed
                test_passed = (
                    sql_valid and 
                    question_valid and 
                    results_reasonable and
                    len(results_data) > 0
                )
                
                if test_passed:
                    passed += 1
                    status = "PASS"
                else:
                    status = "FAIL"
                
                # Store result
                result = {
                    'case_id': case['id'],
                    'question': case['question'],
                    'difficulty': case['difficulty'],
                    'expected_sql': case['expected_sql'],
                    'generated_sql': sql_result,
                    'sql_valid': sql_valid,
                    'question_valid': question_valid,
                    'results_count': len(results_data),
                    'results_reasonable': results_reasonable,
                    'conversion_time': conversion_time,
                    'execution_time': execution_time,
                    'status': status,
                    'actual_results': results_data[:3] if results_data else [],  # Store first 3 results
                    'columns': columns
                }
                
                results.append(result)
                
                print(f"Results: {len(results_data)} rows")
                print(f"Results Reasonable: {results_reasonable}")
                print(f"Status: {status}")
                print(f"Conversion Time: {conversion_time:.3f}s")
                print(f"Execution Time: {execution_time:.3f}s")
                
                if results_data:
                    print("Sample Results:")
                    for j, row in enumerate(results_data[:2]):
                        print(f"  Row {j+1}: {dict(row)}")
                
            except Exception as e:
                print(f"Error running test case: {e}")
                result = {
                    'case_id': case['id'],
                    'question': case['question'],
                    'difficulty': case['difficulty'],
                    'status': 'ERROR',
                    'error': str(e)
                }
                results.append(result)
                self.results['errors'].append(result)
        
        print(f"\nPassing Cases Summary: {passed}/{total} passed")
        self.results['summary']['passing_cases'] = {'passed': passed, 'total': total}
        self.results['passing_cases'] = results
        
        return results
    
    def run_hard_cases(self, cases: List[Dict]) -> List[Dict]:
        """Run the 3 hard test cases that should fail"""
        print("\n" + "="*60)
        print("RUNNING HARD TEST CASES (Expected to Fail)")
        print("="*60)
        
        results = []
        correctly_failed = 0
        total = len(cases)
        
        for i, case in enumerate(cases, 1):
            print(f"\nHard Test Case {i}/{total}: {case['question']}")
            print(f"Difficulty: {case['difficulty']}")
            print(f"Expected to fail because: {case['reason_unanswerable']}")
            print("-" * 50)
            
            try:
                # Convert question to SQL
                start_time = time.time()
                sql_result = self.converter.convert_to_sql(case['question'], use_openai=bool(self.openai_api_key))
                conversion_time = time.time() - start_time
                
                print(f"Generated SQL: {sql_result}")
                print(f"Expected SQL: {case['expected_sql']}")
                
                # Validate SQL
                sql_valid, sql_msg = self.validator.validate_sql(sql_result)
                question_valid, question_msg = self.validator.validate_question(case['question'])
                
                print(f"SQL Valid: {sql_valid} - {sql_msg}")
                print(f"Question Valid: {question_valid} - {question_msg}")
                
                # For hard cases, we expect the question to be invalid
                expected_to_fail = not question_valid
                
                if expected_to_fail:
                    correctly_failed += 1
                    status = "CORRECTLY_FAILED"
                else:
                    status = "INCORRECTLY_PASSED"
                
                # Store result
                result = {
                    'case_id': case['id'],
                    'question': case['question'],
                    'difficulty': case['difficulty'],
                    'expected_sql': case['expected_sql'],
                    'generated_sql': sql_result,
                    'sql_valid': sql_valid,
                    'question_valid': question_valid,
                    'expected_to_fail': True,
                    'correctly_failed': expected_to_fail,
                    'conversion_time': conversion_time,
                    'status': status,
                    'reason_unanswerable': case['reason_unanswerable']
                }
                
                results.append(result)
                
                print(f"Expected to fail: True")
                print(f"Correctly failed: {expected_to_fail}")
                print(f"Status: {status}")
                print(f"Conversion Time: {conversion_time:.3f}s")
                
            except Exception as e:
                print(f"Error running hard test case: {e}")
                result = {
                    'case_id': case['id'],
                    'question': case['question'],
                    'difficulty': case['difficulty'],
                    'status': 'ERROR',
                    'error': str(e)
                }
                results.append(result)
                self.results['errors'].append(result)
        
        print(f"\nHard Cases Summary: {correctly_failed}/{total} correctly failed")
        self.results['summary']['hard_cases'] = {'correctly_failed': correctly_failed, 'total': total}
        self.results['hard_cases'] = results
        
        return results
    
    def _check_results_reasonable(self, results: List[Dict], case: Dict) -> bool:
        """Check if the results are reasonable for the given case"""
        if not results:
            return False
        
        # Basic reasonableness checks based on case type
        if 'count' in case['question'].lower() or 'how many' in case['question'].lower():
            # Should return numeric results
            for row in results:
                for value in row.values():
                    if isinstance(value, (int, float)) and value >= 0:
                        return True
            return False
        
        elif 'latest' in case['question'].lower() or 'current' in case['question'].lower():
            # Should return recent data
            return len(results) > 0
        
        elif 'average' in case['question'].lower() or 'avg' in case['question'].lower():
            # Should return numeric results
            for row in results:
                for value in row.values():
                    if isinstance(value, (int, float)):
                        return True
            return False
        
        else:
            # Generic check - just ensure we have some results
            return len(results) > 0
    
    def generate_report(self) -> str:
        """Generate a comprehensive test report"""
        report = []
        report.append("BITCOIN TEXT-TO-SQL SYSTEM TEST REPORT")
        report.append("=" * 60)
        report.append(f"Generated: {self.results['timestamp']}")
        report.append("")
        
        # Summary
        report.append("EXECUTIVE SUMMARY")
        report.append("-" * 30)
        
        passing_summary = self.results['summary'].get('passing_cases', {})
        hard_summary = self.results['summary'].get('hard_cases', {})
        
        report.append(f"Passing Cases: {passing_summary.get('passed', 0)}/{passing_summary.get('total', 0)} passed")
        report.append(f"Hard Cases: {hard_summary.get('correctly_failed', 0)}/{hard_summary.get('total', 0)} correctly failed")
        
        total_errors = len(self.results['errors'])
        if total_errors > 0:
            report.append(f"Errors: {total_errors}")
        
        # Passing cases details
        if self.results['passing_cases']:
            report.append("")
            report.append("PASSING CASES DETAILS")
            report.append("-" * 30)
            
            for result in self.results['passing_cases']:
                if result['status'] == 'PASS':
                    report.append(f"✓ Case {result['case_id']}: {result['question'][:50]}...")
                else:
                    report.append(f"✗ Case {result['case_id']}: {result['question'][:50]}...")
        
        # Hard cases details
        if self.results['hard_cases']:
            report.append("")
            report.append("HARD CASES DETAILS")
            report.append("-" * 30)
            
            for result in self.results['hard_cases']:
                if result['status'] == 'CORRECTLY_FAILED':
                    report.append(f"✓ Case {result['case_id']}: Correctly rejected")
                else:
                    report.append(f"✗ Case {result['case_id']}: Incorrectly passed")
        
        # Performance metrics
        if self.results['passing_cases']:
            report.append("")
            report.append("PERFORMANCE METRICS")
            report.append("-" * 30)
            
            conversion_times = [r['conversion_time'] for r in self.results['passing_cases'] if 'conversion_time' in r]
            execution_times = [r['execution_time'] for r in self.results['passing_cases'] if 'execution_time' in r]
            
            if conversion_times:
                avg_conversion = sum(conversion_times) / len(conversion_times)
                report.append(f"Average SQL Conversion Time: {avg_conversion:.3f}s")
            
            if execution_times:
                avg_execution = sum(execution_times) / len(execution_times)
                report.append(f"Average SQL Execution Time: {avg_execution:.3f}s")
        
        return "\n".join(report)
    
    def save_results(self, filename: str = None):
        """Save test results to JSON file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"test_results_{timestamp}.json"
        
        try:
            with open(filename, 'w') as f:
                json.dump(self.results, f, indent=2, default=str)
            print(f"\nResults saved to: {filename}")
        except Exception as e:
            print(f"Error saving results: {e}")
    
    def run_all_tests(self):
        """Run all test cases"""
        print("Starting Bitcoin Text-to-SQL System Tests")
        print("=" * 60)
        
        # Load test cases
        passing_cases, hard_cases = self.load_test_cases()
        
        if not passing_cases and not hard_cases:
            print("No test cases loaded. Exiting.")
            return
        
        # Run passing cases
        if passing_cases:
            self.run_passing_cases(passing_cases)
        
        # Run hard cases
        if hard_cases:
            self.run_hard_cases(hard_cases)
        
        # Generate and display report
        report = self.generate_report()
        print("\n" + report)
        
        # Save results
        self.save_results()

def main():
    """Main function"""
    # Configuration
    DB_PATH = "../data/btc.db"
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    
    # Check if database exists
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}")
        print("Please run the ETL sync first to create the database.")
        return
    
    # Initialize and run tests
    runner = TestRunner(DB_PATH, OPENAI_API_KEY)
    runner.run_all_tests()

if __name__ == "__main__":
    main() 