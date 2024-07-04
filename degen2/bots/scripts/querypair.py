from web3 import Web3

# Connect to your node
w3 = Web3(Web3.HTTPProvider("https://rpc.pulsechain.com/"))

# ABI of the Uniswap V2 pair contract
pair_abi = '''
[
    {
        "constant": true,
        "inputs": [],
        "name": "token0",
        "outputs": [
            {
                "name": "",
                "type": "address"
            }
        ],
        "payable": false,
        "stateMutability": "view",
        "type": "function"
    },
    {
        "constant": true,
        "inputs": [],
        "name": "token1",
        "outputs": [
            {
                "name": "",
                "type": "address"
            }
        ],
        "payable": false,
        "stateMutability": "view",
        "type": "function"
    }
]
'''

# Replace with your pair contract address
pair_address = "0xF892d93199B4DE0aB1CDf35799Ccf9D5A425581B"
pair_contract = w3.eth.contract(address=pair_address, abi=pair_abi)

token0 = pair_contract.functions.token0().call()
token1 = pair_contract.functions.token1().call()

print("Token0:", token0)
print("Token1:", token1)
