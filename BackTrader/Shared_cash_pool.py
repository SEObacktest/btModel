import backtrader as bt
from backtrader.indicators import *


class Shared_cash_pool(bt.Strategy):
    """
    共享资金池策略类，主要用于管理多个品种的买卖决策，策略基于不同的技术指标。
    """

    def __init__(self):
        """
        初始化共享资金池策略中的指标，确保每个品种的技术指标独立计算。
        """
        self.sma5 = dict()  # 5日简单移动平均
        self.ema15 = dict()  # 15日指数加权移动平均
        self.bolling_top = dict()  # 布林带上轨
        self.bolling_bot = dict()  # 布林带下轨
        self.notify_flag = 0  # 控制是否打印订单状态
        for index, data in enumerate(self.datas):
            c = data.close
            self.sma5[data] = MovingAverageSimple(c)  # 初始化5日简单移动均线
            self.ema15[data] = ExponentialMovingAverage(c)  # 初始化15日指数加权移动均线
            self.bolling_top[data] = bt.indicators.BollingerBands(c, period=20).top  # 初始化布林带上轨
            self.bolling_bot[data] = bt.indicators.BollingerBands(c, period=20).bot  # 初始化布林带下轨

    def next(self):
        """
        每个时间步执行共享资金池策略。
        """
        self.shared_cash()  # 执行共享资金池策略

    def notify_order(self, order):
        """
        通知订单状态，用于查看订单执行情况。
        """
        if self.notify_flag:
            if order.status in [order.Submitted, order.Accepted]:  # 订单被接受，等待执行
                return
            if order.status in [order.Completed]:
                if order.isbuy():  # 买入订单完成
                    print(f"已买入:{self.data._name}")
                    print(f"数量: {order.executed.size}")
                    print(f"买入价格: {order.executed.price}")
                    print(f"价值: {order.executed.value}")
                elif order.issell():  # 卖出订单完成
                    print(f"已卖出:{self.data._name}")
                    print(f"数量: {order.executed.size}")
                    print(f"卖出价格: {order.executed.price}")
                    print(f"价值: {order.executed.value}")
            elif order.status is order.Canceled:
                print('订单取消')
            elif order.status is order.Rejected:
                print('金额不足拒绝交易')
            elif order.status is order.Margin:
                print('保证金不足')
        else:
            pass

    def shared_cash(self):
        """
        根据共享资金池策略的条件进行每个品种的买入或卖出。
        """
        for data in self.datas:
            size = self.calculate_quantity(data)  # 计算交易数量

            self.buy_function(line=data, size=size)  # 执行买入操作
            self.sell_function(line=data, size=size)  # 执行卖出操作

    def buy_function(self, line, size):
        """
        执行买入操作，当满足买入条件时，调用Backtrader的买入函数。
        """
        close_over_sma = line.close > self.sma5[line][0]  # 当前价格高于5日均线
        close_over_ema = line.close > self.ema15[line][0]  # 当前价格高于15日指数均线
        sma_ema_diff = self.sma5[line][0] - self.ema15[line][0]  # 计算5日均线与15日均线的差值
        buy_cond = (close_over_sma and close_over_ema and sma_ema_diff > 0) or line.close == self.bolling_top[line][0]  # 满足买入条件

        if buy_cond and self.broker.get_value() > 0:  # 确保资金充足
            buy_order = self.buy(data=line, size=size)  # 执行买入
            return buy_order
        else:
            pass

    def sell_function(self, line, size):
        """
        执行卖出操作，当满足卖出条件时，调用Backtrader的卖出函数。
        """
        sell_cond = line.close < self.sma5[line]  # 当前价格低于5日均线

        if sell_cond and self.getposition(line):  # 当前持有仓位时执行卖出
            sell_order = self.close(data=line, size=size)  # 执行卖出
            return sell_order
        else:
            pass

    def calculate_quantity(self, line) -> int:
        """
        根据可用资金计算每次交易的数量。
        """
        total_value = self.broker.get_value()  # 获取总资金
        available_value = total_value * 0.05  # 可用资金为总资金的5%
        close_price = line.close[0]  # 当前价格
        quantity = int(available_value / close_price)  # 计算购买数量
        return quantity

    def print_position(self, line) -> None:
        """
        打印当前持仓信息。
        """
        pos = self.getposition(line)
        print(f"品种: {line._name} 的当前仓位: {pos.size} @price: {pos.price}")
