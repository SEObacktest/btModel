from shared_cash_pool_pointing import Shared_Cash_Pool_Pointing
from tools.data_io import *
from backtest_setup import BackTestSetup
from backtrader.comminfo import ComminfoFuturesPercent,ComminfoFuturesFixed



def setup_cerebro(symbol_list, start_date, end_date):
    cerebro = bt.Cerebro()  # 创建Backtrader回测引擎
    cerebro.broker.set_coc(True)  # 启用未来数据
    cerebro.broker.set_slippage_fixed(1)  # 固定滑点为1
    BackTestSetup.set_cerebro(cerebro=cerebro, opt_judge=False)  # 设置回测引擎
    DataGet.get_fut_data(cerebro=cerebro,
                         codes=symbol_list,
                         start_date=start_date,
                         end_date=end_date)  # 获取数据

    info = pd.read_csv('datasets/future_codes.csv')  # 读取合约信息，保证金比例，手续费比例
    for code in symbol_list:
        margin = info[info['code'] == code]['保证金比例'].iloc[0]  # 取得保证金
        mult = info[info['code'] == code]['合约乘数'].iloc[0]  # 取得合约乘数
        comm = ComminfoFuturesPercent(margin=margin, mult=mult)
        cerebro.broker.addcommissioninfo(comm, name=code)

    return cerebro

def run(params):
    symbol_list, start_date, end_date, ema26, ema12, ema9 = params
    cerebro = setup_cerebro(symbol_list, start_date, end_date)
    # kwags = {'EMA26':params[0],
    #          'EMA12':params[1],
    #          'EMA9':params[2]}
    cerebro.addstrategy(Shared_Cash_Pool_Pointing,
                        backtest_start_date=DataGet.get_date_from_int(start_date),
                        backtest_end_date=DataGet.get_date_from_int(end_date),
                        EMA26=ema26,
                        EMA12=ema12,
                        EMA9=ema9)
    cerebro.run()
    return [ema26, ema12, ema9]