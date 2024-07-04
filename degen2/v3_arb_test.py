import brownie
import degenbot as bot
import os
import time


brownie.network.connect("mainnet-fork")

arbs = []
arbs.append(
    bot.arbitrage.V3LpSwap.from_addresses(
        input_token_address="0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
        swap_pool_addresses=[
            ("0xbb2b8038a1640196fbe3e38816f3e67cba72d940", "V2"),
            ("0x4585FE77225b41b697C938B018E2Ac67Ac5a20c0", "V3"),
        ],
        max_input=10 * 10**18,
    )
)


arbs.append(
    bot.arbitrage.V3LpSwap.from_addresses(
        input_token_address="0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
        swap_pool_addresses=[
            ("0x4585FE77225b41b697C938B018E2Ac67Ac5a20c0", "V3"),
            ("0xbb2b8038a1640196fbe3e38816f3e67cba72d940", "V2"),
        ],
        max_input=10 * 10**18,
    )
)

arbs.append(
    bot.arbitrage.V3LpSwap.from_addresses(
        input_token_address="0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
        swap_pool_addresses=[
            ("0xbb2b8038a1640196fbe3e38816f3e67cba72d940", "V2"),
            ("0xCBCdF9626bC03E24f779434178A73a0B4bad62eD", "V3"),
        ],
        max_input=10 * 10**18,
    )
)


arbs.append(
    bot.arbitrage.V3LpSwap.from_addresses(
        input_token_address="0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
        swap_pool_addresses=[
            ("0xCBCdF9626bC03E24f779434178A73a0B4bad62eD", "V3"),
            ("0xbb2b8038a1640196fbe3e38816f3e67cba72d940", "V2"),
        ],
        max_input=10 * 10**18,
    )
)


arbs.append(
    bot.arbitrage.V3LpSwap.from_addresses(
        input_token_address="0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
        swap_pool_addresses=[
            ("0xCBCdF9626bC03E24f779434178A73a0B4bad62eD", "V3"),
            ("0x4585FE77225b41b697C938B018E2Ac67Ac5a20c0", "V3"),
        ],
        max_input=10 * 10**18,
    )
)


arbs.append(
    bot.arbitrage.V3LpSwap.from_addresses(
        input_token_address="0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
        swap_pool_addresses=[
            ("0x4585FE77225b41b697C938B018E2Ac67Ac5a20c0", "V3"),
            ("0xCBCdF9626bC03E24f779434178A73a0B4bad62eD", "V3"),
        ],
        max_input=10 * 10**18,
    )
)

while True:
    for arb in arbs:
        arb.auto_update()
        arb.calculate_arbitrage()
    time.sleep(5)