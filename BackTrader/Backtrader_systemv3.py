import numpy as np  # 导入NumPy库，用于高效的数值计算
import pandas as pd  # 导入Pandas库，用于数据处理和分析
import tushare as ts  # 导入Tushare库，用于获取股票数据
import time  # 导入时间模块，用于时间相关操作
from backtrader.analyzers import *  # 导入Backtrader分析器，用于回测结果的分析
from backtrader.indicators import *  # 导入Backtrader指标模块，用于策略开发中的技术指标
from backtrader_plotting import Bokeh  # 导入Bokeh模块，用于绘制回测结果的图表
from backtrader_plotting.schemes import Tradimo  # 导入Bokeh的绘图方案
import datetime  # 导入日期时间模块，用于处理时间
import optunity  # 导入Optunity库，用于超参数优化

# =============== 数据获取与处理类 ==================
class DataGet:
    @staticmethod
    def get_str_date_from_int(date_int):
        """
        将日期的整数格式（yyyyMMdd）转换为字符串格式（yyyy-mm-dd）
        :param date_int: 日期的整数表示
        :return: 格式化后的日期字符串
        """
        try:
            date_int = int(date_int)
        except ValueError:
            date_int = int(date_int.replace("-", ""))
        year = date_int // 10000  # 获取年份
        month = (date_int % 10000) // 100  # 获取月份
        day = date_int % 100  # 获取日期

        return "%d-%02d-%02d" % (year, month, day)

    @staticmethod
    def get_date_from_int(date_int):
        """
        将日期的整数格式（yyyyMMdd）转换为日期对象
        :param date_int: 日期的整数表示
        :return: 转换后的日期对象
        """
        date_str = DataGet.get_str_date_from_int(date_int)
        return datetime.datetime.strptime(date_str, "%Y-%m-%d").date()

    @staticmethod
    def login_ts():
        """
        登录Tushare，获取pro_api接口
        :return: 返回Tushare pro_api实例
        """
        token = '7c15d8db9ccc0383e40eb7487930fa9eb88eaca08573fe1da440aa54'
        ts.set_token(token)  # 设置Tushare Token
        pro = ts.pro_api(token)  # 获取Tushare pro接口
        return pro

    @staticmethod
    def get_data(codes, cerebro, start_date, end_date):
        """
        获取指定股票/期货代码的数据，并将其添加到回测引擎（Cerebro）中
        :param codes: 股票/期货代码（可以是单个代码或多个代码的列表）
        :param cerebro: Backtrader回测引擎实例
        :param start_date: 回测开始日期
        :param end_date: 回测结束日期
        """
        pro = DataGet.login_ts()  # 登录Tushare接口
        code_list = codes if isinstance(codes, list) else codes.split()  # 确保codes是列表形式
        # 加载数据
        for code in code_list:
            df = pro.daily(ts_code=f"{code}", start_date=start_date, end_date=end_date)  # 获取日线数据
            df['trade_date'] = pd.to_datetime(df['trade_date'])  # 转换交易日期为日期类型
            df.set_index('trade_date', inplace=True)  # 将交易日期设为索引
            df['openinterest'] = 0  # 初始化持仓量为0
            df = df[['open', 'high', 'low', 'close', 'vol', 'openinterest']].rename(columns={'vol': 'volume'})  # 重命名列
            df = df.sort_index()  # 按日期排序数据
            data = bt.feeds.PandasData(dataname=df)  # 转换为Backtrader的Pandas数据格式
            cerebro.adddata(data, name=code)  # 将数据添加到回测引擎中

# =============== 回测控制类 ==================
class BackTest:
    @staticmethod
    def batch_test(symbol_list, start_date, end_date):
        """
        批量回测，针对多个品种进行回测
        :param symbol_list: 品种代码列表
        :param start_date: 回测开始日期
        :param end_date: 回测结束日期
        """
        for symbol in symbol_list:
            cerebro = bt.Cerebro()  # 创建Backtrader回测引擎
            BackTestSetup.set_cerebro(cerebro=cerebro, opt_judge=False)  # 设置回测引擎
            cerebro.addstrategy(Solo_cash_pool)  # 添加策略（单独资金池策略）
            DataGet.get_data(codes=symbol, cerebro=cerebro, start_date=start_date, end_date=end_date)  # 获取数据
            strat = cerebro.run()[0]  # 运行回测并获取策略实例
            print("========独立资金池批量回测========")
            print(f"品种：{symbol}")
            print(f"回测区间：{DataGet.get_date_from_int(start_date)}至{DataGet.get_date_from_int(end_date)}")
            DataIO.text_report(cerebro=cerebro, strat=strat)  # 输出回测报告
            print("========独立资金池批量回测========")
            pic = Bokeh(style='bar', plot_mode='single', scheme=Tradimo())  # 使用Bokeh绘图
            cerebro.plot(pic)  # 绘制回测结果

    @staticmethod
    def shared_cash_test(symbol_list, start_date, end_date):
        """
        使用共享资金池进行回测
        :param symbol_list: 品种代码列表
        :param start_date: 回测开始日期
        :param end_date: 回测结束日期
        """
        cerebro = bt.Cerebro()  # 创建Backtrader回测引擎
        BackTestSetup.set_cerebro(cerebro=cerebro, opt_judge=False)  # 设置回测引擎
        cerebro.addstrategy(Shared_cash_pool)  # 添加策略（共享资金池策略）
        DataGet.get_data(cerebro=cerebro, codes=symbol_list, start_date=start_date, end_date=end_date)  # 获取数据
        strat = cerebro.run()[0]  # 运行回测并获取策略实例
        print("========共享资金池组合回测========")
        print(f"品种：{symbol_list}")
        print(f"回测区间：{DataGet.get_date_from_int(start_date)}至{DataGet.get_date_from_int(end_date)}")
        DataIO.text_report(cerebro=cerebro, strat=strat)  # 输出回测报告
        print("========共享资金池组合回测========")
        pic = Bokeh(style='bar', plot_mode='single', scheme=Tradimo())  # 使用Bokeh绘图
        cerebro.plot(pic)  # 绘制回测结果

