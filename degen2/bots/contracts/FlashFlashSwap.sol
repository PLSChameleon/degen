// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

interface IERC20 {
    function transfer(address recipient, uint256 amount) external returns (bool);
    function balanceOf(address account) external view returns (uint256);
    function approve(address spender, uint256 amount) external returns (bool);
    function allowance(address owner, address spender) external view returns (uint256);
}

interface IUniswapV2Pair {
    function token0() external view returns (address);
    function token1() external view returns (address);
    function swap(
        uint256 amount0Out,
        uint256 amount1Out,
        address to,
        bytes calldata data
    ) external;
}

interface IUniswapV2Router {
    function swapExactTokensForTokens(
        uint256 amountIn,
        uint256 amountOutMin,
        address[] calldata path,
        address to,
        uint256 deadline
    ) external returns (uint256[] memory amounts);

    function getAmountsIn(
        uint256 amountOut,
        address[] calldata path
    ) external view returns (uint256[] memory amounts);
}

interface IUniswapV2Callee {
    function uniswapV2Call(
        address sender,
        uint256 amount0,
        uint256 amount1,
        bytes calldata data
    ) external;
}

contract FlashFlashSwap is IUniswapV2Callee {
    uint256 public constant DEADLINE = 60;  // 60 seconds expiration for router swap

    address public uniswapV2FactoryAddress;
    address public uniswapV2RouterAddress;

    address public flashBorrowPoolAddress;
    IUniswapV2Router public swapRouter;
    address[] public swapPath;

    constructor(
        address _uniswapV2FactoryAddress,
        address _uniswapV2RouterAddress
    ) {
        uniswapV2FactoryAddress = _uniswapV2FactoryAddress;
        uniswapV2RouterAddress = _uniswapV2RouterAddress;
    }

    function execute(
        address _flashBorrowPoolAddress,
        address _flashBorrowTokenAddress,
        uint256 _flashBorrowTokenAmount,
        address[] calldata _swapPath,
        address _swapRouterAddress
    ) external {

        flashBorrowPoolAddress = _flashBorrowPoolAddress;
        swapPath = _swapPath;
        swapRouter = IUniswapV2Router(_swapRouterAddress);

        uint256 amount0 = 0;
        uint256 amount1 = 0;

        // Set "unlimited" approval whenever this contract interacts with the token
        uint256 approval = IERC20(_flashBorrowTokenAddress).allowance(address(this), _swapRouterAddress);
        if (approval < _flashBorrowTokenAmount) {
            IERC20(_flashBorrowTokenAddress).approve(_swapRouterAddress, type(uint256).max);
        }

        if (_flashBorrowTokenAddress == IUniswapV2Pair(flashBorrowPoolAddress).token0()) {
            amount0 = _flashBorrowTokenAmount;
        } else {
            amount1 = _flashBorrowTokenAmount;
        }

        IUniswapV2Pair(flashBorrowPoolAddress).swap(
            amount0,
            amount1,
            address(this),
            abi.encode("flash")
        );
    }

    function uniswapV2Call(
        address _sender,
        uint256 _amount0,
        uint256 _amount1,
        bytes calldata _data
    ) external override {

        require(msg.sender == flashBorrowPoolAddress, "!LP");

        address token0 = IUniswapV2Pair(msg.sender).token0();
        address token1 = IUniswapV2Pair(msg.sender).token1();

        uint256 amountBorrow;
        address[] memory path = new address[](2);

        if (_amount0 > 0) {
            amountBorrow = _amount0;
            path[0] = token1;
            path[1] = token0;
        } else {
            amountBorrow = _amount1;
            path[0] = token0;
            path[1] = token1;
        }

        uint256 amountRepay = swapRouter.getAmountsIn(amountBorrow, path)[0];

        uint256[] memory amounts = swapRouter.swapExactTokensForTokens(
            amountBorrow,
            amountRepay,
            swapPath,
            address(this),
            block.timestamp + DEADLINE
        );

        uint256 amountReceivedAfterSwap = amounts[amounts.length - 1];

        if (_amount0 > 0) {
            IERC20(token1).transfer(msg.sender, amountRepay);
            IERC20(token1).transfer(tx.origin, amountReceivedAfterSwap - amountRepay);
        } else {
            IERC20(token0).transfer(msg.sender, amountRepay);
            IERC20(token0).transfer(tx.origin, amountReceivedAfterSwap - amountRepay);
        }
    }
}
