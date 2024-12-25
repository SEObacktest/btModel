from shared_cash_pool_pointing import Shared_Cash_Pool_Pointing
from tools.data_io import *
from backtest_setup import BackTestSetup
from backtrader.comminfo import ComminfoFuturesPercent,ComminfoFuturesFixed
import time


#设置cerebre基础参数并，让cerebro获取对应数据
def setup_cerebro(code_list, name_list, per, margins, mults):
    cerebro = bt.Cerebro(stdstats=False)  # 创建Backtrader回测引擎
    cerebro.broker.set_coc(True)  # 启用未来数据
    # cerebro.broker.set_slippage_fixed(1)  # 固定滑点为1
    BackTestSetup.set_cerebro(cerebro=cerebro, opt_judge=False)  # 设置回测引擎

    #获取数据开始时间
    data_startTime = time.time()

    #数据库数据获取
    DataGet.get_fut_data(cerebro=cerebro,
                         codes=code_list,
                         period=per)  # 获取数据

    #获取数据 结束时间
    data_endTime = time.time()

    #打印获取数据时间
    # print("获取数据使用时间：", data_endTime - data_startTime)

    for i,name in enumerate(name_list):
        margin = margins[i]
        mult = mults[i]
        comm=ComminfoFuturesPercent(commission=0.0001,margin=margin,mult=mult)
        #把手续费、保证金和合约乘数打包作为一个整体参数，注意这里的
        #ComminfoFuturesPercent是在库里面重写的方法，源码要在CSDN上看
        cerebro.broker.addcommissioninfo(comm,name=name)
    return cerebro

def localsetup_cerebro(code_list, name_list, per, margins, mults):
    cerebro = bt.Cerebro(stdstats=False)  # 创建Backtrader回测引擎
    cerebro.broker.set_coc(True)  # 启用未来数据
    # cerebro.broker.set_slippage_fixed(1)  # 固定滑点为1
    BackTestSetup.set_cerebro(cerebro=cerebro, opt_judge=False)  # 设置回测引擎

    # 获取数据开始时间
    data_startTime = time.time()

    # 读取本地csv数据
    filepath = r"C:\Users\10643\OneDrive\桌面\工作\BackTrader\database\future.csv"
    DataGet.get_fut_data_from_csv(cerebro=cerebro, codes=code_list, period=per, csv_file=filepath)

    # 获取数据 结束时间
    data_endTime = time.time()

    # 打印获取数据时间
    # print("获取数据使用时间：", data_endTime - data_startTime)

    for i,name in enumerate(name_list):
        margin = margins[i]
        mult = mults[i]
        comm=ComminfoFuturesPercent(commission=0.0001,margin=margin,mult=mult)
        #把手续费、保证金和合约乘数打包作为一个整体参数，注意这里的
        #ComminfoFuturesPercent是在库里面重写的方法，源码要在CSDN上看
        cerebro.broker.addcommissioninfo(comm,name=name)
    return cerebro

def run(params):
    #获取params元组的信息和参数，方便之后进行回测
    code_list, name_list, start_full, end_full, per, margins, mults, ema26,ema12,ema9 = params
    #设置cerebro和获取数据
    cerebro = setup_cerebro(code_list, name_list, per, margins, mults)
    # cerebro=bt.Cerebro(stdstats=False)

    #设置线内结算
    cerebro.broker.set_coc(True)

    # 配置回测框架
    # 将已创建的 Cerebro 实例传递给 BackTestSetup，并禁用优化模式（opt_judge=False
    BackTestSetup.set_cerebro(cerebro=cerebro, opt_judge=False) 
    kwags = {'EMA26':params[0],
             'EMA12':params[1],
             'EMA9':params[2]}
    # 添加策略到 Cerebro
    # Shared_Cash_Pool_Pointing 是策略类
    # 传递回测的起始日期、结束日期和移动平均线参数（EMA26、EMA12、EMA9）
    cerebro.addstrategy(Shared_Cash_Pool_Pointing,
                        backtest_start_date=start_full,
                        backtest_end_date=end_full,
                        EMA26=ema26,
                        EMA12=ema12,
                        EMA9=ema9
                        )

    # 执行回测
    # maxcpus=None 允许使用多核 CPU 提高回测性能
    cerebro.run(maxcpus=None)

    # 返回当前回测使用的 EMA26 参数值
    # 这通常用于记录或分析参数对回测结果的影响
    return [ema26]

def localrun(params):
    #获取params元组的信息和参数，方便之后进行回测
    code_list, name_list, start_full, end_full, per, margins, mults, ema26,ema12,ema9 = params
    #设置cerebro和获取数据
    cerebro = localsetup_cerebro(code_list, name_list, per, margins, mults)
    # cerebro=bt.Cerebro(stdstats=False)

    #设置线内结算
    cerebro.broker.set_coc(True)

    # 配置回测框架
    # 将已创建的 Cerebro 实例传递给 BackTestSetup，并禁用优化模式（opt_judge=False
    BackTestSetup.set_cerebro(cerebro=cerebro, opt_judge=False)
    kwags = {'EMA26':params[0],
             'EMA12':params[1],
             'EMA9':params[2]}
    # 添加策略到 Cerebro
    # Shared_Cash_Pool_Pointing 是策略类
    # 传递回测的起始日期、结束日期和移动平均线参数（EMA26、EMA12、EMA9）
    cerebro.addstrategy(Shared_Cash_Pool_Pointing,
                        backtest_start_date=start_full,
                        backtest_end_date=end_full,
                        EMA26=ema26,
                        EMA12=ema12,
                        EMA9=ema9
                        )

    # 执行回测
    # maxcpus=None 允许使用多核 CPU 提高回测性能
    cerebro.run(maxcpus=None)

    # 返回当前回测使用的 EMA26 参数值
    # 这通常用于记录或分析参数对回测结果的影响
    return [ema26]