# =============== 共享资金池策略类 ==================

class Shared_cash_pool(bt.Strategy):
    """
    共享资金池策略类，主要用于管理多个品种的买卖决策，策略基于不同的技术指标。
    """

    def __init__(self):
        """
        初始化共享资金池策略中的指标，确保每个品种的技术指标独立计算。
        """
        self.sma5 = dict()  # 5日简单移动平均
        self.ema15 = dict()  # 15日指数加权移动平均
        self.bolling_top = dict()  # 布林带上轨
        self.bolling_bot = dict()  # 布林带下轨
        self.notify_flag = 0  # 控制是否打印订单状态
        for index, data in enumerate(self.datas):
            c = data.close
            self.sma5[data] = MovingAverageSimple(c)  # 初始化5日简单移动均线
            self.ema15[data] = ExponentialMovingAverage(c)  # 初始化15日指数加权移动均线
            self.bolling_top[data] = bt.indicators.BollingerBands(c, period=20).top  # 初始化布林带上轨
            self.bolling_bot[data] = bt.indicators.BollingerBands(c, period=20).bot  # 初始化布林带下轨

    def next(self):
        """
        每个时间步执行共享资金池策略。
        """
        self.shared_cash()  # 执行共享资金池策略

    def notify_order(self, order):
        """
        通知订单状态，用于查看订单执行情况。
        """
        if self.notify_flag:
            if order.status in [order.Submitted, order.Accepted]:  # 订单被接受，等待执行
                return
            if order.status in [order.Completed]:
                if order.isbuy():  # 买入订单完成
                    print(f"已买入:{self.data._name}")
                    print(f"数量: {order.executed.size}")
                    print(f"买入价格: {order.executed.price}")
                    print(f"价值: {order.executed.value}")
                elif order.issell():  # 卖出订单完成
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

    def shared_cash(self):
        """
        根据共享资金池策略的条件进行每个品种的买入或卖出。
        """
        for data in self.datas:
            size = self.calculate_quantity(data)  # 计算交易数量

            self.buy_function(line=data, size=size)  # 执行买入操作
            self.sell_function(line=data, size=size)  # 执行卖出操作

    def buy_function(self, line, size):
        """
        执行买入操作，当满足买入条件时，调用Backtrader的买入函数。
        """
        close_over_sma = line.close > self.sma5[line][0]  # 当前价格高于5日均线
        close_over_ema = line.close > self.ema15[line][0]  # 当前价格高于15日指数均线
        sma_ema_diff = self.sma5[line][0] - self.ema15[line][0]  # 计算5日均线与15日均线的差值
        buy_cond = (close_over_sma and close_over_ema and sma_ema_diff > 0) or line.close == self.bolling_top[line][0]  # 满足买入条件

        if buy_cond and self.broker.get_value() > 0:  # 确保资金充足
            buy_order = self.buy(data=line, size=size)  # 执行买入
            return buy_order
        else:
            pass

    def sell_function(self, line, size):
        """
        执行卖出操作，当满足卖出条件时，调用Backtrader的卖出函数。
        """
        sell_cond = line.close < self.sma5[line]  # 当前价格低于5日均线

        if sell_cond and self.getposition(line):  # 当前持有仓位时执行卖出
            sell_order = self.close(data=line, size=size)  # 执行卖出
            return sell_order
        else:
            pass

    def calculate_quantity(self, line) -> int:
        """
        根据可用资金计算每次交易的数量。
        """
        total_value = self.broker.get_value()  # 获取总资金
        available_value = total_value * 0.05  # 可用资金为总资金的5%
        close_price = line.close[0]  # 当前价格
        quantity = int(available_value / close_price)  # 计算购买数量
        return quantity

    def print_position(self, line) -> None:
        """
        打印当前持仓信息。
        """
        pos = self.getposition(line)
        print(f"品种: {line._name} 的当前仓位: {pos.size} @price: {pos.price}")


# =============== 独立资金池策略类 ==================

