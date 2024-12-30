import backtrader as bt

#EMA
class CustomEMA(bt.Indicator):

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
    lines=('sma',)
    params=(
        ('period',None),
    )

    def __init__(self):
        pass

    def next(self):
        lookback_period=len(self)+1
        actual_period=min(self.params.period,lookback_period)
        self.lines.sma[0]=sum(self.data.get(size=actual_period))/actual_period

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
        lowest_price=self.data.get(size=lookback_period)
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
    lines=('TR',)
    params=(
        ('period',None),
    )
    def __init__(self):
        pass

    def __next__(self):
        today_high=self.data0.high[0]
        today_low=self.data0.low[0]
        yesterday_close=self.data0.close[-1]
        max1=max((today_high-today_low),abs(yesterday_close-today_high))
        max2=max(max1,abs(yesterday_close-today_low))
        TR_today=max2
        self.lines.TR[0]=TR_today

#ATR
class ATR(bt.Indicator):
    lines=('ATR',)
    params=(
        ('ATR_period1',None),
        ('ATR_period2',None),
        ('ATR_period3',None),
    )

    def __init__(self):
        self.TR=TR(self.data0)
        self.sma_one=CustomSMA(self.TR,period=self.params.ATR_period1)
        self.sma_two=CustomSMA(self.TR,period=self.params.ATR_period2)
        self.sma_three=CustomSMA(self.TR,period=self.params.ATR_period3)

    def next(self):
        MA1=self.sma_one[0]
        MA2=self.sma_two[0]
        MA3=self.sma_three[0]
        self.lines.ATR[0]=(MA1*0.5)+(MA2*0.2)+(MA3*0.3)