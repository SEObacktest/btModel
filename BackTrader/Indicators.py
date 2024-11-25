import backtrader as bt
class CustomEMA26(bt.Indicator):
    """
    自定义 EMA26 指标，从数据开始的第一天计算。
    """
    lines = ('ema',)
    params = (('period', 26),)

    def __init__(self):
        self.alpha = 2 / (self.params.period + 1)
        self.addminperiod(1)  # 从第一天开始计算

    def nextstart(self):
        # 数据的第一天，初始化 EMA 为收盘价
        self.lines.ema[0] = self.data.close[0]
        # 设置 next 方法为正常计算
        self.next = self._next

    def _next(self):
        # 正常的 EMA 计算
        self.lines.ema[0] = (
            self.alpha * self.data.close[0] +
            (1 - self.alpha) * self.lines.ema[-1]
        )
