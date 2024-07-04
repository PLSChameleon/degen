# interfaces.py

class IERC20:
    def __init__(self, address, provider):
        self.address = address
        self.provider = provider
        self.contract = provider.eth.contract(address=address, abi=[
            {"constant": True, "inputs": [], "name": "balanceOf", "outputs": [{"name": "", "type": "uint256"}], "payable": False, "stateMutability": "view", "type": "function"},
            {"constant": True, "inputs": [], "name": "decimals", "outputs": [{"name": "", "type": "uint8"}], "payable": False, "stateMutability": "view", "type": "function"},
            {"constant": True, "inputs": [], "name": "name", "outputs": [{"name": "", "type": "string"}], "payable": False, "stateMutability": "view", "type": "function"},
            {"constant": True, "inputs": [], "name": "symbol", "outputs": [{"name": "", "type": "string"}], "payable": False, "stateMutability": "view", "type": "function"},
            {"constant": True, "inputs": [], "name": "totalSupply", "outputs": [{"name": "", "type": "uint256"}], "payable": False, "stateMutability": "view", "type": "function"},
            {"constant": False, "inputs": [{"name": "to", "type": "address"}, {"name": "value", "type": "uint256"}], "name": "transfer", "outputs": [{"name": "", "type": "bool"}], "payable": False, "stateMutability": "nonpayable", "type": "function"}
        ])

    def balanceOf(self, account):
        return self.contract.functions.balanceOf(account).call()

    def transfer(self, to, amount):
        tx = self.contract.functions.transfer(to, amount).buildTransaction({'from': self.address, 'gas': 2000000, 'gasPrice': self.provider.eth.gas_price})
        signed_tx = self.provider.eth.account.sign_transaction(tx, private_key=self.private_key)
        return self.provider.eth.send_raw_transaction(signed_tx.rawTransaction)

class IUniswapV2Pair:
    def __init__(self, address, provider):
        self.address = address
        self.provider = provider
        self.contract = provider.eth.contract(address=address, abi=[
            {"constant": True, "inputs": [], "name": "token0", "outputs": [{"name": "", "type": "address"}], "payable": False, "stateMutability": "view", "type": "function"},
            {"constant": True, "inputs": [], "name": "token1", "outputs": [{"name": "", "type": "address"}], "payable": False, "stateMutability": "view", "type": "function"},
            {"constant": False, "inputs": [{"name": "amount0Out", "type": "uint256"}, {"name": "amount1Out", "type": "uint256"}, {"name": "to", "type": "address"}, {"name": "data", "type": "bytes"}], "name": "swap", "outputs": [], "payable": False, "stateMutability": "nonpayable", "type": "function"}
        ])

    def token0(self):
        return self.contract.functions.token0().call()

    def token1(self):
        return self.contract.functions.token1().call()

    def swap(self, amount0Out, amount1Out, to, data):
        tx = self.contract.functions.swap(amount0Out, amount1Out, to, data).buildTransaction({'from': self.address, 'gas': 2000000, 'gasPrice': self.provider.eth.gas_price})
        signed_tx = self.provider.eth.account.sign_transaction(tx, private_key=self.private_key)
        return self.provider.eth.send_raw_transaction(signed_tx.rawTransaction)
