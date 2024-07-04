from brownie import interface

# Replace with your pair contract address
pair_address = "0xYourPairContractAddress"
pair = interface.IUniswapV2Pair(pair_address)

token0 = pair.token0()
token1 = pair.token1()

print("Token0:", token0)
print("Token1:", token1)
