import sys
import os
import time
from decimal import Decimal, getcontext
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

DECIMALS = 10**18
MIN_PROFIT_THRESHOLD = Decimal('0.005')  # 0.5% minimum profit threshold
PLS_SWAP_AMOUNT = Decimal('1000') * DECIMALS
DAI_SWAP_AMOUNT = Decimal('15') * DECIMALS
INITIAL_DAI_AMOUNT = Decimal('100') * DECIMALS  # Initial amount of DAI to acquire

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

def check_arbitrage_opportunity(pool1, pool2, wpls, dai):
    price1 = get_price_from_pool(pool1, wpls.address, dai.address)
    price2 = get_price_from_pool(pool2, wpls.address, dai.address)
    
    if price1 < price2:
        buy_pool, sell_pool = pool1, pool2
        profit_percentage = (price2 - price1) / price1
    else:
        buy_pool, sell_pool = pool2, pool1
        profit_percentage = (price1 - price2) / price2
    
    if profit_percentage > MIN_PROFIT_THRESHOLD:
        return (buy_pool, sell_pool, profit_percentage)
    
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
    router = Contract.from_abi("Router", address=PULSEX_ROUTER_CONTRACT_ADDRESS, abi=abis["v2_router"], owner=degenbot)
    
    amount_in_int = int(amount_in)
    
    if is_exact_input:
        tx = router.swapExactTokensForTokens(
            amount_in_int,
            0,  # Accept any amount out
            [token_in.address, token_out.address],
            account.address,
            int(time.time()) + 60 * 10,
            {'from': account, 'gas_limit': 2000000}
        )
    else:
        tx = router.swapTokensForExactTokens(
            amount_in_int,
            2**256 - 1,  # Unlimited input
            [token_in.address, token_out.address],
            account.address,
            int(time.time()) + 60 * 10,
            {'from': account, 'gas_limit': 2000000}
        )
    
    tx.wait(1)
    return Decimal(tx.return_value[1]) / DECIMALS  # Return the amount out

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

    if not check_and_approve_tokens([dai, wpls], [pulsex_router, nineinch_router], degenbot):
        print("Failed to approve tokens. Exiting.")
        return

     # Amount to wrap
    pls_amount = 1000
    
    # Check initial DAI balance
    dai_balance = dai.balanceOf(degenbot)
    if dai_balance < 100:
        print("Initial DAI balance is below 100. Acquiring 100 DAI...")
        
        # Approve WPLS for the router
        approve_tx = wpls.approve(router.address, pls_amount * 10**18, {'from': degenbot})
        approve_tx.wait(1)
        
        # Check allowance
        allowance = wpls.allowance(degenbot, router.address)
        if allowance < pls_amount * 10**18:
            raise Exception("Allowance for WPLS is not sufficient")
        
        # Wrap PLS to WPLS
        wrap_tx = wpls.deposit({'from': degenbot, 'value': pls_amount * 10**18})
        wrap_tx.wait(1)
        print(f"Wrapped {pls_amount} PLS to WPLS")
        
        # Execute swap
        try:
            acquired_dai = execute_swap(router, wpls, dai, pls_amount * 10**18, True, degenbot)
            print(f"Acquired {acquired_dai} DAI")
        except Exception as e:
            print(f"Swap failed: {e}")
            return
    else:
        print(f"Initial DAI balance is sufficient: {dai_balance}")

    while True:
        try:
            if not network.is_connected():
                print("Network connection lost! Reconnecting...")
                network.connect(BROWNIE_NETWORK)
                print("Reconnected to network")

            # Check token balances
            wpls_balance = Decimal(wpls.balanceOf(degenbot)) / DECIMALS
            dai_balance = Decimal(dai.balanceOf(degenbot)) / DECIMALS
            pls_balance = Decimal(degenbot.balance()) / DECIMALS
            print(f"WPLS balance: {wpls_balance:.6f}, DAI balance: {dai_balance:.6f}, PLS balance: {pls_balance:.6f}")

            # Wrap PLS to WPLS if needed
            if wpls_balance < Decimal('1000') and pls_balance > 0:
                amount_to_wrap = min(pls_balance * DECIMALS, (Decimal('10000') - wpls_balance) * DECIMALS)
                wrap_pls(int(amount_to_wrap), wpls, degenbot)
                wpls_balance = Decimal(wpls.balanceOf(degenbot)) / DECIMALS

            # Check for arbitrage opportunities
            opportunities = [
                check_arbitrage_opportunity(pulsex_lp, nineinch_lp, wpls, dai)
            ]

            best_opportunity = max(opportunities, key=lambda x: x[2] if x else 0)
            
            if best_opportunity:
                buy_pool, sell_pool, profit_percentage = best_opportunity
                print(f"Arbitrage opportunity found! Profit: {profit_percentage:.2%}")
                
                if not DRY_RUN:
                    # Execute buy on cheaper pool
                    buy_amount = execute_swap(buy_pool, dai, wpls, DAI_SWAP_AMOUNT, True, degenbot)
                    
                    # Execute sell on more expensive pool
                    sell_amount = execute_swap(sell_pool, wpls, dai, buy_amount * DECIMALS, False, degenbot)
                    
                    print(f"Arbitrage executed: Bought {buy_amount:.6f}, Sold for {sell_amount:.6f}")
                else:
                    print("Dry run: Arbitrage would have been executed")
            
            else:
                pulsex_price = get_price_from_pool(pulsex_lp, wpls.address, dai.address)
                nineinch_price = get_price_from_pool(nineinch_lp, wpls.address, dai.address)
                print(f"No arbitrage opportunity found")
                print(f"NINE INCH PRICE: {nineinch_price:.6f} DAI/WPLS    PULSEX PRICE: {pulsex_price:.6f} DAI/WPLS")

            time.sleep(LOOP_TIME)

        except Exception as e:
            print(f"An error occurred: {e}")
            time.sleep(LOOP_TIME)

# Only executes main loop if this file is called directly
if __name__ == "__main__":
    main()
