// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

interface IUniswapV2Pair {
    function swap(uint amount0Out, uint amount1Out, address to, bytes calldata data) external;
}

interface ERC20 {
    function transfer(address recipient, uint amount) external returns (bool);
}

contract FlashSwap {
    address public owner;

    constructor() {
        owner = msg.sender;
    }

    modifier onlyOwner() {
        require(msg.sender == owner, "Not the owner");
        _;
    }

    function execute(
        address[16] calldata pairs,
        uint[16] calldata amounts0Out,
        uint[16] calldata amounts1Out,
        address[16] calldata tokens0,
        address[16] calldata tokens1,
        bytes[16] calldata data
    ) external onlyOwner {
        for (uint i = 0; i < pairs.length; i++) {
            IUniswapV2Pair(pairs[i]).swap(
                amounts0Out[i],
                amounts1Out[i],
                address(this),
                data[i]
            );
        }
    }

    function withdraw() external onlyOwner {
        payable(owner).transfer(address(this).balance);
    }

    function withdrawTokens(address token, uint amount) external onlyOwner {
        require(token != address(0), "Invalid token address");
        ERC20(token).transfer(owner, amount);
    }
}