class Solo_cash_pool(bt.Strategy):
    """
    独立资金池策略类，适用于每次交易只涉及一个品种的回测。
    """

    def __init__(self):
        """
        初始化独立资金池策略中的各类指标。
        """
        self.indicatordict = dict()  # 存储各类技术指标
        self.notify_flag = 0  # 控制是否打印订单状态

        # 初始化技术指标
        self.indicatordict['SMA5'] = MovingAverageSimple()  # 5日简单移动平均线
        self.indicatordict['EMA15'] = ExponentialMovingAverage()  # 15日指数移动平均线
        self.indicatordict['MA30'] = MovingAverage()  # 30日移动平均线
        self.indicatordict['MACD'] = MACDHisto()  # MACD指标的柱状图

    def next(self):
        """
        每个时间步执行独立资金池策略。
        """
        self.solo_cash()  # 执行独立资金池策略逻辑

    def notify_order(self, order):
        """
        通知订单状态，用于查看订单执行情况。
        """
        if self.notify_flag:
            # 查看订单情况
            if order.status in [order.Submitted, order.Accepted]:
                return  # 订单已提交或接受，等待执行
            if order.status in [order.Completed]:
                if order.isbuy():
                    # 买入订单完成
                    print(f"已买入:{self.data._name}")
                    print(f"数量: {order.executed.size}")
                    print(f"买入价格: {order.executed.price}")
                    print(f"价值: {order.executed.value}")
                elif order.issell():
                    # 卖出订单完成
                    print(f"已卖出:{self.data._name}")
                    print(f"数量: {order.executed.size}")
                    print(f"卖出价格: {order.executed.price}")
                    print(f"价值: {order.executed.value}")
            elif order.status is order.Canceled:
                print('订单取消')
            elif order.status is order.Rejected:
                print('金额不足，拒绝交易')
            elif order.status is order.Margin:
                print('保证金不足')
        else:
            pass  # 不打印订单状态

    def solo_cash(self):
        """
        根据独立资金池策略的条件进行买入或卖出操作。
        """
        size = self.calculate_quantity(self.datas[0])  # 计算交易数量
        self.buy_function(size=size)  # 执行买入操作
        self.sell_function()  # 执行卖出操作

    def buy_function(self, size):
        """
        执行买入操作，当满足买入条件时，调用Backtrader的买入函数。
        """
        close_over_sma = self.datas[0].close > self.indicatordict['SMA5'][0]  # 当前价格高于5日均线
        close_over_ema = self.datas[0].close > self.indicatordict['EMA15'][0]  # 当前价格高于15日指数均线
        sma_ema_diff = self.indicatordict['SMA5'][0] - self.indicatordict['EMA15'][0]  # 5日均线与15日均线的差值

        buy_cond = (close_over_sma or close_over_ema) and (sma_ema_diff > 0)  # 定义买入条件

        if buy_cond and self.broker.get_value() > 0:  # 检查是否满足买入条件且有足够资金
            buy_order = self.buy(size=size)  # 执行买入操作
            return buy_order
        else:
            pass  # 不满足买入条件，跳过

    def sell_function(self):
        """
        执行卖出操作，当满足卖出条件时，调用Backtrader的卖出函数。
        """
        sell_cond = self.datas[0].close < self.indicatordict['SMA5'][0]  # 当前价格低于5日均线

        if sell_cond and self.getposition():  # 检查是否满足卖出条件且持有仓位
            sell_order = self.close()  # 执行卖出操作
            return sell_order
        else:
            pass  # 不满足卖出条件，跳过

    def calculate_quantity(self, data) -> int:
        """
        根据策略的逻辑计算交易数量，返回一个整数表示交易数量。
        """
        total_value = self.broker.get_value()  # 获取当前总资金
        available_value = total_value * 0.05  # 可用资金为总资金的5%
        close_price = data.close[0]  # 当前收盘价
        quantity = int(available_value / close_price)  # 计算交易数量，取整数
        return quantity

    def print_position(self, line) -> None:
        """
        打印当前持仓信息。
        """
        pos = self.getposition(line)
        print(f"品种: {line._name} 的当前仓位: {pos.size} @price: {pos.price}")

# =============== 策略参数优化共享资金池策略类 ==================

