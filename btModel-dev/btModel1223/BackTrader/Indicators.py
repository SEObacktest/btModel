import backtrader as bt
import math
#EMA
class CustomEMA(bt.Indicator):
#测试通过
    lines = ('ema',)
    params = (('period',None ),)


    def __init__(self):
        
        self.alpha = 2 / (self.params.period + 1)
        self.addminperiod(1)  # 从第一天开始计算
        self.first = True  # 标记是否为第一天

    def next(self):
        if self.first:
            # 第一条数据，初始化 EMA26 为当日收盘价
            self.lines.ema[0] = self.data[0]
            self.first = False
        else:
            # 正常的 EMA26 计算
            self.lines.ema[0] = (
                self.alpha * self.data[0] +
                (1 - self.alpha) * self.lines.ema[-1]
            )

#SMA
class CustomSMA(bt.Indicator):
#测试通过
    lines = ('sma',)
    params = (
        ('period', None),
    )

    def __init__(self):
        # 确保周期参数有效
        if self.p.period is None or not isinstance(self.p.period, int) or self.p.period <= 0:
            raise ValueError("period 必须是正整数")
        
        # 设置最小周期为1，这样从第一个数据点就开始计算
        self.addminperiod(1)

    def next(self):
        try:
            # 获取当前可用的数据点数
            available_points = len(self)
            # 使用实际可用的周期数（不超过设定的周期）
            actual_period = min(self.p.period, available_points)
            
            # 计算和
            total = 0.0
            count = 0
            
            # 从最近的数据开始向前累加
            for i in range(actual_period):
                value = self.data[0 - i]  # 使用相对索引
                if not math.isnan(value):
                    total += value
                    count += 1
            
            # 计算平均值
            if count > 0:
                self.lines.sma[0] = total / count
            else:
                # 如果没有有效数据，使用当前值
                self.lines.sma[0] = self.data[0]
                
        except Exception as e:
            # 发生错误时使用当前值
            self.lines.sma[0] = self.data[0]
#n日内最高价
class NDayHigh(bt.Indicator):
    lines=('NDayHigh',)
    
    params=(
        ('period',None),
    )

    def __init__(self):
        pass

    def next(self):
        current_index=len(self)-1
        lookback_period=min(self.params.period,current_index+1)

        highest_price=max(self.data.get(size=lookback_period))
        self.lines.NDayHigh[0]=highest_price

#n日内最低价
class NDayLow(bt.Indicator):
    lines=('NDayLow',)
    params=(
        ('period',None),
    )
    def __init__(self):
        pass

    def next(self):
        current_index=len(self)-1
        lookback_period=min(current_index+1,self.params.period)
        lowest_price=min(self.data.get(size=lookback_period))
        self.lines.NDayLow[0]=lowest_price

#A分形
class K_A(bt.Indicator):
    lines=('K_A',)
    params=(
        ('period',None),
    )
    def __init__(self):
        pass

    def next(self):
        yesterday_open=self.data0.open[-1]
        yesterday_close=self.data0.close[-1]
        today_close=self.data0.close[0]
        
        if today_close<min(yesterday_close,yesterday_open):
            self.lines.K_A[0]=1
        else:
            self.lines.K_A[0]=0

#V分形
class K_V(bt.Indicator):
    lines=('K_V',)
    params=(
        ('period',None),
    )
    def __init__(self):
        pass

    def next(self):
        yesterday_open=self.data0.open[-1]
        yesterday_close=self.data0.close[-1]
        today_close=self.data0.close[0]
        if today_close>min(yesterday_close,yesterday_open):
            self.lines.K_A[0]=1
        else:
            self.lines.K_A[0]=0

#TR
class TR(bt.Indicator):
#测试通过
    lines=('TR',)
    params=(
        ('period',None),

    )
    def __init__(self):
        pass


    def next(self):
        if (self.data.close)<2:
            return

        today_high=self.data.high[0]
        today_low=self.data.low[0]
        yesterday_close=self.data.close[-1]

        max1=max((today_high-today_low),abs(yesterday_close-today_high))
        max2=max(max1,abs(yesterday_close-today_low))
        TR_today=max2
        self.lines.TR[0]=TR_today



