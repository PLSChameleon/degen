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
NINEINCH_ROUTER_CONTRACT_ADDRESS = "0x11111112542D85B3EF69AE05771c2dCCff4fAa26"
PULSEX_POOL_CONTRACT_ADDRESS = "0xaE8429918FdBF9a5867e3243697637Dc56aa76A1"
NINEINCH_POOL_CONTRACT_ADDRESS = "0x8356eDc1d60B0EdE626BC52980e708A604b0E861"
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


def check_arbitrage_opportunity(pool1, pool2, wpls, dai, min_profit_threshold):
    price1 = get_price_from_pool(pool1, wpls.address, dai.address)
    price2 = get_price_from_pool(pool2, wpls.address, dai.address)
    
    price_diff = abs(price1 - price2)
    potential_profit = price_diff / min(price1, price2)
    
    if potential_profit > min_profit_threshold:
        if price1 < price2:
            return (pool1, pool2, potential_profit)
        else:
            return (pool2, pool1, potential_profit)
    
    return None

def check_and_approve_tokens(tokens, routers, account):
    for token in tokens:
        for router in routers:
            allowance = token.allowance(account, router.address)
            if allowance == 0:
                try:
                    print(f"Approving {token.symbol()} for {router.address}")
                    if not DRY_RUN:
                        token.approve(router.address, 2**256 - 1, {'from': account})
                    print(f"Approved {token.symbol()} for {router.address}")
                except Exception as e:
                    print(f"Failed to approve {token.symbol()} for {router.address}: {e}")
                    return False
    return True

def condition_to_swap_met(lp, wpls, dai, threshold_price):
    """
    Function to check conditions for executing a swap based on WPLS per DAI ratio.
    """
    # Get current price from pool
    wpls_price = get_price_from_pool(lp, wpls.address, dai.address)
    print(f"Current WPLS price on {lp.address}: {wpls_price} DAI")

    # You might want different conditions for different pools
    if lp.address == NINEINCH_POOL_CONTRACT_ADDRESS:
        # Specific condition for 9inch pool
        return wpls_price >= threshold_price * Decimal('1.0')  # Example: 5% higher threshold for 9inch
    else:
        # Original condition for other pools
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

def execute_swap(pool, token_in, token_out, amount_in, is_exact_input, account):
    router = Contract.from_abi("Router", address=PULSEX_ROUTER_CONTRACT_ADDRESS, abi=abis["v2_router"], owner=account)
    
    if is_exact_input:
        # Swap exact tokens for tokens
        tx = router.swapExactTokensForTokens(
            int(amount_in),
            0,  # Accept any amount out
            [token_in.address, token_out.address],
            account.address,
            int(time.time()) + 60 * 10,
            {'from': account, 'gas_limit': 2000000}
        )
    else:
        # Swap tokens for exact tokens
        tx = router.swapTokensForExactTokens(
            int(amount_in),
            2**256 - 1,  # Unlimited input
            [token_in.address, token_out.address],
            account.address,
            int(time.time()) + 60 * 10,
            {'from': account, 'gas_limit': 2000000}
        )
    
    tx.wait(1)
    return Decimal(tx.return_value[1])  # Return the amount out




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
    nineinch_router = Contract.from_abi("NineInchRouter", address=NINEINCH_ROUTER_CONTRACT_ADDRESS, abi=abis["v2_router"], owner=degenbot)

    # Instantiate LiquidityPool with Contract.from_abi
    pulsex_lp = Contract.from_abi("LiquidityPool", address=PULSEX_POOL_CONTRACT_ADDRESS, abi=abis["v2_pool"], owner=degenbot)
    nineinch_lp = Contract.from_abi("NineInchLiquidityPool", address=NINEINCH_POOL_CONTRACT_ADDRESS, abi=abis["v2_pool"], owner=degenbot)

    

    lps = [pulsex_lp, nineinch_lp]
    pools = [pulsex_lp, nineinch_lp]


    MIN_PROFIT_THRESHOLD = Decimal('0.001')  # 0.5% minimum profit threshold


    if not check_and_approve_tokens([dai, wpls], [pulsex_router, nineinch_router], degenbot):
        print("Failed to approve tokens. Exiting.")
        return

    # Set current price as the desired swap amount for testing
    initial_price = get_price_from_pool(pulsex_lp, wpls.address, dai.address)
    print(f"Initial WPLS price for testing: {initial_price} DAI")

    while True:
        try:
            if not network.is_connected():
                print("Network connection lost! Reconnecting...")
                network.connect(BROWNIE_NETWORK)
                print("Reconnected to network")

            # Check token balances
            wpls_balance = wpls.balanceOf(degenbot)
            dai_balance = dai.balanceOf(degenbot)
            pls_balance = degenbot.balance()
            print(f"WPLS balance: {wpls_balance}, DAI balance: {dai_balance}, PLS balance: {pls_balance}")

            # Wrap PLS to WPLS if needed
            if wpls_balance < Decimal(1000) and pls_balance > 0:
                amount_to_wrap = min(pls_balance, Decimal(10000) - wpls_balance)
                wrap_pls(amount_to_wrap, wpls, degenbot)
                wpls_balance = wpls.balanceOf(degenbot)

            # Check for arbitrage opportunity
            opportunity = check_arbitrage_opportunity(pulsex_lp, nineinch_lp, wpls, dai, MIN_PROFIT_THRESHOLD)
            
            if opportunity:
                buy_pool, sell_pool, profit_percentage = opportunity
                print(f"Arbitrage opportunity found! Profit: {profit_percentage:.2%}")
                
                # Determine swap amount (you might want to implement a more sophisticated calculation)
                swap_amount = min(wpls_balance, Decimal(1000))  # Example: Use 1000 WPLS or full balance if less
                
                if not DRY_RUN:
                    # Execute buy on cheaper pool
                    buy_amount = execute_swap(buy_pool, wpls, dai, swap_amount, True, degenbot)
                    
                    # Execute sell on more expensive pool
                    sell_amount = execute_swap(sell_pool, dai, wpls, buy_amount, False, degenbot)
                    
                    print(f"Arbitrage executed: Bought {buy_amount} DAI, Sold for {sell_amount} WPLS")
                else:
                    print("Dry run: Arbitrage would have been executed")
            
            else:
                pulsex_price = get_price_from_pool(pulsex_lp, wpls.address, dai.address)
                nineinch_price = get_price_from_pool(nineinch_lp, wpls.address, dai.address)
                print(f"No arbitrage opportunity found")
                print(f"NINE INCH PRICE: {nineinch_price:.6f} WPLS    PULSEX PRICE: {pulsex_price:.6f}")

            time.sleep(LOOP_TIME)

        except Exception as e:
            print(f"An error occurred: {e}")
            time.sleep(LOOP_TIME)

# Only executes main loop if this file is called directly
if __name__ == "__main__":
    main()
