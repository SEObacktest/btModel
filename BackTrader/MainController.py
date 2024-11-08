from DataIO import DataIO
from BackTest_Control import BackTest
import StrategyOptimization
class MainController:
    @staticmethod
    def start():
        """
        程序的主入口，提供用户交互菜单，允许用户选择不同的功能。
        """
        while True:
            print("*************************************************************************************")
            choose = input("请选择功能：\n1.批量独立资金池回测\n2.共享资金池回测\n3.策略参数优化\n(输入：“*”退出系统)\n")

            if choose == "1":
                # 获取用户输入的股票代码、起始日期和结束日期
                codes, start_date, end_date = DataIO.input_stockInformation()
                # 执行批量独立资金池回测
                BackTest.batch_test(symbol_list=codes, start_date=start_date, end_date=end_date)
                continue
            elif choose == "2":
                # 获取用户输入的股票代码、起始日期和结束日期
                codes, start_date, end_date = DataIO.input_stockInformation()
                # 执行共享资金池回测
                BackTest.shared_cash_test(symbol_list=codes, start_date=start_date, end_date=end_date)
                continue
            elif choose == "3":
                # 获取用户输入的股票代码、起始日期和结束日期
                codes, start_date, end_date = DataIO.input_stockInformation()
                # 执行策略参数优化流程
                StrategyOptimization.strategy_optimization_flow(symbol_list=codes, start_date=start_date,
                                                                end_date=end_date)
                continue
            elif choose == "*":
                # 退出系统
                print("系统已退出！")
                break
            elif choose == "":
                # 输入为空的情况
                print("输入为空！请重试！！！")
                continue
            else:
                # 输入非法字符的情况
                print("非法输入！请重试！！！")
                continue