#ATR
#输出今天的ATR要用[1]而不是[0],别问,问就是我也不知道
class ATR(bt.Indicator):
#测试通过
    lines = ('ATR',)
    params = (
        ('ATR_period1', None),
        ('ATR_period2', None),
        ('ATR_period3', None),
    )

    def __init__(self):
        self.TR=TR(self.data)
        try:
            self.sma_one=CustomSMA(self.TR.lines.TR,period=self.params.ATR_period1)
            self.sma_two=CustomSMA(self.TR.lines.TR,period=self.params.ATR_period2)
            self.sma_three=CustomSMA(self.TR.lines.TR,period=self.params.ATR_period3)
        except Exception as e:
            print(f"创建SMA时出错: {str(e)}")
            raise

        # 设置最小周期
        #max_period=max(self.params.ATR_period1,self.params.ATR_period2,self.params.ATR_period3)
        #self.addminperiod(max_period)


    def prenext(self):
        self.lines.ATR[0]=0

    def next(self):
        try:
            
            MA1=self.sma_one[0]
            MA2=self.sma_two[0]
            MA3=self.sma_three[0]
            self.lines.ATR[0]=(MA1*0.5)+(MA2*0.2)+(MA3*0.3)
            
        except Exception as e:
            print(f"计算ATR时出错: {str(e)}")
            self.lines.ATR[0] = 0  # 出错时设置默认值

#QUAR1_ATR
class QUAR1_ATR(bt.Indicator):
#测试通过
    lines=('QUAR1_ATR',)
    params=(
        ('ATR_period1',None),
        ('ATR_period2',None),
        ('ATR_period3',None),
    )

    def __init__(self):
        self.ATR=ATR(self.data,ATR_period1=self.params.ATR_period1,
                    ATR_period2=self.params.ATR_period2,
                    ATR_period3=self.params.ATR_period3)

    def next(self):
        today_ATR=self.ATR[0]
        yesterday_ATR=self.ATR[-1]
        if yesterday_ATR!=0:
            today_QUAR1_ATR=(today_ATR-yesterday_ATR)/yesterday_ATR
        else:
            today_QUAR1_ATR=0
        
        self.lines.QUAR1_ATR[0]=today_QUAR1_ATR
#QC
class QC(bt.Indicator):
#测试通过
    lines=('QC',)
    params=(
        ('ATR_period1',None),
        ('ATR_period2',None),
        ('ATR_period3',None),
    )

    def __init__(self):
        self.QUAR1_ATR=QUAR1_ATR(self.data,
            ATR_period1=self.params.ATR_period1,
            ATR_period2=self.params.ATR_period2,
            ATR_period3=self.params.ATR_period3
        )

    def next(self):
        if math.isnan(self.QUAR1_ATR[0]):
            today_QC=0
        else:
            today_QC=1
        self.lines.QC[0]=today_QC

#VOL金叉死叉
class VOL_CROSS(bt.Indicator):
#测试通过
    lines=('VOL_CROSS',)
    params=(
        ('MA_PERIOD1',5),
        ('MA_PERIOD2',20),
    )

    def __init__(self):
        self.VOLMA5=CustomSMA(self.data.volume,period=self.params.MA_PERIOD1)
        self.VOLMA20=CustomSMA(self.data.volume,period=self.params.MA_PERIOD2)
    
    def next(self):
        if self.VOLMA5[-1]<self.VOLMA20[-1] and self.VOLMA5[0]>self.VOLMA20[0]:
            self.lines.VOL_CROSS[0]=1
        elif self.VOLMA5[-1]>self.VOLMA20[-1] and self.VOLMA5[0]<self.VOLMA20[0]:
            self.lines.VOL_CROSS[0]=-1
        else:
            self.lines.VOL_CROSS[0]=0
        #1是金叉，-1是死叉，0是默认

