import numpy as np
import pandas as pd
import tushare as ts
import time
from backtrader.analyzers import *
from backtrader.indicators import *
from backtrader_plotting import Bokeh
from backtrader_plotting.schemes import Tradimo
import datetime
import optunity


# =============== 数据获取与处理类 ==================

class DataGet:
    @staticmethod
    def get_str_date_from_int(date_int):
        try:
            date_int = int(date_int)
        except ValueError:
            date_int = int(date_int.replace("-", ""))
        year = date_int // 10000
        month = (date_int % 10000) // 100
        day = date_int % 100

        return "%d-%02d-%02d" % (year, month, day)

    @staticmethod
    def get_date_from_int(date_int):
        date_str = DataGet.get_str_date_from_int(date_int)

        return datetime.datetime.strptime(date_str, "%Y-%m-%d").date()

    @staticmethod
    def login_ts():
        token = '7c15d8db9ccc0383e40eb7487930fa9eb88eaca08573fe1da440aa54'
        ts.set_token(token)
        pro = ts.pro_api(token)
        return pro

    @staticmethod
    def get_data(codes, cerebro, start_date, end_date):
        pro = DataGet.login_ts()
        code_list = codes
        if not isinstance(codes, list):
            code_list = codes.split()
        else:
            pass
        # 加载数据
        for code in code_list:
            df = pro.daily(ts_code=f"{code}", start_date=start_date, end_date=end_date)  # 获取期货数据
            df['trade_date'] = pd.to_datetime(df['trade_date'])
            df.set_index('trade_date', inplace=True)
            df['openinterest'] = 0
            df = df[['open', 'high', 'low', 'close', 'vol', 'openinterest']].rename(columns={'vol': 'volume'})
            df = df.sort_index()
            data = bt.feeds.PandasData(dataname=df)
            cerebro.adddata(data, name=code)


# =============== 回测控制类 ==================


class BackTest:
    @staticmethod
    def batch_test(symbol_list, start_date, end_date):
        for symbol in symbol_list:
            cerebro = bt.Cerebro()
            BackTestSetup.set_cerebro(cerebro=cerebro, opt_judge=False)
            cerebro.addstrategy(Solo_cash_pool)
            DataGet.get_data(codes=symbol, cerebro=cerebro, start_date=start_date, end_date=end_date)
            strat = cerebro.run()[0]
            print("========独立资金池批量回测========")
            print(f"品种：{symbol}")
            print(f"回测区间：{DataGet.get_date_from_int(start_date)}至{DataGet.get_date_from_int(end_date)}")
            DataIO.text_report(cerebro=cerebro, strat=strat)
            print("========独立资金池批量回测========")
            pic = Bokeh(style='bar', plot_mode='single', scheme=Tradimo())
            cerebro.plot(pic)

    @staticmethod
    def shared_cash_test(symbol_list, start_date, end_date):
        cerebro = bt.Cerebro()
        BackTestSetup.set_cerebro(cerebro=cerebro, opt_judge=False)
        cerebro.addstrategy(Shared_cash_pool)
        DataGet.get_data(cerebro=cerebro, codes=symbol_list, start_date=start_date, end_date=end_date)
        strat = cerebro.run()[0]
        print("========共享资金池组合回测========")
        print(f"品种：{symbol_list}")
        print(f"回测区间：{DataGet.get_date_from_int(start_date)}至{DataGet.get_date_from_int(end_date)}")
        DataIO.text_report(cerebro=cerebro, strat=strat)
        print("========共享资金池组合回测========")
        pic = Bokeh(style='bar', plot_mode='single', scheme=Tradimo())
        cerebro.plot(pic)


# =============== 共享资金池策略类 ==================