class OptSharedCash(bt.Strategy):
    """
    策略参数优化共享资金池策略类，使用参数优化技术对共享资金池策略进行调整。
    """
    params = dict(N1=10, N2=20)  # 定义策略参数，可用于优化

    def __init__(self):
        """
        初始化策略，创建并初始化需要的指标，并根据传入的参数调整指标的周期。
        """
        # 创建指标字典
        self.sma5 = dict()  # 简单移动平均线，周期为N1
        self.ema15 = dict()  # 指数移动平均线，周期为N2
        self.ma30 = dict()  # 移动平均线，默认周期
        self.bolling_top = dict()  # 布林带上轨
        self.bolling_bot = dict()  # 布林带下轨
        self.notify_flag = 0  # 控制是否打印订单通知

        # 遍历所有数据集，为每个数据集计算对应的指标
        for index, data in enumerate(self.datas):
            c = data.close
            # 使用传入的参数N1和N2来调整指标的周期
            self.sma5[data] = MovingAverageSimple(c, period=int(self.p.N1))  # 简单移动平均线，周期为N1
            self.ema15[data] = ExponentialMovingAverage(c, period=int(self.p.N2))  # 指数移动平均线，周期为N2
            self.ma30[data] = MovingAverage(c)  # 默认周期的移动平均线
            # 初始化布林带指标
            self.bolling_top[data] = bt.indicators.BollingerBands(c, period=20).top  # 布林带上轨
            self.bolling_bot[data] = bt.indicators.BollingerBands(c, period=20).bot  # 布林带下轨

    def next(self):
        """
        每个时间步执行策略操作。
        """
        self.shared_cash()  # 执行共享资金池策略

    def notify_order(self, order):
        """
        订单状态通知，用于监控订单的执行状态。
        """
        if self.notify_flag:
            # 查看订单情况
            if order.status in [order.Submitted, order.Accepted]:
                return  # 订单已提交或被接受，等待执行
            if order.status in [order.Completed]:
                if order.isbuy():
                    # 买入订单已完成
                    print(f"已买入:{self.data._name}")
                    print(f"数量: {order.executed.size}")
                    print(f"买入价格: {order.executed.price}")
                    print(f"价值: {order.executed.value}")
                elif order.issell():
                    # 卖出订单已完成
                    print(f"已卖出:{self.data._name}")
                    print(f"数量: {order.executed.size}")
                    print(f"卖出价格: {order.executed.price}")
                    print(f"价值: {order.executed.value}")
            elif order.status == order.Canceled:
                print('订单取消')
            elif order.status == order.Rejected:
                print('金额不足拒绝交易')
            elif order.status == order.Margin:
                print('保证金不足')
        else:
            pass  # 不打印订单通知

    def shared_cash(self):
        """
        共享资金池策略的核心逻辑，遍历所有数据集，计算交易数量，执行买入和卖出操作。
        """
        for data in self.datas:
            size = self.calculate_quantity(data)  # 计算交易数量
            self.buy_function(line=data, size=size)  # 执行买入操作
            self.sell_function(line=data, size=size)  # 执行卖出操作

    def buy_function(self, line, size):
        """
        根据策略条件执行买入操作。
        """
        # 定义买入条件
        close_over_sma = line.close > self.sma5[line][0]  # 当前价格高于简单移动平均线
        close_over_ema = line.close > self.ema15[line][0]  # 当前价格高于指数移动平均线
        sma_ema_diff = self.sma5[line][0] - self.ema15[line][0]  # 简单均线与指数均线的差值
        # 满足以下条件之一即可买入
        buy_cond = (close_over_sma and close_over_ema and sma_ema_diff > 0) or \
                   (line.close == self.bolling_top[line][0])  # 价格等于布林带上轨

        if buy_cond and self.broker.get_value() > 0:
            # 满足买入条件且有足够资金，执行买入
            buy_order = self.buy(data=line, size=size)
            return buy_order
        else:
            pass  # 不满足买入条件，跳过

    def sell_function(self, line, size):
        """
        根据策略条件执行卖出操作。
        """
        # 定义卖出条件
        sell_cond = self.indicatordict[line][0] < self.indicatordict[line][-1] < self.indicatordict[line][-2]
        # sell_cond = line.close < self.sma5[line]  # 另一种卖出条件（注释掉的备选方案）

        if sell_cond and self.getposition(line):
            # 满足卖出条件且持有仓位，执行卖出
            sell_order = self.close(data=line, size=size)
            return sell_order
        else:
            pass  # 不满足卖出条件，跳过

    def calculate_quantity(self, line) -> int:
        """
        根据可用资金和当前价格计算交易数量。
        返回一个整数表示交易数量。
        """
        total_value = self.broker.get_value()  # 获取当前的总资金
        available_value = total_value * 0.05  # 可用资金为总资金的5%
        close_price = line.close[0]  # 当前收盘价
        quantity = int(available_value / close_price)  # 计算交易数量，取整数

        return quantity

    def print_position(self, line) -> None:
        """
        打印当前持仓信息。
        """
        pos = self.getposition(line)
        print(f"品种: {line._name} 的当前仓位: {pos.size} @price: {pos.price}")

# =============== 策略参数优化独立资金池策略类 ==================

