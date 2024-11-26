import backtrader as bt
from tools import DataGet
from shared_cash_pool_pointing import Shared_Cash_Pool_Pointing
class Test():

    def start_test(self):
        cerebro=bt.Cerebro()
        cerebro.broker.set_coc(True)
        DataGet.get_data(['000001.SZ','000002.SZ','000003.SZ'],cerebro,start_date=20200101,end_date=20200401)
        cerebro.addstrategy(Shared_Cash_Pool_Pointing,backtest_start_date=DataGet.get_date_from_int(20200101),backtest_end_date=DataGet.get_date_from_int(20200401))
        cerebro.run()[0]


test=Test()
test.start_test()