class Shared_cash_pool(bt.Strategy):

    def __init__(self):
        # 在这里添加并初始化需要使用的指标类

        self.sma5 = dict()
        self.ema15 = dict()
        self.bolling_top = dict()
        self.bolling_bot = dict()
        self.notify_flag = 0
        for index, data in enumerate(self.datas):
            c = data.close
            self.sma5[data] = MovingAverageSimple(c)
            self.ema15[data] = ExponentialMovingAverage(c)
            self.bolling_top[data] = bt.indicators.BollingerBands(c, period=20).top
            self.bolling_bot[data] = bt.indicators.BollingerBands(c, period=20).bot

    def next(self):
        self.shared_cash()

    def notify_order(self, order):  # 固定写法，查看订单情况
        if self.notify_flag:
            # 查看订单情况
            if order.status in [order.Submitted, order.Accepted]:  # 接受订单交易，正常情况
                return
            if order.status in [order.Completed]:
                if order.isbuy():
                    print(f"已买入:{self.data._name}")
                    print(f"数量: {order.executed.size}")
                    print(f"买入价格: {order.executed.price}")
                    print(f"价值: {order.executed.value}")
                elif order.issell():
                    print(f"已卖出:{self.data._name}")
                    print(f"数量: {order.executed.size}")
                    print(f"卖出价格: {order.executed.price}")
                    print(f"价值: {order.executed.value}")
            elif order.status is order.Canceled:
                print('订单取消')
            elif order.status is order.Rejected:
                print('金额不足拒绝交易')
            elif order.status is order.Margin:
                print('保证金不足')
        else:
            pass

    # 共享资金池组合回测
    def shared_cash(self):
        for data in self.datas:
            size = self.calculate_quantity(data)

            self.buy_function(line=data, size=size)
            self.sell_function(line=data, size=size)

    def buy_function(self, line, size):
        close_over_sma = line.close > self.sma5[line][0]
        close_over_ema = line.close > self.ema15[line][0]
        sma_ema_diff = self.sma5[line][0] - self.ema15[line][0]
        buy_cond = (close_over_sma and close_over_ema and sma_ema_diff > 0) or line.close == self.bolling_top[line][0]

        # 这里最后要被替换成直接调用策略类，外部传入
        if buy_cond and self.broker.get_value() > 0:
            '''
            满足策略条件，则进行买入
            '''
            buy_order = self.buy(data=line, size=size)
            return buy_order
        else:
            pass

    def sell_function(self, line, size):
        sell_cond = line.close < self.sma5[line]
        # 这里最后要被替换成直接调用策略类，外部传入
        if sell_cond and self.getposition(line):  # 获取当前的总资金:
            '''
            满足策略条件，则进行卖出
            '''
            sell_order = self.close(data=line, size=size)
            return sell_order
        else:
            pass

    def calculate_quantity(self, line) -> int:
        # 在这里根据策略的逻辑计算交易数量
        # 返回一个整数表示交易数量
        total_value = self.broker.get_value()  # 获取当前的总资金
        available_value = total_value * 0.05  # 可用资金为总资金的5%
        close_price = line.close[0]  # 当前品种的收盘价
        quantity = int(available_value / close_price)  # 计算交易数量，取整数

        return quantity

    def print_position(self, line) -> None:
        pos = self.getposition(line)
        print(f"品种: {line._name} 的当前仓位: {pos.size} @price: {pos.price}")


# =============== 独立资金池策略类 ==================