class OptSoloCash(bt.Strategy):
    """
    策略参数优化独立资金池策略类，适用于单个品种的回测，并支持参数优化。
    """

    params = dict(N1=10, N2=20)  # 定义策略参数N1和N2，用于指标的周期设定

    def __init__(self):
        """
        初始化策略，创建并初始化需要的技术指标，并根据传入的参数调整指标的周期。
        """
        self.indicatordict = dict()  # 存储各类技术指标
        self.notify_flag = 0  # 控制是否打印订单状态

        # 初始化技术指标，使用策略参数N1和N2作为周期
        self.indicatordict['SMA5'] = MovingAverageSimple(self.datas[0].close, period=self.p.N1)  # 简单移动平均线
        self.indicatordict['EMA15'] = ExponentialMovingAverage(self.datas[0].close, period=self.p.N2)  # 指数移动平均线

    def next(self):
        """
        每个时间步执行策略逻辑，包括买入和卖出操作。
        """
        self.solo_cash()  # 执行独立资金池策略逻辑

    def notify_order(self, order):
        """
        通知订单状态，用于查看订单的执行情况。
        """
        if self.notify_flag:
            # 查看订单状态
            if order.status in [order.Submitted, order.Accepted]:
                return  # 订单已提交或被接受，等待执行
            if order.status in [order.Completed]:
                if order.isbuy():
                    # 买入订单完成
                    print(f"已买入: {self.data._name}")
                    print(f"数量: {order.executed.size}")
                    print(f"买入价格: {order.executed.price}")
                    print(f"价值: {order.executed.value}")
                elif order.issell():
                    # 卖出订单完成
                    print(f"已卖出: {self.data._name}")
                    print(f"数量: {order.executed.size}")
                    print(f"卖出价格: {order.executed.price}")
                    print(f"价值: {order.executed.value}")
            elif order.status == order.Canceled:
                print('订单取消')
            elif order.status == order.Rejected:
                print('金额不足，拒绝交易')
            elif order.status == order.Margin:
                print('保证金不足')
        else:
            pass  # 不打印订单状态

    def solo_cash(self):
        """
        根据策略的条件执行买入和卖出操作。
        """
        size = self.calculate_quantity(self.datas[0])  # 计算交易数量
        self.buy_function(size=size)  # 执行买入操作
        self.sell_function()  # 执行卖出操作

    def buy_function(self, size):
        """
        执行买入操作，当满足买入条件时，调用Backtrader的买入函数。
        """
        # 获取当前的收盘价和指标值
        current_close = self.datas[0].close[0]
        sma_value = self.indicatordict['SMA5'][0]
        ema_value = self.indicatordict['EMA15'][0]

        # 定义买入条件
        close_over_sma = current_close > sma_value  # 当前价格高于SMA
        close_over_ema = current_close > ema_value  # 当前价格高于EMA
        sma_ema_diff = sma_value - ema_value  # SMA与EMA的差值

        buy_cond = close_over_sma and close_over_ema and sma_ema_diff > 0  # 满足所有条件

        if buy_cond and self.broker.get_cash() >= current_close * size:
            # 满足买入条件且有足够资金，执行买入
            buy_order = self.buy(size=size)
            return buy_order
        else:
            pass  # 不满足买入条件或资金不足，跳过

    def sell_function(self):
        """
        执行卖出操作，当满足卖出条件时，调用Backtrader的卖出函数。
        """
        # 获取当前的收盘价和SMA值
        current_close = self.datas[0].close[0]
        sma_value = self.indicatordict['SMA5'][0]

        # 定义卖出条件
        sell_cond = current_close < sma_value  # 当前价格低于SMA

        if sell_cond and self.getposition().size > 0:
            # 满足卖出条件且持有仓位，执行卖出
            sell_order = self.close()
            return sell_order
        else:
            pass  # 不满足卖出条件或无持仓，跳过

    def calculate_quantity(self, data) -> int:
        """
        根据策略的逻辑计算交易数量，返回一个整数表示交易数量。
        """
        total_value = self.broker.get_value()  # 获取当前的总资产
        available_value = total_value * 0.05  # 可用资金为总资金的5%
        close_price = data.close[0]  # 当前品种的收盘价
        quantity = int(available_value / close_price)  # 计算交易数量，取整数

        return quantity

    def print_position(self, line) -> None:
        """
        打印当前持仓信息。
        """
        pos = self.getposition(line)
        print(f"品种: {line._name} 的当前仓位: {pos.size} @价格: {pos.price}")


# =============== 信息输入输出类 ==================

