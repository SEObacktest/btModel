import backtrader as bt
from BackTrader.tools.log_func import Log

class AddPos(bt.Strategy):

    def rebalance_long_positions(self, specific_assets=None):
        Log.log(self,f"Checking Long Position Now")
        current_value=self.broker.getvalue()
        Log.log(self,f"Total Value:{current_value:.2f}")
        # 获取当前持有的所有多头仓位
        if specific_assets is None:  # 平衡所有持有的多头仓位
            held_assets=[data for data in self.datas if self.getposition(data).size>0]
        else:
            held_assets = [data for data in specific_assets if self.getposition(data).size > 0]
        for data in held_assets:
            position=self.getposition(data)
            if position.size!=0:
                current_price=data.close[0]
                current_pos_value=position.size*current_price
                target_pos_value=current_value*self.target_percent
                target_pos=int(target_pos_value/current_price)

                Log.log(self,f"{data._name}:Long Position Now:{position.size:.2f},Value Now:{current_pos_value:.2f}")
                Log.log(self,f"{data._name}:Target Long Position:{target_pos:.2f},Target Value:{target_pos_value:.2f}")

                delta_size=target_pos-position.size

                if delta_size>0:
                    Log.log(self,f"Rebalance Buy In:{data._name} for {delta_size:.2f}")
                    self.buy(data=data,size=delta_size)
                 
                elif delta_size<0:
                    Log.log(self,f"Rebalance Sold:{data._name} for {delta_size:.2f}")
                    self.sell(data=data,size=delta_size)

                elif delta_size==0:
                    pass

                
    def rebalance_short_positions(self, specific_assets=None):
        Log.log(self,f"Checking Short Position Now")  # 记录开始检查空头仓位的日志
        current_value=self.broker.getvalue()  # 获取当前投资组合的总价值
        Log.log(self,f"Total Value:{current_value:.2f}")  # 记录当前投资组合的总价值
        # 获取当前持有的所有空头仓位
        if specific_assets is None:  # 平衡所有持有的空头仓位
            held_assets = [data for data in self.datas if self.getposition(data).size < 0]
        else:  # 平衡指定的空头仓位
            held_assets = [data for data in specific_assets if self.getposition(data).size < 0]
        #  遍历所有持有的空头仓位
        for data in held_assets:
            position=self.getposition(data)
            if position.size!=0:  # 检查仓位大小是否为0（理论上不应该为0，因为已经筛选出持有空头仓位的股票）
                current_price=data.close[0]  # 获取当前股票的价格
                current_pos_value=position.size*current_price  # 计算当前仓位的价值
                target_pos_value=current_value*self.target_percent*(-1)  # 计算目标仓位的价值（负数表示空头仓位）
                target_pos=int(target_pos_value/current_price)  # 计算目标仓位的数量
                # 记录当前仓位的信息
                Log.log(self,f"{data._name}:Short Position Now:{position.size:.2f},Value Now:{current_pos_value:.2f}")
                # 记录目标仓位的信息
                Log.log(self,f"{data._name}:Target Short Position:{target_pos:.2f},Target Value:{target_pos_value:.2f}")
                # 计算需要调整的仓位数量
                delta_size=target_pos-position.size
                # 如果需要减少空头仓位（即买入平仓）
                if delta_size>0:
                    Log.log(self,f"Rebalance Close Short:{data._name} for {delta_size:.2f}")
                    self.buy(data=data,size=delta_size)
                # 如果需要增加空头仓位（即卖出开仓）
                elif delta_size<0:
                    Log.log(self,f"Rebalance Open Short:{data._name} for {delta_size:.2f}")
                    self.sell(data=data,size=delta_size)
                # 如果不需要调整仓位
                elif delta_size==0:
                    pass


    def allocate_proceeds(self,proceeds,sold_data):
        held_assets=[data for data in self.datas if self.getposition(data).size>0 and data!=sold_data]
        num_held=len(held_assets)

        if num_held==0:
            self.log(self,"No assets held to allocate proceeds.")
            return
        
        allocation_per_asset=proceeds/num_held

        self.log(self,f"Allocating {allocation_per_asset:.2f} to each of {num_held} held assets.")

        for data in held_assets:
            size=int(allocation_per_asset/data.close[0])
            if size>0:
                Log.log(self,f"ALLOCATE BUY,{data._name},Size:{size},Price:{data.close[0]:.2f}")
                self.buy(data=data,size=size)
                Log.log(self,"The Buying Above is Rebuy.")
            else:
                Log.log(self,f'Insufficient allocation for {data._name},Allocation:{allocation_per_asset:.2f},Price:{data.close[0]:.2f}')