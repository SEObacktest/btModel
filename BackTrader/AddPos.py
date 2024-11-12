import backtrader as bt
import Log_Func

class addpos(bt.Strategy):


    def rebalance_long_positions(self):
        Log_Func.Log.log(self,f"Checking Long Position Now")
        current_value=self.broker.getvalue()
        Log_Func.Log.log(self,f"Total Value:{current_value:.2f}")
        held_assets=[data for data in self.datas if self.getposition(data).size>0]
        for data in held_assets:
            position=self.getposition(data)
            if position.size!=0:
                current_price=data.close[0]
                current_pos_value=position.size*current_price
                target_pos_value=current_value*self.target_percent
                target_pos=int(target_pos_value/current_price)

                Log_Func.Log.log(self,f"{data._name}:Long Position Now:{position.size:.2f},Value Now:{current_pos_value:.2f}")
                Log_Func.Log.log(self,f"{data._name}:Target Long Position:{target_pos:.2f},Target Value:{target_pos_value:.2f}")

                delta_size=target_pos-position.size

                if delta_size>0:
                    Log_Func.Log.log(self,f"Rebalance Buy In:{data._name} for {delta_size:.2f}")
                    self.buy(data=data,size=delta_size)
                 
                elif delta_size<0:
                    Log_Func.Log.log(self,f"Rebalance Sold:{data._name} for {delta_size:.2f}")
                    self.sell(data=data,size=delta_size)

                elif delta_size==0:
                    pass

                
    def rebalance_short_positions(self):
        Log_Func.Log.log(self,f"Checking Short Position Now")
        current_value=self.broker.getvalue()
        Log_Func.Log.log(self,f"Total Value:{current_value:.2f}")
        held_assets=[data for data in self.datas if self.getposition(data).size<0]
        for data in held_assets:
            position=self.getposition(data)
            if position.size!=0:
                current_price=data.close[0]
                current_pos_value=position.size*current_price
                target_pos_value=current_value*self.target_percent*(-1)
                target_pos=int(target_pos_value/current_price)

                Log_Func.Log.log(self,f"{data._name}:Short Position Now:{position.size:.2f},Value Now:{current_pos_value:.2f}")
                Log_Func.Log.log(self,f"{data._name}:Target Short Position:{target_pos:.2f},Target Value:{target_pos_value:.2f}")

                delta_size=target_pos-position.size

                if delta_size>0:
                    Log_Func.Log.log(self,f"Rebalance Close Short:{data._name} for {delta_size:.2f}")
                    self.buy(data=data,size=delta_size)
                 
                elif delta_size<0:
                    Log_Func.Log.log(self,f"Rebalance Open Short:{data._name} for {delta_size:.2f}")
                    self.sell(data=data,size=delta_size)

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
                Log_Func.Log.log(self,f"ALLOCATE BUY,{data._name},Size:{size},Price:{data.close[0]:.2f}")
                self.buy(data=data,size=size)
                Log_Func.Log.log(self,"The Buying Above is Rebuy.")
            else:
                Log_Func.Log.log(self,f'Insufficient allocation for {data._name},Allocation:{allocation_per_asset:.2f},Price:{data.close[0]:.2f}')