class Solo_cash_pool(bt.Strategy):

    def __init__(self):
        # 在这里添加并初始化需要使用的指标类
        self.indicatordict = dict()
        self.notify_flag = 0
        self.indicatordict['SMA5'] = MovingAverageSimple()
        self.indicatordict['EMA15'] = ExponentialMovingAverage()
        self.indicatordict['MA30'] = MovingAverage()
        self.indicatordict['MACD'] = MACDHisto()

    def next(self):
        self.solo_cash()

    def notify_order(self, order):  # 固定写法，查看订单情况
        if self.notify_flag:
            # 查看订单情况
            if order.status in [order.Submitted, order.Accepted]:  # 接受订单交易，正常情况
                return
            if order.status in [order.Completed]:
                if order.isbuy():
                    print(f"已买入:{self.data._name}")
                    print(f"数量: {order.executed.size}")
                    print(f"买入价格: {order.executed.price}")
                    print(f"价值: {order.executed.value}")
                elif order.issell():
                    print(f"已卖出:{self.data._name}")
                    print(f"数量: {order.executed.size}")
                    print(f"卖出价格: {order.executed.price}")
                    print(f"价值: {order.executed.value}")
            elif order.status is order.Canceled:
                print('订单取消')
            elif order.status is order.Rejected:
                print('金额不足拒绝交易')
            elif order.status is order.Margin:
                print('保证金不足')
        else:
            pass

    def solo_cash(self):
        size = self.calculate_quantity(self.datas[0])
        self.buy_function(size=size)
        self.sell_function()

    def buy_function(self, size):
        close_over_sma = self.datas[0].close > self.indicatordict['SMA5'][0]
        close_over_ema = self.datas[0].close > self.indicatordict['EMA15'][0]
        sma_ema_diff = self.indicatordict['SMA5'][0] - self.indicatordict['EMA15'][0]
        buy_cond = (close_over_sma or close_over_ema and sma_ema_diff > 0)

        if buy_cond and self.broker.get_value() > 0:
            '''
            满足策略条件，则进行买入
            '''
            buy_order = self.buy(size=size)
            return buy_order
        else:
            pass

    def sell_function(self):
        sell_cond = self.datas[0].close < self.indicatordict['SMA5'][0]

        if sell_cond and self.getposition():
            '''
            满足策略条件，则进行卖出
            '''
            sell_order = self.close()
            return sell_order
        else:
            pass

    def calculate_quantity(self, data) -> int:
        # 在这里根据策略的逻辑计算交易数量
        # 返回一个整数表示交易数量

        total_value = self.broker.get_value()  # 获取当前的总资金
        available_value = total_value * 0.05  # 可用资金为总资金的5%
        close_price = data.close[0]  # 当前品种的收盘价
        quantity = int(available_value / close_price)  # 计算交易数量，取整数
        return quantity

    def print_position(self, line) -> None:
        pos = self.getposition(line)
        print(f"品种: {line._name} 的当前仓位: {pos.size} @price: {pos.price}")


# =============== 策略参数优化共享资金池策略类 ==================


class OptSharedCash(bt.Strategy):
    params = dict(N1=10, N2=20)

    def __init__(self):
        # 在这里添加并初始化需要使用的指标类

        self.sma5 = dict()
        self.ema15 = dict()
        self.ma30 = dict()
        self.bolling_top = dict()
        self.bolling_bot = dict()
        self.notify_flag = 0
        for index, data in enumerate(self.datas):
            c = data.close
            self.sma5[data] = MovingAverageSimple(c, period=int(self.p.N1))
            self.ema15[data] = ExponentialMovingAverage(c, period=int(self.p.N2))
            self.ma30[data] = MovingAverage(c)
            self.bolling_top[data] = bt.indicators.BollingerBands(c, period=20).top
            self.bolling_bot[data] = bt.indicators.BollingerBands(c, period=20).bot

    def next(self):
        self.shared_cash()

    def notify_order(self, order):  # 固定写法，查看订单情况
        if self.notify_flag:
            # 查看订单情况
            if order.status in [order.Submitted, order.Accepted]:  # 接受订单交易，正常情况
                return
            if order.status in [order.Completed]:
                if order.isbuy():
                    print(f"已买入:{self.data._name}")
                    print(f"数量: {order.executed.size}")
                    print(f"买入价格: {order.executed.price}")
                    print(f"价值: {order.executed.value}")
                elif order.issell():
                    print(f"已卖出:{self.data._name}")
                    print(f"数量: {order.executed.size}")
                    print(f"卖出价格: {order.executed.price}")
                    print(f"价值: {order.executed.value}")
            elif order.status is order.Canceled:
                print('订单取消')
            elif order.status is order.Rejected:
                print('金额不足拒绝交易')
            elif order.status is order.Margin:
                print('保证金不足')
        else:
            pass

    # 共享资金池组合回测
    def shared_cash(self):
        for data in self.datas:
            size = self.calculate_quantity(data)
            self.buy_function(line=data, size=size)
            self.sell_function(line=data, size=size)

    def buy_function(self, line, size):
        close_over_sma = line.close > self.sma5[line][0]
        close_over_ema = line.close > self.ema15[line][0]
        sma_ema_diff = self.sma5[line][0] - self.ema15[line][0]
        buy_cond = (close_over_sma and close_over_ema and sma_ema_diff > 0) or line.close == self.bolling_top[line][0]

        # 这里最后要被替换成直接调用策略类，外部传入
        if buy_cond and self.broker.get_value() > 0:
            '''
            满足策略条件，则进行买入
            '''
            buy_order = self.buy(data=line, size=size)
            return buy_order
        else:
            pass

    def sell_function(self, line, size):
        sell_cond = self.indicatordict[line][0] < self.indicatordict[line][-1] < self.indicatordict[line][-2]
        # sell_cond = line.close < self.sma5[line]
        # 这里最后要被替换成直接调用策略类，外部传入
        if sell_cond and self.getposition(line):  # 获取当前的总资金:
            '''
            满足策略条件，则进行卖出
            '''
            sell_order = self.close(data=line, size=size)
            return sell_order
        else:
            pass

    def calculate_quantity(self, line) -> int:
        # 在这里根据策略的逻辑计算交易数量
        # 返回一个整数表示交易数量
        total_value = self.broker.get_value()  # 获取当前的总资金
        available_value = total_value * 0.05  # 可用资金为总资金的5%
        close_price = line.close[0]  # 当前品种的收盘价
        quantity = int(available_value / close_price)  # 计算交易数量，取整数

        return quantity

    def print_position(self, line) -> None:
        pos = self.getposition(line)
        print(f"品种: {line._name} 的当前仓位: {pos.size} @price: {pos.price}")


