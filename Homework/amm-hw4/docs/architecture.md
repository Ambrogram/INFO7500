# AMM Architecture & Design Documentation

## Overview

This document explains the architecture and design principles behind our simplified AMM implementation, which is based on Uniswap V2's constant product formula.

## Core Design Principles

### 1. Constant Product Formula (x * y = k)

The fundamental principle of our AMM is the constant product formula:

```
reserveA * reserveB = k (constant)
```

This formula ensures that:
- The product of reserves remains constant before and after trades
- Price changes are inversely proportional to trade size
- Larger trades have higher price impact (slippage)

### 2. Automated Price Discovery

Prices are determined automatically by the ratio of reserves:
```
priceA = reserveB / reserveA
priceB = reserveA / reserveB
```

No external price feeds or oracles are needed - the market determines prices through supply and demand.

## Mathematical Implementation

### Swap Calculations

#### Token A → Token B Swap

When swapping token A for token B:

```solidity
function getAmountOut(uint256 amountA) public view returns (uint256 amountB) {
    if (amountA == 0) return 0;
    if (reserveA == 0 || reserveB == 0) return 0;
    
    uint256 amountAWithFee = amountA * (FEE_DENOMINATOR - FEE_NUMERATOR);
    uint256 numerator = amountAWithFee * reserveB;
    uint256 denominator = (reserveA * FEE_DENOMINATOR) + amountAWithFee;
    amountB = numerator / denominator;
}
```

**Formula:**
```
amountOut = (amountIn * (1 - fee) * reserveB) / (reserveA + amountIn * (1 - fee))
```

**Where:**
- `amountIn` = amount of token A being sold
- `fee` = 0.3% (30/10000)
- `reserveA` = current reserve of token A
- `reserveB` = current reserve of token B

#### Token B → Token A Swap

When swapping token B for token A:

```solidity
function getAmountIn(uint256 amountB) public view returns (uint256 amountA) {
    if (amountB == 0) return 0;
    if (reserveA == 0 || reserveB == 0) return 0;
    
    uint256 numerator = reserveA * amountB * FEE_DENOMINATOR;
    uint256 denominator = (reserveB - amountB) * (FEE_DENOMINATOR - FEE_NUMERATOR);
    amountA = (numerator / denominator) + 1; // Add 1 to account for rounding
}
```

**Formula:**
```
amountIn = (reserveA * amountOut * fee_denominator) / ((reserveB - amountOut) * (fee_denominator - fee_numerator)) + 1
```

**Where:**
- `amountOut` = desired amount of token A to receive
- `fee_denominator` = 10000
- `fee_numerator` = 30 (0.3%)

### Liquidity Provision

#### First Deposit

For the first deposit, liquidity tokens are calculated as:
```solidity
if (totalSupply == 0) {
    // First deposit
    liquidity = Math.sqrt(amountA * amountB) - MINIMUM_LIQUIDITY;
    _mint(address(0), MINIMUM_LIQUIDITY); // Lock minimum liquidity
}
```

**Formula:**
```
liquidity = √(amountA * amountB) - MINIMUM_LIQUIDITY
```

The minimum liquidity is locked forever to prevent division by zero in future calculations.

#### Subsequent Deposits

For additional deposits, liquidity is calculated proportionally:
```solidity
} else {
    // Calculate liquidity based on current reserves
    uint256 liquidityA = (amountA * totalSupply) / _reserveA;
    uint256 liquidityB = (amountB * totalSupply) / _reserveB;
    liquidity = Math.min(liquidityA, liquidityB);
}
```

**Formula:**
```
liquidityA = (amountA * totalSupply) / reserveA
liquidityB = (amountB * totalSupply) / reserveB
liquidity = min(liquidityA, liquidityB)
```

This ensures that new liquidity providers receive tokens proportional to the existing pool ratio.

### Liquidity Removal

