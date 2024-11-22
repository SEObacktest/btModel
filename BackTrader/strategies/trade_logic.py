import backtrader as bt
from tools import log_func
from tools.log_func import Log
# import sys
# sys.path.append("..")
# from BackTrader import shared_cash_pool
# from BackTrader.tools import add_pos

class TradeLogic():

    def buy_function(self,strategy:bt.Strategy,line:bt.DataSeries,size:float):
        bpk1=(strategy.diff[line][-1]<=strategy.dea[line][-1])
        bpk2=(strategy.diff[line][0]>strategy.dea[line][0])
        if(bpk1 and bpk2):
            pos=strategy.getposition(line).size
            if pos==0 and strategy.broker.getcash()>0:
                Log.log(strategy, f'BUY CREATE, {line._name}, Size: {size}, Price: {line.close[0]:.2f}')
                strategy.buy(data=line,size=size)
            elif pos<0 and strategy.broker.getcash()>0:
                Log.log(strategy, f'CLOSE SHORT CREATE, {line._name}, Size: {pos}, Price: {line.close[0]:.2f}')
                strategy.close(data=line)
                Log.log(strategy, f'BUY CREATE, {line._name}, Size: {size}, Price: {line.close[0]:.2f}')
                strategy.buy(data=line,size=size)
        else:
            pass
    def sell_function(self,strategy:bt.Strategy,line,size):
        spk1=(strategy.diff[line][-1]>strategy.dea[line][-1])
        spk2=(strategy.diff[line][0]<=strategy.dea[line][0])
        if (spk1 and spk2):
            pos=strategy.getposition(line).size
            if pos==0 and strategy.broker.getcash()>0:
                Log.log(strategy, f'OPEN SHORT CREATE, {line._name}, Size: {size}, Price: {line.close[0]:.2f}')
                strategy.sell(data=line, size=size)
            elif pos>0 and strategy.broker.getcash()>0:
                Log.log(strategy, f'SELL CREATE,{line._name},Size:{pos},Price:{line.close[0]:.2f}')
                strategy.close(data=line)
                Log.log(strategy, f'OPEN SHORT CREATE, {line._name}, Size: {size}, Price: {line.close[0]:.2f}')
                strategy.sell(data=line, size=size)

    def rebalance_long_positions(self,strategy:bt.Strategy, specific_assets=None):
        Log.log(strategy,f"Checking Long Position Now")
        current_value=strategy.broker.getvalue()
        Log.log(strategy,f"Total Value:{current_value:.2f}")
        # 获取当前持有的所有多头仓位
        if specific_assets is None:  # 平衡所有持有的多头仓位
            held_assets=[data for data in strategy.datas if strategy.getposition(data).size>0]
        else:
            held_assets = [data for data in specific_assets if strategy.getposition(data).size > 0]
        for data in held_assets:
            position=strategy.getposition(data)
            if position.size!=0:
                current_price=data.close[0]
                current_pos_value=position.size*current_price
                target_pos_value=current_value*strategy.target_percent
                target_pos=int(target_pos_value/current_price)

                Log.log(strategy,f"{data._name}:Long Position Now:{position.size:.2f},Value Now:{current_pos_value:.2f}")
                Log.log(strategy,f"{data._name}:Target Long Position:{target_pos:.2f},Target Value:{target_pos_value:.2f}")

                delta_size=target_pos-position.size

                if delta_size>0:
                    Log.log(strategy,f"Rebalance Buy In:{data._name} for {delta_size:.2f}")
                    strategy.buy(data=data,size=delta_size)
                 
                elif delta_size<0:
                    Log.log(strategy,f"Rebalance Sold:{data._name} for {delta_size:.2f}")
                    strategy.sell(data=data,size=delta_size)

                elif delta_size==0:
                    pass

    def rebalance_short_positions(self,strategy:bt.Strategy, specific_assets=None):
        Log.log(strategy,f"Checking Short Position Now")  # 记录开始检查空头仓位的日志
        current_value=strategy.broker.getvalue()  # 获取当前投资组合的总价值
        Log.log(strategy,f"Total Value:{current_value:.2f}")  # 记录当前投资组合的总价值
        # 获取当前持有的所有空头仓位
        if specific_assets is None:  # 平衡所有持有的空头仓位
            held_assets = [data for data in strategy.datas if strategy.getposition(data).size < 0]
        else:  # 平衡指定的空头仓位
            held_assets = [data for data in specific_assets if strategy.getposition(data).size < 0]
        #  遍历所有持有的空头仓位
        for data in held_assets:
            position=strategy.getposition(data)
            if position.size!=0:  # 检查仓位大小是否为0（理论上不应该为0，因为已经筛选出持有空头仓位的股票）
                current_price=data.close[0]  # 获取当前股票的价格
                current_pos_value=position.size*current_price  # 计算当前仓位的价值
                target_pos_value=current_value*strategy.target_percent*(-1)  # 计算目标仓位的价值（负数表示空头仓位）
                target_pos=int(target_pos_value/current_price)  # 计算目标仓位的数量
                # 记录当前仓位的信息
                Log.log(strategy,f"{data._name}:Short Position Now:{position.size:.2f},Value Now:{current_pos_value:.2f}")
                # 记录目标仓位的信息
                Log.log(strategy,f"{data._name}:Target Short Position:{target_pos:.2f},Target Value:{target_pos_value:.2f}")
                # 计算需要调整的仓位数量
                delta_size=target_pos-position.size
                # 如果需要减少空头仓位（即买入平仓）
                if delta_size>0:
                    Log.log(strategy,f"Rebalance Close Short:{data._name} for {delta_size:.2f}")
                    strategy.buy(data=data,size=delta_size)
                # 如果需要增加空头仓位（即卖出开仓）
                elif delta_size<0:
                    Log.log(strategy,f"Rebalance Open Short:{data._name} for {delta_size:.2f}")
                    strategy.sell(data=data,size=delta_size)
                # 如果不需要调整仓位
                elif delta_size==0:
                    pass

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
            log_func.Log.log(self, f'OPEN SHORT CREATE, {line._name}, Size: {size}, Price: {line.close[0]:.2f}')
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
            log_func.Log.log(self, f'CLOSE SHORT CREATE, {line._name}, Size: {pos}, Price: {line.close[0]:.2f}')
            self.close(data=line)
        else:
            pass

    def grading_open_long_function(self,top_stocks):
        for stock in top_stocks['Stock']:
            best_data=None
            for  data in self.datas:
                if data._name==stock:
                    best_data=data
                    break
            if best_data:
                size=shared_cash_pool.Shared_cash_pool.calculate_quantity(self,best_data)
                pos=self.getposition(best_data).size
                if pos==0:
                    log_func.Log.log(self, f'OPEH LONG CREATE, {best_data._name}, Size: {size}, Price: {best_data.close[0]:.2f}')
                    self.buy(data=best_data,size=size)
                elif pos<0:
                    log_func.Log.log(self, f'CLOSE SHORT CREATE, {best_data._name}, Size: {pos}, Price: {best_data.close[0]:.2f}')
                    self.close(data=best_data)
                    log_func.Log.log(self, f'OPEN LONG CREATE, {best_data._name}, Size: {size}, Price: {best_data.close[0]:.2f}')
                    self.buy(data=best_data,size=size)
                elif pos>0:    
                    add_pos.addpos.rebalance_long_positions(self,specific_assets=best_data)


    def grading_open_short_function(self, bot_stocks):
        for stock in bot_stocks['Stock']:
            worst_data=None
            for  data in self.datas:
                if data._name==stock:
                    worst_data=data
                    break
            if worst_data:
                size=shared_cash_pool.Shared_cash_pool.calculate_quantity(self,worst_data)
                pos=self.getposition(worst_data).size
                if pos==0:
                    log_func.Log.log(self, f'OPEN SHORT CREATE, {worst_data._name}, Size: {size}, Price: {worst_data.close[0]:.2f}')
                    self.sell(data=worst_data,size=size)
                elif pos>0:
                    log_func.Log.log(self, f'CLOSE LONG CREATE, {worst_data._name}, Size: {pos}, Price: {worst_data.close[0]:.2f}')
                    self.close(data=worst_data)
                    log_func.Log.log(self, f'OPEN SHORT CREATE, {worst_data._name}, Size: {size}, Price: {worst_data.close[0]:.2f}')
                    self.sell(data=worst_data,size=size)
                elif pos<0:    
                    add_pos.AddPos.rebalance_short_positions(self,specific_assets=worst_data)

    def grading_middle_function(self, middle_stocks):
        """处理打分后排名中间的品种"""
        # 遍历股票名称
        for stock in middle_stocks['Stock']:
            middle_data = None
            for data in self.datas:
                if data._name == stock:
                    middle_data = data
                    break
            # 如果原来持有
            size = shared_cash_pool.Shared_cash_pool.calculate_quantity(self, middle_data)
            pos = self.getposition(middle_data).size
            # 持有空头 → 平空
            if pos < 0:
                log_func.Log.log(self,
                                 f'CLOSE SHORT CREATE, {middle_data._name}, Size: {size}, Price: {middle_data.close[0]:.2f}')
                self.close(data=middle_data)
            # 持有多头 → 平多
            elif pos > 0:
                log_func.Log.log(self,
                                 f'CLOSE LONG CREATE, {middle_data._name}, Size: {size}, Price: {middle_data.close[0]:.2f}')
                self.close(data=middle_data)
            # 如果没有 → pass
            elif pos == 0:
                pass