# =============== 策略参数优化独立资金池策略类 ==================

class OptSoloCash(bt.Strategy):
    params = dict(N1=10, N2=20)

    def __init__(self):
        # 在这里添加并初始化需要使用的指标类
        self.indicatordict = dict()
        self.notify_flag = 0
        self.indicatordict['SMA5'] = MovingAverageSimple(self.p.N1)
        self.indicatordict['EMA15'] = ExponentialMovingAverage(self.p.N2)

    def next(self):
        self.solo_cash()

    def notify_order(self, order):  # 固定写法，查看订单情况
        if self.notify_flag:
            # 查看订单情况
            if order.status in [order.Submitted, order.Accepted]:  # 接受订单交易，正常情况
                return
            if order.status in [order.Completed]:
                if order.isbuy():
                    print(f"已买入:{self.data._name}")
                    print(f"数量: {order.executed.size}")
                    print(f"买入价格: {order.executed.price}")
                    print(f"价值: {order.executed.value}")
                elif order.issell():
                    print(f"已卖出:{self.data._name}")
                    print(f"数量: {order.executed.size}")
                    print(f"卖出价格: {order.executed.price}")
                    print(f"价值: {order.executed.value}")
            elif order.status is order.Canceled:
                print('订单取消')
            elif order.status is order.Rejected:
                print('金额不足拒绝交易')
            elif order.status is order.Margin:
                print('保证金不足')
        else:
            pass

    def solo_cash(self):
        size = self.calculate_quantity(self.datas[0])
        self.buy_function(size=size)
        self.sell_function()

    def buy_function(self, size):
        close_over_sma = self.datas[0].close > self.indicatordict['SMA5'][0]
        close_over_ema = self.datas[0].close > self.indicatordict['EMA15'][0]
        sma_ema_diff = self.indicatordict['SMA5'][0] - self.indicatordict['EMA'][0]
        buy_cond = (close_over_sma and close_over_ema and sma_ema_diff > 0)

        if buy_cond and self.broker.get_value() > 0:
            '''
            满足策略条件，则进行买入
            '''
            buy_order = self.buy(size=size)
            return buy_order
        else:
            pass

    def sell_function(self):
        sell_cond = self.datas.close[0] < self.indicatordict['SMA5'][0]

        if sell_cond and self.getposition():
            '''
            满足策略条件，则进行卖出
            '''
            sell_order = self.close()
            return sell_order
        else:
            pass

    def calculate_quantity(self, data) -> int:
        # 在这里根据策略的逻辑计算交易数量
        # 返回一个整数表示交易数量

        total_value = self.broker.get_value()  # 获取当前的总资金
        available_value = total_value * 0.05  # 可用资金为总资金的5%
        close_price = data.close  # 当前品种的收盘价
        quantity = int(available_value / close_price)  # 计算交易数量，取整数
        return quantity

    def print_position(self, line) -> None:
        pos = self.getposition(line)
        print(f"品种: {line._name} 的当前仓位: {pos.size} @price: {pos.price}")


