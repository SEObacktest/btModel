import backtrader as bt
from DataGet import DataGet
from DataIO import DataIO
from OptSoloCash import OptSoloCash
from OptSharedCash import OptSharedCash
import optunity
from BackTest_Control import BackTestSetup


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