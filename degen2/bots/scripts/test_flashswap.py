from brownie import FlashSwap, accounts, interface

def main():
    # Load the deployed FlashSwap contract
    flash_swap = FlashSwap.at('0x7E134497b975C30D4a770Ce9db96edd77Ef6F5fd')  # Replace with your deployed contract address
    
    # Define the two Atropa pools and associated tokens
    pairs = [
        '0xd7E98780C10c9c716A87A7f76E76cB1d49556dA1',  # Replace with actual pool addresses
        '0xF892d93199B4DE0aB1CDf35799Ccf9D5A425581B'
    ]

    amounts0_out = [
        473070000000000000000,  # Replace with the actual amounts
        0
    ]

    amounts1_out = [
        0,  # Replace with the actual amounts
        468340000000000000000
    ]

    tokens0 = [
        '0xYourToken0Address1',  # Replace with actual token addresses
        '0xYourToken0Address2'
    ]

    tokens1 = [
        '0xYourToken1Address1',  # Replace with actual token addresses
        '0xYourToken1Address2'
    ]

    data = [
        '0x',  # Replace with actual data for the swap
        '0x'
    ]

    # Execute the flash swap
    tx = flash_swap.execute(
        pairs,
        amounts0_out,
        amounts1_out,
        tokens0,
        tokens1,
        data,
        {'from': accounts.load('testmaster'), 'gas_limit': 5000000}  # Ensure you have the 'testmaster' account loaded or use a different account
    )
    print(f"Transaction Hash: {tx.txid}")
