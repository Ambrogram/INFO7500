-- SQLite schema for Bitcoin blocks and transactions
-- Covers all data elements from getblock RPC call with verbosity=2

-- Blocks table
CREATE TABLE IF NOT EXISTS blocks (
    hash TEXT PRIMARY KEY,
    confirmations INTEGER,
    size INTEGER,
    weight INTEGER,
    height INTEGER UNIQUE,
    version INTEGER,
    versionHex TEXT,
    merkleroot TEXT,
    tx TEXT, -- JSON array of transaction hashes
    time INTEGER,
    mediantime INTEGER,
    nonce INTEGER,
    bits TEXT,
    difficulty REAL,
    chainwork TEXT,
    nTx INTEGER,
    previousblockhash TEXT,
    nextblockhash TEXT,
    strippedsize INTEGER,
    weight INTEGER,
    sigops INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Transactions table
CREATE TABLE IF NOT EXISTS transactions (
    txid TEXT PRIMARY KEY,
    hash TEXT,
    version INTEGER,
    size INTEGER,
    vsize INTEGER,
    weight INTEGER,
    locktime INTEGER,
    block_hash TEXT,
    block_height INTEGER,
    block_time INTEGER,
    confirmations INTEGER,
    time INTEGER,
    blocktime INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (block_hash) REFERENCES blocks(hash),
    FOREIGN KEY (block_height) REFERENCES blocks(height)
);

-- Transaction inputs table
CREATE TABLE IF NOT EXISTS tx_inputs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    txid TEXT,
    vout INTEGER,
    sequence INTEGER,
    coinbase TEXT,
    txinwitness TEXT, -- JSON array
    prevout_hash TEXT,
    prevout_n INTEGER,
    scriptsig TEXT,
    scriptsig_asm TEXT,
    inner_witnessscript_asm TEXT,
    inner_redeemscript_asm TEXT,
    FOREIGN KEY (txid) REFERENCES transactions(txid)
);

-- Transaction outputs table
CREATE TABLE IF NOT EXISTS tx_outputs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    txid TEXT,
    n INTEGER,
    scriptPubKey TEXT,
    scriptPubKey_asm TEXT,
    scriptPubKey_type TEXT,
    scriptPubKey_addresses TEXT, -- JSON array
    value REAL,
    FOREIGN KEY (txid) REFERENCES transactions(txid)
);

-- Block statistics table for quick queries
CREATE TABLE IF NOT EXISTS block_stats (
    height INTEGER PRIMARY KEY,
    total_fees REAL,
    total_size INTEGER,
    total_weight INTEGER,
    total_inputs INTEGER,
    total_outputs INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_blocks_height ON blocks(height);
CREATE INDEX IF NOT EXISTS idx_blocks_time ON blocks(time);
CREATE INDEX IF NOT EXISTS idx_transactions_block_hash ON transactions(block_hash);
CREATE INDEX IF NOT EXISTS idx_transactions_block_height ON transactions(block_height);
CREATE INDEX IF NOT EXISTS idx_tx_inputs_txid ON tx_inputs(txid);
CREATE INDEX IF NOT EXISTS idx_tx_outputs_txid ON tx_outputs(txid);
CREATE INDEX IF NOT EXISTS idx_tx_outputs_addresses ON tx_outputs(scriptPubKey_addresses);

-- View for common queries
CREATE VIEW IF NOT EXISTS v_block_summary AS
SELECT 
    b.height,
    b.hash,
    b.time,
    b.nTx,
    b.size,
    b.weight,
    b.difficulty,
    COALESCE(bs.total_fees, 0) as total_fees
FROM blocks b
LEFT JOIN block_stats bs ON b.height = bs.height
ORDER BY b.height DESC;

-- View for transaction details
CREATE VIEW IF NOT EXISTS v_transaction_details AS
SELECT 
    t.txid,
    t.block_height,
    t.block_time,
    t.size,
    t.weight,
    t.confirmations,
    COUNT(ti.id) as input_count,
    COUNT(to.id) as output_count,
    SUM(to.value) as total_output_value
FROM transactions t
LEFT JOIN tx_inputs ti ON t.txid = ti.txid
LEFT JOIN tx_outputs to ON t.txid = to.txid
GROUP BY t.txid, t.block_height, t.block_time, t.size, t.weight, t.confirmations; 