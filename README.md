# 三角套利机器人设计

---

## 一、目的

使用100美元的初始资金，在低费用的Binance Smart Chain (BSC)上，选择流动性较好的交易对，通过频繁的小额套利积累收益。选择BSC上的主要去中心化交易所PancakeSwap进行交易。

## 二、模块设计

### 2.1 市场数据收集模块

* **交易对的选择**

  * 利用The Graph来查询PancakeSwap子图流动池信息。

  * 获取这些交易对的详细数据，交易对id、价格、交易额、流动性等。

  * 基于这些数据，选择TVL高、交易量大、流动性好、波动适中的交易对。

    ```json
    {
      pools(
        first: 40
        orderBy: totalValueLockedUSD
        orderDirection: desc
        where: {
         	liquidity_gt: "10000", 
          totalValueLockedUSD_gt: "10000", 
          volumeUSD_gt: "1000"}
      ) {
        id	#流动池的唯一标识符
        token0 {
          id	#代币的唯一标识符
          symbol	#代币的符号
        }
        token1 {
          id
          symbol
        }
        volumeUSD	#累计交易量
      	totalValueLockedUSD	#总锁定价值
        createdAtTimestamp
    		liquidity	#流动池当前流动性
        tick	#流动池的当前价格刻度
    		feeTier #费用
      }
    }
    ```

* **交易路径规划（例如：BUSD -> USDT -> BNB -> BUSD）**
  
  * 首先，我选择了一个常见的基础资产——**USDT**，因为它是稳定币，通常具有较大的交易量和流动性。
  
  * 接下来，我从返回的结果中寻找与**USDT**相关的交易对，并确认这些交易对是否满足以下条件：
  
    * **高 TVL**：表明该交易对中锁定的资产较多，流动性较好。
    * **大交易量**：表明该交易对市场活跃度高。
    * **低滑点**：流动性好的交易对通常滑点较低，适合套利。
  
  * 构建三角套利路径
  
    在找到合适的交易对后，我根据逻辑将它们链接起来，形成一个从**USDT**出发，经过其他资产，最终回到 USDT 的路径。具体步骤如下：
  
    1. **USDT -> WBNB**:
  
       **交易对**: `USDT-WBNB`
  
       **交易对 ID**: `0x36696169c63e42cd08ce11f5deebbcebae652050`
  
       **理由**: USDT 是一个常用的起始资产，而 WBNB 是 BSC 网络上的核心资产之一。这个交易对的 TVL 和交易量都很高，流动性好，适合作为路径的起点。
  
    2. **WBNB -> ETH**:
  
       **交易对**: `WBNB-ETH`
  
       **交易对 ID**: `0x4bba1018b967e59220b22ca03f68821a3276c9a6`
  
       **理由**: ETH 是另一个主流资产，并且在 BSC 网络上有较高的流动性。将 WBNB 转换为 ETH 可以保持路径的流动性和市场深度。
  
    3. **ETH -> USDT**:
  
       **交易对**: `ETH-USDT`
  
       **交易对 ID**: `0x7f51c8aaa6b0599abd16674e2b17fec7a9f674a1`
  
       **理由**: 最后一步是将 ETH 转换回 USDT，完成整个套利路径。这个交易对的 TVL 也4较高，且交易量适中，确保交易顺利完成。
  
  在确认了每一步的交易对和资产后，我确保路径中的每个交易对都有足够的流动性和市场活跃度，以支持多次交易而不会引起显著的价格滑点。通过循环交易，理论上可以利用市场中的价格差异获利。
  
* **价格数据实时获取**

  * 确定了交易对，通过Infura连接到BSC节点。
  * 通过调用智能合约方法，实时获取交易对的价格、流动性，从而计算出滑点等数据。
  
    ```python
    infura_url = f"https://bsc-mainnet.infura.io/v3/{os.getenv('INFURA_API_KEY')}"
    self.web3 = Web3(Web3.HTTPProvider(infura_url))
    self.usdt_wbnb_contract = self.create_contract(USDT_WBNB_PAIR_ID)
    self.eth_wbnb_contract = self.create_contract(ETH_WBNB_PAIR_ID)
    self.eth_usdt_contract = self.create_contract(ETH_USDT_PAIR_ID)
    ```
  * 利用这些实时价格数据，监控市场并等待合适的套利机会.一旦确定套利机会，立即执行三笔交易，完成套利流程。
  
    ```python
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
    ```

### 2.2 交易执行模块

* **自动化交易**：使用Web3与PancakeSwap智能合约交互，发送交易请求。

  ```python
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
          Web3.to_checksum_address(to_address),   # recipient: 接收地址
          is_token0_in,                           # zeroForOne: true 表示用 token0 兑换 token1
          amount_in,                              # amountSpecified: 指定输入代币数量
          0,                                      # sqrtPriceLimitX96: 设置滑点限制为 0，表示无滑点限制
          b''                                     # data: 额外数据（通常为空）
      ).build_transaction({
          'from': self.wallet_address,
          'gas': 250000,
          'gasPrice': self.web3.to_wei('5', 'gwei'),
          'nonce': self.web3.eth.get_transaction_count(Web3.to_checksum_address(self.wallet_address)),
      })
      # 签署交易
      signed_txn = self.web3.eth.account.sign_transaction(transaction, private_key=self.private_key)
      # 发送交易
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
  ```
* **交易监控**：监控交易执行情况，处理交易失败或网络延迟等问题。

  todo
* **收益结算**：计算每次套利后的净收益，并将结果存储到数据库中。

  todo
