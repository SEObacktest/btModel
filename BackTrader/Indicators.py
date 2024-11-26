import backtrader as bt

class CustomEMA(bt.Indicator):
    """
    自定义 EMA26 指标，从股票数据开始的第一天计算。
    - 第一日的 EMA26 值为当日的收盘价。
    - 后续 EMA26 按照标准公式计算。
    """
    lines = ('ema',)
    params = (('period',None ),)


    def __init__(self):
        
        self.alpha = 2 / (self.params.period + 1)
        self.addminperiod(1)  # 从第一天开始计算
        self.first = True  # 标记是否为第一天

    def next(self):
        if self.first:
            # 第一条数据，初始化 EMA26 为当日收盘价
            self.lines.ema[0] = self.data[0]
            self.first = False
        else:
            # 正常的 EMA26 计算
            self.lines.ema[0] = (
                self.alpha * self.data[0] +
                (1 - self.alpha) * self.lines.ema[-1]
            )

