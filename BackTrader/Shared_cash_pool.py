import backtrader as bt
from backtrader.indicators import *
from log import Log
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
        for index, data in enumerate(self.datas):
            c = data.close
            self.sma5[data] = MovingAverageSimple(c)  # 初始化5日简单移动均线
            self.ema15[data] = ExponentialMovingAverage(c)  # 初始化15日指数加权移动均线
            self.bolling_top[data] = bt.indicators.BollingerBands(c, period=20).top  # 初始化布林带上轨
            self.bolling_bot[data] = bt.indicators.BollingerBands(c, period=20).bot  # 初始化布林带下轨
            self.out_money[data]=0#平仓得到的钱初始化
            self.sell_num[data]=0#平仓卖出的品类数初始化
            self.num_of_codes[data]=0#持仓的总品类数初始化
            self.num_of_rest[data]=0#每天平仓后剩余的持仓品类数初始化
            self.sell_judge[data]=0


    def log(self, txt, dt=None):
        """ 日志记录函数 """
        dt = dt or self.datas[0].datetime.date(0)
        print(f'{dt.isoformat()} {txt}')


    def next(self):
        """
        每个时间步执行共享资金池策略。
        """
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
                    self.log(
                    f"BUY EXECUTED,{data._name}, Size:{order.executed.size},"
                    f"Price:{order.executed.price:.2f},"
                    f"Cost:{order.executed.value:.2f},"
                    f"Commission:{order.executed.comm:.2f}"
                    )
                elif order.issell():  # 卖出订单完成
                    net_proceeds=order.executed.value-order.executed.comm
                    self.proceeds+=net_proceeds
                    self.log(
                    f"SELL EXECUTED,{data._name},Size:{order.executed.size},"
                    f"Price:{order.executed.price:.2f},"
                    f"Proceeds:{order.executed.value:.2f},"
                    f"Commission:{order.executed.comm:.2f},"
                    f"Net Proceeds:{net_proceeds:.2f}"
                    )
                    self.allocate_proceeds(net_proceeds,sold_data=data)
            elif order.status is order.Canceled:
                print('ORDER CANCELED')
            elif order.status is order.Rejected:
                print('ORDER REJECTED')
            elif order.status is order.Margin:
                print('ORDER MARGIN')
        else:
            pass

    def shared_cash(self):
        """
        根据共享资金池策略的条件进行每个品种的买入或卖出。
        """
        for data in self.datas:
            pos=self.getposition(data).size
            if pos==0:
                size=self.calculate_quantity(data)
                self.buy_function(line=data,size=size)
            else:
                self.sell_function(line=data)

    def buy_function(self, line, size):
        """
        执行买入操作，当满足买入条件时，调用Backtrader的买入函数。
        """
        close_over_sma = line.close > self.sma5[line][0]  # 当前价格高于5日均线
        close_over_ema = line.close > self.ema15[line][0]  # 当前价格高于15日指数均线
        sma_ema_diff = self.sma5[line][0] - self.ema15[line][0]  # 计算5日均线与15日均线的差值
        buy_cond = (close_over_sma and close_over_ema and sma_ema_diff > 0) or line.close == self.bolling_top[line][0]  # 满足买入条件

        if buy_cond and self.broker.getcash() > 0:  # 确保资金充足
            self.log(f'BUY CREATE, {line._name}, Size: {size}, Price: {line.close[0]:.2f}')
            self.buy(data=line,size=size)
        else:
            pass

    def sell_function(self, line):
        """
        执行卖出操作，当满足卖出条件时，调用Backtrader的卖出函数。
        """
    
        sell_cond = line.close < self.sma5[line]  # 当前价格低于5日均线

        if sell_cond and self.getposition(line).size>0:  # 当前持有仓位时执行卖出
            pos=self.getposition(line).size
            self.log(f'SELL CREATE,{line._name},Size:{pos},Price:{line.close[0]:.2f}')
            self.sell(data=line,size=pos)

    def allocate_proceeds(self,proceeds,sold_data):
        held_assets=[data for data in self.datas if self.getposition(data).size>0 and data!=sold_data]
        num_held=len(held_assets)

        if num_held==0:
            self.log("No assets held to allocate proceeds.")
            return
        
        allocation_per_asset=proceeds/num_held

        self.log(f"Allocating {allocation_per_asset:.2f} to each of {num_held} held assets.")

        for data in held_assets:
            size=int(allocation_per_asset/data.close[0])
            if size>0:
                self.log(f"ALLOCATE BUY,{data._name},Size:{size},Price:{data.close[0]:.2f}")
                self.buy(data=data,size=size)
                self.log("The Buying Above is Rebuy.")
            else:
                self.log(f'Insufficient allocation for {data._name},Allocation:{allocation_per_asset:.2f},Price:{data.close[0]:.2f}')




    def calculate_quantity(self, line) -> int:
        """
        根据可用资金计算每次交易的数量。
        """
        available_cash=self.broker.getcash()*0.05
        close_price=line.close[0]
        quantity=int(available_cash/close_price)
        return quantity
    
    def stop(self):
        self.log(f'Total Proceeds from Sell Orders:{self.proceeds:.2f}')

    def print_position(self, line) -> None:
        """
        打印当前持仓信息。
        """
        pos = self.getposition(line)
        print(f"品种: {line._name} 的当前仓位: {pos.size} @price: {pos.price}")

