// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
import "@openzeppelin/contracts/utils/math/Math.sol";

/**
 * @title AMMPool
 * @dev A simplified Automated Market Maker based on Uniswap V2 principles
 * Implements constant product formula: x * y = k
 */
contract AMMPool is ReentrancyGuard {
    using SafeERC20 for IERC20;
    using Math for uint256;

    // Token addresses
    IERC20 public immutable tokenA;
    IERC20 public immutable tokenB;
    
    // Pool state
    uint256 public reserveA;
    uint256 public reserveB;
    uint256 public totalSupply;
    mapping(address => uint256) public liquidityBalances;
    
    // Constants
    uint256 public constant MINIMUM_LIQUIDITY = 1000;
    uint256 public constant FEE_DENOMINATOR = 10000;
    uint256 public constant FEE_NUMERATOR = 30; // 0.3% fee
    
    // Events
    event Deposit(address indexed user, uint256 amountA, uint256 amountB, uint256 liquidity);
    event Swap(address indexed user, address indexed tokenIn, uint256 amountIn, uint256 amountOut);
    event Redeem(address indexed user, uint256 liquidity, uint256 amountA, uint256 amountB);
    
    // Errors
    error InsufficientLiquidity();
    error InsufficientOutputAmount();
    error InsufficientInputAmount();
    error InvalidToken();
    error ZeroAmount();
    error ZeroLiquidity();
    
    /**
     * @dev Constructor
     * @param _tokenA Address of first token
     * @param _tokenB Address of second token
     */
    constructor(address _tokenA, address _tokenB) {
        require(_tokenA != address(0) && _tokenB != address(0), "Invalid token addresses");
        require(_tokenA != _tokenB, "Tokens must be different");
        
        tokenA = IERC20(_tokenA);
        tokenB = IERC20(_tokenB);
    }
    
    /**
     * @dev Get current reserves
     * @return _reserveA Reserve of token A
     * @return _reserveB Reserve of token B
     */
    function getReserves() public view returns (uint256 _reserveA, uint256 _reserveB) {
        _reserveA = reserveA;
        _reserveB = reserveB;
    }
    
    /**
     * @dev Calculate amount of token B for given amount of token A
     * @param amountA Amount of token A
     * @return amountB Amount of token B
     */
    function getAmountOut(uint256 amountA) public view returns (uint256 amountB) {
        if (amountA == 0) return 0;
        if (reserveA == 0 || reserveB == 0) return 0;
        
        uint256 amountAWithFee = amountA * (FEE_DENOMINATOR - FEE_NUMERATOR);
        uint256 numerator = amountAWithFee * reserveB;
        uint256 denominator = (reserveA * FEE_DENOMINATOR) + amountAWithFee;
        amountB = numerator / denominator;
    }
    
    /**
     * @dev Calculate amount of token A for given amount of token B
     * @param amountB Amount of token B
     * @return amountA Amount of token A
     */
    function getAmountIn(uint256 amountB) public view returns (uint256 amountA) {
        if (amountB == 0) return 0;
        if (reserveA == 0 || reserveB == 0) return 0;
        
        uint256 numerator = reserveA * amountB * FEE_DENOMINATOR;
        uint256 denominator = (reserveB - amountB) * (FEE_DENOMINATOR - FEE_NUMERATOR);
        amountA = (numerator / denominator) + 1; // Add 1 to account for rounding
    }
    
    /**
     * @dev Add liquidity to the pool
     * @param amountA Amount of token A to add
     * @param amountB Amount of token B to add
     * @return liquidity Amount of liquidity tokens minted
     */
    function deposit(uint256 amountA, uint256 amountB) 
        external 
        nonReentrant 
        returns (uint256 liquidity) 
    {
        if (amountA == 0 || amountB == 0) revert ZeroAmount();
        
        // Transfer tokens from user
        tokenA.safeTransferFrom(msg.sender, address(this), amountA);
        tokenB.safeTransferFrom(msg.sender, address(this), amountB);
        
        uint256 _reserveA = reserveA;
        uint256 _reserveB = reserveB;
        
        if (totalSupply == 0) {
            // First deposit
            liquidity = Math.sqrt(amountA * amountB) - MINIMUM_LIQUIDITY;
            _mint(address(0), MINIMUM_LIQUIDITY); // Lock minimum liquidity
        } else {
            // Calculate liquidity based on current reserves
            uint256 liquidityA = (amountA * totalSupply) / _reserveA;
            uint256 liquidityB = (amountB * totalSupply) / _reserveB;
            liquidity = Math.min(liquidityA, liquidityB);
        }
        
        if (liquidity == 0) revert InsufficientLiquidity();
        
        _mint(msg.sender, liquidity);
        _updateReserves(_reserveA + amountA, _reserveB + amountB);
        
        emit Deposit(msg.sender, amountA, amountB, liquidity);
    }
    
    /**
     * @dev Swap tokens using constant product formula
     * @param tokenIn Address of token being sold
     * @param amountIn Amount of tokens being sold
     * @param minAmountOut Minimum amount of tokens to receive
     * @return amountOut Amount of tokens received
     */
    function swap(
        address tokenIn,
        uint256 amountIn,
        uint256 minAmountOut
    ) external nonReentrant returns (uint256 amountOut) {
        if (amountIn == 0) revert ZeroAmount();
        if (tokenIn != address(tokenA) && tokenIn != address(tokenB)) revert InvalidToken();
        
        address tokenOut = tokenIn == address(tokenA) ? address(tokenB) : address(tokenA);
        
        // Calculate output amount
        if (tokenIn == address(tokenA)) {
            amountOut = getAmountOut(amountIn);
        } else {
            amountOut = getAmountIn(amountIn);
        }
        
        if (amountOut < minAmountOut) revert InsufficientOutputAmount();
        
        // Transfer tokens from user
        IERC20(tokenIn).safeTransferFrom(msg.sender, address(this), amountIn);
        
        // Transfer tokens to user
        IERC20(tokenOut).safeTransfer(msg.sender, amountOut);
        
        // Update reserves
        if (tokenIn == address(tokenA)) {
            _updateReserves(reserveA + amountIn, reserveB - amountOut);
        } else {
            _updateReserves(reserveA - amountOut, reserveB + amountIn);
        }
        
        emit Swap(msg.sender, tokenIn, amountIn, amountOut);
    }
    
    /**
     * @dev Remove liquidity from the pool
     * @param liquidity Amount of liquidity tokens to burn
     * @return amountA Amount of token A received
     * @return amountB Amount of token B received
     */
    function redeem(uint256 liquidity) 
        external 
        nonReentrant 
        returns (uint256 amountA, uint256 amountB) 
    {
        if (liquidity == 0) revert ZeroAmount();
        if (liquidity > balanceOf(msg.sender)) revert InsufficientInputAmount();
        
        uint256 _totalSupply = totalSupply;
        amountA = (liquidity * reserveA) / _totalSupply;
        amountB = (liquidity * reserveB) / _totalSupply;
        
        if (amountA == 0 || amountB == 0) revert InsufficientLiquidity();
        
        // Burn liquidity tokens
        _burn(msg.sender, liquidity);
        
        // Transfer tokens to user
        tokenA.safeTransfer(msg.sender, amountA);
        tokenB.safeTransfer(msg.sender, amountB);
        
        // Update reserves
        _updateReserves(reserveA - amountA, reserveB - amountB);
        
        emit Redeem(msg.sender, liquidity, amountA, amountB);
    }
    
    /**
     * @dev Update reserves (internal function)
     * @param _reserveA New reserve of token A
     * @param _reserveB New reserve of token B
     */
    function _updateReserves(uint256 _reserveA, uint256 _reserveB) private {
        reserveA = _reserveA;
        reserveB = _reserveB;
    }
    
    /**
     * @dev Mint liquidity tokens (internal function)
     * @param to Address to mint tokens to
     * @param amount Amount of tokens to mint
     */
    function _mint(address to, uint256 amount) private {
        totalSupply += amount;
        liquidityBalances[to] += amount;
    }
    
    /**
     * @dev Burn liquidity tokens (internal function)
     * @param from Address to burn tokens from
     * @param amount Amount of tokens to burn
     */
    function _burn(address from, uint256 amount) private {
        totalSupply -= amount;
        liquidityBalances[from] -= amount;
    }
    
    /**
     * @dev Get balance of liquidity tokens for an address
     * @param account Address to check balance for
     * @return Balance of liquidity tokens
     */
    function balanceOf(address account) public view returns (uint256) {
        return liquidityBalances[account];
    }
}