# =============== 信息输入输出类 ==================

class DataIO:
    @staticmethod
    def get_stock_codes():
        # 查询当前所有正常上市交易的股票列表
        pro = DataGet.login_ts()
        data = pro.stock_basic(exchange='', list_status='L', fields='ts_code,name,area,industry,list_date')
        new_col = ['code', '股票名', '地区', '行业', '上市日期']
        data.columns = new_col
        data.to_csv("codes.csv")
        print("========现有上市交易品种列表========")
        print(data)
        print("================================")

    @staticmethod
    def show_stock_codes():
        # 显示所有列
        pd.set_option('display.max_columns', None)
        # # 显示所有行
        pd.set_option('display.max_rows', None)
        data = pd.read_csv("./codes.csv", index_col=0)
        new_col = ['code', '股票名', '地区', '行业', '上市日期']
        data.columns = new_col
        print("===================现有上市交易品种代码列表===================")
        print(data)
        print("===============================================")
        name_dict = dict()

        for index, row in data.iterrows():
            information_list = list()
            information_list.append(row['code'])
            information_list.append(row['上市日期'])
            name_dict[row['股票名']] = information_list

        return name_dict

    @staticmethod
    def input_stockInformation():
        name_dict = DataIO.show_stock_codes()

        codes = list()  # 品种代码列表
        names = list()
        print("请对应股票代码表输入，需要回测的股票名称,结束请输入“#” ")
        print("===============================================")
        while 1:
            name = input("请继续输入：\n").strip()
            if name is "#":
                break
            if name not in name_dict:
                print("输入股票名不存在，请重新输入")
                continue
            names.append(name)
        for name in names:
            codes.append(name_dict[name][0])
        while 1:
            if names is None:
                break
            judge = True
            try:
                start_date = int(input("请按说明格式输入回测起始日期：\n（例如：若为2021年9月10日则应输入：20210910）\n").strip())
                if start_date == "":
                    print("输入为空！请重试！！！")
                    continue
            except ValueError:
                print("非法输入！请重试！！！")
                continue
            # 输入日期不可早于list_date
            for name in names:
                if name_dict[name][1] > start_date:
                    print("起始日期不可早于该股票上市日期,请重新输入！！！")
                    print(f"股票：{name},上市日期为：{name_dict[name][1]}")
                    judge = False
                    break
                if DataGet.get_date_from_int(start_date) > datetime.date.today():
                    print("起始日期不可晚于今日，请重新输入！！！")
                    judge = False
                    break

            if judge is False:
                continue
            while 1:
                end_date = int(input("请按说明格式输入回测结束日期：\n（例如：若为2021年9月10日则应输入：20210910）\n").strip())
                if DataGet.get_date_from_int(end_date) > datetime.date.today():
                    print("结束日期不可晚于今日，请重新输入！！！")
                    continue
                if end_date < start_date:
                    print("结束日期不可早于起始日期！！！请重试！！！")
                    continue
                break

            break
        return codes, start_date, end_date

    @staticmethod
    def add_analysers(cerebro):
        print("请选择需要计算的回测指标，并在下方输入选项前的数字标号：\n1.年化收益\n2.夏普比率\n3.权益回撤\n4.年化收益率")
        while 1:

            num = input("请输入：（输入”0“结束输入）\n")
            if num == "0":
                break
            elif num == "1":
                cerebro.addanalyzer(AnnualReturn, _name='AnnualReturn')
            elif num == "2":
                cerebro.addanalyzer(SharpeRatio, timeframe=bt.TimeFrame.Years, _name='SharpeRatio')
            elif num == "3":
                cerebro.addanalyzer(DrawDown, _name='DrawDown')
            elif num == "4":
                cerebro.addanalyzer(TimeReturn, timeframe=bt.TimeFrame.Years, _name='TimeReturn')
            else:
                print("非法输入！请重试！！！")

    @staticmethod
    def add_plotElements(cerebro):
        cerebro.addobserver(bt.observers.BuySell)
        print("请选择可视化绘制的回测曲线，并在下方输入选项前的数字标号\n1.收益曲线\n2.回撤曲线\n3.总体权益曲线")
        while 1:

            num = input("请输入：（输入”0“结束输入）\n")
            if num == "0":
                break
            elif num == "1":
                cerebro.addobserver(bt.observers.TimeReturn)
            elif num == "2":
                # 查看回撤序列
                cerebro.addobserver(bt.observers.DrawDown)
            elif num == "3":
                cerebro.addobserver(bt.observers.FundValue)
            else:
                print("非法输入！请重试！！！")
                continue

    @staticmethod
    def text_report(cerebro, strat):
        endingcash = cerebro.broker.get_value()
        if endingcash <= 0:
            endingcash = 0
        else:
            pass
        print(f"期初权益：{cerebro.broker.startingcash}")
        print(f"期末权益：{endingcash}")
        profit = endingcash - cerebro.broker.startingcash
        print(f"收益:{round(profit, 2)}")
        profit_percent = round(profit / cerebro.broker.startingcash, 2) * 100
        if profit < 0:
            profit_percent = -profit_percent
        else:
            pass
        print(f"收益率：{round(profit_percent, 2)}%")
        if hasattr(strat.analyzers, "SharpeRatio"):
            print(f"夏普比率:{round(strat.analyzers.SharpeRatio.get_analysis()['sharperatio'], 2)}")
        if hasattr(strat.analyzers, "DrawDown"):
            print(f"最大回撤率:{round(strat.analyzers.DrawDown.get_analysis()['max']['drawdown'], 2)}%")
            print(f"最大回撤资金:{round(-strat.analyzers.DrawDown.get_analysis()['max']['moneydown'], 2)}")
        if hasattr(strat.analyzers, "AnnualReturn"):
            print(
                f"年化平均收益率:{round(float(np.mean(list(strat.analyzers.AnnualReturn.get_analysis().values()))), 2) * 100}%")

    @staticmethod
    def input_OptInformation():
        n1_list = []
        n2_list = []
        num = 0
        name = ""
        while 1:
            try:
                print("*************************************************************************************")
                print("可用的参数优化算法:\n1.粒子群优化算法\n2.SOBOL序列\n3.随机搜索算法（耗时较久）\n4.CMA-ES\n5.网格搜索算法\n")
                name_choose = int(input("请选择优化算法并输入对应优化算法前的数字序号：\n"))
                if name_choose == 1:
                    name = "particle swarm"
                    break
                if name_choose == 2:
                    name = "sobol"
                    break
                if name_choose == 3:
                    name = "random search"
                    break
                if name_choose == 4:
                    name = "cma-es"
                    break
                if name_choose == 5:
                    name = "grid search"
                    break
                if name_choose == "":
                    print("输入为空！请重试！！！")
                    continue
                else:
                    print("不存在该选项！请重试！！！")
                    continue
            except ValueError:
                print("非法输入，请输入整数数字，请重试！")
                continue
        while 1:
            try:
                num = int(input("请输入算法优化次数："))
                break
            except ValueError:
                print("请输入整数数字，请重试！")
                continue
        # 策略参数的优化范围

        while 1:
            judge = True
            try:
                for i in range(2):
                    start = int(input(f"请输入参数{i + 1}的优化范围下限:\n"))
                    if start == "":
                        print("输入为空，请重试！")
                        judge = False
                        n1_list.clear()
                        n2_list.clear()
                        break
                    end = int(input(f"请输入参数{i + 1}的优化范围上限:\n"))
                    if end == "":
                        judge = False
                        print("输入为空，请重试！")
                        n1_list.clear()
                        n2_list.clear()
                        break
                    if start > end:
                        print("参数上限不可小于参数下限！请重新输入！")
                        n1_list.clear()
                        n2_list.clear()
                        judge = False
                        break
                    if i == 0:
                        n1_list.append(start)
                        n1_list.append(end)
                    else:
                        n2_list.append(start)
                        n2_list.append(end)
                if judge is True:
                    break
                else:
                    continue
            except ValueError:
                print("非法输入，请重试！")
                n1_list.clear()
                n2_list.clear()
                continue

        print(num, n1_list, n2_list)
        return name, num, n1_list, n2_list

    @staticmethod
    def printOptParameters(name, optimal_pars):
        print(f'采用{name}算法优化后的参数信息:')
        print('N1 = %.2f' % optimal_pars['N1'])
        print('N2 = %.2f' % optimal_pars['N2'])


