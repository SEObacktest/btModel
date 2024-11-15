import backtrader as bt
import Log_Func
import pandas as pd
import Shared_cash_pool
import AddPos
class Buy_And_Sell_Strategy(bt.Strategy):

    '''def buy_function(self, line, size):
        """
        执行买入操作，当满足买入条件时，调用Backtrader的买入函数。
        """
        close_over_sma = line.close > self.sma5[line][0]  # 当前价格高于5日均线
        close_over_ema = line.close > self.ema15[line][0]  # 当前价格高于15日指数均线
        sma_ema_diff = self.sma5[line][0] - self.ema15[line][0]  # 计算5日均线与15日均线的差值
        #buy_cond = (close_over_sma and close_over_ema and sma_ema_diff > 0) or line.close == self.bolling_top[line][0]  # 满足买入条件
        buy_cond = (close_over_sma and close_over_ema and sma_ema_diff > 0)   # 满足买入条件
        if buy_cond and self.broker.getcash() > 0:  # 确保资金充足
            Log_Func.Log.log(self,f'BUY CREATE, {line._name}, Size: {size}, Price: {line.close[0]:.2f}')
            self.buy(data=line,size=size)
        else:
            pass'''
    
    def buy_function(self,line,size):
        bpk1=(self.diff[line][-1]<=self.dea[line][-1])
        bpk2=(self.diff[line][0]>self.dea[line][0])
        if(bpk1 and bpk2):
            pos=self.getposition(line).size
            if pos==0 and self.broker.getcash()>0:
                Log_Func.Log.log(self,f'BUY CREATE, {line._name}, Size: {size}, Price: {line.close[0]:.2f}')
                self.buy(data=line,size=size)
            elif pos<0 and self.broker.getcash()>0:
                Log_Func.Log.log(self,f'CLOSE SHORT CREATE, {line._name}, Size: {pos}, Price: {line.close[0]:.2f}')
                self.close(data=line)
                Log_Func.Log.log(self,f'BUY CREATE, {line._name}, Size: {size}, Price: {line.close[0]:.2f}')
                self.buy(data=line,size=size)
        else:
            pass
    
    def sell_function(self,line,size):
        spk1=(self.diff[line][-1]>self.dea[line][-1])
        spk2=(self.diff[line][0]<=self.dea[line][0])
        if (spk1 and spk2):
            pos=self.getposition(line).size
            if pos==0 and self.broker.getcash()>0:
                Log_Func.Log.log(self,f'OPEN SHORT CREATE, {line._name}, Size: {size}, Price: {line.close[0]:.2f}')
                self.sell(data=line, size=size)
            elif pos>0 and self.broker.getcash()>0:
                Log_Func.Log.log(self,f'SELL CREATE,{line._name},Size:{pos},Price:{line.close[0]:.2f}')
                self.close(data=line)
                Log_Func.Log.log(self,f'OPEN SHORT CREATE, {line._name}, Size: {size}, Price: {line.close[0]:.2f}')
                self.sell(data=line, size=size)

    '''def sell_function(self, line):
        """
        执行卖出操作，当满足卖出条件时，调用Backtrader的卖出函数。
        """
    
        sell_cond = line.close < self.sma5[line]  # 当前价格低于5日均线

        if sell_cond and self.getposition(line).size>0:  # 当前持有仓位时执行卖出
            pos=self.getposition(line).size
            Log_Func.Log.log(self,f'SELL CREATE,{line._name},Size:{pos},Price:{line.close[0]:.2f}')
            self.close(data=line)'''


    def open_short_function(self, line, size):
        """
        执行买空操作，当满足买空条件时，调用Backtrader的买空函数。
        """
        close_above_sma = line.close > self.sma5[line][0]  # 当前价格高于5日均线
        close_above_ema = line.close > self.ema15[line][0]  # 当前价格高于15日指数均线
        sma_ema_diff = self.sma5[line][0] - self.ema15[line][0]  # 计算5日均线与15日均线的差值
        buy_short_cond = (close_above_sma and close_above_ema and sma_ema_diff > 0) or line.close == self.bolling_top[line][0]  # 满足买空条件
        # 确保没有持仓且、资金充足满足买空条件，则执行买空操作
        if buy_short_cond and not self.position and self.broker.getcash() > 0:
            Log_Func.Log.log(self,f'OPEN SHORT CREATE, {line._name}, Size: {size}, Price: {line.close[0]:.2f}')
            self.sell(data=line, size=size)
        else:
            pass

    def close_short_function(self, line):
        """
        执行卖空操作，当满足卖空条件时，调用Backtrader的卖空函数。
        """
        close_below_sma = line.close < self.sma5[line][0]  # 当前价格低于5日均线
        close_below_ema = line.close < self.ema15[line][0]  # 当前价格低于15日指数均线
        sma_ema_diff = self.sma5[line][0] - self.ema15[line][0]  # 计算5日均线与15日均线的差值
        sell_short_cond = (close_below_sma and close_below_ema and sma_ema_diff < 0) or line.close == self.bolling_bot[line][0]  # 满足卖空条件

        if sell_short_cond and self.broker.getcash() > 0:  # 确保资金充足，则执行卖空操作
            pos=self.getposition(line).size
            Log_Func.Log.log(self,f'CLOSE SHORT CREATE, {line._name}, Size: {pos}, Price: {line.close[0]:.2f}')
            self.close(data=line)
        else:
            pass


    # def grading_open_long_function(self,rank):
    def grading_top_function(self, top_stocks):
        '''
        处理打分后排名高的品种
        '''
        # top_stocks=rank.nlargest(1,'Score')
        for stock in top_stocks['Stock']:
            best_data=None
            for  data in self.datas:
                if data._name==stock:
                    best_data=data
                    break
            
            if best_data:
                size=Shared_cash_pool.Shared_cash_pool.calculate_quantity(self,best_data)
                pos=self.getposition(best_data).size
                if pos==0:  #  没有持仓→开空
                    Log_Func.Log.log(self,f'OPEH LONG CREATE, {best_data._name}, Size: {size}, Price: {best_data.close[0]:.2f}')
                    self.buy(data=best_data,size=size)
                elif pos<0:  # 持有空头→平空→开多
                    Log_Func.Log.log(self,f'CLOSE SHORT CREATE, {best_data._name}, Size: {pos}, Price: {best_data.close[0]:.2f}')
                    self.close(data=best_data)
                    Log_Func.Log.log(self,f'OPEN LONG CREATE, {best_data._name}, Size: {size}, Price: {best_data.close[0]:.2f}')
                    self.buy(data=best_data,size=size)
                elif pos>0: # 持有多头→check
                    AddPos.addpos.rebalance_long_positions(self,specific_assets=best_data)


    # def grading_open_short_function(self, rank):
    def grading_worst_function(self, worst_stocks):
        """ 处理打分后排名低的品种 """
        # bot_stocks=rank.nsmallest(1,'Score')
        # 遍历得分最低的股票
        for stock in worst_stocks['Stock']:
            worst_data=None
            for  data in self.datas:
                if data._name==stock:
                    worst_data=data
                    break
            if worst_data:
                size=Shared_cash_pool.Shared_cash_pool.calculate_quantity(self,worst_data)
                pos=self.getposition(worst_data).size
                if pos==0:  # 没有持仓→开空头
                    Log_Func.Log.log(self,f'OPEN SHORT CREATE, {worst_data._name}, Size: {size}, Price: {worst_data.close[0]:.2f}')
                    self.sell(data=worst_data,size=size)
                elif pos>0:  # 持有多头→平多→开空头
                    Log_Func.Log.log(self,f'CLOSE LONG CREATE, {worst_data._name}, Size: {pos}, Price: {worst_data.close[0]:.2f}')
                    self.close(data=worst_data)
                    Log_Func.Log.log(self,f'OPEN SHORT CREATE, {worst_data._name}, Size: {size}, Price: {worst_data.close[0]:.2f}')
                    self.sell(data=worst_data,size=size)
                elif pos<0:  # 持有空头→check
                    AddPos.addpos.rebalance_short_positions(self,specific_assets=worst_data)

    def grading_middle_function(self, middle_stocks):
        """处理打分后排名中间的品种"""

        # 遍历股票名称
        for stock in middle_stocks['Stock']:
            middle_data=None
            for  data in self.datas:
                if data._name==stock:
                    middle_data=data
                    break
            # 如果原来持有
            size = Shared_cash_pool.Shared_cash_pool.calculate_quantity(self, middle_data)
            pos = self.getposition(middle_data).size
            # 持有空头 → 平空
            if pos <0:
                Log_Func.Log.log(self,
                                 f'CLOSE SHORT CREATE, {middle_data._name}, Size: {size}, Price: {middle_data.close[0]:.2f}')
                self.close(data=middle_data)
            # 持有多头 → 平多
            elif pos > 0:
                Log_Func.Log.log(self,
                                 f'CLOSE LONG CREATE, {middle_data._name}, Size: {size}, Price: {middle_data.close[0]:.2f}')
                self.close(data=middle_data)
            # 如果没有 → pass
            elif pos == 0:
                pass