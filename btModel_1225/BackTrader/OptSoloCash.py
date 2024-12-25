import backtrader as bt
from backtrader.indicators import *

class OptSoloCash(bt.Strategy):
    """
    策略参数优化独立资金池策略类，适用于单个品种的回测，并支持参数优化。
    """

    params = dict(N1=10, N2=20)  # 定义策略参数N1和N2，用于指标的周期设定

    def __init__(self):
        """
        初始化策略，创建并初始化需要的技术指标，并根据传入的参数调整指标的周期。
        """
        self.indicatordict = dict()  # 存储各类技术指标
        self.notify_flag = 0  # 控制是否打印订单状态

        # 初始化技术指标，使用策略参数N1和N2作为周期
        self.indicatordict['SMA5'] = MovingAverageSimple(self.datas[0].close, period=self.p.N1)  # 简单移动平均线
        self.indicatordict['EMA15'] = ExponentialMovingAverage(self.datas[0].close, period=self.p.N2)  # 指数移动平均线

    def next(self):
        """
        每个时间步执行策略逻辑，包括买入和卖出操作。
        """
        self.solo_cash()  # 执行独立资金池策略逻辑

    def notify_order(self, order):
        """
        通知订单状态，用于查看订单的执行情况。
        """
        if self.notify_flag:
            # 查看订单状态
            if order.status in [order.Submitted, order.Accepted]:
                return  # 订单已提交或被接受，等待执行
            if order.status in [order.Completed]:
                if order.isbuy():
                    # 买入订单完成
                    print(f"已买入: {self.data._name}")
                    print(f"数量: {order.executed.size}")
                    print(f"买入价格: {order.executed.price}")
                    print(f"价值: {order.executed.value}")
                elif order.issell():
                    # 卖出订单完成
                    print(f"已卖出: {self.data._name}")
                    print(f"数量: {order.executed.size}")
                    print(f"卖出价格: {order.executed.price}")
                    print(f"价值: {order.executed.value}")
            elif order.status == order.Canceled:
                print('订单取消')
            elif order.status == order.Rejected:
                print('金额不足，拒绝交易')
            elif order.status == order.Margin:
                print('保证金不足')
        else:
            pass  # 不打印订单状态

    def solo_cash(self):
        """
        根据策略的条件执行买入和卖出操作。
        """
        size = self.calculate_quantity(self.datas[0])  # 计算交易数量
        self.buy_function(size=size)  # 执行买入操作
        self.sell_function()  # 执行卖出操作

    def buy_function(self, size):
        """
        执行买入操作，当满足买入条件时，调用Backtrader的买入函数。
        """
        # 获取当前的收盘价和指标值
        current_close = self.datas[0].close[0]
        sma_value = self.indicatordict['SMA5'][0]
        ema_value = self.indicatordict['EMA15'][0]

        # 定义买入条件
        close_over_sma = current_close > sma_value  # 当前价格高于SMA
        close_over_ema = current_close > ema_value  # 当前价格高于EMA
        sma_ema_diff = sma_value - ema_value  # SMA与EMA的差值

        buy_cond = close_over_sma and close_over_ema and sma_ema_diff > 0  # 满足所有条件

        if buy_cond and self.broker.get_cash() >= current_close * size:
            # 满足买入条件且有足够资金，执行买入
            buy_order = self.buy(size=size)
            return buy_order
        else:
            pass  # 不满足买入条件或资金不足，跳过

    def sell_function(self):
        """
        执行卖出操作，当满足卖出条件时，调用Backtrader的卖出函数。
        """
        # 获取当前的收盘价和SMA值
        current_close = self.datas[0].close[0]
        sma_value = self.indicatordict['SMA5'][0]

        # 定义卖出条件
        sell_cond = current_close < sma_value  # 当前价格低于SMA

        if sell_cond and self.getposition().size > 0:
            # 满足卖出条件且持有仓位，执行卖出
            sell_order = self.close()
            return sell_order
        else:
            pass  # 不满足卖出条件或无持仓，跳过

    def calculate_quantity(self, data) -> int:
        """
        根据策略的逻辑计算交易数量，返回一个整数表示交易数量。
        """
        total_value = self.broker.get_value()  # 获取当前的总资产
        available_value = total_value * 0.05  # 可用资金为总资金的5%
        close_price = data.close[0]  # 当前品种的收盘价
        quantity = int(available_value / close_price)  # 计算交易数量，取整数

        return quantity

    def print_position(self, line) -> None:
        """
        打印当前持仓信息。
        """
        pos = self.getposition(line)
        print(f"品种: {line._name} 的当前仓位: {pos.size} @价格: {pos.price}")
