import backtrader as bt
from backtrader.indicators import *

class Solo_cash_pool(bt.Strategy):
    """
    独立资金池策略类，适用于每次交易只涉及一个品种的回测。
    """

    def __init__(self):
        """
        初始化独立资金池策略中的各类指标。
        """
        self.indicatordict = dict()  # 存储各类技术指标
        self.notify_flag = 0  # 控制是否打印订单状态

        # 初始化技术指标
        self.indicatordict['SMA5'] = MovingAverageSimple()  # 5日简单移动平均线
        self.indicatordict['EMA15'] = ExponentialMovingAverage()  # 15日指数移动平均线
        self.indicatordict['MA30'] = MovingAverage()  # 30日移动平均线
        self.indicatordict['MACD'] = MACDHisto()  # MACD指标的柱状图

    def next(self):
        """
        每个时间步执行独立资金池策略。
        """
        self.solo_cash()  # 执行独立资金池策略逻辑

    def notify_order(self, order):
        """
        通知订单状态，用于查看订单执行情况。
        """
        if self.notify_flag:
            # 查看订单情况
            if order.status in [order.Submitted, order.Accepted]:
                return  # 订单已提交或接受，等待执行
            if order.status in [order.Completed]:
                if order.isbuy():
                    # 买入订单完成
                    print(f"已买入:{self.data._name}")
                    print(f"数量: {order.executed.size}")
                    print(f"买入价格: {order.executed.price}")
                    print(f"价值: {order.executed.value}")
                elif order.issell():
                    # 卖出订单完成
                    print(f"已卖出:{self.data._name}")
                    print(f"数量: {order.executed.size}")
                    print(f"卖出价格: {order.executed.price}")
                    print(f"价值: {order.executed.value}")
            elif order.status is order.Canceled:
                print('订单取消')
            elif order.status is order.Rejected:
                print('金额不足，拒绝交易')
            elif order.status is order.Margin:
                print('保证金不足')
        else:
            pass  # 不打印订单状态

    def solo_cash(self):
        """
        根据独立资金池策略的条件进行买入或卖出操作。
        """
        size = self.calculate_quantity(self.datas[0])  # 计算交易数量
        self.buy_function(size=size)  # 执行买入操作
        self.sell_function()  # 执行卖出操作

    def buy_function(self, size):
        """
        执行买入操作，当满足买入条件时，调用Backtrader的买入函数。
        """
        close_over_sma = self.datas[0].close > self.indicatordict['SMA5'][0]  # 当前价格高于5日均线
        close_over_ema = self.datas[0].close > self.indicatordict['EMA15'][0]  # 当前价格高于15日指数均线
        sma_ema_diff = self.indicatordict['SMA5'][0] - self.indicatordict['EMA15'][0]  # 5日均线与15日均线的差值

        buy_cond = (close_over_sma or close_over_ema) and (sma_ema_diff > 0)  # 定义买入条件

        if buy_cond and self.broker.get_value() > 0:  # 检查是否满足买入条件且有足够资金
            buy_order = self.buy(size=size)  # 执行买入操作
            return buy_order
        else:
            pass  # 不满足买入条件，跳过

    def sell_function(self):
        """
        执行卖出操作，当满足卖出条件时，调用Backtrader的卖出函数。
        """
        sell_cond = self.datas[0].close < self.indicatordict['SMA5'][0]  # 当前价格低于5日均线

        if sell_cond and self.getposition():  # 检查是否满足卖出条件且持有仓位
            sell_order = self.close()  # 执行卖出操作
            return sell_order
        else:
            pass  # 不满足卖出条件，跳过

    def calculate_quantity(self, data) -> int:
        """
        根据策略的逻辑计算交易数量，返回一个整数表示交易数量。
        """
        total_value = self.broker.get_value()  # 获取当前总资金
        available_value = total_value * 0.05  # 可用资金为总资金的5%
        close_price = data.close[0]  # 当前收盘价
        quantity = int(available_value / close_price)  # 计算交易数量，取整数
        return quantity

    def print_position(self, line) -> None:
        """
        打印当前持仓信息。
        """
        pos = self.getposition(line)
        print(f"品种: {line._name} 的当前仓位: {pos.size} @price: {pos.price}")