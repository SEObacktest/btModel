import backtrader as bt
from backtrader.indicators import *
from strategies import SharedLogic
from tools import Log 
import pandas as pd
import Indicators
import datetime
class Shared_Cash_Pool_Pointing(bt.Strategy):
    params = (
        ('backtest_start_date', None),
        ('backtest_end_date', None),
        ('EMA26',None),
        ('EMA12',None),
        ('EMA9',None),
    )

    def __init__(self):
        #各种打分用的指标
        self.init_cash=100000000
        self.cash=100000000
        self.DIFF=dict()
        self.MACD=dict()
        self.notify_flag=1
        self.profit=dict()#分品类保存利润的字典
        self.profit_contribution=dict()
        self.EMA26=dict()
        self.EMA12=dict()
        self.DEA=dict()
        self.target_percent=0.05
        self.start_date=dict()
        self.first_date=dict()
        self.current_date=2000-1-1
        self.order_list=dict()
        for data in self.datas:
            c=data.close
            self.profit[data._name]=0#各品类初始化为0
            self.profit_contribution[data._name]=0
            self.first_date[data]=None
            self.EMA26[data]=Indicators.CustomEMA(c,period=self.params.EMA26)
            self.EMA12[data]=Indicators.CustomEMA(c,period=self.params.EMA12)
            self.DIFF[data]=self.EMA12[data]-self.EMA26[data]
            self.DEA[data] =Indicators.CustomEMA(self.DIFF[data], period=self.params.EMA9)
            self.MACD[data]=2*(self.DIFF[data]-self.DEA[data])
            self.order_list[data]=[0]

    def prenext(self):
        current_date = self.datetime.date(0)
        if self.params.backtest_start_date <= current_date <= self.params.backtest_end_date:
            self.shared_cash_pointing_prenext()
            for data in self.datas:
                if current_date>=self.getdatabyname(data._name).datetime.date(0):
                    Log.log(self,f'{data._name}的收盘价:{data.close[0]}')
                    Log.log(self,f'{data._name}的指标,EMA26:{self.EMA26[data][0]},')
                    Log.log(self,f'{data._name}的指标,EMA12:{self.EMA12[data][0]},')
                    Log.log(self,f'{data._name}的指标,DIFF:{self.DIFF[data][0]},')
                    Log.log(self,f'{data._name}的指标,DEA:{self.DEA[data][0]},')
                    Log.log(self,f'{data._name}的指标,MACD:{self.MACD[data][0]},')
    
            Log.log(self,f'今天的可用资金:{self.cash}')
            print(self.profit)
            Log.log(self,f'今天的权益:{self.getvalue()}')

    def next(self):
        self.current_date = self.datas[0].datetime.date(0)
        if self.params.backtest_start_date <= self.current_date <= self.params.backtest_end_date:
            self.shared_cash_pointing()#执行策略
            for data in self.datas:
                #if current_date>=self.getdatabyname(data._name).datetime.date(0):
                #if current_date>=self.start_date[data]:
                #if len(data)>0:
                    Log.log(self,f'{data._name}的收盘价:{data.close[0]}')
                    Log.log(self,f'{data._name}的指标,EMA26:{self.EMA26[data][0]},')
                    Log.log(self,f'{data._name}的指标,EMA12:{self.EMA12[data][0]},')
                    Log.log(self,f'{data._name}的指标,DIFF:{self.DIFF[data][0]},')
                    Log.log(self,f'{data._name}的指标,DEA:{self.DEA[data][0]},')
                    Log.log(self,f'{data._name}的指标,MACD:{self.MACD[data][0]},')
                    hold_equity=self.getposition(data).size*data.close[0]
                    Log.log(self,f'{data._name}的权益:{abs(hold_equity)}')

                #else:
                    #continue
            Log.log(self,f'今天的可用资金:{self.cash}')
            print(self.profit)
            Log.log(self,f'今天的权益:{self.getvalue()}')

    def stop(self):
        #最后一天结束后，把持仓品类的权益释放出来加到各个品种利润上面
        for data in self.datas:
            if self.getposition(data).size!=0:
                self.profit[data._name]+=abs(self.getposition(data).size)*abs(data.close[0])
        self.calculate_contribution()
        
        Log.log(self,f"期初权益:{self.init_cash},{self.params.EMA26},{self.params.EMA12},{self.params.EMA9},{self.params.backtest_start_date},{self.params.backtest_end_date}",dt=self.params.backtest_end_date)

        Log.log(self,f"期末权益:{self.getvalue()},{self.params.EMA26},{self.params.EMA12},{self.params.EMA9},{self.params.backtest_start_date},{self.params.backtest_end_date}",dt=self.params.backtest_end_date)

        print(self.profit)
        print(self.profit_contribution)

    def notify_order(self,order):
        if self.notify_flag:
            data=order.data#获取这笔订单对应的品类
            if order is None:
                Log.log(self,f'Receive a none order')
                return
            if order.status in [order.Submitted, order.Accepted]:
                return
            if order.status in [order.Completed]:
                
                if order.isbuy():  

                    Log.log(self,
                    f"订单完成:买单,{data._name}, 手数:{(order.executed.size)},"
                    f"每手价格:{order.executed.price:.2f},"
                    f"总价格:{(order.executed.value):.2f},"
                    f"手续费:{order.executed.comm:.2f},"
                    f"该品种现有持仓:{self.getposition(data)}"
                    )
                    self.order_list[data].append(self.getposition(data).size)
                    if self.order_list[data][-1]>0 and self.order_list[data][-2]>=0 and self.order_list[data][-1]>self.order_list[data][-2]:
                        self.cashflow(data,-1,order)#开多仓/加多仓
                    
                    if self.order_list[data][-1]<=0 and self.order_list[data][-2]<0 and self.order_list[data][-1]>self.order_list[data][-2]:
                        self.cashflow(data,1,order)#平空仓/减空仓
                    #观察日志，发现手数和金额同号的时候是开/加仓，反之是平/减仓
                    #if (order.executed.size*order.executed.value)>0:
                        #self.cashflow(data,-1,order)
                        
                    #elif (order.executed.size*order.executed.value)<0:
                        #self.cashflow(data,1,order)
                    

                
                elif order.issell():
                    Log.log(self,
                    f"订单完成:卖单,{data._name},手数:{(order.executed.size)},"
                    f"每手价格:{order.executed.price:.2f},"
                    f"总价格:{(order.executed.value):.2f},"
                    f"手续费:{order.executed.comm:.2f},"
                    f"该品种现有持仓:{self.getposition(data)}"
                    )
                    self.order_list[data].append(self.getposition(data).size)
                    if self.order_list[data][-1]>=0 and self.order_list[data][-2]>0 and self.order_list[data][-1]<self.order_list[data][-2]:
                        self.cashflow(data,1,order)#平多仓/减多仓
                    if self.order_list[data][-1]<0 and self.order_list[data][-2]<=0 and self.order_list[data][-1]<self.order_list[data][-2]:
                        self.cashflow(data,-1,order)#开空仓/加空仓
                    #观察日志，发现手数和金额同号的时候是开/加仓，反之是平/减仓
                    #if (order.executed.size*order.executed.value)>0:
                        #self.cashflow(data,-1,order)
                        
                    #elif (order.executed.size*order.executed.value)<0:
                        #self.cashflow(data,1,order)

    def cashflow(self,data,symbol,order):
        #通过订单和品类，改变字典中这个品类的利润
        if symbol==1:
            self.profit[data._name]+=abs(order.executed.value)
            #通过executed.value来加减利润
            Log.log(self,f'品类:{data._name}的利润增加额:{abs(order.executed.value)}')
            self.cash=self.cash+abs(order.executed.value)
        elif symbol==-1:
            self.profit[data._name]-=abs(order.executed.value)
            Log.log(self,f'品类:{data._name}的利润减少额:{abs(order.executed.value)}')
            self.cash=self.cash-abs(order.executed.value)


    def shared_cash_pointing(self):#具体的策略（打分方式是随便写的）
        self.point=dict()#字典当打分表，记录每个品种的打分情况
        current_date=self.datetime.date(0)
        for data in self.datas:#满足一个指标就加一分
            #if current_date>self.getdatabyname(data._name).datetime.date(0):  
            if 1:
                self.point[data._name]=0
                if round(self.DIFF[data][0],2)>round(self.DEA[data][0],2) and round(self.DIFF[data][-1],2)<=round(self.DEA[data][-1],2):
                    self.point[data._name]+=3
                if round(self.MACD[data][0],2)>round(self.MACD[data][-1],2):
                    self.point[data._name]+=2
                if round(self.MACD[data][0],2)>0:
                    self.point[data._name]+=1
                if round(self.DIFF[data][0],2)<=round(self.DEA[data][0],2) and round(self.DIFF[data][-1],2)>round(self.DEA[data][-1],2):
                    self.point[data._name]-=3
                if round(self.MACD[data][0],2)<=round(self.MACD[data][-1],2):
                    self.point[data._name]-=2
                if round(self.MACD[data][0],2)<=0:
                    self.point[data._name]-=1
                if self.EMA26[data][0]>2:
                    self.point[data._name]+=1

        scores_df=pd.DataFrame(list(self.point.items()),columns=['Stock','Score'])#记录打分表
        if len(scores_df)>=2:
        #if 1:
            self.grading_open_long_function(scores_df)
        #分高的执行开多
            self.grading_open_short_function(scores_df)
        #分低的执行开空
            self.grading_close_function(scores_df)
        #中间的平仓'''
        

    def shared_cash_pointing_prenext(self):#具体的策略（打分方式是随便写的）
        self.point=dict()#字典当打分表，记录每个品种的打分情况
        current_date=self.datetime.date(0)
        for data in self.datas:#满足一个指标就加一分
            if current_date>=self.getdatabyname(data._name).datetime.date(0):  
                self.point[data._name]=0
                if round(self.DIFF[data][0],2)>round(self.DEA[data][0],2) and round(self.DIFF[data][-1],2)<=round(self.DEA[data][-1],2):
                    self.point[data._name]+=3
                if round(self.MACD[data][0],2)>round(self.MACD[data][-1],2):
                    self.point[data._name]+=2
                if round(self.MACD[data][0],2)>0:
                    self.point[data._name]+=1
                if round(self.DIFF[data][0],2)<=round(self.DEA[data][0],2) and round(self.DIFF[data][-1],2)>round(self.DEA[data][-1],2):
                    self.point[data._name]-=3
                if round(self.MACD[data][0],2)<=round(self.MACD[data][-1],2):
                    self.point[data._name]-=2
                if round(self.MACD[data][0],2)<=0:
                    self.point[data._name]-=1
                if self.EMA26[data][0]>2:
                    self.point[data._name]+=1

        scores_df=pd.DataFrame(list(self.point.items()),columns=['Stock','Score'])#记录打分表

        if len(scores_df)>=2:
        #if 1:
            self.grading_open_long_function(scores_df)
        #分高的执行开多
            self.grading_open_short_function(scores_df)
        #分低的执行开空
            self.grading_close_function(scores_df)
        #中间的平仓'''
        

    def grading_open_long_function(self,rank):#打分靠前的开多
        rank_sorted=rank.sort_values(by=['Score','Stock'],ascending=[False,True])#按分排序
        print(rank_sorted)
        top_stocks=rank_sorted.iloc[[0]]#分最高的那个开多
        print(top_stocks)
        for stock in top_stocks['Stock']:#从品类代码反得到data对象
            best_data=None
            for  data in self.datas:
                if data._name==stock:
                    best_data=data
                    break
            
            if best_data:
                size=self.calculate_quantity(self,best_data)
                #计算开多手数
                pos=self.getposition(best_data).size
                #获取现有持仓
                if pos==0:
                    #没有持仓，直接开多
                    Log.log(self,f'订单创建:开多, {best_data._name}, 手数: {size}, 成交价: {best_data.close[0]:.2f}')
                    self.buy(data=best_data,size=size)
                    
                    
                elif pos<0:
                    #持有空头，先平空再开多
                    Log.log(self,f'订单创建:先平空, {best_data._name}, 手数: {pos}, 成交价: {best_data.close[0]:.2f}')
                    order=self.close(data=best_data)
                    
                    Log.log(self,f'订单创建:后开多, {best_data._name}, 手数: {size}, 成交价: {best_data.close[0]:.2f}')
                    order=self.buy(data=best_data,size=size)
                    
                elif pos>0:    
                    #本就持有多头，执行调仓
                    self.rebalance_long_positions(best_data)


    def grading_open_short_function(self, rank):#打分靠后的开空
        rank_sorted=rank.sort_values(by=['Score','Stock'],ascending=[False,True])#按分数排序
        bot_stocks=rank_sorted.iloc[[-1]]#找分最低的
        print(bot_stocks)
        for stock in bot_stocks['Stock']:#获取data对象
            worst_data=None
            for  data in self.datas:
                if data._name==stock:
                    worst_data=data
                    break
            if worst_data:
                size=self.calculate_quantity(self,worst_data)
                #计算开空手数
                pos=self.getposition(worst_data).size#获取持仓
                if pos==0:#没有持仓，直接开空
                    Log.log(self,f'订单创建:开空, {worst_data._name}, Size: {size}, Price: {worst_data.close[0]:.2f}')
                    order=self.sell(data=worst_data,size=size)
                    
                elif pos>0:#持有多头，先平多再开空
                    Log.log(self,f'订单创建:先平多, {worst_data._name}, Size: {pos}, Price: {worst_data.close[0]:.2f}')
                    order=self.close(data=worst_data)
                    
                    Log.log(self,f'订单创建:后开空, {worst_data._name}, Size: {size}, Price: {worst_data.close[0]:.2f}')
                    order=self.sell(data=worst_data,size=size)
                elif pos<0:#本来就持有空头，执行调仓
                    self.rebalance_short_positions(specific_assets=worst_data)

    def grading_close_function(self,rank):#分数靠中间的平仓
        rank_sorted=rank.sort_values(by=['Score','Stock'],ascending=[False,True])#排序
        rank_sorted_cut=rank_sorted.iloc[1:-1]#截取中间的
        print(rank_sorted_cut)
        for stock in rank_sorted_cut['Stock']:#获取data对象
            close_data=None
            for  data in self.datas:
                if data._name==stock:
                    close_data=data
                    break
            if close_data:
                pos=self.getposition(close_data).size
                if pos!=0:#有仓位，就平仓
                    Log.log(self,f'订单创建:平中间分数,{close_data._name},手数,{pos},价格: {close_data.close[0]:.2f}')
                    order=self.close(data=close_data)
    
    def calculate_quantity(self, st:bt.Strategy,line:bt.DataSeries) -> int:
        available_cash=self.cash*0.05
        close_price=line.close[0]
        quantity=int(available_cash/close_price)
        return quantity
    
    def rebalance_long_positions(self,specific_assets):#给多头调仓
        self.target_percent=0.05
        Log.log(self,f"检查现有多头持仓")
        current_value=self.cash#现有权益
        data=specific_assets
        position=self.getposition(data)#现有仓位
        current_price=data.close[0]#今日收盘价
        current_pos_value=position.size*current_price#现有仓位价值
        target_pos_value=current_value*(self.target_percent)#目标仓位价值
        target_pos=int(target_pos_value/current_price)#目标仓位

        Log.log(self,f"{data._name}:现有多头手数:{position.size:.2f},现有多头权益:{current_pos_value:.2f}")
        Log.log(self,f"{data._name}:目标多头手数:{target_pos:.2f},目标多头权益:{target_pos_value:.2f}")

        delta_size=target_pos-position.size#算要加/减多少仓位

        if delta_size>0:#买入增加多头
            Log.log(self,f"买入增加多头:{data._name} 手数 {abs(delta_size):.2f}")
            order=self.buy(data=data,size=delta_size)
            

        elif delta_size<0:#卖出减少多头
            Log.log(self,f"卖出减少多头:{data._name} 手数 {abs(delta_size):.2f}")
            order=self.sell(data=data,size=delta_size)
            

        elif delta_size==0:
            pass

                
    def rebalance_short_positions(self, specific_assets):#给空头调仓
        Log.log(self,f"检查现有空头持仓")  # 记录开始检查空头仓位的日志
        current_value=self.getvalue()  # 获取当前投资组合的总价值
        Log.log(self,f"总权益:{current_value:.2f}")  # 记录当前投资组合的总价值
        # 获取当前持有的所有空头仓位
        data=specific_assets
        position=self.getposition(data)
        current_price=data.close[0]  # 获取当前股票的价格
        current_pos_value=position.size*current_price  # 计算当前仓位的价值
        target_pos_value=current_value*self.target_percent*(-1)  # 计算目标仓位的价值（负数表示空头仓位）
        target_pos=int(target_pos_value/current_price)  # 计算目标仓位的数量
        # 记录当前仓位的信息
        Log.log(self,f"{data._name}:现有空头手数:{abs(position.size):.2f},现有空头权益:{abs(current_pos_value):.2f}")
        # 记录目标仓位的信息
        Log.log(self,f"{data._name}:目标空头手数:{abs(target_pos):.2f},目标空头权益:{abs(target_pos_value):.2f}")
        # 计算需要调整的仓位数量
        delta_size=target_pos-position.size
        # 如果需要减少空头仓位（即买入平仓）
        if delta_size>0:
            Log.log(self,f"买入减少空头:{data._name} 手数 {delta_size:.2f}")
            order=self.buy(data=data,size=delta_size)
            
        elif delta_size<0:
            Log.log(self,f"卖出增加空头:{data._name} for {abs(delta_size):.2f}")
            order=self.sell(data=data,size=delta_size)
            
        # 如果不需要调整仓位
        elif delta_size==0:
            pass


    def allocate_proceeds(self,proceeds,sold_data):#均分策略
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

    def getvalue(self):
        
        value=self.cash
        for data in self.datas:
            value+=abs(data.close[0]*self.getposition(data).size)

        return value
    
    def calculate_contribution(self):
        total_profit=0
        for data in self.datas:
            total_profit+=abs(self.profit[data._name])

        if total_profit!=0:
            for data in self.datas:
                if self.profit[data._name]>=0 and total_profit>0:
                    self.profit_contribution[data._name]=self.profit[data._name]/total_profit
                elif self.profit[data._name]>=0 and total_profit<0:
                    self.profit_contribution[data._name]=abs(self.profit[data._name]/total_profit)
                elif self.profit[data._name]<=0 and total_profit>0:
                    self.profit_contribution[data._name]=(-1)*abs(self.profit[data._name]/total_profit)
                elif self.profit[data._name]<=0 and total_profit<0:
                    self.profit_contribution[data._name]=(-1)*abs(self.profit[data._name]/total_profit)

