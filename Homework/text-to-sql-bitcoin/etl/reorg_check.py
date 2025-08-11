#!/usr/bin/env python3
"""
Bitcoin Reorg Checker
Optional script to validate blockchain consistency by checking the last N blocks
"""

import sqlite3
import requests
import json
import logging
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ReorgChecker:
    def __init__(self, db_path: str, rpc_url: str, rpc_auth: Tuple[str, str]):
        self.db_path = db_path
        self.rpc_url = rpc_url
        self.rpc_auth = rpc_auth
        self.session = requests.Session()
        self.session.auth = rpc_auth
    
    def rpc_call(self, method: str, params: List = None) -> Dict:
        """Make RPC call to bitcoind"""
        payload = {
            "jsonrpc": "1.0",
            "id": "reorg_check",
            "method": method,
            "params": params or []
        }
        
        try:
            response = self.session.post(self.rpc_url, json=payload, timeout=30)
            response.raise_for_status()
            result = response.json()
            
            if 'error' in result and result['error'] is not None:
                raise Exception(f"RPC Error: {result['error']}")
                
            return result['result']
        except Exception as e:
            logger.error(f"RPC call failed for {method}: {e}")
            raise
    
    def get_db_connection(self) -> sqlite3.Connection:
        """Get SQLite database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def check_block_consistency(self, num_blocks: int = 144) -> Dict[str, any]:
        """Check consistency of the last N blocks (default: 144 = ~1 day)"""
        logger.info(f"Checking consistency of last {num_blocks} blocks")
        
        try:
            # Get latest block height from database
            conn = self.get_db_connection()
            cursor = conn.execute("SELECT MAX(height) as max_height FROM blocks")
            db_latest = cursor.fetchone()
            
            if not db_latest or db_latest['max_height'] is None:
                raise Exception("No blocks found in database")
            
            db_latest_height = db_latest['max_height']
            start_height = max(0, db_latest_height - num_blocks + 1)
            
            logger.info(f"Checking blocks from height {start_height} to {db_latest_height}")
            
            # Get blocks from database
            cursor = conn.execute("""
                SELECT height, hash, previousblockhash, time 
                FROM blocks 
                WHERE height >= ? 
                ORDER BY height
            """, (start_height,))
            
            db_blocks = {row['height']: dict(row) for row in cursor.fetchall()}
            
            # Get blocks from bitcoind
            bitcoind_blocks = {}
            for height in range(start_height, db_latest_height + 1):
                try:
                    block_hash = self.rpc_call('getblockhash', [height])
                    block_info = self.rpc_call('getblock', [block_hash, 1])
                    
                    bitcoind_blocks[height] = {
                        'height': height,
                        'hash': block_hash,
                        'previousblockhash': block_info.get('previousblockhash', ''),
                        'time': block_info.get('time', 0)
                    }
                    
                    # Small delay to avoid overwhelming RPC
                    time.sleep(0.1)
                    
                except Exception as e:
                    logger.error(f"Failed to get block {height} from bitcoind: {e}")
                    continue
            
            # Compare blocks
            inconsistencies = []
            missing_blocks = []
            
            for height in range(start_height, db_latest_height + 1):
                if height not in db_blocks:
                    missing_blocks.append(height)
                    continue
                
                if height not in bitcoind_blocks:
                    logger.warning(f"Block {height} not found in bitcoind")
                    continue
                
                db_block = db_blocks[height]
                btc_block = bitcoind_blocks[height]
                
                # Check hash consistency
                if db_block['hash'] != btc_block['hash']:
                    inconsistency = {
                        'height': height,
                        'type': 'hash_mismatch',
                        'db_hash': db_block['hash'],
                        'bitcoind_hash': btc_block['hash'],
                        'description': 'Block hash mismatch between database and bitcoind'
                    }
                    inconsistencies.append(inconsistency)
                
                # Check previous block hash consistency
                if height > start_height:
                    prev_height = height - 1
                    if prev_height in db_blocks and prev_height in bitcoind_blocks:
                        db_prev_hash = db_blocks[prev_height]['hash']
                        btc_prev_hash = btc_block['previousblockhash']
                        
                        if db_prev_hash != btc_prev_hash:
                            inconsistency = {
                                'height': height,
                                'type': 'prev_hash_mismatch',
                                'db_prev_hash': db_prev_hash,
                                'bitcoind_prev_hash': btc_prev_hash,
                                'description': 'Previous block hash mismatch'
                            }
                            inconsistencies.append(inconsistency)
            
            conn.close()
            
            # Generate report
            total_blocks_checked = len(bitcoind_blocks)
            consistency_percentage = ((total_blocks_checked - len(inconsistencies)) / total_blocks_checked * 100) if total_blocks_checked > 0 else 0
            
            report = {
                'check_time': datetime.now().isoformat(),
                'blocks_checked': {
                    'start_height': start_height,
                    'end_height': db_latest_height,
                    'total': total_blocks_checked
                },
                'consistency': {
                    'percentage': round(consistency_percentage, 2),
                    'total_inconsistencies': len(inconsistencies),
                    'missing_blocks': len(missing_blocks)
                },
                'inconsistencies': inconsistencies,
                'missing_blocks': missing_blocks,
                'status': 'healthy' if len(inconsistencies) == 0 else 'inconsistent'
            }
            
            return report
            
        except Exception as e:
            logger.error(f"Block consistency check failed: {e}")
            raise
    
    def check_chain_work(self, num_blocks: int = 144) -> Dict[str, any]:
        """Check chainwork consistency of the last N blocks"""
        logger.info(f"Checking chainwork consistency of last {num_blocks} blocks")
        
        try:
            conn = self.get_db_connection()
            cursor = conn.execute("SELECT MAX(height) as max_height FROM blocks")
            db_latest = cursor.fetchone()
            
            if not db_latest or db_latest['max_height'] is None:
                raise Exception("No blocks found in database")
            
            db_latest_height = db_latest['max_height']
            start_height = max(0, db_latest_height - num_blocks + 1)
            
            # Get chainwork from database
            cursor = conn.execute("""
                SELECT height, chainwork, difficulty 
                FROM blocks 
                WHERE height >= ? 
                ORDER BY height
            """, (start_height,))
            
            db_chainwork = {row['height']: dict(row) for row in cursor.fetchall()}
            
            # Get chainwork from bitcoind
            bitcoind_chainwork = {}
            for height in range(start_height, db_latest_height + 1):
                try:
                    block_hash = self.rpc_call('getblockhash', [height])
                    block_info = self.rpc_call('getblock', [block_hash, 1])
                    
                    bitcoind_chainwork[height] = {
                        'height': height,
                        'chainwork': block_info.get('chainwork', ''),
                        'difficulty': block_info.get('difficulty', 0)
                    }
                    
                    time.sleep(0.1)
                    
                except Exception as e:
                    logger.error(f"Failed to get block {height} chainwork from bitcoind: {e}")
                    continue
            
            # Compare chainwork
            chainwork_inconsistencies = []
            
            for height in range(start_height, db_latest_height + 1):
                if height not in db_chainwork or height not in bitcoind_chainwork:
                    continue
                
                db_block = db_chainwork[height]
                btc_block = bitcoind_chainwork[height]
                
                if db_block['chainwork'] != btc_block['chainwork']:
                    inconsistency = {
                        'height': height,
                        'type': 'chainwork_mismatch',
                        'db_chainwork': db_block['chainwork'],
                        'bitcoind_chainwork': btc_block['chainwork'],
                        'description': 'Chainwork mismatch between database and bitcoind'
                    }
                    chainwork_inconsistencies.append(inconsistency)
                
                if abs(db_block['difficulty'] - btc_block['difficulty']) > 0.001:
                    inconsistency = {
                        'height': height,
                        'type': 'difficulty_mismatch',
                        'db_difficulty': db_block['difficulty'],
                        'bitcoind_difficulty': btc_block['difficulty'],
                        'description': 'Difficulty mismatch between database and bitcoind'
                    }
                    chainwork_inconsistencies.append(inconsistency)
            
            conn.close()
            
            total_blocks_checked = len(bitcoind_chainwork)
            chainwork_consistency = ((total_blocks_checked - len(chainwork_inconsistencies)) / total_blocks_checked * 100) if total_blocks_checked > 0 else 0
            
            report = {
                'check_time': datetime.now().isoformat(),
                'blocks_checked': total_blocks_checked,
                'chainwork_consistency': round(chainwork_consistency, 2),
                'total_inconsistencies': len(chainwork_inconsistencies),
                'inconsistencies': chainwork_inconsistencies,
                'status': 'healthy' if len(chainwork_inconsistencies) == 0 else 'inconsistent'
            }
            
            return report
            
        except Exception as e:
            logger.error(f"Chainwork consistency check failed: {e}")
            raise
    
    def run_full_consistency_check(self, num_blocks: int = 144) -> Dict[str, any]:
        """Run a full consistency check including both block and chainwork validation"""
        logger.info("Running full consistency check")
        
        try:
            # Run block consistency check
            block_report = self.check_block_consistency(num_blocks)
            
            # Run chainwork consistency check
            chainwork_report = self.check_chain_work(num_blocks)
            
            # Combine reports
            full_report = {
                'check_time': datetime.now().isoformat(),
                'blocks_checked': num_blocks,
                'block_consistency': block_report,
                'chainwork_consistency': chainwork_report,
                'overall_status': 'healthy' if (block_report['consistency']['total_inconsistencies'] == 0 and 
                                               chainwork_report['total_inconsistencies'] == 0) else 'inconsistent'
            }
            
            return full_report
            
        except Exception as e:
            logger.error(f"Full consistency check failed: {e}")
            raise

def main():
    """Main function for testing"""
    # Configuration
    DB_PATH = "../data/btc.db"
    RPC_URL = "http://127.0.0.1:8332"
    RPC_AUTH = ('bitcoinrpc', 'your_rpc_password')  # Update with your credentials
    
    # Check if database exists
    import os
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}")
        print("Please run the ETL sync first to create the database.")
        return
    
    # Initialize checker
    checker = ReorgChecker(DB_PATH, RPC_URL, RPC_AUTH)
    
    try:
        # Run full consistency check
        report = checker.run_full_consistency_check(num_blocks=144)
        
        print("Bitcoin Blockchain Consistency Check Report")
        print("=" * 50)
        print(f"Check Time: {report['check_time']}")
        print(f"Blocks Checked: {report['blocks_checked']}")
        print(f"Overall Status: {report['overall_status']}")
        print()
        
        # Block consistency summary
        block_consistency = report['block_consistency']
        print("Block Consistency:")
        print(f"  Percentage: {block_consistency['consistency']['percentage']}%")
        print(f"  Inconsistencies: {block_consistency['consistency']['total_inconsistencies']}")
        print(f"  Missing Blocks: {block_consistency['consistency']['missing_blocks']}")
        print()
        
        # Chainwork consistency summary
        chainwork_consistency = report['chainwork_consistency']
        print("Chainwork Consistency:")
        print(f"  Percentage: {chainwork_consistency['chainwork_consistency']}%")
        print(f"  Inconsistencies: {chainwork_consistency['total_inconsistencies']}")
        print()
        
        # Show details of inconsistencies if any
        if block_consistency['consistency']['total_inconsistencies'] > 0:
            print("Block Inconsistencies:")
            for inc in block_consistency['inconsistencies'][:5]:  # Show first 5
                print(f"  Height {inc['height']}: {inc['description']}")
            if len(block_consistency['inconsistencies']) > 5:
                print(f"  ... and {len(block_consistency['inconsistencies']) - 5} more")
            print()
        
        if chainwork_consistency['total_inconsistencies'] > 0:
            print("Chainwork Inconsistencies:")
            for inc in chainwork_consistency['inconsistencies'][:5]:  # Show first 5
                print(f"  Height {inc['height']}: {inc['description']}")
            if len(chainwork_consistency['inconsistencies']) > 5:
                print(f"  ... and {len(chainwork_consistency['inconsistencies']) - 5} more")
            print()
        
        if report['overall_status'] == 'healthy':
            print("✅ Blockchain is consistent!")
        else:
            print("⚠️  Blockchain inconsistencies detected!")
            print("Consider running the ETL sync again to fix issues.")
        
    except Exception as e:
        print(f"Consistency check failed: {e}")

if __name__ == "__main__":
    main() 