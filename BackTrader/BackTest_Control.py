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
from multi import run,localrun

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

    def shared_cash_fut_pointing_mutil(code_list, name_list, start_date, end_date, period, margins, mults):
        #记录开始时间
        start_time = time.time()
        EMA26_list = range(10, 20, 5)  # 接下来几行是预备多线并发的参数优化，可以忽略
        EMA12_list=range(8,18,5)
        EMA9_list=range(5,15,5)

        #将日期字符串格式（yyyyMMdd、yyyyMMddHHmm、yyyyMMddHHmmss）转换为日期对象。
        start_full = DataGet.get_str_to_datetime(start_date)
        end_full = DataGet.get_str_to_datetime(end_date)  # datetime.datetime格式

        # 创建参数组合列表，用于回测时的参数优化
        # 使用嵌套的笛卡尔积生成所有可能的参数组合
        # 每个组合包括：
        # - code_list: 品种代码列表
        # - name_list: 品种名称列表
        # - start_full: 回测起始时间（datetime 格式）
        # - end_full: 回测结束时间（datetime 格式）
        # - period: 回测周期（如分钟线、日线等）
        # - margins: 保证金比例列表
        # - mults: 合约乘数列表
        # - ema26, ema12, ema9: 不同的移动平均线周期参数
        params_combinations = [(code_list, name_list, start_full, end_full, period, margins, mults, ema26, ema12, ema9)
                               for ema26, ema12, ema9 in product(EMA26_list, EMA12_list, EMA9_list)]

        # params = [(code_list, name_list, start_full, end_full, period, margins, mults, ema26)
        #                        for ema26 in product(EMA26_list)]

        #用户输入数据获取方式
        sqlOrlocal = input("数据获取：1.数据库 2.本地\n")

        if sqlOrlocal == '1':
            # 数据库读数据
            # 使用多进程池并行运行回测任务
            # Pool(12): 创建一个包含 12 个进程的进程池，用于并行处理任务
            # p.map(run, params_combinations): 将参数组合列表 (params_combinations) 中的每个参数组
            # 传递给函数 run 进行处理，并行运行所有回测任务
            # - run: 回测的核心逻辑函数
            # - params_combinations: 所有参数组合，每个组合对应一个回测任务
            # 结果 (results) 是一个包含每个回测任务返回值的列表
            with Pool(12) as p:
                results = p.map(run, params_combinations)
        #如何选择本地则读取本地csv文件
        elif sqlOrlocal == '2':
            # 读取本地csv数据
            with Pool(12) as p:
                results = p.map(localrun, params_combinations)
        else:
            print("非法输入请重试")



        # df = pd.DataFrame(results, columns=['EMA26', 'EMA12', 'EMA9'])

        df = pd.DataFrame(results, columns=['EMA26'])

        # df.to_csv("./result/共享资金池打分回测结果.csv")

        print("========共享资金池打分回测========")
        #打印回测品种
        print(f"品种：{name_list}")
        #打印回测时间区间
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

        # 创建一个 Backtrader 的 Cerebro 引擎实例，用于管理回测框架
        # 参数 stdstats=False 表示关闭默认统计指标的绘制
        # 1. 默认情况下，Cerebro 会绘制一些标准统计指标（如盈亏曲线、杠杆率等）。
        # 2. 设置 stdstats=False 可以禁用这些默认统计，以便用户添加自定义的分析和绘图逻辑。
        cerebro = bt.Cerebro(stdstats=False)

        # 设置交易代理（broker）的订单成交模式
        # cerebro.broker.set_coc(True) 启用 "Close on Close" 模式
        # 1. 当设置为 True 时：
        #    - 允许订单在当前 K 线内（即当前时间段）成交，通常按当前 K 线的价格范围执行。
        #    - 适合快速响应的策略或需要高频交易的回测场景。
        # 2. 如果设置为 False（默认值）：
        #    - 订单需要等待下一根 K 线（即下一时间段的数据）才能成交。
        #    - 更贴近真实交易中的订单处理方式。
        cerebro.broker.set_coc(True)  # 启用未来数据

        #cerebro.broker.set_slippage_fixed(1)  # 固定滑点为1

        # 调用 BackTestSetup 类的 set_cerebro 方法，用于配置回测框架
        # 参数说明：
        # 1. cerebro=cerebro：将已经创建好的 Cerebro 引擎实例传递给 BackTestSetup，用于管理回测流程。
        # 2. opt_judge=False：禁用优化模式判断，表示当前回测不进行参数优化。
        #    - 如果 opt_judge=True，则可能会启动参数优化流程。
        # 这段代码的目的是初始化和配置回测环境，确保回测按照预期的逻辑运行
        BackTestSetup.set_cerebro(cerebro=cerebro, opt_judge=False)  # 设置回测引擎

        print("*************************************************************************************")
        # 让用户选择回测数据来源
        sqlOrlocal=input("数据获取：1.数据库 2.本地\n")

        # 记录开始时间
        start_time = time.time()

        #如果选择数据库就数据库读取数据

        if sqlOrlocal == '1':
            # 数据库读数据
            DataGet.get_fut_data(cerebro=cerebro, codes=code_list, period=period)
        #如何选择本地则读取本地csv文件
        elif sqlOrlocal == '2':
            # 读取本地csv数据
            filepath = r"C:\Users\10643\OneDrive\桌面\工作\BackTrader\database\future.csv"
            DataGet.get_fut_data_from_csv(cerebro=cerebro, codes=code_list, period=period, csv_file=filepath)
        else:
            print("非法输入请重试")

            #sqltextFile读数据
        # sqlFilepath=r"C:\Users\10643\OneDrive\桌面\工作\BackTrader\database\future_2024-12-24_11-40-39_mysql_data_0U48z.sql"
        # DataGet.get_fut_data_from_file(file_path=sqlFilepath, codes=code_list, cerebro=cerebro, period=period)

        #记录数据获取结束时间
        time1 = time.time()
        #打印结束时间
        print('获取数据花费时间：', time1 - start_time)

        # 遍历每个交易品种，设置对应的保证金比例、合约乘数和手续费率
        for i, name in enumerate(name_list):
            # 获取当前品种对应的保证金比例和合约乘数
            margin = margins[i]
            mult = mults[i]

            # 创建一个期货交易参数对象（包含手续费率、保证金比例和合约乘数）
            # 注意：ComminfoFuturesPercent 是自定义的类，用于定义这些交易参数
            # commission=0.0001 表示手续费率为 0.01%（交易金额的万分之一）
            # margin=margin 指定当前品种的保证金比例
            # mult=mult 指定当前品种的合约乘数
            comm=ComminfoFuturesPercent(commission=0.0001,margin=margin,mult=mult)
            #comm=ComminfoFuturesPercent(commission=0,margin=margin,mult=mult)
            #把手续费、保证金和合约乘数打包作为一个整体参数，注意这里的
            #ComminfoFuturesPercent是在库里面重写的方法，源码要在CSDN
            #上看

            # 将该交易参数对象添加到回测引擎的 broker 中，并指定适用的品种名称
            # 通过这种方式，每个品种的交易规则可以独立配置并应用到回测中
            cerebro.broker.addcommissioninfo(comm,name=name)

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

