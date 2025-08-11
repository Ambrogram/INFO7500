# Bitcoin Text-to-SQL System

A comprehensive system that converts natural language questions about Bitcoin blockchain data into SQL queries and executes them on a local SQLite database.

## 🚀 Features

- **ETL Pipeline**: Syncs Bitcoin blocks and transactions from a local bitcoind node
- **Text-to-SQL Conversion**: Converts natural language questions to SQL using rule-based and AI-powered approaches
- **SQL Validation**: Whitelist-based SQL validation with security checks
- **Comprehensive Testing**: 10 passing test cases + 3 hard cases to find system limits
- **Reorg Handling**: Automatically handles blockchain reorganizations
- **Performance Monitoring**: Tracks conversion and execution times

## 📋 Requirements

- Python 3.8+
- Bitcoin Core node (bitcoind) with RPC enabled
- SQLite3
- 50GB+ free disk space for blockchain data
- Optional: OpenAI API key for enhanced SQL generation

## 🛠️ Installation

### 1. Clone the repository
```bash
git clone <repository-url>
cd text-to-sql-bitcoin
```

### 2. Install Python dependencies
```bash
pip install -r requirements.txt
```

### 3. Set up Bitcoin Core
```bash
# Copy and configure the Bitcoin config file
cp infra/bitcoin.conf.example infra/bitcoin.conf
# Edit infra/bitcoin.conf with your RPC credentials
```

### 4. Set environment variables
```bash
cp scripts/env.example .env
# Edit .env with your configuration
```

## 🚀 Quick Start

### Option 1: Docker (Recommended)
```bash
cd infra
docker-compose up -d
```

### Option 2: Manual Setup
1. Start your bitcoind node
2. Ensure RPC is accessible at `http://127.0.0.1:8332`
3. Update RPC credentials in `etl/etl_sync.py`

### 3. Sync Blockchain Data
```bash
# Sync last 100k blocks (takes several hours)
chmod +x scripts/ingest_last_100k.sh
./scripts/ingest_last_100k.sh

# Or run ETL manually
cd etl
python3 etl_sync.py
```

### 4. Test the System
```bash
cd tests
python3 run_tests.py
```

### 5. Try Text-to-SQL
```bash
cd text2sql
python3 text_to_sql.py
```

## 📊 Database Schema

The system creates a comprehensive SQLite database with the following structure:

- **blocks**: Block information (height, hash, time, difficulty, etc.)
- **transactions**: Transaction details (txid, size, weight, etc.)
- **tx_inputs**: Transaction inputs with script information
- **tx_outputs**: Transaction outputs with addresses and values
- **block_stats**: Aggregated block statistics
- **Views**: Pre-built views for common queries

## 🧪 Test Cases

### Passing Cases (10)
1. **Easy**: Count total blocks, get latest block height
2. **Medium**: Average block size, transactions in last 24h
3. **Hard**: Complex filtering and aggregation queries

### Hard Cases (3) - Expected to Fail
1. **Future Price Prediction**: Cannot predict future Bitcoin prices
2. **Psychological Analysis**: Cannot analyze market sentiment
3. **Mining Strategy Optimization**: Cannot provide mining advice

## 🔧 Configuration

### Bitcoin RPC Settings
```bash
# In infra/bitcoin.conf
rpcuser=bitcoinrpc
rpcpassword=your_secure_password
rpcport=8332
txindex=1
```

### Environment Variables
```bash
# In .env
BITCOIN_RPC_URL=http://127.0.0.1:8332
BITCOIN_RPC_USER=bitcoinrpc
BITCOIN_RPC_PASSWORD=your_password
OPENAI_API_KEY=your_openai_key  # Optional
```

## 📁 Project Structure

```
text-to-sql-bitcoin/
├── README.md                      # This file
├── requirements.txt               # Python dependencies
├── infra/                        # Infrastructure files
│   ├── bitcoin.conf.example      # Bitcoin config template
│   └── docker-compose.yml        # Docker setup
├── sql/                          # Database schema
│   └── schema.sql               # SQLite table definitions
├── etl/                          # Data extraction
│   └── etl_sync.py              # Blockchain sync script
├── text2sql/                     # Core functionality
│   ├── text_to_sql.py           # Text-to-SQL converter
│   └── validator.py             # SQL validator
├── tests/                        # Test suite
│   ├── run_tests.py             # Test runner
│   ├── cases_pass.json          # Passing test cases
│   └── cases_hard.json          # Hard test cases
├── scripts/                      # Utility scripts
│   ├── env.example              # Environment template
│   └── ingest_last_100k.sh      # One-click sync script
└── data/                         # Database storage
    └── btc.db                   # SQLite database
```

## 🔒 Security Features

- **SQL Injection Prevention**: Whitelist-based validation
- **Query Limits**: Maximum 10,000 results per query
- **Dangerous Operation Blocking**: Prevents DROP, DELETE, UPDATE operations
- **Question Validation**: Rejects unanswerable or complex questions

## 📈 Performance

- **ETL Sync**: ~100 blocks/second (varies by system)
- **SQL Generation**: <1 second for rule-based, 2-5 seconds for AI-powered
- **Query Execution**: Depends on query complexity and data size
- **Storage**: ~1GB per 10,000 blocks

## 🧪 Testing

### Run All Tests
```bash
cd tests
python3 run_tests.py
```

### Test Categories
- **Unit Tests**: Individual component testing
- **Integration Tests**: End-to-end workflow testing
- **Performance Tests**: Timing and resource usage
- **Security Tests**: SQL injection and validation testing

## 🚨 Troubleshooting

### Common Issues

1. **RPC Connection Failed**
   - Check if bitcoind is running
   - Verify RPC credentials in config
   - Ensure RPC port is accessible

2. **Database Locked**
   - Close other applications using the database
   - Check for zombie processes
   - Restart the ETL process

3. **Out of Disk Space**
   - Monitor disk usage during sync
   - Consider syncing fewer blocks initially
   - Use external storage for large datasets

4. **Slow Performance**
   - Increase database cache size
   - Use SSD storage
   - Optimize Bitcoin Core settings

### Logs
- ETL logs: `etl_sync.log`
- Application logs: Check console output
- Bitcoin Core logs: Check bitcoind output

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Bitcoin Core development team
- SQLite developers
- OpenAI for GPT models
- Python community

## 📞 Support

For issues and questions:
1. Check the troubleshooting section
2. Review existing GitHub issues
3. Create a new issue with detailed information

---

**Note**: This system is designed for educational and research purposes. Always validate results and use appropriate security measures in production environments.
