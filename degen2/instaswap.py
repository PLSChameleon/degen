import sys
import os
import time
from decimal import Decimal
from brownie import accounts, network, Contract
from dotenv import dotenv_values
import json
from web3 import Web3
from degenbot import *

# Constants
PULSEX_ROUTER_CONTRACT_ADDRESS = "0x165C3410fC91EF562C50559f7d2289fEbed552d9"
PULSEX_POOL_CONTRACT_ADDRESS = "0xaE8429918FdBF9a5867e3243697637Dc56aa76A1"
WPLS_CONTRACT_ADDRESS = "0xA1077a294dDE1B09bB078844df40758a5D0f9a27"
DAI_CONTRACT_ADDRESS = "0x6B175474E89094C44Da98b954EedeAC495271d0F"

SLIPPAGE = Decimal("0.001")  # Tolerated slippage in swap price (0.1%)
ETHEREUM_NODE_URL = "https://rpc-pulsechain.g4mm4.io"




# Initialize Web3 instance
web3 = Web3(Web3.HTTPProvider(ETHEREUM_NODE_URL))
set_web3(web3)

# Simulate swaps and approvals
DRY_RUN = False
LOOP_TIME = 2  # Increased loop time for better readability of logs

# Current script directory
script_dir = os.path.dirname(os.path.abspath(__file__))



ABI_PATHS = {
    "v2_pool": os.path.join(script_dir, "abi", "v2_pool_abi.json"),
    "v2_router": os.path.join(script_dir, "abi", "v2_router_abi.json"),
    "v2_factory": os.path.join(script_dir, "abi", "v2_factory_abi.json"),
    "erc20": os.path.join(script_dir, "abi", "erc20_abi.json"),
    "wpls": os.path.join(script_dir, "abi", "wpls_contract_abi.json"),
}

# Load ABIs
abis = {}
for key, path in ABI_PATHS.items():
    try:
        with open(path, "r") as abi_file:
            abis[key] = json.load(abi_file)
    except FileNotFoundError:
        sys.exit(f"ABI JSON file '{path}' not found.")
    except Exception as e:
        sys.exit(f"Failed to load ABI JSON file '{path}': {e}")

try:
    env_values = dotenv_values("limit_bot.env")
    BROWNIE_NETWORK = env_values.get("BROWNIE_NETWORK")
    BROWNIE_ACCOUNT = env_values.get("BROWNIE_ACCOUNT")

    if not BROWNIE_NETWORK or not BROWNIE_ACCOUNT:
        sys.exit("Environment variables BROWNIE_NETWORK or BROWNIE_ACCOUNT not found in limit_bot.env")

except Exception as e:
    sys.exit(f"Failed to load environment variables: {e}")

def get_price_from_pool(pool_contract, token0, token1):
    """
    Function to get the price of token0 in terms of token1 from the pool reserves.
    """
    reserves = pool_contract.getReserves()
    reserve0 = Decimal(reserves[0])
    reserve1 = Decimal(reserves[1])
    
    if pool_contract.token0() == token0:
        price = reserve1 / reserve0  # token0 price in terms of token1
    else:
        price = reserve0 / reserve1  # token0 price in terms of token1
    
    return price

def condition_to_swap_met(pulsex_lp, wpls, dai, threshold_price):
    """
    Function to check conditions for executing a swap based on WPLS per DAI ratio.
    Replace with your actual logic based on token prices, market conditions, etc.
    """
    # Get current price from pool
    wpls_price = get_price_from_pool(pulsex_lp, wpls.address, dai.address)
    print(f"Current WPLS price: {wpls_price} DAI")  # Log the current price

    # Check if WPLS per DAI exceeds the desired threshold
    return wpls_price >= threshold_price

def wrap_pls(amount, wpls_contract, account):
    """
    Function to wrap PLS into WPLS.
    """
    try:
        tx = wpls_contract.deposit({'from': account, 'value': amount})
        tx.wait(1)
        print(f"Wrapped {amount} PLS to WPLS")
    except Exception as e:
        print(f"Failed to wrap PLS: {e}")

