from shared_cash_pool_pointing import Shared_Cash_Pool_Pointing
from tools.data_io import *
from backtest_setup import BackTestSetup
from backtrader.comminfo import ComminfoFuturesPercent,ComminfoFuturesFixed
from shared_cash_pool_pointing_opt import Shared_Cash_Pool_Pointing_Opt
import time


def setup_cerebro(code_list, name_list, per, margins, mults):
    cerebro = bt.Cerebro(stdstats=False)  # 创建Backtrader回测引擎
    cerebro.broker.set_coc(True)  # 启用未来数据
    # cerebro.broker.set_slippage_fixed(1)  # 固定滑点为1
    BackTestSetup.set_cerebro(cerebro=cerebro, opt_judge=False,is_preloaded=True)  # 设置回测引擎
    DataGet.get_fut_data(cerebro=cerebro,
                         codes=code_list,
                         period=per)  # 获取数据
    for i,name in enumerate(name_list):
        margin = margins[i]
        mult = mults[i]
        comm=ComminfoFuturesPercent(commission=0.0001,margin=margin,mult=mult)
        #把手续费、保证金和合约乘数打包作为一个整体参数，注意这里的
        #ComminfoFuturesPercent是在库里面重写的方法，源码要在CSDN上看
        cerebro.broker.addcommissioninfo(comm,name=name)
    return cerebro

def run(params):
    code_list, name_list, start_full, end_full, per, margins, mults, ema26,ema12,ema9 = params
    cerebro = setup_cerebro(code_list, name_list, per, margins, mults)
    # cerebro=bt.Cerebro(stdstats=False)
    cerebro.broker.set_coc(True)
    BackTestSetup.set_cerebro(cerebro=cerebro, opt_judge=False) 
    kwags = {'EMA26':params[0],
             'EMA12':params[1],
             'EMA9':params[2]}
    cerebro.addstrategy(Shared_Cash_Pool_Pointing_Opt,
                        backtest_start_date=start_full,
                        backtest_end_date=end_full,
                        EMA26=ema26,
                        EMA12=ema12,
                        EMA9=ema9
                        )
    cerebro.run(maxcpus=None)
    return [ema26]