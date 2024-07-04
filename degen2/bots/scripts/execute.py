from brownie import Contract, accounts
import json

def main():
    try:
        # Load your account
        account = accounts.load('testmaster')

        # Load the ABI for FlashFlashSwap
        with open('../build/contracts/FlashFlashSwap.json', 'r') as abi_file:
            contract_data = json.load(abi_file)
            flashFlashSwap_abi = contract_data['abi']

        # Contract addresses and parameters
        flashBorrowPoolAddress = '0xd7E98780C10c9c716A87A7f76E76cB1d49556dA1'
        flashBorrowTokenAddress = '0xCc78A0acDF847A2C1714D2A925bB4477df5d48a6'
        flashBorrowTokenAmount = int(1e18)  # Borrowing 1 WETH for example, adjust as needed
        swapPath = [flashBorrowTokenAddress, '0xA1077a294dDE1B09bB078844df40758a5D0f9a27']  # WETH to DAI path
        swapRouterAddress = '0x165C3410fC91EF562C50559f7d2289fEbed552d9'


        # The address of your deployed FlashFlashSwap contract
        flashFlashSwapAddress = '0x4c43af2D2BDb535c3Be40b94BedE74C150Cb94D9'

        # Create a contract object for your FlashFlashSwap using the loaded ABI
        flash_flash_swap = Contract.from_abi("FlashFlashSwap", flashFlashSwapAddress, flashFlashSwap_abi)

        # Execute the flash swap
        tx = flash_flash_swap.execute(
            flashBorrowPoolAddress,
            flashBorrowTokenAddress,
            flashBorrowTokenAmount,
            swapPath,
            swapRouterAddress,
            {'from': account, 'gas_limit': 8000000}  # Adjust the gas limit as needed
        )

        # Wait for the transaction to be confirmed
        tx.wait(1)

        print(f"Flash swap executed: {tx.txid}")

    except Exception as e:
        print(f"Error: {str(e)}")