def main():
    try:
        network.connect(BROWNIE_NETWORK)
        print(f"Connected to network: {BROWNIE_NETWORK}")  # Log network connection
    except Exception as e:
        sys.exit(f"Could not connect to network! Verify your Brownie network settings using 'brownie networks list': {e}")

    try:
        degenbot = accounts.load(BROWNIE_ACCOUNT)
        print(f"Loaded account: {BROWNIE_ACCOUNT}")  # Log account loading
    except Exception as e:
        sys.exit(f"Could not load account! Verify your Brownie account settings using 'brownie accounts list': {e}")

    # Instantiate ERC20 tokens with the web3 instance
    dai = Contract.from_abi("DAI", address=DAI_CONTRACT_ADDRESS, abi=abis["erc20"], owner=degenbot)
    wpls = Contract.from_abi("WPLS", address=WPLS_CONTRACT_ADDRESS, abi=abis["wpls"], owner=degenbot)

    # Load Router contract using brownie's Contract.from_abi
    pulsex_router = Contract.from_abi("Router", address=PULSEX_ROUTER_CONTRACT_ADDRESS, abi=abis["v2_router"], owner=degenbot)

    # Instantiate LiquidityPool with Contract.from_abi
    pulsex_lp = Contract.from_abi("LiquidityPool", address=PULSEX_POOL_CONTRACT_ADDRESS, abi=abis["v2_pool"], owner=degenbot)

    lps = [pulsex_lp]

    # Approve tokens for Router if necessary
    for token in [dai, wpls]:
        allowance = token.allowance(degenbot, pulsex_router)
        if allowance == 0 and not DRY_RUN:
            try:
                token.approve(pulsex_router, 2**256 - 1, {'from': degenbot})
                print(f"Approved {token.symbol()} for Router")  # Log token approval
            except Exception as e:
                print(f"Failed to approve {token.symbol()}: {e}")
                return

    # Set current price as the desired swap amount for testing
    initial_price = get_price_from_pool(pulsex_lp, wpls.address, dai.address)
    print(f"Initial WPLS price for testing: {initial_price} DAI")

    # Main loop for checking prices and executing swaps
    while True:
        try:
            if not network.is_connected():
                print("Network connection lost! Reconnecting...")
                network.connect(BROWNIE_NETWORK)
                print("Reconnected to network")  # Log reconnection

            # Check token balances before attempting swap
            wpls_balance = wpls.balanceOf(degenbot)
            dai_balance = dai.balanceOf(degenbot)
            pls_balance = degenbot.balance()  # Get PLS balance
            print(f"WPLS balance: {wpls_balance}, DAI balance: {dai_balance}, PLS balance: {pls_balance}")  # Log balances

            # Wrap PLS to WPLS if needed
            if wpls_balance < Decimal(1000) and pls_balance > 0:
                amount_to_wrap = min(pls_balance, Decimal(10000) - wpls_balance)
                wrap_pls(amount_to_wrap, wpls, degenbot)
                wpls_balance = wpls.balanceOf(degenbot)

            # Check token prices and execute swaps when conditions are met
            for lp in lps:
                print(f"Checking prices on {lp.name}...")  # Log pool checking
                token_in_qty = Decimal(1000)  # Example token quantity to swap

                # Ensure there are enough tokens for the swap
                if wpls_balance < token_in_qty:
                    print(f"Not enough WPLS to perform the swap. Required: {token_in_qty}, Available: {wpls_balance}")
                    continue

                token_out_qty = Decimal(14.64)  # Example token quantity expected from swap

                # Check if conditions to swap are met
                if condition_to_swap_met(lp, wpls, dai, initial_price):
                    print(f"Executing swap on {lp.name}...")  # Log swap execution
                    try:
                        # Example swap logic
                        if not DRY_RUN:
                            pulsex_router.swapExactTokensForTokens(
                                int(token_in_qty),
                                int(token_out_qty * (Decimal(1) - SLIPPAGE)),
                                [wpls.address, dai.address],
                                degenbot.address,
                                int(time.time()) + 60 * 10,
                                {'from': degenbot, 'gas_limit': 2000000}  # Example gas limit
                            )
                        print(f"Swap executed: {token_in_qty} WPLS to {token_out_qty} DAI")  # Log successful swap
                    except Exception as e:
                        print(f"Failed to execute swap: {e}")

            # Control loop timing
            time.sleep(LOOP_TIME)

        except Exception as e:
            print(f"An error occurred: {e}")
            time.sleep(LOOP_TIME)

# Only executes main loop if this file is called directly
if __name__ == "__main__":
    main()
