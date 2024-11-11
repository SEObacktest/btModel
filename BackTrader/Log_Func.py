import backtrader as bt

class Log(bt.Strategy):

    def log(self, txt, dt=None):
        """ 日志记录函数 """
        dt = dt or self.datas[0].datetime.date(0)
        print(f'{dt.isoformat()} {txt}')