import { ethers } from "hardhat";

async function main() {
  const [deployer, user1, user2] = await ethers.getSigners();

  console.log("Interacting with AMM Pool contracts...");
  console.log("Deployer:", deployer.address);
  console.log("User 1:", user1.address);
  console.log("User 2:", user2.address);

  // Get deployed contract addresses (you'll need to update these after deployment)
  const tokenAAddress = process.env.TOKEN_A_ADDRESS || "0x...";
  const tokenBAddress = process.env.TOKEN_B_ADDRESS || "0x...";
  const poolAddress = process.env.POOL_ADDRESS || "0x...";

  if (tokenAAddress === "0x..." || tokenBAddress === "0x..." || poolAddress === "0x...") {
    console.log("Please set the contract addresses in environment variables first:");
    console.log("TOKEN_A_ADDRESS, TOKEN_B_ADDRESS, POOL_ADDRESS");
    console.log("Or update this script with the actual addresses after deployment");
    return;
  }

  const tokenA = await ethers.getContractAt("MockERC20", tokenAAddress);
  const tokenB = await ethers.getContractAt("MockERC20", tokenBAddress);
  const ammPool = await ethers.getContractAt("AMMPool", poolAddress);

  console.log("\n=== AMM Pool Interaction Demo ===");

  // Check initial balances
  console.log("\n1. Checking initial balances:");
  const deployerBalanceA = await tokenA.balanceOf(deployer.address);
  const deployerBalanceB = await tokenB.balanceOf(deployer.address);
  console.log(`Deployer Token A: ${ethers.formatUnits(deployerBalanceA, 6)} mUSDC`);
  console.log(`Deployer Token B: ${ethers.formatUnits(deployerBalanceB, 18)} mETH`);

  // Check pool reserves
  const [reserveA, reserveB] = await ammPool.getReserves();
  console.log(`Pool Reserve A: ${ethers.formatUnits(reserveA, 6)} mUSDC`);
  console.log(`Pool Reserve B: ${ethers.formatUnits(reserveB, 18)} mETH`);

  // Add liquidity (deposit)
  console.log("\n2. Adding liquidity to the pool:");
  const depositAmountA = ethers.parseUnits("1000", 6); // 1000 mUSDC
  const depositAmountB = ethers.parseUnits("1", 18);   // 1 mETH

  try {
    // Approve tokens
    console.log("Approving tokens for pool...");
    await tokenA.approve(poolAddress, depositAmountA);
    await tokenB.approve(poolAddress, depositAmountB);

    // Add liquidity
    console.log("Adding liquidity...");
    const tx = await ammPool.deposit(depositAmountA, depositAmountB);
    await tx.wait();
    console.log("✅ Liquidity added successfully!");

    // Check new reserves
    const [newReserveA, newReserveB] = await ammPool.getReserves();
    console.log(`New Pool Reserve A: ${ethers.formatUnits(newReserveA, 6)} mUSDC`);
    console.log(`New Pool Reserve B: ${ethers.formatUnits(newReserveB, 18)} mETH`);

  } catch (error: any) {
    console.error("❌ Failed to add liquidity:", error.message);
  }

  // Perform a swap
  console.log("\n3. Performing a swap:");
  const swapAmountIn = ethers.parseUnits("100", 6); // 100 mUSDC
  const minAmountOut = ethers.parseUnits("0.09", 18); // 0.09 mETH

  try {
    // Calculate expected output
    const expectedOutput = await ammPool.getAmountOut(swapAmountIn);
    console.log(`Expected output: ${ethers.formatUnits(expectedOutput, 18)} mETH`);

    // Approve token for swap
    await tokenA.approve(poolAddress, swapAmountIn);

    // Perform swap
    console.log("Executing swap...");
    const swapTx = await ammPool.swap(tokenAAddress, swapAmountIn, minAmountOut);
    await swapTx.wait();
    console.log("✅ Swap executed successfully!");

    // Check new reserves after swap
    const [afterSwapReserveA, afterSwapReserveB] = await ammPool.getReserves();
    console.log(`After Swap - Reserve A: ${ethers.formatUnits(afterSwapReserveA, 6)} mUSDC`);
    console.log(`After Swap - Reserve B: ${ethers.formatUnits(afterSwapReserveB, 18)} mETH`);

  } catch (error: any) {
    console.error("❌ Failed to perform swap:", error.message);
  }

  // Check final balances
  console.log("\n4. Final balances:");
  const finalBalanceA = await tokenA.balanceOf(deployer.address);
  const finalBalanceB = await tokenB.balanceOf(deployer.address);
  console.log(`Final Token A: ${ethers.formatUnits(finalBalanceA, 6)} mUSDC`);
  console.log(`Final Token B: ${ethers.formatUnits(finalBalanceB, 18)} mETH`);

  console.log("\n=== Demo completed! ===");
  console.log("You can now:");
  console.log("- Add more liquidity");
  console.log("- Perform more swaps");
  console.log("- Remove liquidity (redeem)");
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });
