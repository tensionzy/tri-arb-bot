import os
import unittest
from web3 import Web3
from dotenv import load_dotenv
from src.trades.PancakeSwapTrade import PancakeSwapTrade
from config.constants import USDT_WBNB_PAIR_ID, PAIR_API


class TestPancakeSwapTrade(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        load_dotenv()
        # 设置 Web3 实例，连接到 BSC 测试链
        cls.web3 = Web3(Web3.HTTPProvider('https://data-seed-prebsc-1-s1.binance.org:8545'))

        # 测试钱包地址和私钥（确保该地址有足够的测试 BNB 和 USDT）
        cls.wallet_address = os.getenv('WALLET_ADDRESS')
        cls.private_key = os.getenv('WALLET_PRIVATE_KEY')

        # Router 合约地址和 ABI （替换为实际 PancakeSwap 测试网 Router 合约）
        cls.router_address = Web3.to_checksum_address(USDT_WBNB_PAIR_ID)  # PancakeSwap 测试网 Router 地址
        cls.router_abi = PAIR_API  # Router 的 ABI (确保你有正确的 Router ABI)

        # 加载 PancakeSwap Router 合约
        cls.router_contract = cls.web3.eth.contract(address=cls.router_address, abi=cls.router_abi)

        # 初始化 PancakeSwapTrade 实例
        cls.trade = PancakeSwapTrade(cls.web3, cls.wallet_address, cls.private_key)

    def test_execute_trade_usdt_to_wbnb(self):
        """
        测试 USDT 兑换 WBNB 的交易执行
        """
        # 准备交易参数
        usdt_amount_in = Web3.to_wei(100, 'mwei')  # 100 USDT, USDT 使用 mwei 单位

        # 目标地址为钱包地址本身
        to_address = self.wallet_address

        # 执行交易（测试 usdt -> wbnb）
        try:
            receipt = self.trade.execute_trade(
                contract=self.router_contract,
                amount_in=usdt_amount_in,
                to_address=to_address,
                is_token0_in=True  # 表示用 token0 (USDT) 兑换 token1 (WBNB)
            )

            # 检查交易是否成功
            self.assertIsNotNone(receipt, "交易失败，没有返回交易收据")
            print(f"交易成功，交易哈希: {receipt['transactionHash'].hex()}")

        except Exception as e:
            self.fail(f"交易执行失败: {str(e)}")

    @classmethod
    def tearDownClass(cls):
        pass  # 可以添加一些测试结束后的清理逻辑


if __name__ == '__main__':
    unittest.main()