import backtrader as bt
from backtrader.indicators import *
import Log_Func
import pandas as pd
import Shared_cash_pool
import BuyAndSell
class Shared_Cash_Pool_Pointing(bt.Strategy):
    def __init__(self):

        self.ema5=dict()
        self.ema10=dict()
        self.ema15=dict()
        self.sma5=dict()
        self.sma10=dict()
        self.sma15=dict()
        self.ema12=dict()
        self.ema26=dict()
        self.diff=dict()
        self.dea=dict()
        self.notify_flag=1
        for data in self.datas:
            c=data.close
            self.ema5[data]=ExponentialMovingAverage(c,period=5)
            self.ema10[data]=ExponentialMovingAverage(c,period=10)
            self.ema15[data]=ExponentialMovingAverage(c,period=15)
            self.sma5[data]=MovingAverageSimple(c,period=5)
            self.sma10[data]=MovingAverageSimple(c,period=10)
            self.sma15[data]=MovingAverageSimple(c,period=15)
            self.ema12[data]=ExponentialMovingAverage(c,period=12)
            self.ema26[data]=ExponentialMovingAverage(c,period=26)
            self.diff[data]=self.ema12[data]-self.ema26[data]
            self.dea[data]=ExponentialMovingAverage(self.diff[data],period=9)

    def next(self):
        self.shared_cash_pointing()

    def notify_order(self,order):
        if self.notify_flag:
            if order is None:
                Log_Func.Log.log(f'Receive a none order')
                return
            if order.status in [order.Submitted, order.Accepted]:
                return
            if order.status in [order.Completed]:
                data=order.data
                if order.isbuy():  
                    Log_Func.Log.log(self,
                    f"OPEN BUY EXECUTED,{data._name}, Size:{order.executed.size},"
                    f"Price:{order.executed.price:.2f},"
                    f"Cost:{order.executed.value:.2f},"
                    f"Commission:{order.executed.comm:.2f}"
                    )
                
                elif order.issell():
                    Log_Func.Log.log(self,
                    f"OPEN SELL EXECUTED,{data._name},Size:{order.executed.size},"
                    f"Price:{order.executed.price:.2f},"
                    f"Cost:{order.executed.value:.2f},"
                    f"Commission:{order.executed.comm:.2f}"
                    )

                elif order.isclose():
                    Log_Func.Log.log(self,
                    f"CLOSE EXECUTED,{data._name},Size:{order.executed.size},"
                    f"Price:{order.executed.price:.2f},"
                    f"Cost:{order.executed.value:.2f},"
                    f"Commission:{order.executed.comm:.2f}"
                    )


    def shared_cash_pointing(self):
        self.point=dict()#字典当打分表，记录每个品种的打分情况
        for data in self.datas:#满足一个指标就加一分
            self.point[data._name]=0
            if self.ema5[data][0]>5:
                self.point[data._name]+=1
            if self.ema10[data][0]>5:
                self.point[data._name]+=1
            if self.ema15[data][0]>10:
                self.point[data._name]+=1
            if self.sma5[data][0]>5:
                self.point[data._name]+=1
            if self.sma10[data][0]>10:
                self.point[data._name]+=1
            if self.sma15[data][0]>15:
                self.point[data._name]+=1
        #包含股票名称和得分的DataFrame
        scores_df=pd.DataFrame(list(self.point.items()),columns=['Stock','Score'])
        # 按照得分排序
        scores_df = scores_df.sort_values(by='Score', ascending=False)
        # 获取排名前2、后2及中间的股票名称
        top_stocks = scores_df.head(1)
        worst_stocks = scores_df.tail(1)
        middle_stocks = scores_df.iloc[1:-1]
        BuyAndSell.Buy_And_Sell_Strategy.grading_top_function(self, top_stocks)
        BuyAndSell.Buy_And_Sell_Strategy.grading_worst_function(self,worst_stocks)
        BuyAndSell.Buy_And_Sell_Strategy.grading_middle_function(self,middle_stocks)
        # BuyAndSell.Buy_And_Sell_Strategy.grading_top_function(self,scores_df)




        




