import backtrader as bt
from backtrader.indicators import *
from optunity.solvers.util import score

from tools import Log
import pandas as pd

class Shared_Cash_Peak_Valley(bt.Strategy):
    params = (
        ('period', 20),
    )
    def __init__(self):
        # 初始化时为每个数据流（即每只股票）创建指标
        self.highest = {}
        self.lowest = {}
        self.middle = {}
        self.score = {}

        for data in self.datas:
            # 计算20天内的最高价和最低价
            self.highest[data] = bt.indicators.Highest(self.data.high, period=self.params.period)
            self.lowest[data] = bt.indicators.Lowest(self.data.low, period=self.params.period)

            # 计算中间值
            self.middle[data] = (self.highest[data] + self.lowest[data]) / 2

            # 计算分数
            # self.percent_change[data] = bt.indicators.PercentChange(self.data.close, period=1)
            # 价格等于中间值时，分数为0
            # 当价格高于中间值时，分数为正
            # 当价格低于中间值时，分数为负
            self.score[data] = (self.data.close - self.middle[data]) /  (self.highest[data] - self.lowest[data]) * 100

    def next(self):
        self.peak_valley()#执行策略

    def peak_valley(self):#具体的策略
        scores = []
        for data in self.datas:#满足一个指标就加一分
            score = self.score[data][0]
            scores.append((data, score))
            # 按分数排序
            scores.sort(key=lambda x: x[1], reverse=True)
            # 处理买入和卖出逻辑
            self.handle_trades(scores)

    def handle_trades(self, scores):  # 买卖条件需具体定义
        # # 买入分数最高的且没有持仓的股票
        # for data, score in scores:
        #     if not self.getposition(data).size and score > 0:
        #         self.buy(data=data)
        #         break  # 只买入一只股票
        #
        # # 卖出分数最低的且有持仓的股票
        # for data, score in reversed(scores):
        #     if self.getposition(data).size and score < 0:
        #         self.sell(data=data)
        #         break  # 只卖出一只股票

            bought = False
            sold = False
            for data, score in scores:
                if not self.getposition(data).size and score > 0 and not bought:
                    self.buy(data=data)
                    bought = True
                    break  # 只买入一只股票

            for data, score in reversed(scores):
                if self.getposition(data).size and score < 0 and not sold:
                    self.sell(data=data)
                    sold = True
                    break  # 只卖出一只股票

    def notify_order(self, order):
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(
                    f'BUY EXECUTED, Price: {order.executed.price:.2f}, Cost: {order.executed.value:.2f}, Comm: {order.executed.comm:.2f}')
            else:
                self.log(
                    f'SELL EXECUTED, Price: {order.executed.price:.2f}, Cost: {order.executed.value:.2f}, Comm: {order.executed.comm:.2f}')
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')

    def log(self, txt, dt=None, data=None):
        dt = dt or self.datas[0].datetime.date(0)
        data_name = getattr(data, 'name', 'Unknown')
        print(f'{dt.isoformat()}, {data_name}: {txt}')

