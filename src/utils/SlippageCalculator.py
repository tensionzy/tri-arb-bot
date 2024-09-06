import math


class SlippageCalculator:
    @staticmethod
    def calculate_sqrt_price_limit(current_price, slippage_tolerance_percent):
        """
        计算滑点容忍范围内的 sqrtPriceLimitX96 值。

        :param current_price: 当前价格（假设价格为 1 表示 token0/token1 的比例）
        :param slippage_tolerance_percent: 滑点容忍度（以百分比表示，如 1 表示 1%）
        :return: sqrtPriceLimitX96 值
        """
        # 计算滑点容忍范围内的价格上限
        price_upper_limit = current_price * (1 + (slippage_tolerance_percent / 100))

        # 计算价格上限的平方根
        sqrt_price_limit = math.sqrt(price_upper_limit)

        # 转换为 Q64.96 格式的整数值
        sqrt_price_limit_x96 = int(sqrt_price_limit * (2 ** 96))

        return sqrt_price_limit_x96

    @staticmethod
    def calculate_sqrt_price_limit_lower(current_price, slippage_tolerance_percent):
        """
        计算滑点容忍范围内的 sqrtPriceLimitX96 值的下限。

        :param current_price: 当前价格（假设价格为 1 表示 token0/token1 的比例）
        :param slippage_tolerance_percent: 滑点容忍度（以百分比表示，如 1 表示 1%）
        :return: sqrtPriceLimitX96 值
        """
        # 计算滑点容忍范围内的价格下限
        price_lower_limit = current_price * (1 - (slippage_tolerance_percent / 100))

        # 计算价格下限的平方根
        sqrt_price_limit = math.sqrt(price_lower_limit)

        # 转换为 Q64.96 格式的整数值
        sqrt_price_limit_x96 = int(sqrt_price_limit * (2 ** 96))

        return sqrt_price_limit_x96