class DataIO:
    """
    数据输入输出类，提供与用户交互的功能，包括获取股票代码、选择回测指标、设置参数优化等。
    """

    @staticmethod
    def get_stock_codes():
        """
        获取当前所有正常上市交易的股票列表，并将其保存到本地文件'codes.csv'中。
        """
        # 登录Tushare获取数据接口
        pro = DataGet.login_ts()
        # 获取上市状态为'L'（上市）的股票基本信息
        data = pro.stock_basic(exchange='', list_status='L', fields='ts_code,name,area,industry,list_date')
        # 重命名列名为中文，方便显示
        new_col = ['code', '股票名', '地区', '行业', '上市日期']
        data.columns = new_col
        # 将股票列表保存为CSV文件
        data.to_csv("codes.csv")
        # 打印当前上市交易的品种列表
        print("========现有上市交易品种列表========")
        print(data)
        print("================================")

    @staticmethod
    def show_stock_codes():
        """
        显示所有上市交易的股票代码，并返回股票名称与代码、上市日期的对应字典。
        :return: 股票名称与其代码和上市日期的字典
        """
        # 设置Pandas显示选项，显示所有列和所有行
        pd.set_option('display.max_columns', None)
        pd.set_option('display.max_rows', None)
        # 读取之前保存的股票代码CSV文件
        data = pd.read_csv("./codes.csv", index_col=0)
        # 重命名列名为中文
        new_col = ['code', '股票名', '地区', '行业', '上市日期']
        data.columns = new_col
        # 打印股票代码列表
        print("===================现有上市交易品种代码列表===================")
        print(data)
        print("===============================================")
        # 创建一个字典，用于存储股票名称与其代码和上市日期的对应关系
        name_dict = dict()

        # 遍历每一行数据，填充name_dict
        for index, row in data.iterrows():
            information_list = list()
            information_list.append(row['code'])  # 添加股票代码
            information_list.append(row['上市日期'])  # 添加上市日期
            name_dict[row['股票名']] = information_list  # 键为股票名称，值为信息列表

        return name_dict  # 返回股票信息字典

    @staticmethod
    def input_stockInformation():
        """
        交互式地获取用户想要回测的股票名称、回测起始日期和结束日期。
        :return: 用户选择的股票代码列表、回测起始日期和结束日期
        """
        # 显示股票代码列表并获取股票信息字典
        name_dict = DataIO.show_stock_codes()

        codes = list()  # 存储用户选择的股票代码
        names = list()  # 存储用户输入的股票名称
        print("请对应股票代码表输入，需要回测的股票名称,结束请输入“#” ")
        print("===============================================")
        # 循环获取用户输入的股票名称
        while True:
            name = input("请继续输入：\n").strip()
            if name == "#":
                break  # 输入'#'表示结束输入
            if name not in name_dict:
                print("输入股票名不存在，请重新输入")
                continue  # 如果股票名称不存在，提示重新输入
            names.append(name)  # 添加到名称列表中
        # 根据名称列表获取对应的股票代码
        for name in names:
            codes.append(name_dict[name][0])
        # 获取回测的起始日期和结束日期
        while True:
            if not names:
                break  # 如果没有选择任何股票，直接退出
            judge = True
            try:
                # 输入回测起始日期
                start_date = int(input("请按说明格式输入回测起始日期：\n（例如：若为2021年9月10日则应输入：20210910）\n").strip())
                if start_date == "":
                    print("输入为空！请重试！！！")
                    continue
            except ValueError:
                print("非法输入！请重试！！！")
                continue
            # 检查起始日期是否合法
            for name in names:
                if int(name_dict[name][1]) > start_date:
                    print("起始日期不可早于该股票上市日期,请重新输入！！！")
                    print(f"股票：{name},上市日期为：{name_dict[name][1]}")
                    judge = False
                    break
                if DataGet.get_date_from_int(start_date) > datetime.date.today():
                    print("起始日期不可晚于今日，请重新输入！！！")
                    judge = False
                    break

            if not judge:
                continue  # 如果起始日期不合法，重新输入
            while True:
                try:
                    # 输入回测结束日期
                    end_date = int(input("请按说明格式输入回测结束日期：\n（例如：若为2021年9月10日则应输入：20210910）\n").strip())
                    if DataGet.get_date_from_int(end_date) > datetime.date.today():
                        print("结束日期不可晚于今日，请重新输入！！！")
                        continue
                    if end_date < start_date:
                        print("结束日期不可早于起始日期！！！请重试！！！")
                        continue
                    break  # 结束日期输入正确，退出循环
                except ValueError:
                    print("非法输入！请重试！！！")
                    continue
            break  # 起始日期和结束日期均输入正确，退出循环
        return codes, start_date, end_date  # 返回股票代码列表和日期

    @staticmethod
    def add_analysers(cerebro):
        """
        交互式地添加回测分析器，用户可以选择需要计算的回测指标。
        :param cerebro: Backtrader的Cerebro引擎实例
        """
        print("请选择需要计算的回测指标，并在下方输入选项前的数字标号：\n1.年化收益\n2.夏普比率\n3.权益回撤\n4.年化收益率")
        while True:
            # 获取用户输入的指标选项
            num = input("请输入：（输入”0“结束输入）\n")
            if num == "0":
                break  # 输入'0'表示结束输入
            elif num == "1":
                # 添加年化收益分析器
                cerebro.addanalyzer(AnnualReturn, _name='AnnualReturn')
            elif num == "2":
                # 添加夏普比率分析器
                cerebro.addanalyzer(SharpeRatio, timeframe=bt.TimeFrame.Years, _name='SharpeRatio')
            elif num == "3":
                # 添加权益回撤分析器
                cerebro.addanalyzer(DrawDown, _name='DrawDown')
            elif num == "4":
                # 添加年化收益率分析器
                cerebro.addanalyzer(TimeReturn, timeframe=bt.TimeFrame.Years, _name='TimeReturn')
            else:
                print("非法输入！请重试！！！")  # 输入不合法，提示重试

    @staticmethod
    def add_plotElements(cerebro):
        """
        交互式地添加可视化绘制的回测曲线，用户可以选择需要显示的曲线。
        :param cerebro: Backtrader的Cerebro引擎实例
        """
        # 添加买卖点观察器
        cerebro.addobserver(bt.observers.BuySell)
        print("请选择可视化绘制的回测曲线，并在下方输入选项前的数字标号\n1.收益曲线\n2.回撤曲线\n3.总体权益曲线")
        while True:
            # 获取用户输入的可视化选项
            num = input("请输入：（输入”0“结束输入）\n")
            if num == "0":
                break  # 输入'0'表示结束输入
            elif num == "1":
                # 添加收益曲线观察器
                cerebro.addobserver(bt.observers.TimeReturn)
            elif num == "2":
                # 添加回撤曲线观察器
                cerebro.addobserver(bt.observers.DrawDown)
            elif num == "3":
                # 添加总体权益曲线观察器
                cerebro.addobserver(bt.observers.FundValue)
            else:
                print("非法输入！请重试！！！")
                continue  # 输入不合法，提示重试

    @staticmethod
    def text_report(cerebro, strat):
        """
        输出回测的文本报告，包括期初权益、期末权益、收益、收益率等信息。
        :param cerebro: Backtrader的Cerebro引擎实例
        :param strat: 运行后的策略实例
        """
        endingcash = cerebro.broker.get_value()  # 获取期末权益
        if endingcash <= 0:
            endingcash = 0
        # 输出期初和期末权益
        print(f"期初权益：{cerebro.broker.startingcash}")
        print(f"期末权益：{endingcash}")
        profit = endingcash - cerebro.broker.startingcash  # 计算收益
        print(f"收益:{round(profit, 2)}")
        # 计算收益率
        profit_percent = round(profit / cerebro.broker.startingcash, 2) * 100
        if profit < 0:
            profit_percent = -profit_percent
        print(f"收益率：{round(profit_percent, 2)}%")
        # 输出夏普比率
        if hasattr(strat.analyzers, "SharpeRatio"):
            sharpe_ratio = strat.analyzers.SharpeRatio.get_analysis().get('sharperatio', None)
            if sharpe_ratio is not None:
                print(f"夏普比率:{round(sharpe_ratio, 2)}")
        # 输出最大回撤信息
        if hasattr(strat.analyzers, "DrawDown"):
            drawdown = strat.analyzers.DrawDown.get_analysis()
            print(f"最大回撤率:{round(drawdown['max']['drawdown'], 2)}%")
            print(f"最大回撤资金:{round(-drawdown['max']['moneydown'], 2)}")
        # 输出年化平均收益率
        if hasattr(strat.analyzers, "AnnualReturn"):
            annual_returns = strat.analyzers.AnnualReturn.get_analysis()
            avg_annual_return = np.mean(list(annual_returns.values()))
            print(f"年化平均收益率:{round(float(avg_annual_return), 2) * 100}%")

    @staticmethod
    def input_OptInformation():
        """
        交互式地获取策略参数优化的信息，包括优化算法、优化次数、参数范围等。
        :return: 优化算法名称、优化次数、参数N1的范围列表、参数N2的范围列表
        """
        n1_list = []  # 存储参数N1的范围
        n2_list = []  # 存储参数N2的范围
        num = 0       # 优化次数
        name = ""     # 优化算法名称
        # 选择优化算法
        while True:
            try:
                print("*************************************************************************************")
                print("可用的参数优化算法:\n1.粒子群优化算法\n2.SOBOL序列\n3.随机搜索算法（耗时较久）\n4.CMA-ES\n5.网格搜索算法\n")
                name_choose = int(input("请选择优化算法并输入对应优化算法前的数字序号：\n"))
                if name_choose == 1:
                    name = "particle swarm"
                    break
                elif name_choose == 2:
                    name = "sobol"
                    break
                elif name_choose == 3:
                    name = "random search"
                    break
                elif name_choose == 4:
                    name = "cma-es"
                    break
                elif name_choose == 5:
                    name = "grid search"
                    break
                else:
                    print("不存在该选项！请重试！！！")
                    continue
            except ValueError:
                print("非法输入，请输入整数数字，请重试！")
                continue
        # 输入优化次数
        while True:
            try:
                num = int(input("请输入算法优化次数："))
                break
            except ValueError:
                print("请输入整数数字，请重试！")
                continue
        # 输入策略参数的优化范围
        while True:
            judge = True
            try:
                for i in range(2):  # 对于参数N1和N2
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
                if judge:
                    break  # 参数范围输入正确，退出循环
                else:
                    continue
            except ValueError:
                print("非法输入，请重试！")
                n1_list.clear()
                n2_list.clear()
                continue

        print(num, n1_list, n2_list)  # 输出优化次数和参数范围
        return name, num, n1_list, n2_list  # 返回优化信息

    @staticmethod
    def printOptParameters(name, optimal_pars):
        """
        打印参数优化后的最优参数信息。
        :param name: 优化算法名称
        :param optimal_pars: 最优参数的字典
        """
        print(f'采用{name}算法优化后的参数信息:')
        print('N1 = %.2f' % optimal_pars['N1'])
        print('N2 = %.2f' % optimal_pars['N2'])


