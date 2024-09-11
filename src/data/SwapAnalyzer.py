import os
from decimal import Decimal
from dotenv import load_dotenv
from web3 import Web3
from config.constants import USDT_WBNB_PAIR_ID, ETH_WBNB_PAIR_ID, ETH_USDT_PAIR_ID, PAIR_API
from src.utils.SmsSender import SmsSender
from src.trades.PancakeSwapTrade import PancakeSwapTrade


class SwapAnalyzer:
    def __init__(self):
        """
        初始化 SwapAnalyzer 类，加载环境变量并创建 Web3 实例。
        """
        load_dotenv()
        infura_url = f"https://bsc-mainnet.infura.io/v3/{os.getenv('INFURA_API_KEY')}"
        self.web3 = Web3(Web3.HTTPProvider(infura_url))
        self.usdt_wbnb_contract = self.create_contract(USDT_WBNB_PAIR_ID)
        self.eth_wbnb_contract = self.create_contract(ETH_WBNB_PAIR_ID)
        self.eth_usdt_contract = self.create_contract(ETH_USDT_PAIR_ID)
        self.sms_sender = SmsSender(
            access_key_id=os.getenv('ALIBABA_CLOUD_ACCESS_KEY_ID'),
            access_key_secret=os.getenv('ALIBABA_CLOUD_ACCESS_KEY_SECRET')
        )
        self.trade = PancakeSwapTrade(
            web3=self.web3,
            wallet_address=os.getenv('WALLET_ADDRESS'),
            private_key=os.getenv('WALLET_PRIVATE_KEY')
        )
        self.usdt_amount_in = 9.9

    def create_contract(self, pair_id: str):
        """
        创建合约对象
        :param pair_id: 交易对的合约地址
        :return: 合约对象
        """
        return self.web3.eth.contract(address=Web3.to_checksum_address(pair_id), abi=PAIR_API)

    @staticmethod
    def get_pool_info(contract):
        """
        获取池信息（价格、流动性及相关储备量）
        :param contract: 合约对象
        :return: 包含池信息的字典
        """
        slot0 = contract.functions.slot0().call()
        sqrt_price_x96 = slot0[0]  # sqrtPriceX96 from slot0
        liquidity = contract.functions.liquidity().call()
        token0 = contract.functions.token0().call()
        token1 = contract.functions.token1().call()

        # 计算价格
        price = (sqrt_price_x96 ** 2) / (2 ** 192)

        # 获取 tick 间隔中的流动性
        tick_spacing = contract.functions.tickSpacing().call()

        return {
            "price": price,
            "liquidity": liquidity,
            "token0": token0,
            "token1": token1,
            "tick_spacing": tick_spacing,
            "sqrt_price_x96": sqrt_price_x96
        }

    @staticmethod
    def calculate_amount_out(pool_data, amount_in, is_token0_in):
        """
        计算兑换结果
        :param pool_data: 池信息数据
        :param amount_in: 输入金额
        :param is_token0_in: 输入是否为 token0
        :return: 兑换得到的代币数量
        """
        sqrt_price = Decimal(pool_data["sqrt_price_x96"]) / Decimal(2 ** 96)

        if is_token0_in:
            reserve_in = Decimal(pool_data["liquidity"]) / sqrt_price
            reserve_out = Decimal(pool_data["liquidity"]) * sqrt_price
        else:
            reserve_in = Decimal(pool_data["liquidity"]) * sqrt_price
            reserve_out = Decimal(pool_data["liquidity"]) / sqrt_price

        fee_tier = Decimal('0.0005')  # 0.05% 的手续费
        amount_in_after = Decimal(amount_in) * (1 - fee_tier)

        return (amount_in_after * reserve_out) / (reserve_in + amount_in_after)

    def analyze_swaps(self):
        """
        分析三角交换，输出每个步骤的结果并检查是否亏损。
        """
        usdt_wbnb_data = self.get_pool_info(self.usdt_wbnb_contract)
        eth_wbnb_data = self.get_pool_info(self.eth_wbnb_contract)
        eth_usdt_data = self.get_pool_info(self.eth_usdt_contract)

        print(f"USDT-WBNB 数据: {usdt_wbnb_data}")
        print(f"ETH-WBNB 数据: {eth_wbnb_data}")
        print(f"ETH-USDT 数据: {eth_usdt_data}")

        # 1. 计算 USDT -> WBNB
        wbnb_received = self.calculate_amount_out(usdt_wbnb_data, self.usdt_amount_in, True)
        print(f"{self.usdt_amount_in} USDT 交换得到 WBNB 数量: {wbnb_received} WBNB")

        # 2. 计算 WBNB -> ETH
        eth_received = self.calculate_amount_out(eth_wbnb_data, wbnb_received, False)
        print(f"{wbnb_received} 数量 WBNB 交换得到 ETH 数量: {eth_received} ETH")

        # 3. 计算 ETH -> USDT
        usdt_received = self.calculate_amount_out(eth_usdt_data, eth_received, True)
        print(f"{eth_received} 数量 ETH 交换得到 USDT 数量: {usdt_received} USDT")

        if usdt_received > self.usdt_amount_in:
            print(f"警告: 最终收到的 USDT ({usdt_received}) 大于初始输入的 USDT ({self.usdt_amount_in})！有可用套利机会")
            # 发送短信提醒
            self.sms_sender.send_sms(
                phone_number=os.getenv('SMS_PHONE'),
                sign_name='joey的短信提醒',
                template_code='SMS_472065257',
                template_param=f'{{"usdt_received":"{usdt_received}", "amount_in":"{self.usdt_amount_in}"}}'
            )

            # 执行套利交易
            self.execute_arbitrage()

    def execute_arbitrage(self):
        """
        执行三次交易以完成三角套利。
        """
        try:
            # 1. USDT -> WBNB
            tx_hash_1, wbnb_received = self.trade.execute_trade(
                contract=self.usdt_wbnb_contract,
                amount_in=Web3.to_wei(self.usdt_amount_in, 'mwei'),
                to_address=os.getenv('WALLET_ADDRESS'),
                is_token0_in=True
            )
            print(f"USDT -> WBNB 交易成功，交易哈希: {tx_hash_1}, 兑换WBNB: {wbnb_received}")

            # 2. WBNB -> ETH
            tx_hash_2, eth_received = self.trade.execute_trade(
                contract=self.eth_wbnb_contract,
                amount_in=Web3.to_wei(wbnb_received, 'ether'),
                to_address=os.getenv('WALLET_ADDRESS'),
                is_token0_in=False
            )
            print(f"WBNB -> ETH 交易成功，交易哈希: {tx_hash_2}, 兑换ETH: {eth_received}")

            # 3. ETH -> USDT
            tx_hash_3, usdt_received = self.trade.execute_trade(
                contract=self.eth_usdt_contract,
                amount_in=Web3.to_wei(eth_received, 'ether'),
                to_address=os.getenv('WALLET_ADDRESS'),
                is_token0_in=True
            )
            print(f"ETH -> USDT 交易成功，交易哈希: {tx_hash_3}, 兑换USDT: {usdt_received}")
        except Exception as e:
            print(f"套利交易失败: {str(e)}")


if __name__ == '__main__':
    analyzer = SwapAnalyzer()
    analyzer.analyze_swaps()
