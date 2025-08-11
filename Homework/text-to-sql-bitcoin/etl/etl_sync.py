#!/usr/bin/env python3
"""
Bitcoin ETL Sync Program
Fetches blocks from bitcoind and writes to SQLite database
Supports checkpointing and reorg handling
"""

import json
import sqlite3
import time
import logging
from typing import Dict, List, Optional, Tuple
import requests
from datetime import datetime
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('etl_sync.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class BitcoinETL:
    def __init__(self, rpc_url: str, db_path: str):
        self.rpc_url = rpc_url
        self.db_path = db_path
        self.session = requests.Session()
        self.session.auth = ('bitcoinrpc', 'your_rpc_password')  # Update with your credentials
        
    def rpc_call(self, method: str, params: List = None) -> Dict:
        """Make RPC call to bitcoind"""
        payload = {
            "jsonrpc": "1.0",
            "id": "etl_sync",
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
    
    def init_database(self):
        """Initialize database with schema"""
        with open('../sql/schema.sql', 'r') as f:
            schema = f.read()
        
        conn = self.get_db_connection()
        try:
            conn.executescript(schema)
            conn.commit()
            logger.info("Database initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
        finally:
            conn.close()
    
    def get_latest_block_height(self) -> int:
        """Get the latest block height from bitcoind"""
        try:
            info = self.rpc_call('getblockchaininfo')
            return info['blocks']
        except Exception as e:
            logger.error(f"Failed to get latest block height: {e}")
            raise
    
    def get_db_latest_height(self) -> int:
        """Get the latest block height from database"""
        conn = self.get_db_connection()
        try:
            cursor = conn.execute("SELECT MAX(height) as max_height FROM blocks")
            result = cursor.fetchone()
            return result['max_height'] if result and result['max_height'] else -1
        except Exception as e:
            logger.error(f"Failed to get latest height from database: {e}")
            return -1
        finally:
            conn.close()
    
    def fetch_block(self, block_hash: str) -> Dict:
        """Fetch block data with verbosity=2"""
        try:
            return self.rpc_call('getblock', [block_hash, 2])
        except Exception as e:
            logger.error(f"Failed to fetch block {block_hash}: {e}")
            raise
    
    def insert_block(self, conn: sqlite3.Connection, block_data: Dict):
        """Insert block data into database"""
        try:
            # Insert block
            conn.execute("""
                INSERT OR REPLACE INTO blocks (
                    hash, confirmations, size, weight, height, version, versionHex,
                    merkleroot, tx, time, mediantime, nonce, bits, difficulty,
                    chainwork, nTx, previousblockhash, nextblockhash, strippedsize,
                    sigops, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                block_data['hash'],
                block_data.get('confirmations', 0),
                block_data.get('size', 0),
                block_data.get('weight', 0),
                block_data['height'],
                block_data.get('version', 0),
                block_data.get('versionHex', ''),
                block_data.get('merkleroot', ''),
                json.dumps(block_data.get('tx', [])),
                block_data.get('time', 0),
                block_data.get('mediantime', 0),
                block_data.get('nonce', 0),
                block_data.get('bits', ''),
                block_data.get('difficulty', 0.0),
                block_data.get('chainwork', ''),
                block_data.get('nTx', 0),
                block_data.get('previousblockhash', ''),
                block_data.get('nextblockhash', ''),
                block_data.get('strippedsize', 0),
                block_data.get('sigops', 0),
                datetime.now().isoformat()
            ))
            
            # Insert transactions
            if 'tx' in block_data and isinstance(block_data['tx'], list):
                for tx in block_data['tx']:
                    self.insert_transaction(conn, tx, block_data['hash'], block_data['height'], block_data['time'])
            
            conn.commit()
            logger.info(f"Inserted block {block_data['height']} ({block_data['hash'][:8]}...)")
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Failed to insert block {block_data['height']}: {e}")
            raise
    
    def insert_transaction(self, conn: sqlite3.Connection, tx_data: Dict, block_hash: str, block_height: int, block_time: int):
        """Insert transaction data into database"""
        try:
            # Insert transaction
            conn.execute("""
                INSERT OR REPLACE INTO transactions (
                    txid, hash, version, size, vsize, weight, locktime,
                    block_hash, block_height, block_time, confirmations,
                    time, blocktime, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                tx_data['txid'],
                tx_data.get('hash', ''),
                tx_data.get('version', 0),
                tx_data.get('size', 0),
                tx_data.get('vsize', 0),
                tx_data.get('weight', 0),
                tx_data.get('locktime', 0),
                block_hash,
                block_height,
                block_time,
                tx_data.get('confirmations', 0),
                tx_data.get('time', 0),
                tx_data.get('blocktime', 0),
                datetime.now().isoformat()
            ))
            
            # Insert inputs
            if 'vin' in tx_data:
                for vin in tx_data['vin']:
                    self.insert_input(conn, vin, tx_data['txid'])
            
            # Insert outputs
            if 'vout' in tx_data:
                for vout in tx_data['vout']:
                    self.insert_output(conn, vout, tx_data['txid'])
                    
        except Exception as e:
            logger.error(f"Failed to insert transaction {tx_data['txid']}: {e}")
            raise
    
    def insert_input(self, conn: sqlite3.Connection, vin: Dict, txid: str):
        """Insert transaction input data"""
        try:
            conn.execute("""
                INSERT INTO tx_inputs (
                    txid, vout, sequence, coinbase, txinwitness,
                    prevout_hash, prevout_n, scriptsig, scriptsig_asm,
                    inner_witnessscript_asm, inner_redeemscript_asm
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                txid,
                vin.get('vout', 0),
                vin.get('sequence', 0),
                vin.get('coinbase', ''),
                json.dumps(vin.get('txinwitness', [])),
                vin.get('prevout', {}).get('hash', ''),
                vin.get('prevout', {}).get('n', 0),
                vin.get('scriptsig', ''),
                vin.get('scriptsig_asm', ''),
                vin.get('inner_witnessscript_asm', ''),
                vin.get('inner_redeemscript_asm', '')
            ))
        except Exception as e:
            logger.error(f"Failed to insert input for transaction {txid}: {e}")
            raise
    
    def insert_output(self, conn: sqlite3.Connection, vout: Dict, txid: str):
        """Insert transaction output data"""
        try:
            conn.execute("""
                INSERT INTO tx_outputs (
                    txid, n, scriptPubKey, scriptPubKey_asm, scriptPubKey_type,
                    scriptPubKey_addresses, value
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                txid,
                vout.get('n', 0),
                vout.get('scriptPubKey', {}).get('hex', ''),
                vout.get('scriptPubKey', {}).get('asm', ''),
                vout.get('scriptPubKey', {}).get('type', ''),
                json.dumps(vout.get('scriptPubKey', {}).get('addresses', [])),
                vout.get('value', 0.0)
            ))
        except Exception as e:
            logger.error(f"Failed to insert output for transaction {txid}: {e}")
            raise
    
    def handle_reorg(self, conn: sqlite3.Connection, new_block: Dict) -> bool:
        """Handle blockchain reorganization"""
        try:
            # Check if we have a fork
            prev_hash = new_block.get('previousblockhash')
            if not prev_hash:
                return False
            
            # Check if previous block exists and is at expected height
            cursor = conn.execute("SELECT height FROM blocks WHERE hash = ?", (prev_hash,))
            prev_block = cursor.fetchone()
            
            if prev_block and prev_block['height'] == new_block['height'] - 1:
                return False  # No reorg
            
            # We have a reorg - find the fork point
            logger.warning(f"Reorg detected at height {new_block['height']}")
            
            # Find the fork point by walking back
            fork_height = new_block['height'] - 1
            while fork_height >= 0:
                cursor = conn.execute("SELECT hash FROM blocks WHERE height = ?", (fork_height,))
                block = cursor.fetchone()
                if block and block['hash'] == new_block.get('previousblockhash'):
                    break
                fork_height -= 1
            
            if fork_height >= 0:
                # Remove blocks after fork point
                conn.execute("DELETE FROM blocks WHERE height > ?", (fork_height,))
                conn.execute("DELETE FROM transactions WHERE block_height > ?", (fork_height,))
                conn.execute("DELETE FROM tx_inputs WHERE txid IN (SELECT txid FROM transactions WHERE block_height > ?)", (fork_height,))
                conn.execute("DELETE FROM tx_outputs WHERE txid IN (SELECT txid FROM transactions WHERE block_height > ?)", (fork_height,))
                conn.commit()
                logger.info(f"Removed blocks after height {fork_height} due to reorg")
                return True
            
        except Exception as e:
            logger.error(f"Failed to handle reorg: {e}")
            conn.rollback()
        
        return False
    
    def sync_blocks(self, start_height: int = None, max_blocks: int = None):
        """Sync blocks from start_height to latest"""
        try:
            latest_height = self.get_latest_block_height()
            current_height = start_height or self.get_db_latest_height() + 1
            
            if max_blocks:
                end_height = min(current_height + max_blocks - 1, latest_height)
            else:
                end_height = latest_height
            
            logger.info(f"Starting sync from height {current_height} to {end_height}")
            
            conn = self.get_db_connection()
            try:
                for height in range(current_height, end_height + 1):
                    try:
                        # Get block hash by height
                        block_hash = self.rpc_call('getblockhash', [height])
                        
                        # Fetch full block data
                        block_data = self.fetch_block(block_hash)
                        
                        # Check for reorg
                        if self.handle_reorg(conn, block_data):
                            # Reorg handled, continue with current block
                            pass
                        
                        # Insert block
                        self.insert_block(conn, block_data)
                        
                        # Progress update
                        if height % 100 == 0:
                            logger.info(f"Synced {height - current_height + 1} blocks...")
                        
                        # Small delay to avoid overwhelming the RPC
                        time.sleep(0.1)
                        
                    except Exception as e:
                        logger.error(f"Failed to sync block {height}: {e}")
                        continue
                
                logger.info(f"Sync completed. Synced {end_height - current_height + 1} blocks")
                
            finally:
                conn.close()
                
        except Exception as e:
            logger.error(f"Sync failed: {e}")
            raise

def main():
    """Main function"""
    # Configuration
    RPC_URL = "http://127.0.0.1:8332"
    DB_PATH = "../data/btc.db"
    
    # Create data directory if it doesn't exist
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    
    # Initialize ETL
    etl = BitcoinETL(RPC_URL, DB_PATH)
    
    try:
        # Initialize database
        etl.init_database()
        
        # Sync blocks (last 100k blocks or until disk space runs out)
        etl.sync_blocks(max_blocks=100000)
        
    except KeyboardInterrupt:
        logger.info("Sync interrupted by user")
    except Exception as e:
        logger.error(f"Sync failed: {e}")
        raise

if __name__ == "__main__":
    main() 