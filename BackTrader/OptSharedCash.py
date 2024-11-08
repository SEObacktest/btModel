import backtrader as bt
from backtrader.indicators import *

class OptSharedCash(bt.Strategy):
    """
    策略参数优化共享资金池策略类，使用参数优化技术对共享资金池策略进行调整。
    """
    params = dict(N1=10, N2=20)  # 定义策略参数，可用于优化

    def __init__(self):
        """
        初始化策略，创建并初始化需要的指标，并根据传入的参数调整指标的周期。
        """
        # 创建指标字典
        self.sma5 = dict()  # 简单移动平均线，周期为N1
        self.ema15 = dict()  # 指数移动平均线，周期为N2
        self.ma30 = dict()  # 移动平均线，默认周期
        self.bolling_top = dict()  # 布林带上轨
        self.bolling_bot = dict()  # 布林带下轨
        self.notify_flag = 0  # 控制是否打印订单通知
        self.out_money=dict()
        # 遍历所有数据集，为每个数据集计算对应的指标
        for index, data in enumerate(self.datas):
            c = data.close
            # 使用传入的参数N1和N2来调整指标的周期
            self.sma5[data] = MovingAverageSimple(c, period=int(self.p.N1))  # 简单移动平均线，周期为N1
            self.ema15[data] = ExponentialMovingAverage(c, period=int(self.p.N2))  # 指数移动平均线，周期为N2
            self.ma30[data] = MovingAverage(c)  # 默认周期的移动平均线
            self.out_money[data]=0
            # 初始化布林带指标
            self.bolling_top[data] = bt.indicators.BollingerBands(c, period=20).top  # 布林带上轨
            self.bolling_bot[data] = bt.indicators.BollingerBands(c, period=20).bot  # 布林带下轨

    def next(self):
        """
        每个时间步执行策略操作。
        """
        self.shared_cash()  # 执行共享资金池策略

    def notify_order(self, order):
        """
        订单状态通知，用于监控订单的执行状态。
        """
        if self.notify_flag:
            # 查看订单情况
            if order.status in [order.Submitted, order.Accepted]:
                return  # 订单已提交或被接受，等待执行
            if order.status in [order.Completed]:
                if order.isbuy():
                    # 买入订单已完成
                    print(f"已买入:{self.data._name}")
                    print(f"数量: {order.executed.size}")
                    print(f"买入价格: {order.executed.price}")
                    print(f"价值: {order.executed.value}")
                elif order.issell():
                    # 卖出订单已完成
                    print(f"已卖出:{self.data._name}")
                    print(f"数量: {order.executed.size}")
                    print(f"卖出价格: {order.executed.price}")
                    print(f"价值: {order.executed.value}")
            elif order.status == order.Canceled:
                print('订单取消')
            elif order.status == order.Rejected:
                print('金额不足拒绝交易')
            elif order.status == order.Margin:
                print('保证金不足')
        else:
            pass  # 不打印订单通知

    def shared_cash(self):
        """
        共享资金池策略的核心逻辑，遍历所有数据集，计算交易数量，执行买入和卖出操作。
        """
        for data in self.datas:
            size = self.calculate_quantity(data)  # 计算交易数量
            self.buy_function(line=data, size=size)  # 执行买入操作
            self.sell_function(line=data, size=size)  # 执行卖出操作

    def buy_function(self, line, size):
        """
        根据策略条件执行买入操作。
        """
        # 定义买入条件
        close_over_sma = line.close > self.sma5[line][0]  # 当前价格高于简单移动平均线
        close_over_ema = line.close > self.ema15[line][0]  # 当前价格高于指数移动平均线
        sma_ema_diff = self.sma5[line][0] - self.ema15[line][0]  # 简单均线与指数均线的差值
        # 满足以下条件之一即可买入
        buy_cond = (close_over_sma and close_over_ema and sma_ema_diff > 0) or \
                   (line.close == self.bolling_top[line][0])  # 价格等于布林带上轨

        if buy_cond and self.broker.get_value() > 0:
            # 满足买入条件且有足够资金，执行买入
            buy_order = self.buy(data=line, size=size)
            return buy_order
        else:
            pass  # 不满足买入条件，跳过

    def sell_function(self, line, size):
        """
        根据策略条件执行卖出操作。
        """
        # 定义卖出条件
        sell_cond = self.indicatordict[line][0] < self.indicatordict[line][-1] < self.indicatordict[line][-2]
        # sell_cond = line.close < self.sma5[line]  # 另一种卖出条件（注释掉的备选方案）

        if sell_cond and self.getposition(line):
            # 满足卖出条件且持有仓位，执行卖出
            sell_order = self.close(data=line, size=size)
            return sell_order
        else:
            pass  # 不满足卖出条件，跳过

    def calculate_quantity(self, line) -> int:
        """
        根据可用资金和当前价格计算交易数量。
        返回一个整数表示交易数量。
        """
        total_value = self.broker.get_value()  # 获取当前的总资金
        available_value = total_value * 0.05  # 可用资金为总资金的5%
        close_price = line.close[0]  # 当前收盘价
        quantity = int(available_value / close_price)  # 计算交易数量，取整数

        return quantity

    def print_position(self, line) -> None:
        """
        打印当前持仓信息。
        """
        pos = self.getposition(line)
        print(f"品种: {line._name} 的当前仓位: {pos.size} @price: {pos.price}")