When removing liquidity:
```solidity
function redeem(uint256 liquidity) external returns (uint256 amountA, uint256 amountB) {
    uint256 _totalSupply = totalSupply;
    amountA = (liquidity * reserveA) / _totalSupply;
    amountB = (liquidity * reserveB) / _totalSupply;
    
    // Burn liquidity tokens and transfer underlying tokens
    _burn(msg.sender, liquidity);
    tokenA.safeTransfer(msg.sender, amountA);
    tokenB.safeTransfer(msg.sender, amountB);
}
```

**Formula:**
```
amountA = (liquidity * reserveA) / totalSupply
amountB = (liquidity * reserveB) / totalSupply
```

## Fee Structure

### Fee Calculation

Our AMM charges a 0.3% fee on all swaps:
- **Fee Denominator**: 10000
- **Fee Numerator**: 30
- **Effective Fee**: 30/10000 = 0.3%

### Fee Collection

Fees are collected by adjusting the swap calculations:
- For A→B swaps: `amountAWithFee = amountA * (10000 - 30) / 10000`
- For B→A swaps: The fee is built into the `getAmountIn` calculation

## Security Considerations

### 1. Reentrancy Protection

All external functions are protected with `ReentrancyGuard`:
```solidity
function deposit(uint256 amountA, uint256 amountB) 
    external 
    nonReentrant 
    returns (uint256 liquidity)
```

### 2. Safe Token Transfers

We use OpenZeppelin's `SafeERC20` for all token operations:
```solidity
using SafeERC20 for IERC20;
tokenA.safeTransferFrom(msg.sender, address(this), amountA);
```

### 3. Input Validation

Comprehensive parameter validation:
```solidity
if (amountA == 0 || amountB == 0) revert ZeroAmount();
if (tokenIn != address(tokenA) && tokenIn != address(tokenB)) revert InvalidToken();
```

### 4. Custom Errors

Gas-efficient error handling:
```solidity
error InsufficientLiquidity();
error InsufficientOutputAmount();
error InvalidToken();
error ZeroAmount();
```

## Gas Optimization

### 1. Storage Layout

- Immutable variables for token addresses
- Packed storage for reserves
- Efficient data structures

### 2. Function Optimization

- View functions for calculations
- Minimal storage writes
- Efficient math operations

### 3. Error Handling

- Custom errors instead of require statements
- Early returns for edge cases

## Limitations & Simplifications

### 1. Liquidity Tracking

**Current Implementation:**
- Only tracks total supply of liquidity tokens
- No individual balance tracking
- Simplified for educational purposes

**Production Implementation Would Include:**
- Mapping from address to liquidity balance
- Proper LP token distribution
- Fee distribution to LPs

### 2. Price Oracle

**Current Implementation:**
- No external price feeds
- Pure AMM price discovery

**Production Implementation Would Include:**
- Price oracle integration
- MEV protection
- Flash loan protection

### 3. Fee Distribution

**Current Implementation:**
- Fees stay in the pool
- No LP fee distribution

**Production Implementation Would Include:**
- Fee distribution to LPs
- Protocol fee collection
- Dynamic fee adjustment

## Future Enhancements

### 1. Advanced Features

- Concentrated liquidity (Uniswap V3 style)
- Multiple fee tiers
- Flash swaps
- Price oracles

### 2. Governance

- DAO governance
- Parameter adjustment
- Fee modification
- Upgrade mechanisms

### 3. Cross-Chain

- Bridge integration
- Multi-chain pools
- Cross-chain swaps

## Testing Strategy

### 1. Unit Tests

- Individual function testing
- Edge case coverage
- Error condition testing

### 2. Integration Tests

- End-to-end workflows
- Multi-user scenarios
- Gas optimization testing

### 3. Coverage Goals

- **Line Coverage**: 100%
- **Branch Coverage**: 100%
- **Function Coverage**: 100%

## Conclusion

This AMM implementation provides a solid foundation for understanding automated market makers while maintaining security and efficiency. The constant product formula ensures fair price discovery, while the fee structure provides incentives for liquidity providers.

The simplified design makes it ideal for educational purposes while demonstrating real-world DeFi concepts and best practices.
