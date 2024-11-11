import backtrader as bt
from DataGet import DataGet
from BackTestSetup import BackTestSetup
from Solo_cash_pool import Solo_cash_pool
from DataIO import DataIO
from backtrader_plotting import Bokeh  # 导入Bokeh模块，用于绘制回测结果的图表
from backtrader_plotting.schemes import Tradimo  # 导入Bokeh的绘图方案
from Shared_cash_pool import Shared_cash_pool

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
        cerebro.broker.set_coc(True) 
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