# =============== 策略参数优化类 ==================

class StrategyOptimization:
    """
    策略参数优化类，用于执行策略的参数优化流程，支持对不同策略和回测模式进行优化。
    """

    @staticmethod
    def strategy_optimization_flow(symbol_list, start_date, end_date):
        """
        策略参数优化的主要流程函数，负责设置回测引擎、加载数据、执行优化过程等。

        :param symbol_list: 品种代码列表
        :param start_date: 回测开始日期（格式：YYYYMMDD）
        :param end_date: 回测结束日期（格式：YYYYMMDD）
        """
        cerebro = bt.Cerebro()  # 创建Backtrader的回测引擎实例
        BackTestSetup.set_cerebro(cerebro=cerebro, opt_judge=True)  # 设置回测引擎的参数

        # 加载数据到回测引擎中
        for symbol in symbol_list:
            DataGet.get_data(codes=symbol, cerebro=cerebro, start_date=start_date, end_date=end_date)

        # 定义独立资金池策略的优化函数
        def runSoloCashOpt(N1, N2):
            cerebro.addstrategy(OptSoloCash, N1=N1, N2=N2)  # 添加策略到回测引擎
            return cerebro.broker.getvalue()  # 返回回测结束时的资金价值

        # 定义共享资金池策略的优化函数
        def runSharedCashOpt(N1, N2):
            cerebro.addstrategy(OptSharedCash, N1=N1, N2=N2)  # 添加策略到回测引擎
            return cerebro.broker.getvalue()  # 返回回测结束时的资金价值

        # 获取用户输入的优化算法、次数和参数范围
        print("*************************************************************************************")
        name, num, n1_list, n2_list = DataIO.input_OptInformation()

        while True:
            # 选择策略优化的回测模式
            choose = input("请选择策略优化所使用的回测模式：\n1.批量独立资金池回测\n2.共享资金池回测\n(输入：“0”结束选择)\n")

            if choose == "1":
                # 执行独立资金池策略的参数优化
                opt = optunity.maximize(f=runSoloCashOpt,
                                        num_evals=num,
                                        solver_name=name,
                                        N1=n1_list,
                                        N2=n2_list)
                optimal_pars, details, _ = opt

                DataIO.printOptParameters(name, optimal_pars=optimal_pars)  # 输出最优参数信息
                break
            if choose == "2":
                # 为共享资金池策略创建新的回测引擎实例
                cerebro_new = bt.Cerebro()
                BackTestSetup.set_cerebro(cerebro=cerebro_new, opt_judge=True)
                for symbol in symbol_list:
                    DataGet.get_data(codes=symbol, cerebro=cerebro_new, start_date=start_date, end_date=end_date)
                # 执行共享资金池策略的参数优化
                opt = optunity.maximize(f=runSharedCashOpt,
                                        num_evals=num,
                                        solver_name=name,
                                        N1=n1_list,
                                        N2=n2_list)
                optimal_pars, details, _ = opt

                DataIO.printOptParameters(name, optimal_pars=optimal_pars)  # 输出最优参数信息
                break
            if choose == "0":
                break  # 结束选择
            if choose == "":
                print("输入为空！请重试！！！")
                continue
            else:
                print("非法输入！请重试！！！")
                continue


