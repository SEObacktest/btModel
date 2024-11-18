import backtrader as bt
from tools.log_func import Log
class TradeLogic():
    @staticmethod
    def buy_function(strategy:bt.Strategy,line:bt.DataSeries,size:float):
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
    @staticmethod
    def sell_function(strategy:bt.Strategy,line,size):
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
    @staticmethod
    def rebalance_long_positions(strategy:bt.Strategy, specific_assets=None):
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

    @staticmethod
    def rebalance_short_positions(strategy:bt.Strategy, specific_assets=None):
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