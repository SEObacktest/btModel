import backtrader as bt

class Log():
    @staticmethod
    def log(strategy:bt.Strategy, txt, dt=None):
        """ 日志记录函数 """
        dt = dt or strategy.datas[0].datetime.date(0)
        print(f'{dt.isoformat()} {txt}')