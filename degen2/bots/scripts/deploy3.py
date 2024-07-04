# scripts/deploy.py

from brownie import FlashSwap, accounts

def main():
    uniswapV2FactoryAddress = '0x29eA7545DEf87022BAdc76323F373EA1e707C523'  # Example Uniswap V2 Factory address
    uniswapV2RouterAddress = '0x165C3410fC91EF562C50559f7d2289fEbed552d9'  # Example Uniswap V2 Router address

    # Use the first account in the accounts list for deployment
    account = accounts.lost('testmaster')

    # Deploy the FlashSwap contract
    flash_swap = FlashSwap2.deploy(
        uniswapV2FactoryAddress,
        uniswapV2RouterAddress,
        {'from': account}
    )

    print(f"FlashSwap contract deployed at: {flash_swap.address}")
