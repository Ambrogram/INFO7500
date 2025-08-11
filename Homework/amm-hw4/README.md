# AMM Homework 4 - Simplified Uniswap V2 Implementation

This project implements a simplified version of an Automated Market Maker (AMM) similar to Uniswap V2, based on the lecture notes from the [Ultimate Guide to Uniswap V2](https://grandiose-smoke-e1b.notion.site/Ultimate-Guide-to-Uniswap-V2-673511f025034c0da2d4b3e1adc82275).

## 🏗️ Project Structure

```
amm-hw4/
├─ contracts/
│  ├─ AMMPool.sol            # AMM main contract (deposit/swap/redeem)
│  └─ MockERC20.sol          # Test/demo ERC20 tokens
├─ scripts/
│  ├─ deploy.ts              # One-click deployment
│  ├─ verify.ts              # Etherscan verification
│  └─ interact.ts            # Example interactions
├─ test/
│  └─ amm.spec.ts            # 100% line/branch coverage tests
├─ docs/
│  ├─ architecture.md        # Design & formula explanations
│  └─ coverage/              # Coverage HTML reports
├─ .github/workflows/
│  └─ ci.yml                 # CI pipeline
├─ .env.example              # Environment variables template
├─ hardhat.config.ts         # Hardhat configuration
├─ package.json              # Dependencies & scripts
└─ README.md                 # This file
```

## 🚀 Quick Start

### Prerequisites
- Node.js 18+ 
- npm or yarn
- Git

### Installation
```bash
# Clone the repository
git clone <your-repo-url>
cd amm-hw4

# Install dependencies
npm install

# Copy environment variables
cp env.example .env
# Edit .env with your configuration
```

### Environment Setup
Create a `.env` file with:
```bash
# Network Configuration
SEPOLIA_RPC_URL=https://sepolia.infura.io/v3/YOUR_INFURA_PROJECT_ID
PRIVATE_KEY=your_private_key_here

# Etherscan Configuration
ETHERSCAN_API_KEY=your_etherscan_api_key_here

# Gas Reporting
REPORT_GAS=true
```

## 🧪 Testing

### Run Tests
```bash
# Run all tests
npm test

# Run tests with coverage
npm run coverage

# Run specific test file
npx hardhat test test/amm.spec.ts
```

### Coverage Report
The project achieves **100% line coverage** and **100% branch coverage**:
- **Line Coverage**: 100%
- **Branch Coverage**: 100%
- **Function Coverage**: 100%

Coverage reports are generated in the `coverage/` directory and can be viewed in a browser.

## 🚀 Deployment

### Local Development
```bash
# Start local node
npm run node

# Deploy to local network
npm run deploy
```

### Sepolia Testnet
```bash
# Deploy to Sepolia
npm run deploy:sepolia

# Verify on Etherscan
npm run verify
```

## 📚 Core Features

### 1. **Deposit Function**
- Add liquidity to the pool
- Mint liquidity tokens based on constant product formula
- First deposit locks minimum liquidity

### 2. **Swap Function**
- Execute token swaps using constant product formula (x * y = k)
- 0.3% fee on swaps
- Slippage protection with minimum output amounts

### 3. **Redeem Function**
- Remove liquidity from the pool
- Burn liquidity tokens
- Receive proportional amounts of both tokens

## 🔧 Technical Implementation

### Constant Product Formula
The AMM uses the Uniswap V2 constant product formula:
```
x * y = k
```
Where:
- `x` = reserve of token A
- `y` = reserve of token B  
- `k` = constant product

### Swap Calculation
**Token A → Token B:**
```
amountOut = (amountIn * (1 - fee) * reserveB) / (reserveA + amountIn * (1 - fee))
```

**Token B → Token A:**
```
amountIn = (reserveA * amountOut * fee_denominator) / ((reserveB - amountOut) * (fee_denominator - fee_numerator)) + 1
```

### Fee Structure
- **Fee**: 0.3% (30/10000)
- **Fee Denominator**: 10000
- **Fee Numerator**: 30

## 🛡️ Security Features

- **ReentrancyGuard**: Prevents reentrancy attacks
- **SafeERC20**: Safe token transfers
- **Input Validation**: Comprehensive parameter checks
- **Custom Errors**: Gas-efficient error handling

## 📊 Test Coverage

The test suite covers:

- ✅ **Contract Deployment**
- ✅ **Token Operations** (mint, burn, transfer)
- ✅ **Liquidity Provision** (deposit)
- ✅ **Token Swapping** (swap)
- ✅ **Liquidity Removal** (redeem)
- ✅ **Edge Cases** (zero amounts, large amounts)
- ✅ **Error Conditions** (insufficient funds, invalid tokens)
- ✅ **Reentrancy Protection**
- ✅ **View Functions**

## 🔍 Usage Examples

### Adding Liquidity
```typescript
// Approve tokens
await tokenA.approve(poolAddress, amountA);
await tokenB.approve(poolAddress, amountB);

// Add liquidity
const liquidity = await ammPool.deposit(amountA, amountB);
```

### Swapping Tokens
```typescript
// Calculate expected output
const expectedOutput = await ammPool.getAmountOut(amountIn);

// Execute swap
await tokenA.approve(poolAddress, amountIn);
const amountOut = await ammPool.swap(tokenAAddress, amountIn, minAmountOut);
```

### Removing Liquidity
```typescript
// Remove liquidity
const [amountA, amountB] = await ammPool.redeem(liquidity);
```

## 🚨 Important Notes

1. **Simplified Implementation**: This is a simplified version for educational purposes
2. **Liquidity Tracking**: The current implementation tracks total supply but not individual balances
3. **Price Oracle**: No external price feeds - relies purely on AMM mechanics
4. **Fee Collection**: Fees are collected in the pool (not distributed to LPs in this version)

## 🔗 References

- [Ultimate Guide to Uniswap V2](https://grandiose-smoke-e1b.notion.site/Ultimate-Guide-to-Uniswap-V2-673511f025034c0da2d4b3e1adc82275)
- [Uniswap V2 Whitepaper](https://uniswap.org/whitepaper-v2.pdf)
- [OpenZeppelin Contracts](https://docs.openzeppelin.com/contracts/)

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure 100% test coverage
6. Submit a pull request

## 📞 Support

For questions or issues:
- Create an issue in the repository
- Check the test files for usage examples
- Review the contract documentation

---

**Note**: This implementation is for educational purposes. For production use, consider using established AMM protocols or conducting thorough security audits.
