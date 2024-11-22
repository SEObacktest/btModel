from .trade_logic import TradeLogic
from tools import Log
import backtrader as bt

class SharedLogic():
    def __init__(self):
        self.log=Log()
        self.logic=TradeLogic()
    def shared_cash(self,st:bt.Strategy):
        """
        根据共享资金池策略的条件进行每个品种的买入或卖出。
        """
        
        for data in st.datas:
            pos=st.getposition(data).size
            if pos<=0:
                size=self.calculate_quantity(st,data)
                self.logic.buy_function(st,line=data,size=size)
                #BuyAndSell.Buy_And_Sell_Strategy.open_short_function(st,line=data,size=size)
            else:
                size=self.calculate_quantity(st,data)
                self.logic.sell_function(st,line=data,size=size)
                #BuyAndSell.Buy_And_Sell_Strategy.close_short_function(st,line=data)
        self.logic.rebalance_long_positions(st)
        self.logic.rebalance_short_positions(st) 

    def calculate_quantity(self, st:bt.Strategy,line:bt.DataSeries) -> int:
        available_cash=st.broker.getcash()*0.05
        close_price=line.close[0]
        quantity=int(available_cash/close_price)
        return quantity