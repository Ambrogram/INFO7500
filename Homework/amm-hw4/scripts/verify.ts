import { ethers, run } from "hardhat";

async function main() {
  const contractAddress = process.env.CONTRACT_ADDRESS;
  const constructorArguments = process.env.CONSTRUCTOR_ARGS;

  if (!contractAddress) {
    console.error("Please set CONTRACT_ADDRESS environment variable");
    process.exit(1);
  }

  console.log("Verifying contract at address:", contractAddress);

  try {
    await run("verify:verify", {
      address: contractAddress,
      constructorArguments: constructorArguments ? JSON.parse(constructorArguments) : [],
    });
    console.log("✅ Contract verified successfully on Etherscan!");
  } catch (error: any) {
    if (error.message.includes("Already Verified")) {
      console.log("✅ Contract is already verified on Etherscan!");
    } else {
      console.error("❌ Verification failed:", error.message);
    }
  }
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });
