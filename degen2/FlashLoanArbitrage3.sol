// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

interface IUniswapV2Pair {
    function swap(uint amount0Out, uint amount1Out, address to, bytes calldata data) external;
}

contract FlashSwap {
    address public owner;
    address public uniswapV2Factory;

    constructor(address _uniswapV2Factory) {
        owner = msg.sender;
        uniswapV2Factory = _uniswapV2Factory;
    }

    modifier onlyOwner() {
        require(msg.sender == owner, "Not the owner");
        _;
    }

    // Function to execute the flash swap
    function execute(
        address[] calldata pairs,
        uint[] calldata amounts0Out,
        uint[] calldata amounts1Out,
        address[] calldata tokens0,
        address[] calldata tokens1,
        bytes[] calldata data
    ) external onlyOwner {
        require(pairs.length == amounts0Out.length, "Length mismatch");
        require(pairs.length == amounts1Out.length, "Length mismatch");
        require(pairs.length == tokens0.length, "Length mismatch");
        require(pairs.length == tokens1.length, "Length mismatch");
        require(pairs.length == data.length, "Length mismatch");

        for (uint i = 0; i < pairs.length; i++) {
            IUniswapV2Pair(pairs[i]).swap(
                amounts0Out[i],
                amounts1Out[i],
                address(this),
                data[i]
            );
        }
    }

    // Fallback function to receive ETH from swap
    receive() external payable {}

    // Withdraw funds from the contract
    function withdraw(address token, uint amount) external onlyOwner {
        require(token != address(0), "Invalid token address");
        payable(owner).transfer(amount);
    }

    // Withdraw any tokens sent to the contract
    function withdrawTokens(address token, uint amount) external onlyOwner {
        require(token != address(0), "Invalid token address");
        require(IERC20(token).transfer(owner, amount), "Transfer failed");
    }
}
