import backtrader as bt
import Log_Func
class Buy_And_Sell_Strategy(bt.Strategy):

    def buy_function(self, line, size):
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
            pass

    def sell_function(self, line):
        """
        执行卖出操作，当满足卖出条件时，调用Backtrader的卖出函数。
        """
    
        sell_cond = line.close < self.sma5[line]  # 当前价格低于5日均线

        if sell_cond and self.getposition(line).size>0:  # 当前持有仓位时执行卖出
            pos=self.getposition(line).size
            Log_Func.Log.log(self,f'SELL CREATE,{line._name},Size:{pos},Price:{line.close[0]:.2f}')
            self.close(data=line)


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