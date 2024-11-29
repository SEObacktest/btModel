import time,datetime
import numpy as np
import pandas as pd
import backtrader as bt
from multiprocessing import Pool
from itertools import product
from shared_cash_pool_pointing import Shared_Cash_Pool_Pointing
from tools.data_get import DataGet
from tools.data_io import *
import config


def run(params,start_date=config.start_date,end_date=config.end_date):
    cerebro=bt.Cerebro()
    kwags={"EMA26":params[0],
        "EMA12":params[1],
        "EMA9":params[2]}
        #codes,start_date,end_date=DataIO.input_futureInformation()
    cerebro.addstrategy(Shared_Cash_Pool_Pointing,
                        backtest_start_date=DataGet.get_date_from_int(start_date),
                        backtest_end_date=DataGet.get_date_from_int(end_date),
                        **kwags)

    cerebro.run()

    '''if __name__=="__main__":
        EMA26_list=range(10,20,5)
        EMA12_list=range(8,18,5)
        EMA9_list=range(5,15,5)
        params_list=product(product(EMA26_list,EMA12_list),EMA9_list)
        with Pool(3) as p:
            results=p.map(run,params_list)'''