# =============== 策略参数优化类 ==================

class StrategyOptimization:

    @staticmethod
    def strategy_optimization_flow(symbol_list, start_date, end_date):
        cerebro = bt.Cerebro()
        BackTestSetup.set_cerebro(cerebro=cerebro, opt_judge=True)
        for symbol in symbol_list:
            DataGet.get_data(codes=symbol, cerebro=cerebro, start_date=start_date, end_date=end_date)

        # 事先要加好数据，回测只重复执行添加策略这个过程
        def runSoloCashOpt(N1, N2):
            cerebro.addstrategy(OptSoloCash, N1=N1, N2=N2)
            return cerebro.broker.getvalue()

        def runSharedCashOpt(N1, N2):
            cerebro.addstrategy(OptSharedCash, N1=N1, N2=N2)
            return cerebro.broker.getvalue()

        # 事先要加好数据，回测只重复执行添加策略这个过程

        print("*************************************************************************************")
        name, num, n1_list, n2_list = DataIO.input_OptInformation()
        while 1:
            choose = input("请选择策略优化所使用的回测模式：\n1.批量独立资金池回测\n2.共享资金池回测\n(输入：“0”结束选择)\n")

            if choose == "1":
                opt = optunity.maximize(f=runSoloCashOpt,
                                        num_evals=num,
                                        solver_name=name,
                                        N1=n1_list,
                                        N2=n2_list)
                optimal_pars, details, _ = opt

                DataIO.printOptParameters(name, optimal_pars=optimal_pars)

                break
            if choose == "2":
                cerebro_new = bt.Cerebro()
                BackTestSetup.set_cerebro(cerebro=cerebro_new, opt_judge=True)
                for symbol in symbol_list:
                    DataGet.get_data(codes=symbol, cerebro=cerebro_new, start_date=start_date, end_date=end_date)
                opt = optunity.maximize(f=runSharedCashOpt,
                                        num_evals=num,
                                        solver_name=name,
                                        N1=n1_list,
                                        N2=n2_list)
                optimal_pars, details, _ = opt

                DataIO.printOptParameters(name, optimal_pars=optimal_pars)
                break
            if choose == "0":
                break
            if choose == "":
                print("输入为空！请重试！！！")
                continue
            else:
                print("非法输入！请重试！！！")
                continue


