// SPDX-License-Identifier: MIT
pragma solidity >=0.7.0 <0.9.0;

interface IUniswapV2Router02 {
    function swapExactTokensForTokens(
        uint amountIn,
        uint amountOutMin,
        address[] calldata path,
        address to,
        uint deadline
    ) external returns (uint[] memory amounts);

    function getAmountsIn(
        uint amountOut,
        address[] calldata path
    ) external view returns (uint[] memory amounts);
}

interface IUniswapV2Pair {
    function token0() external view returns (address);
    function token1() external view returns (address);
    function swap(uint amount0Out, uint amount1Out, address to, bytes calldata data) external;
}

interface IERC20 {
    function totalSupply() external view returns (uint256);
    function balanceOf(address account) external view returns (uint256);
    function transfer(address recipient, uint256 amount) external returns (bool);
    function allowance(address owner, address spender) external view returns (uint256);
    function approve(address spender, uint256 amount) external returns (bool);
    function transferFrom(address sender, address recipient, uint256 amount) external returns (bool);
}

contract thisswap {
    address public uniswapFactory;
    address public uniswapRouter;

    event Debug(string message, uint256 value);
    event DebugAddress(string message, address addr);

    constructor(address _uniswapFactory, address _uniswapRouter) {
        uniswapFactory = _uniswapFactory;
        uniswapRouter = _uniswapRouter;
    }

    function execute(
        address flashBorrowPoolAddress,
        address flashBorrowTokenAddress,
        uint256 flashBorrowTokenAmount,
        address[] calldata swapPath,
        address swapRouterAddress
    ) external {
        emit Debug("Started execute", flashBorrowTokenAmount);
        emit DebugAddress("FlashBorrowPoolAddress", flashBorrowPoolAddress);
        emit DebugAddress("FlashBorrowTokenAddress", flashBorrowTokenAddress);
        emit DebugAddress("SwapRouterAddress", swapRouterAddress);

        uint256 amount0 = 0;
        uint256 amount1 = 0;

        if (flashBorrowTokenAddress == IUniswapV2Pair(flashBorrowPoolAddress).token0()) {
            amount0 = flashBorrowTokenAmount;
        } else {
            amount1 = flashBorrowTokenAmount;
        }

        IUniswapV2Pair(flashBorrowPoolAddress).swap(
            amount0,
            amount1,
            address(this),
            bytes("flash")
        );

        emit Debug("End of execute", 0);
    }

    function uniswapV2Call(
        address _sender,
        uint256 _amount0,
        uint256 _amount1,
        bytes calldata _data
    ) external {
        emit Debug("Started uniswapV2Call", _amount0 > 0 ? _amount0 : _amount1);
        
        address token0 = IUniswapV2Pair(msg.sender).token0();
        address token1 = IUniswapV2Pair(msg.sender).token1();
        emit DebugAddress("Token0", token0);
        emit DebugAddress("Token1", token1);

        uint256 amountBorrow = _amount0 > 0 ? _amount0 : _amount1;
        address[] memory path = new address[](2);
        
        if (_amount0 > 0) {
            path[0] = token1;
            path[1] = token0;
        } else {
            path[0] = token0;
            path[1] = token1;
        }

        uint256 amountRepay = IUniswapV2Router02(uniswapRouter).getAmountsIn(
            amountBorrow,
            path
        )[0];

        uint256 amountReceivedAfterSwap = IUniswapV2Router02(uniswapRouter).swapExactTokensForTokens(
            amountBorrow,
            amountRepay,
            path,
            address(this),
            block.timestamp + 60
        )[path.length - 1];

        if (_amount0 > 0) {
            IERC20(token1).transfer(msg.sender, amountRepay);
            IERC20(token1).transfer(tx.origin, amountReceivedAfterSwap - amountRepay);
        } else {
            IERC20(token0).transfer(msg.sender, amountRepay);
            IERC20(token0).transfer(tx.origin, amountReceivedAfterSwap - amountRepay);
        }

        emit Debug("End of uniswapV2Call", amountReceivedAfterSwap);
    }
}