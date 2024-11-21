import tushare as ts
import backtrader as bt
import pandas as pd
import matplotlib.pyplot as plt
import sys
sys.path.append("..")
from BackTrader.tools import *

class Peak_Valley(bt.Strategy):
    params = (
        ('period', 20),
        ('hand', 100)
    )
    def __init__(self):
        # 计算20天内的最高价和最低价
        self.highest = bt.indicators.Highest(self.data.high, period=self.params.period)
        self.lowest = bt.indicators.Lowest(self.data.low, period=self.params.period)

        # 计算中间值
        self.middle = (self.highest + self.lowest) / 2

        # 计算分数
        # 价格等于中间值时，分数为0
        # 当价格高于中间值时，分数为正
        # 当价格低于中间值时，分数为负
        self.percent_change = bt.indicators.PercentChange(self.data.close, period=1)
        self.score = self.percent_change * 100

    def next(self):
        # 打印每天的价格和分数
        print(f'Date: {self.data.datetime.date(0)}, Close: {self.data.close[0]:.2f}, Score: {self.score[0]:.2f}')
        size = self.broker.getposition(self.data).size
        # 生成买卖信号
        if self.score[0] > 0 and size == 0 and self.broker.getcash() > 0:
            # 分数高于买入阈值且没有持仓时，买入
            self.buy()
            log_func.Log.log(self, f'BUY CREATE, {self.data._name}, Size: {size}, Price: {line.close[0]:.2f}')
        elif self.score[0] < 0 and size > 0 :
            # 分数低于卖出阈值且有持仓时，卖出
            self.sell()
            print(f'Sell signal at {self.data.datetime.date(0)} with score {self.score[0]:.2f}')


def get_tushare_data(stock_code, start_date, end_date):
    # 设置 Tushare token
    pro = data_get.DataGet.login_ts()

    # 获取数据
    df = pro.daily(ts_code=stock_code, start_date=start_date, end_date=end_date)

    # 转换日期格式
    df['trade_date'] = pd.to_datetime(df['trade_date'])
    df.set_index('trade_date', inplace=True)

    # 重命名列以符合 backtrader 的要求
    df = df[['open', 'high', 'low', 'close', 'vol']]
    df.rename(columns={'vol': 'volume'}, inplace=True)

    return df

if __name__ == '__main__':
    # 创建 Cerebro 实例
    cerebro = bt.Cerebro()
    # 添加策略
    cerebro.addstrategy(Peak_Valley)
    # 获取数据
    stock_code = '600519.SH'  # 贵州茅台
    start_date = '20210101'
    end_date = '20221231'
    data = get_tushare_data(stock_code, start_date, end_date)
    # 将数据转换为 backtrader 数据对象
    data_feed = bt.feeds.PandasData(dataname=data)
    cerebro.adddata(data_feed)
    # 设置初始资金
    cerebro.broker.setcash(100000.0)
    # 运行回测
    cerebro.run()
    # 打印最终资金
    print(f'Final Portfolio Value: {cerebro.broker.getvalue():,.2f}')
    # 生成可视化图
    fig = cerebro.plot(style='candle', volume=False)[0][0]
    plt.show()