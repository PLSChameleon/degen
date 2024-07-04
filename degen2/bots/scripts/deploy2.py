from brownie import accounts, ThisSwap

def main():
    deployer = accounts.load('testmaster')  # Ensure this account is loaded and has enough ETH

    # Deploy the FlashSwap contract without passing the Uniswap V2 Factory address
    flash_swap = thisswap.deploy({'from': deployer})

    # Print the deployed contract address
    print(f"FlashSwap contract deployed at {flash_swap.address}")

    # Verify contract details
    print(f"FlashSwap ABI: {flash_swap.abi}")
    print(f"FlashSwap Address: {flash_swap.address}")

if __name__ == "__main__":
    main()