class SCORE(bt.Indicator):
#测试通过
    lines=('SCORE',)
    params=(
        ('MA_PERIOD1',5),
        ('MA_PERIOD2',10),
        ('MA_PERIOD3',20),
        ('MA_PERIOD4',40),
    )

    def __init__(self):
        self.MA5=CustomSMA(self.data.close,period=self.params.MA_PERIOD1)
        self.MA10=CustomSMA(self.data.close,period=self.params.MA_PERIOD2)
        self.MA20=CustomSMA(self.data.close,period=self.params.MA_PERIOD3)
        self.MA40=CustomSMA(self.data.close,period=self.params.MA_PERIOD4)
        self.VOL_CROSS=VOL_CROSS(self.data)
    def next(self):
        MA5=self.MA5[0]
        MA10=self.MA10[0]
        MA20=self.MA20[0]
        MA40=self.MA40[0]
        SCORE=0
        if MA5 > MA10 and MA10 > MA20 and MA40 > MA20:
            # C1: MA5 > MA10 AND MA10 > MA20 AND MA40 > MA20
            SCORE=24
        elif MA10 > MA5 and MA5 > MA40 and MA40 > MA20:
            # C2: MA10 > MA5 AND MA5 > MA40 AND MA40 > MA20
            SCORE=23
        elif MA40 > MA10 and MA10 > MA5 and MA5 > MA20:
            # C3: MA40 > MA10 AND MA10 > MA5 AND MA5 > MA20
            SCORE=22
        elif MA5 > MA20 and MA20 > MA40 and MA40 > MA10:
            # C4: MA5 > MA20 AND MA20 > MA40 AND MA40 > MA10
            SCORE=21
        elif MA5 > MA10 and MA10 > MA20 and MA20 > MA40:
            # C5: MA5 > MA10 AND MA10 > MA20 AND MA20 > MA40
            SCORE=20
        elif MA10 > MA5 and MA5 > MA20 and MA20 > MA40:
            # C6: MA10 > MA5 AND MA5 > MA20 AND MA20 > MA40
            SCORE=19
        elif MA5 > MA20 and MA20 > MA10 and MA10 > MA40:
            # C7: MA5 > MA20 AND MA20 > MA10 AND MA10 > MA40
            SCORE=18
        elif MA40 > MA5 and MA5 > MA20 and MA20 > MA10:
            # C8: MA40 > MA5 AND MA5 > MA20 AND MA20 > MA10
            SCORE=17
        elif MA20 > MA10 and MA10 > MA5 and MA5 > MA40:
            # C9: MA20 > MA10 AND MA10 > MA5 AND MA5 > MA40
            SCORE=16
        elif MA5 > MA40 and MA40 > MA10 and MA10 > MA20:
            # C10: MA5 > MA40 AND MA40 > MA10 AND MA10 > MA20
            SCORE=15
        elif MA20 > MA40 and MA40 > MA5 and MA5 > MA10:
            # C11: MA20 > MA40 AND MA40 > MA5 AND MA5 > MA10
            SCORE=14
        elif MA5 > MA40 and MA40 > MA20 and MA20 > MA10:
            # C12: MA5 > MA40 AND MA40 > MA20 AND MA20 > MA10
            SCORE=13
        elif MA40 > MA10 and MA10 > MA20 and MA20 > MA5:
            # C13: MA40 > MA10 AND MA10 > MA20 AND MA20 > MA5
            SCORE=12
        elif MA10 > MA40 and MA40 > MA20 and MA20 > MA5:
            # C14: MA10 > MA40 AND MA40 > MA20 AND MA20 > MA5
            SCORE=11
        elif MA40 > MA5 and MA5 > MA10 and MA10 > MA20:
            # C15: MA40 > MA5 AND MA5 > MA10 AND MA10 > MA20
            SCORE=10
        elif MA10 > MA20 and MA20 > MA5 and MA5 > MA40:
            # C16: MA10 > MA20 AND MA20 > MA5 AND MA5 > MA40
             SCORE=9
        elif MA20 > MA40 and MA40 > MA10 and MA10 > MA5:
            # C17: MA20 > MA40 AND MA40 > MA10 AND MA10 > MA5
             SCORE=8
        elif MA40 > MA20 and MA20 > MA5 and MA5 > MA10:
            # C18: MA40 > MA20 AND MA20 > MA5 AND MA5 > MA10
            SCORE=7
        elif MA10 > MA20 and MA20 > MA40 and MA40 > MA5:
            # C19: MA10 > MA20 AND MA20 > MA40 AND MA40 > MA5
            SCORE=6
        elif MA10 > MA40 and MA40 > MA5 and MA5 > MA20:
            # C20: MA10 > MA40 AND MA40 > MA5 AND MA5 > MA20
            SCORE=5
        elif MA20 > MA5 and MA5 > MA40 and MA40 > MA10:
            # C21: MA20 > MA5 AND MA5 > MA40 AND MA40 > MA10
            SCORE=4
        elif MA20 > MA5 and MA5 > MA10 and MA10 > MA40:
            # C22: MA20 > MA5 AND MA5 > MA10 AND MA10 > MA40
            SCORE=3
        elif MA20 > MA10 and MA10 > MA40 and MA40 > MA5:
            # C23: MA20 > MA10 AND MA10 > MA40 AND MA40 > MA5
            SCORE=2
        elif MA40 > MA20 and MA20 > MA10 and MA10 > MA5:
            # C24: MA40 > MA20 AND MA20 > MA10 AND MA10 > MA5
            SCORE=1

        if self.VOL_CROSS[0]==1:
            SCORE+=1
        elif self.VOL_CROSS[0]==-1:
            SCORE-=1
        else:
            pass
        self.lines.SCORE[0]=SCORE