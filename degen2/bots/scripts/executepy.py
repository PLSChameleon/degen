from brownie import accounts, network, thisswap
from brownie.network.contract import Contract

def main():
    # Load your account using Brownie accounts
    acct = accounts.load('testmaster')

    # Ensure you're on the correct network
    network_name = 'pulsechain-main'  # or 'ropsten', 'kovan', etc.
    if network.show_active() != network_name:
        network.connect(network_name)

    # Contract details
    thisswap_address = '0x91bC49ec56F308C3201d77C4126EdF67913c6874'  # Replace with your contract's address
    thisswap_contract = Contract.from_abi("thisswap", thisswap_address, thisswap.abi)

    # Parameters for the execute function
    flashBorrowPoolAddress = '0x...'
    flashBorrowTokenAddress = '0x...'
    flashBorrowTokenAmount = 1000000000000000000  # Example: 1 token (assuming 18 decimals)
    swapPath = ['0x...', '0x...']  # Example path
    swapRouterAddress = '0x...'

    # Execute the function
    tx = thisswap_contract.execute(
        flashBorrowPoolAddress,
        flashBorrowTokenAddress,
        flashBorrowTokenAmount,
        swapPath,
        swapRouterAddress,
        {'from': acct}
    )

    print(f'Transaction sent! Hash: {tx.txid}')