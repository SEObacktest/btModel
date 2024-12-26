import backtrader as bt
from tools.data_get import DataGet
from backtest_setup import BackTestSetup
import backtrader as bt
from tools.data_get import DataGet
from backtest_setup import BackTestSetup
from solo_cash_pool import Solo_cash_pool
from tools.data_io import DataIO
from backtrader_plotting import Bokeh  # 导入Bokeh模块，用于绘制回测结果的图表
from backtrader_plotting.schemes import Tradimo  # 导入Bokeh的绘图方案
from shared_cash_pool import Shared_cash_pool
from shared_cash_pool_pointing import Shared_Cash_Pool_Pointing
from shared_cash_peak_valley import Shared_Cash_Peak_Valley
import pandas as pd
from backtrader.comminfo import ComminfoFuturesPercent,ComminfoFuturesFixed
from tools.db_mysql import get_engine
import time
from itertools import product
from multiprocessing import Pool
from multi import run

class BackTest:
    @staticmethod
    def preload_data(code_list, period):
        """预加载数据到缓存"""
        print("预加载数据到缓存...")
        cerebro = bt.Cerebro()  # 临时创建一个cerebro实例用于数据加载
        DataGet.get_fut_data(cerebro=cerebro, codes=code_list, period=period)
        print("数据预加载完成")

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

    def shared_cash_fut_pointing_mutil(code_list, name_list, start_date, end_date, period, margins, mults):
        start_time = time.time()
        BackTest.preload_data(code_list, period)
        EMA26_list = range(10, 20, 5)  # 接下来几行是预备多线并发的参数优化，可以忽略
        EMA12_list=range(8,18,5)
        EMA9_list=range(5,15,5)
        start_full = DataGet.get_str_to_datetime(start_date)
        end_full = DataGet.get_str_to_datetime(end_date)  # datetime.datetime格式
        params_combinations = [(code_list, name_list, start_full, end_full, period, margins, mults, ema26, ema12, ema9)
                               for ema26, ema12, ema9 in product(EMA26_list, EMA12_list, EMA9_list)]
        # params = [(code_list, name_list, start_full, end_full, period, margins, mults, ema26)
        #                        for ema26 in product(EMA26_list)]
        with Pool(12) as p:
            results = p.map(run, params_combinations)
        # df = pd.DataFrame(results, columns=['EMA26', 'EMA12', 'EMA9'])
        df = pd.DataFrame(results, columns=['EMA26'])
        # df.to_csv("./result/共享资金池打分回测结果.csv")
        print("========共享资金池打分回测========")
        print(f"品种：{name_list}")
        print(f"回测区间：{start_full}至{end_full}")
        # DataIO.text_report(cerebro=cerebro, strat=strat)  # 输出回测报告
        print("========共享资金池打分回测========")
        # 记录结束时间并计算总耗时
        end_time = time.time()
        elapsed_time = end_time - start_time
        print("花费时间：", elapsed_time)

    def shared_cash_fut_pointing_test(code_list,name_list, start_date, end_date,period,margins,mults):
        """
        使用共享资金池进行打分回测
        :param code_list: 品种代码列表
        :param name_list: 品种名称列表
        :param start_date: 回测开始日期
        :param end_date: 回测结束日期
        :param period: 回测周期
        :param margins: 保证金比例列表
        :param mults: 合约乘数列表
        """
        # 记录开始时间
        start_time = time.time()
        cerebro = bt.Cerebro(stdstats=False)  # 创建Backtrader回测引擎
        cerebro.broker.set_coc(True)#启用未来数据
        #cerebro.broker.set_slippage_fixed(1)#固定滑点为1
        BackTestSetup.set_cerebro(cerebro=cerebro, opt_judge=False)  # 设置回测引擎
        time1 = time.time()
        DataGet.get_fut_data(cerebro=cerebro,
                             codes=code_list,
                             period=period)  # 获取数据
        print('获取数据花费时间：', time1 - start_time)
        for i,name in enumerate(name_list):
            margin = margins[i]
            mult = mults[i]
            comm=ComminfoFuturesPercent(commission=0.0001,margin=margin,mult=mult)
            #comm=ComminfoFuturesPercent(commission=0,margin=margin,mult=mult)
            #把手续费、保证金和合约乘数打包作为一个整体参数，注意这里的
            #ComminfoFuturesPercent是在库里面重写的方法，源码要在CSDN
            #上看
            cerebro.broker.addcommissioninfo(comm,name=name)
            #设定参数
        start_full = DataGet.get_str_to_datetime(start_date)
        end_full = DataGet.get_str_to_datetime(end_date)  # datetime.datetime格式
        cerebro.addstrategy(Shared_Cash_Pool_Pointing,
                            backtest_start_date=start_full,
                            backtest_end_date=end_full,
                            EMA26=26,
                            EMA12=12,
                            EMA9=9)

        cerebro.run()#运行回测，使用所有可用的 CPU

        print("========共享资金池打分回测========")
        print(f"品种：{name_list}")
        print(f"回测区间：{start_full}至{end_full}")
        #DataIO.text_report(cerebro=cerebro, strat=strat)  # 输出回测报告
        print("========共享资金池打分回测========")
        # 记录结束时间并计算总耗时
        end_time = time.time()
        elapsed_time = end_time - start_time
        print("花费时间：", elapsed_time)
        #pic = Bokeh(style='bar', plot_mode='single', scheme=Tradimo())  # 使用Bokeh绘图
        #cerebro.plot(pic)  # 绘制回测结果'''

    def shared_cash_pointing_test(symbol_list, start_date, end_date):

        """
        使用共享资金池进行打分回测
        :param symbol_list: 品种代码列表
        :param start_date: 回测开始日期
        :param end_date: 回测结束日期
        """
        cerebro = bt.Cerebro()  # 创建Backtrader回测引擎
        cerebro.broker.set_coc(True)
        BackTestSetup.set_cerebro(cerebro=cerebro, opt_judge=False)  # 设置回测引擎
        cerebro.addstrategy(Shared_Cash_Pool_Pointing,backtest_start_date=DataGet.get_date_from_int(start_date),backtest_end_date=DataGet.get_date_from_int(end_date))  # 添加策略（打分策略）
        DataGet.get_data(cerebro=cerebro, codes=symbol_list, start_date=start_date, end_date=end_date)  # 获取数据
        strat = cerebro.run()[0]  # 运行回测并获取策略实例
        print("========共享资金池打分回测========")
        print(f"品种：{symbol_list}")
        print(f"回测区间：{DataGet.get_date_from_int(start_date)}至{DataGet.get_date_from_int(end_date)}")
        DataIO.text_report(cerebro=cerebro, strat=strat)  # 输出回测报告
        print("========共享资金池打分回测========")

