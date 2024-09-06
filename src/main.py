import time
from src.data.SwapAnalyzer import SwapAnalyzer


def main():
    analyzer = SwapAnalyzer()
    while True:
        try:
            analyzer.analyze_swaps()
        except Exception as e:
            print(f"发生错误: {e}")

        # 设置循环间隔时间（例如每 60 秒执行一次）
        time.sleep(60)


if __name__ == "__main__":
    main()