# =============== 回测设置控制类 ==================
class BackTestSetup:
    @staticmethod
    def set_cerebro(cerebro, opt_judge):
        public_cash = 100000000
        commission = 0.00025
        cerebro.broker.setcash(public_cash)  # 设置初始资金
        cerebro.broker.set_coc(False)
        cerebro.broker.setcommission(commission=commission)
        if opt_judge is False:
            DataIO.add_analysers(cerebro=cerebro)
            DataIO.add_plotElements(cerebro=cerebro)
        print("数据加载中.....")
        time.sleep(2)
        if opt_judge is False:
            print("回测进行中....")
            time.sleep(2)


# =============== 主控制类 ==================

class MainController:
    @staticmethod
    def start():

        while 1:
            print("*************************************************************************************")
            choose = input("请选择功能：\n1.批量独立资金池回测\n2.共享资金池回测\n3.策略参数优化\n(输入：“*”退出系统)\n")

            if choose == "1":
                codes, start_date, end_date = DataIO.input_stockInformation()

                BackTest.batch_test(symbol_list=codes, start_date=start_date, end_date=end_date)
                continue
            if choose == "2":
                codes, start_date, end_date = DataIO.input_stockInformation()

                BackTest.shared_cash_test(symbol_list=codes, start_date=start_date, end_date=end_date)
                continue
            if choose == "3":
                codes, start_date, end_date = DataIO.input_stockInformation()

                StrategyOptimization.strategy_optimization_flow(symbol_list=codes, start_date=start_date,
                                                                end_date=end_date)
                continue
            if choose == "*":
                print("系统已退出！")
                break
            if choose == "":
                print("输入为空！请重试！！！")
                continue
            else:
                print("非法输入！请重试！！！")
                continue


if __name__ == '__main__':
    MainController.start()
