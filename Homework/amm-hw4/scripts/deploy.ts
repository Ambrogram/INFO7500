import { ethers } from "hardhat";

async function main() {
  const [deployer] = await ethers.getSigners();

  console.log("Deploying contracts with the account:", deployer.address);
  console.log("Account balance:", (await ethers.provider.getBalance(deployer.address)).toString());

  // Deploy MockERC20 Token A (USDC-like)
  const MockERC20 = await ethers.getContractFactory("MockERC20");
  const tokenA = await MockERC20.deploy("Mock USDC", "mUSDC", 6, 1000000); // 1M USDC
  await tokenA.waitForDeployment();
  console.log("Token A deployed to:", await tokenA.getAddress());

  // Deploy MockERC20 Token B (ETH-like)
  const tokenB = await MockERC20.deploy("Mock ETH", "mETH", 18, 1000); // 1K ETH
  await tokenB.waitForDeployment();
  console.log("Token B deployed to:", await tokenB.getAddress());

  // Deploy AMM Pool
  const AMMPool = await ethers.getContractFactory("AMMPool");
  const ammPool = await AMMPool.deploy(await tokenA.getAddress(), await tokenB.getAddress());
  await ammPool.waitForDeployment();
  console.log("AMM Pool deployed to:", await ammPool.getAddress());

  // Mint some tokens to the deployer for testing
  const tokenABalance = await tokenA.balanceOf(deployer.address);
  const tokenBBalance = await tokenB.balanceOf(deployer.address);
  
  console.log("\nToken balances after deployment:");
  console.log("Token A (mUSDC):", ethers.formatUnits(tokenABalance, 6));
  console.log("Token B (mETH):", ethers.formatUnits(tokenBBalance, 18));

  // Verify deployment
  const poolTokenA = await ammPool.tokenA();
  const poolTokenB = await ammPool.tokenB();
  
  console.log("\nPool verification:");
  console.log("Pool Token A:", poolTokenA);
  console.log("Pool Token B:", poolTokenB);
  console.log("Deployed Token A:", await tokenA.getAddress());
  console.log("Deployed Token B:", await tokenB.getAddress());

  if (poolTokenA === await tokenA.getAddress() && poolTokenB === await tokenB.getAddress()) {
    console.log("✅ Pool deployment verified successfully!");
  } else {
    console.log("❌ Pool deployment verification failed!");
  }

  console.log("\nDeployment completed successfully!");
  console.log("You can now:");
  console.log("1. Approve tokens for the pool");
  console.log("2. Add liquidity using deposit()");
  console.log("3. Perform swaps using swap()");
  console.log("4. Remove liquidity using redeem()");
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });
