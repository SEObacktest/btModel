'''from tools.data_io import DataIO
import time


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
        #commission = 0.00025      # 设置交易手续费率
        commission=0
        cerebro.broker.setcash(public_cash)  # 设置初始资金
        cerebro.broker.setcommission(commission=commission)  # 设置交易手续费

        if not opt_judge:
            pass
            # 如果不是优化模式，添加分析器和绘图元素
            #DataIO.add_analysers(cerebro=cerebro)       # 添加回测分析器
            #DataIO.add_plotElements(cerebro=cerebro)    # 添加绘图元素
        print("数据加载中.....")
        time.sleep(2)  # 模拟数据加载时间
        if not opt_judge:
            print("回测进行中....")
            time.sleep(2)  # 模拟回测执行时间'''

from tools.data_io import DataIO
from tools.data_get import DataGet
import time
import backtrader as bt

class BackTestSetup:
    """
    回测设置控制类，用于统一设置回测引擎的参数，如初始资金、手续费、分析器等。
    """
    
    @staticmethod
    def preload_data_setup(code_list, period):
        """
        预加载数据到缓存的专用设置
        
        :param code_list: 需要预加载的代码列表
        :param period: 数据周期
        """
        print("开始预加载数据到缓存...")
        temp_cerebro = bt.Cerebro()  # 创建临时cerebro实例
        # 仅用于数据加载，不需要其他设置
        DataGet.get_fut_data(cerebro=temp_cerebro, codes=code_list, period=period)
        print("数据预加载完成")

    @staticmethod
    def set_cerebro(cerebro, opt_judge, is_preloaded=False):
        """
        配置回测引擎的通用参数。

        :param cerebro: Backtrader的回测引擎实例
        :param opt_judge: 是否进行参数优化的标志
        :param is_preloaded: 数据是否已预加载的标志
        """
        public_cash = 100000000  # 设置初始资金为一亿
        commission = 0
        cerebro.broker.setcash(public_cash)
        cerebro.broker.setcommission(commission=commission)

        if not opt_judge:
            pass
            # 如果不是优化模式，添加分析器和绘图元素
            #DataIO.add_analysers(cerebro=cerebro)
            #DataIO.add_plotElements(cerebro=cerebro)
        
        if not is_preloaded:
            print("数据加载中.....")
            time.sleep(2)
        else:
            print("使用预加载的缓存数据.....")
            
        if not opt_judge:
            print("回测进行中....")
            time.sleep(2)
  