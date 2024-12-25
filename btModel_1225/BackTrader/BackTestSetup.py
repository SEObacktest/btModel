from DataIO import DataIO
import time


class BackTestSetup:
    """
    回测设置控制类，用于统一设置回测引擎的参数，如初始资金、手续费、分析器等。
    """

    @staticmethod
    def set_cerebro(cerebro, opt_judge):
        """
        配置回测引擎的通用参数。

        :param cerebro: Backtrader的回测引擎实例
        :param opt_judge: 是否进行参数优化的标志，True表示优化模式，不添加分析器和绘图元素
        """
        public_cash = 100000000  # 设置初始资金为一亿
        #commission = 0.00025      # 设置交易手续费率
        commission=0
        cerebro.broker.setcash(public_cash)  # 设置初始资金
        cerebro.broker.setcommission(commission=commission)  # 设置交易手续费

        if not opt_judge:
            # 如果不是优化模式，添加分析器和绘图元素
            DataIO.add_analysers(cerebro=cerebro)       # 添加回测分析器
            DataIO.add_plotElements(cerebro=cerebro)    # 添加绘图元素
        print("数据加载中.....")
        time.sleep(2)  # 模拟数据加载时间
        if not opt_judge:
            print("回测进行中....")
            time.sleep(2)  # 模拟回测执行时间
  