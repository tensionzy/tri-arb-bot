from web3 import Web3


class PancakeSwapTrade:
    def __init__(self, web3: Web3, wallet_address: str, private_key: str):
        """
        初始化交易类，设置Web3实例、钱包地址和私钥。
        """
        self.web3 = web3
        self.wallet_address = wallet_address
        self.private_key = private_key

    def execute_trade(self, contract, amount_in, to_address, is_token0_in):
        """
        执行代币交换交易。
        :param is_token0_in: 输入代币是否是token0
        :param contract: 流动池合约对象
        :param amount_in: 输入代币数量
        :param to_address: 接收交换代币的地址
        :return: 交易哈希, 交换代币数量
        """
        transaction = contract.functions.swap(
            recipient=Web3.to_checksum_address(to_address),  # 接收地址
            zeroForOne=is_token0_in,  # is_token0_in 表示用 token0 兑换 token1, False 表示用 token1 兑换 token0
            amountSpecified=amount_in,  # 指定输入或输出的代币数量（取决于你是想指定输入数量还是输出数量）
            sqrtPriceLimitX96=0,  # 设置价格滑点限制，可以根据需要调整
            data=b''  # 额外的数据，通常为空
        ).buildTransaction({
            'from': self.wallet_address,
            'gas': 250000,
            'gasPrice': self.web3.to_wei('5', 'gwei'),
            'nonce': self.web3.eth.get_transaction_count(Web3.to_checksum_address(self.wallet_address)),
        })

        signed_txn = self.web3.eth.account.signTransaction(transaction, private_key=self.private_key)
        tx_hash = self.web3.eth.send_raw_transaction(signed_txn.rawTransaction)

        # 等待交易收据, 获取交换后的代币数量
        receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash)
        # 检查交易状态
        if receipt['status'] == 1:
            # 交易成功，解析事件日志以获取兑换的token1数量
            for log in receipt['logs']:
                # 检查事件日志是否与指定合约地址匹配
                if log['address'].lower() == contract.address.lower():
                    # 获取事件数据
                    event = getattr(contract.events, 'Swap')
                    event_data = event().processLog(log)

                    amount_out = 'amount1Out' if is_token0_in else 'amount0Out'
                    return tx_hash, event_data['args'][amount_out]

            print("未找到匹配的 Swap 事件日志")
        else:
            # 交易失败
            print(f"交易失败，状态码：{receipt['status']}")
            return None
