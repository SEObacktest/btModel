import backtrader as bt
from backtrader.indicators import *
from datetime import time
import AddPos
import DataIO
import BuyAndSell
import Log_Func
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
        self.notify_flag = 1  # 控制是否打印订单状态
        self.out_money=dict()
        self.sell_num=dict()
        self.num_of_codes=dict()
        self.num_of_rest=dict()
        self.sell_judge=dict()
        self.proceeds=0
        self.pending_allocation=0
        self.checking_time=time(14,50)
        self.target_percent=0.05
        self.ema12=dict()
        self.ema26=dict()
        self.diff=dict()
        self.dea=dict()
        for index, data in enumerate(self.datas):
            c = data.close
            self.sma5[data] = MovingAverageSimple(c,period=10)  # 初始化5日简单移动均线
            self.ema15[data] = ExponentialMovingAverage(c,period=10)  # 初始化15日指数加权移动均线
            self.bolling_top[data] = bt.indicators.BollingerBands(c, period=20).top  # 初始化布林带上轨
            self.bolling_bot[data] = bt.indicators.BollingerBands(c, period=20).bot  # 初始化布林带下轨
            self.out_money[data]=0#平仓得到的钱初始化
            self.sell_num[data]=0#平仓卖出的品类数初始化
            self.num_of_codes[data]=0#持仓的总品类数初始化
            self.num_of_rest[data]=0#每天平仓后剩余的持仓品类数初始化
            self.sell_judge[data]=0
            self.update_percent_judge=0
            self.ema12[data]=ExponentialMovingAverage(c,period=12)
            self.ema26[data]=ExponentialMovingAverage(c,period=26)
            self.diff[data]=self.ema12[data]-self.ema26[data]
            self.dea[data]=ExponentialMovingAverage(self.diff[data],period=9)




    def next(self):
        """
        每个时间步执行共享资金池策略。
        """
        if self.update_percent_judge==0:
            DataIO.DataIO.change_target_percent(self)
            self.update_percent_judge+=1
        self.shared_cash()  # 执行共享资金池策略


    def notify_order(self, order):
        """
        通知订单状态，用于查看订单执行情况。
        """
        if self.notify_flag:
            if order is None:
                print("Received a None Order")
                return
            if order.status in [order.Submitted, order.Accepted]:  # 订单被接受，等待执行
                return
            if order.status in [order.Completed]:
                data=order.data
                if order.isbuy():  # 买入订单完成
                    Log_Func.Log.log(self,
                    f"BUY EXECUTED,{data._name}, Size:{order.executed.size},"
                    f"Price:{order.executed.price:.2f},"
                    f"Cost:{order.executed.value:.2f},"
                    f"Commission:{order.executed.comm:.2f}"
                    )
                elif order.issell() or order.isclose():  # 卖出订单完成
                    #net_proceeds=order.executed.value-order.executed.comm
                    #self.proceeds+=net_proceeds
                    Log_Func.Log.log(self,
                    f"SELL EXECUTED,{data._name},Size:{order.executed.size},"
                    f"Price:{order.executed.price:.2f},"
                    f"Cost:{order.executed.value:.2f},"
                    #f"Cost:{order.executed.size*order.executed.price}"
                    f"Commission:{order.executed.comm:.2f},"
                    #f"Net Proceeds:{net_proceeds:.2f}"
                    )
                    #if self.getposition(data).size==0:
                    #self.allocate_proceeds(net_proceeds,sold_data=data)
            elif order.status is order.Canceled:
                Log_Func.Log.log(self,'ORDER CANCELED')
            elif order.status is order.Rejected:
                Log_Func.Log.log(self,'ORDER REJECTED')
            elif order.status is order.Margin:
                Log_Func.Log.log(self,'ORDER MARGIN')
        else:
            pass

    def shared_cash(self):
        """
        根据共享资金池策略的条件进行每个品种的买入或卖出。
        """
        
        for data in self.datas:
            pos=self.getposition(data).size
            if pos<=0:
                size=self.calculate_quantity(data)
                BuyAndSell.Buy_And_Sell_Strategy.buy_function(self,line=data,size=size)
                #BuyAndSell.Buy_And_Sell_Strategy.open_short_function(self,line=data,size=size)
            else:
                size=self.calculate_quantity(data)
                BuyAndSell.Buy_And_Sell_Strategy.sell_function(self,line=data,size=size)
                #BuyAndSell.Buy_And_Sell_Strategy.close_short_function(self,line=data)
        AddPos.addpos.rebalance_long_positions(self)
        AddPos.addpos.rebalance_short_positions(self)

    
    def calculate_quantity(self, line) -> int:
        """
        根据可用资金计算每次交易的数量。
        """
        available_cash=self.broker.getcash()*0.05
        close_price=line.close[0]
        quantity=int(available_cash/close_price)
        return quantity
    
    def stop(self):
        Log_Func.Log.log(self,f'Total Proceeds from Sell Orders:{self.proceeds:.2f}')

    def print_position(self, line) -> None:
        """
        打印当前持仓信息。
        """
        pos = self.getposition(line)
        print(f"品种: {line._name} 的当前仓位: {pos.size} @price: {pos.price}")

