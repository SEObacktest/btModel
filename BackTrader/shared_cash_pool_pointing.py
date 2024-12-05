import backtrader as bt
from backtrader.indicators import *
import backtrader as bt
from backtrader.indicators import *
from strategies import SharedLogic
from tools import Log 
import pandas as pd
import Indicators
import datetime
class Shared_Cash_Pool_Pointing(bt.Strategy):
    #初始化参数，这些参数在策略被实例化的实话会重新通过实参传入
    params = (
        ('backtest_start_date', None),
        ('backtest_end_date', None),
        ('EMA26',None),
        ('EMA12',None),
        ('EMA9',None),
    )

    def __init__(self):
        #各种打分用的指标
        columns = ['时间', '合约名', '信号', '单价', '手数', '总价', '手续费', '可用资金','开仓均价']
        self.num_of_trade=0#总交易次数
        self.log=dict()#在同一笔交易上记录信息
        self.info=pd.DataFrame(columns=columns)#记录总的订单信息，信号明细
        self.info.index=range(1,len(self.info)+1)
        self.init_cash=100000000#初始资金
        self.cash=100000000#初始资金
        self.DIFF=dict()#MACD策略当中的DIFF指标
        self.MACD=dict()#MACD策略当中的MACD指标
        self.notify_flag=1#控制订单打印的BOOL变量
        self.profit=dict()#分品类保存利润的字典
        self.profit_contribution=dict()#分品类保存利润贡献度的字典
        self.EMA26=dict()#分品类保存26日均线
        self.EMA12=dict()#分品类保存12日均线
        self.DEA=dict()#MACD策略当中的DEA指标
        self.target_percent=0.05#调整仓位的比例
        self.start_date=dict()
        self.first_date=dict()
        self.current_date=2000-1-1
        self.order_list=dict()#订单记录
        self.paper_profit=dict()
        self.average_open_cost=dict()

        for data in self.datas:#每个品类都需要初始化一次
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
            self.paper_profit[data]=0
            self.log[data]=0
            self.average_open_cost[data]=0

    def prenext(self):
        #prenext模块，这个模块用来执行当“只有部分品种有数据”的时候的回测。
        #举个例子，A品种从1月1号开始有数据，B品种从3月1号开始有数据。
        #回测从1月1号开始，我们当然希望从1月1号开始先回测A品种，等3月1号开始
        #再把B品种加进来，这种有数据断层的时间我们就要通过prenext来执行

        current_date = self.datetime.date(0)#获取回测当天的时间(模拟时间)
        #如果模拟时间在回测区间内
        if self.params.backtest_start_date <= current_date <= self.params.backtest_end_date:
            self.shared_cash_pointing_prenext()#执行具体的策略
            for data in self.datas:#遍历每个品种
                #这一行目前有争议，逻辑不清，但是可以实现功能，先保留
                if current_date>=self.getdatabyname(data._name).datetime.date(0):
                    Log.log(self,f'{data._name}的收盘价:{data.close[0]}')
                    Log.log(self,f'{data._name}的指标,EMA26:{self.EMA26[data][0]},')
                    Log.log(self,f'{data._name}的指标,EMA12:{self.EMA12[data][0]},')
                    Log.log(self,f'{data._name}的指标,DIFF:{self.DIFF[data][0]},')
                    Log.log(self,f'{data._name}的指标,DEA:{self.DEA[data][0]},')
                    Log.log(self,f'{data._name}的指标,MACD:{self.MACD[data][0]},')
                    #输出各种指标
            Log.log(self,f'今天的可用资金:{self.cash}')
            #Log.log(self,f'今天的可用资金:{self.broker.get_cash()}')
            print(self.profit)
            Log.log(self,f'今天的权益:{self.getvalue()}')
            #Log.log(self,f'今天的权益:{self.broker.get_value()}')

    def next(self):
        #next模块，接上面的例子，从3月1号开始A和B都有数据了，那么就开始执行next模块
        #prenext模块和next模块是循环执行的，这个策略是日线模型，那么就是每天执行一次

        self.current_date = self.datas[0].datetime.date(0)
        #获取模拟时间

        if self.params.backtest_start_date <= self.current_date <= self.params.backtest_end_date:
            #同上
            self.shared_cash_pointing()#执行策略
            #同上
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
                    #持仓权益：仓位(手数)*当天收盘价
                    Log.log(self,f'{data._name}的权益:{abs(hold_equity)}')
                    #同上
                #else:
                    #continue
            Log.log(self,f'今天的可用资金:{self.cash}')
            #Log.log(self,f'今天的可用资金:{self.broker.get_cash()}')
            print(self.profit)
            Log.log(self,f'今天的权益:{self.getvalue()}')
            #Log.log(self,f'今天的权益:{self.broker.get_value()}')

    def stop(self):
        #stop模块，在最后一天结束后执行，整个回测过程只执行一次
        #最后一天结束后，把持仓品类的权益释放出来加到各个品种利润上面
        #考虑我们计算每个品种利润的方式，初始的时候，利润是0，如果有开仓，就减掉开仓成本，如果有
        #平仓，就加上平仓收益，由于到了最后一天可能上一笔开仓未平，我们要把这最后一笔开仓成本
        #通过当天(最后一天)的收盘价释放出来，实际上就是一个模拟平仓的过程
        for data in self.datas:#遍历所有品种
            if self.getposition(data).size!=0:#如果有持仓
                self.profit[data._name]+=abs(self.getposition(data).size)*abs(data.close[0])
                #调整利润
        self.calculate_contribution()
        #计算各个品种对于总利润的贡献
        
        Log.log(self,f"期初权益:{self.init_cash},{self.params.EMA26},{self.params.EMA12},{self.params.EMA9},{self.params.backtest_start_date},{self.params.backtest_end_date}",dt=self.params.backtest_end_date)

        Log.log(self,f"期末权益:{self.broker.get_value()},{self.params.EMA26},{self.params.EMA12},{self.params.EMA9},{self.params.backtest_start_date},{self.params.backtest_end_date}",dt=self.params.backtest_end_date)

        print(self.profit)
        print(self.profit_contribution)
        self.info.to_csv('signal_info.csv',index=True,mode='w',encoding='utf-8')


    def notify_order(self,order):
        #在一笔订单完成后输出有关于这笔订单的信息，这部分也可参照BackTrader源文档，因为写法基本固定
        if self.notify_flag:#控制订单打印的BOOL变量为真
            flag=0
            data=order.data#获取这笔订单对应的品类
            current_time=self.datetime.date(0)#时间
            dataname=order.data._name#合约名称
            unit_price=order.executed.price#单价
            trade_nums=order.executed.size#手数
            #trade_value=order.executed.value#总价
            trade_value=order.margin
            trade_comm=order.executed.comm
            trade_type=None
            available_cash=self.broker.get_cash()
            total_value=self.broker.get_value()
            if order is None:
                Log.log(self,f'Receive a none order')
                return
            if order.status in [order.Submitted, order.Accepted]:
                return
            if order.status in [order.Completed]:
                
                if order.isbuy():#如果是买单，注意买单分四种：开多/加多/平空/减空

                    Log.log(self,
                    f"订单完成:买单,{data._name}, 手数:{(order.executed.size)},"
                    f"每手价格:{order.executed.price:.2f},"
                    f"总价格:{(order.executed.value):.2f},"
                    f"手续费:{order.executed.comm:.2f},"
                    f"该品种现有持仓:{self.getposition(data).size}"
                    )
                    self.order_list[data].append(self.getposition(data).size)
                    #order_list[data]记载了data这个品类每笔交易上持仓数量的变化
                    #方便我们判断开平仓
                    #注意在BackTrader系统当中，空头的持仓为负数
                    if self.order_list[data][-1]>0 and self.order_list[data][-2]>=0 and self.order_list[data][-1]>self.order_list[data][-2]:
                    #如果现在和这笔订单完成之前，持仓都为正，且现在比之前更大，那么就是开多仓/加多仓
                        #self.cashflow(data,-1,order)#调整可用现金
                        #available_cash=self.cash#调整后获取现金
                        #total_value=self.broker.get_value()
                        if self.order_list[data][-2]==0:#开多仓
                            trade_type="开多仓"
                            self.log[data]=self.log[data]+abs(order.executed.price)*abs(order.executed.size)
                            #统计开仓总成本
                            self.paper_profit[data]=0
                            self.paper_profit[data]-=(abs(order.executed.value)+abs(order.executed.comm))
                            self.cash-=(abs(order.executed.value)+abs(order.executed.comm))
                            #可用资金(现金)的变化:要减掉交出的保证金和手续费
                            #记录浮盈
                            self.average_open_cost[data]=abs(self.log[data]/(self.getposition(data).size))
                            #在该订单执行完毕后，更新此笔交易的平均开仓成本(以收盘价计)
                            #注意这里不要以保证金计，要用收盘价计
                        else:
                            trade_type="加多仓"
                            self.log[data]=self.log[data]+abs(order.executed.price)*abs(order.executed.size)
                            #增加成本
                            self.paper_profit[data]-=(abs(order.executed.value)+abs(order.executed.comm))
                            #记录浮盈
                            self.average_open_cost[data]=abs(self.log[data]/(self.getposition(data).size))
                            self.cash-=(abs(order.executed.value)+abs(order.executed.comm))
                            #可用资金(现金)的变化:要减掉交出的保证金和手续费
                            #在该订单执行完毕后，更新此笔交易的平均开仓成本(以收盘价计)

                    if self.order_list[data][-1]<=0 and self.order_list[data][-2]<0 and self.order_list[data][-1]>self.order_list[data][-2]:
                    #如果现在和这笔订单完成之前，持仓都为负，且现在比之前更大，那么就是平空仓/减空仓
                        #self.cashflow(data,1,order)#调整可用现金
                        #available_cash=self.cash#调整后获取现金
                        #total_value=self.broker.get_value()
                        if self.order_list[data][-1]==0:#平空仓
                            trade_type="平空仓"
                            self.paper_profit[data]=self.paper_profit[data]+abs(order.executed.value)-order.executed.comm
                            #记录浮盈
                            self.cash=self.cash+abs(order.executed.value)
                            #可用现金要加上退回来的保证金
                            self.cash=self.cash-abs(order.executed.comm)
                            #减掉手续费
                            if data.close[0]<self.average_open_cost[data]:
                            #如果现在的收盘价小于平均开仓成本，说明空头盈利
                                self.cash+=abs(order.executed.size)*abs(data.close[0]-self.average_open_cost[data])
                                #盈利额=手数*|(收盘价-平均开仓成本)|
                            else:
                            #如果现在的收盘价大于等于平均开仓成本，说明空头亏损(至少是不盈利)
                                self.cash-=abs(order.executed.size)*abs(data.close[0]-self.average_open_cost[data])
                                #亏损额=手数*|(收盘价-平均开仓成本)|
                            flag=1#平仓之后要把总成本和平均持仓成本全部变成0

                        else:
                            trade_type="减空仓"
                            self.paper_profit[data]=self.paper_profit[data]+abs(order.executed.value)-order.executed.comm
                            self.cash=self.cash+abs(order.executed.value)
                            #可用现金要加上退回来的保证金
                            self.cash=self.cash-abs(order.executed.comm)
                            #减去手续费
                            self.log[data]=self.log[data]-abs(order.executed.size)*self.average_open_cost[data]
                            #减仓时候要把减的那些手的开仓成本从总成本当中去掉
                            if data.close[0]<self.average_open_cost[data]:
                                #如果现在的收盘价小于平均开仓成本，说明空头盈利
                                self.cash+=abs(order.executed.size)*abs(data.close[0]-self.average_open_cost[data])
                                #盈利额=手数*|(收盘价-平均开仓成本)|
                            else:
                            #如果现在的收盘价大于等于平均开仓成本，说明空头亏损(至少是不盈利)
                                self.cash-=abs(order.executed.size)*abs(data.close[0]-self.average_open_cost[data])
                                #亏损额=手数*|(收盘价-平均开仓成本)|


                    #观察日志，发现手数和金额同号的时候是开/加仓，反之是平/减仓
                    #if (order.executed.size*order.executed.value)>0:
                        #self.cashflow(data,-1,order)
                        
                    #elif (order.executed.size*order.executed.value)<0:
                        #self.cashflow(data,1,order)
                    

                
                elif order.issell():#卖单的情况，同上
                    Log.log(self,
                    f"订单完成:卖单,{data._name},手数:{(order.executed.size)},"
                    f"每手价格:{order.executed.price:.2f},"
                    f"总价格:{(order.executed.value):.2f},"
                    f"手续费:{order.executed.comm:.2f},"
                    f"该品种现有持仓:{self.getposition(data).size}"
                    )
                    self.order_list[data].append(self.getposition(data).size)
                    if self.order_list[data][-1]>=0 and self.order_list[data][-2]>0 and self.order_list[data][-1]<self.order_list[data][-2]:
                        #self.cashflow(data,1,order)#平多仓/减多仓
                        #available_cash=self.cash#调整后获取现金
                        #total_value=self.broker.get_value()
                        if self.order_list[data][-1]==0:#平多仓
                            trade_type="平多仓"
                            self.paper_profit[data]=self.paper_profit[data]+abs(order.executed.value)-order.executed.comm
                            #记录浮盈
                            self.cash+=abs(order.executed.value)#现金要加上退回来的保证金
                            self.cash=self.cash-abs(order.executed.comm)
                            #减去手续费
                            if self.average_open_cost[data]<data.close[0]:#如果平均开仓成本<收盘价，说明多头盈利
                                self.cash+=abs(order.executed.size)*abs(data.close[0]-self.average_open_cost[data])
                                #盈利额=手数*|(收盘价-平均开仓成本)|
                            else:#如果平均开仓成本>=收盘价，说明多头不盈利
                                self.cash-=abs(order.executed.size)*abs(data.close[0]-self.average_open_cost[data])
                                #亏损额=手数*|(收盘价-平均开仓成本)|
                            flag=1#平仓之后要把总成本和平均持仓成本全部变成0

                        else:
                            trade_type="减多仓"
                            self.log[data]=self.log[data]-abs(order.executed.size)*self.average_open_cost[data]
                            #注意：减多仓要把减的那些手的开仓成本去掉，不然影响后面的计算
                            self.paper_profit[data]=self.paper_profit[data]+abs(order.executed.value)-order.executed.comm
                            #记录浮盈
                            self.cash+=abs(order.executed.value)#现金要加上退回来的保证金
                            self.cash=self.cash-abs(order.executed.comm)
                            #减去手续费
                            if self.average_open_cost[data]<data.close[0]:#如果平均开仓成本<收盘价，说明多头盈利
                                self.cash+=abs(order.executed.size)*abs(data.close[0]-self.average_open_cost[data])
                                #盈利额=手数*|(收盘价-平均开仓成本)|
                            else:#如果平均开仓成本>=收盘价，说明多头不盈利
                                self.cash-=abs(order.executed.size)*abs(data.close[0]-self.average_open_cost[data])
                                #亏损额=手数*|(收盘价-平均开仓成本)|


                    if self.order_list[data][-1]<0 and self.order_list[data][-2]<=0 and self.order_list[data][-1]<self.order_list[data][-2]:
                        #self.cashflow(data,-1,order)#开空仓/加空仓
                        #available_cash=self.cash#调整后获取现金
                        #total_value=self.broker.get_value()
                        if self.order_list[data][-2]==0:
                            trade_type="开空仓"
                            self.log[data]=self.log[data]+abs(order.executed.price)*abs(order.executed.size)
                            self.average_open_cost[data]=abs(self.log[data]/(self.getposition(data).size))
                            self.paper_profit[data]-=(abs(order.executed.value)+abs(order.executed.comm))
                            self.cash-=(abs(order.executed.value)+abs(order.executed.comm))
                            #可用资金(现金)的变化:要减掉交出的保证金和手续费
                            #记录浮盈
                            #在该订单执行完毕后，更新此笔交易的平均开仓成本(以收盘价计)
                            #注意这里不要以保证金计，要用收盘价计
                        else:
                            trade_type="加空仓"
                            self.log[data]=self.log[data]+abs(order.executed.price)*abs(order.executed.size)
                            #
                            self.average_open_cost[data]=abs(self.log[data]/(self.getposition(data).size))
                            self.paper_profit[data]-=(abs(order.executed.value)+abs(order.executed.comm))
                            self.cash-=(abs(order.executed.value)+abs(order.executed.comm))


                    #观察日志，发现手数和金额同号的时候是开/加仓，反之是平/减仓
                    #if (order.executed.size*order.executed.value)>0:
                        #self.cashflow(data,-1,order)
                        
                    #elif (order.executed.size*order.executed.value)<0:
                        #self.cashflow(data,1,order)

                self.info.loc[self.num_of_trade]=[current_time,dataname,trade_type,unit_price,trade_nums,trade_value,trade_comm,self.cash,self.average_open_cost[data]]
                self.num_of_trade+=1#交易次数+1
                if flag==1:
                    self.log[data]=0
                    self.average_open_cost[data]=0

    def cashflow(self,data,symbol,order):
        #通过订单和品类，改变字典中这个品类的利润
        if symbol==1:#symbol用来判断是开/平，从而确定利润改变的方向：增/减
            self.profit[data._name]=self.profit[data._name]+abs(order.executed.value)
            self.profit[data._name]=self.profit[data._name]-abs(order.executed.comm)
            #通过executed.value来加减利润
            Log.log(self,f'品类:{data._name}的利润增加额:{abs(order.executed.value)}')
            self.cash=self.cash+abs(order.executed.value)
            self.cash=self.cash-abs(order.executed.comm)
        elif symbol==-1:
            self.profit[data._name]=self.profit[data._name]-abs(order.executed.value)
            self.profit[data._name]=self.profit[data._name]-abs(order.executed.comm)
            Log.log(self,f'品类:{data._name}的利润减少额:{abs(order.executed.value)}')
            self.cash=self.cash-abs(order.executed.value)
            self.cash=self.cash-abs(order.executed.comm)


    def shared_cash_pointing(self):#具体的策略（打分方式是随便写的）
        self.point=dict()#字典当打分表，记录每个品种的打分情况
        current_date=self.datetime.date(0)
        for data in self.datas:#满足一个指标就加一分
            #if current_date>self.getdatabyname(data._name).datetime.date(0):  
            if 1:
                self.point[data._name]=0
                if round(self.DIFF[data][0],2)>round(self.DEA[data][0],2) and round(self.DIFF[data][-1],2)<=round(self.DEA[data][-1],2):
                    #MACD金叉，加三分
                    self.point[data._name]+=3
                if round(self.MACD[data][0],2)>round(self.MACD[data][-1],2):
                    #MACD值比上一个交易日大，加两分
                    self.point[data._name]+=2
                if round(self.MACD[data][0],2)>0:
                    #MACD值大于0，加一分
                    self.point[data._name]+=1

                if round(self.DIFF[data][0],2)<=round(self.DEA[data][0],2) and round(self.DIFF[data][-1],2)>round(self.DEA[data][-1],2):
                    #MACD死叉，减三分
                    self.point[data._name]-=3
                if round(self.MACD[data][0],2)<=round(self.MACD[data][-1],2):
                    #MACD值比上一个交易日小，减两分
                    self.point[data._name]-=2
                if round(self.MACD[data][0],2)<=0:
                    #MACD值大于0，减少一分
                    self.point[data._name]-=1

                if self.EMA26[data][0]>2:
                    #修正项，如果26日均线>2就加一分
                    self.point[data._name]+=1

        scores_df=pd.DataFrame(list(self.point.items()),columns=['Stock','Score'])#记录打分表
        if len(scores_df)>=2:#至少要有两个品种这个共享回测才有意义
        #if 1:
            self.grading_open_long_function(scores_df)
        #分高的执行开多
            self.grading_open_short_function(scores_df)
        #分低的执行开空
            self.grading_close_function(scores_df)
        #中间的平仓'''
        

    def shared_cash_pointing_prenext(self):#具体的策略（打分方式是随便写的）
        #这个是专门给prenext模块用的，逻辑和上面的一样
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
        #计算手数，手数=可用资金*0.05/当日收盘价
        available_cash=self.broker.get_cash()*0.05
        close_price=line.close[0]
        quantity=int(available_cash/close_price)
        return quantity
    
    def rebalance_long_positions(self,specific_assets):#给多头调仓
        #保证我们的每个品种多头权益(如果他是多头的话)始终占总权益的5%
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
        #同上
        Log.log(self,f"检查现有空头持仓")  # 记录开始检查空头仓位的日志
        current_value=self.broker.get_value()  # 获取当前投资组合的总价值
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
        #老版本的策略，可以忽略
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
        #很粗糙的自己写的一个getvalue方法，权益=可用现金+所有品种持仓权益
        value=self.cash
        for data in self.datas:
            value+=abs(data.close[0]*self.getposition(data).size)

        return value
    
    def calculate_contribution(self):
        #计算品种贡献度，其实就是每个品种的利润/总利润(注意下正负号就行)
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


    def cal_next_bar_is_last_trading_day(self,data):
        try:
            next_next_close = data.close[2]
        except IndexError:
            return True
        except:
            print("something else error")
        return False
    
    def last_trading_day(self,data):
        try:
            next_close=data.close[1]
        except IndexError:
            return True
        except:
            print("something else error")
        return False

    def close_all_position(self):#全平
        for data in self.datas:
            self.close(data=data)