# =============== 回测设置控制类 ==================

class BackTestSetup:
    """
    回测设置控制类，用于统一设置回测引擎的参数，如初始资金、手续费、分析器等。
    """

    @staticmethod
    def set_cerebro(cerebro, opt_judge):
        """
        配置回测引擎的通用参数。

        :param cerebro: Backtrader的回测引擎实例
        :param opt_judge: 是否进行参数优化的标志，True表示优化模式，不添加分析器和绘图元素
        """
        public_cash = 100000000  # 设置初始资金为一亿
        commission = 0.00025      # 设置交易手续费率

        cerebro.broker.setcash(public_cash)  # 设置初始资金
        cerebro.broker.set_coc(False)        # 设置是否在下一个bar执行订单，False表示在当前bar执行
        cerebro.broker.setcommission(commission=commission)  # 设置交易手续费

        if not opt_judge:
            # 如果不是优化模式，添加分析器和绘图元素
            DataIO.add_analysers(cerebro=cerebro)       # 添加回测分析器
            DataIO.add_plotElements(cerebro=cerebro)    # 添加绘图元素
        print("数据加载中.....")
        time.sleep(2)  # 模拟数据加载时间
        if not opt_judge:
            print("回测进行中....")
            time.sleep(2)  # 模拟回测执行时间
  

  # =============== 主控制类 ==================

class MainController:
    @staticmethod
    def start():
        """
        程序的主入口，提供用户交互菜单，允许用户选择不同的功能。
        """
        while True:
            print("*************************************************************************************")
            choose = input("请选择功能：\n1.批量独立资金池回测\n2.共享资金池回测\n3.策略参数优化\n(输入：“*”退出系统)\n")

            if choose == "1":
                # 获取用户输入的股票代码、起始日期和结束日期
                codes, start_date, end_date = DataIO.input_stockInformation()
                # 执行批量独立资金池回测
                BackTest.batch_test(symbol_list=codes, start_date=start_date, end_date=end_date)
                continue
            elif choose == "2":
                # 获取用户输入的股票代码、起始日期和结束日期
                codes, start_date, end_date = DataIO.input_stockInformation()
                # 执行共享资金池回测
                BackTest.shared_cash_test(symbol_list=codes, start_date=start_date, end_date=end_date)
                continue
            elif choose == "3":
                # 获取用户输入的股票代码、起始日期和结束日期
                codes, start_date, end_date = DataIO.input_stockInformation()
                # 执行策略参数优化流程
                StrategyOptimization.strategy_optimization_flow(symbol_list=codes, start_date=start_date,
                                                                end_date=end_date)
                continue
            elif choose == "*":
                # 退出系统
                print("系统已退出！")
                break
            elif choose == "":
                # 输入为空的情况
                print("输入为空！请重试！！！")
                continue
            else:
                # 输入非法字符的情况
                print("非法输入！请重试！！！")
                continue


if __name__ == '__main__':
    # 程序入口，启动主控制器
    MainController.start()
