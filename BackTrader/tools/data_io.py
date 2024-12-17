from .data_get import DataGet
import pandas as pd
import datetime
from backtrader.analyzers import *
import numpy as np
import tools.log_func as log
import config
from db_mysql import get_engine

class DataIO():
    """
    数据输入输出类，提供与用户交互的功能，包括获取股票代码、选择回测指标、设置参数优化等。
    """

    start_date=None
    end_date=None

    def __init__(self):
        self.start_date=None
        self.end_date=None
        
    @staticmethod
    def get_stock_codes():
        """
        获取当前所有正常上市交易的股票列表，并将其保存到本地文件'codes.csv'中。
        """
        # 登录Tushare获取数据接口
        pro = DataGet.login_ts()
        # 获取上市状态为'L'（上市）的股票基本信息
        data = pro.stock_basic(exchange='', list_status='L', fields='ts_code,name,area,industry,list_date')
        # 重命名列名为中文，方便显示
        new_col = ['code', '股票名', '地区', '行业', '上市日期']
        data.columns = new_col
        # 将股票列表保存为CSV文件
        data.to_csv("codes.csv")
        # 打印当前上市交易的品种列表
        print("========现有上市交易品种列表========")
        print(data)
        print("================================")
    @staticmethod
    def get_future_codes():
        # 登录Tushare获取数据接口
        pro = DataGet.login_ts()
        # 获取上市状态为'L'（上市）的股票基本信息
        data = pro.fut_basic(exchange='CFFEX', fut_type=2, fields='ts_code,name,list_date,delist_date,multiplier,per_unit')
        # 重命名列名为中文，方便显示
        new_col = ['code', '期货名', '上市日期','最后交易日期','合约乘数','每手交易单位']
        data.columns = new_col
        exchange_list=['DCE','CZCE','SHFE','INE','GFEX']
        for exchange_name in exchange_list:
            data_new = pro.fut_basic(exchange=exchange_name, fut_type=2, fields='ts_code,name,list_date,delist_date,multiplier,per_unit')
            # 重命名列名为中文，方便显示
            new_col = ['code', '期货名', '上市日期','最后交易日期','合约乘数','每手交易单位']
            data_new.columns = new_col
            data=pd.concat([data,data_new],axis=0)
        # 将股票列表保存为CSV文件
        data.to_csv("future_codes_info.csv")
        # 打印当前上市交易的品种列表
        print("========交易品种列表========")
        print(data)
        print("================================")

    def get_future_info():
        # 登录Tushare获取数据接口
        pro = DataGet.login_ts()
        # 获取上市状态为'L'（上市）的股票基本信息
        data = pro.fut_settle(exchange='CFFEX',trade_date='2024-11-25')
        # 重命名列名为中文，方便显示
        #new_col = ['code', '期货名', '上市日期','最后交易日期','合约乘数','每手交易单位']
        #data.columns = new_col
        exchange_list=['DCE','CZCE','SHFE','INE','GFEX']
        for exchange_name in exchange_list:
            data_new = pro.fut_settle(exchange=exchange_name,trade_date='2024-11-25')
            #new_col = ['code', '交易日期','手续费率','买保证金率','卖保证金率']
            #data_new.columns = new_col
            data=pd.concat([data,data_new],axis=0)
        # 将股票列表保存为CSV文件
        data.to_csv("future_codes_info.csv")
        # 打印当前上市交易的品种列表
        print("========交易品种列表========")
        print(data)
        print("================================")
    @staticmethod
    def show_stock_codes():
        """
        显示所有上市交易的股票代码，并返回股票名称与代码、上市日期的对应字典。
        :return: 股票名称与其代码和上市日期的字典
        """
        # 设置Pandas显示选项，显示所有列和所有行
        pd.set_option('display.max_columns', None)
        pd.set_option('display.max_rows', None)
        # 读取之前保存的股票代码CSV文件
        data = pd.read_csv("datasets/codes.csv", index_col=0)
        # 重命名列名为中文
        new_col = ['code', '股票名', '地区', '行业', '上市日期']
        data.columns = new_col
        # 打印股票代码列表
        print("===================现有上市交易品种代码列表===================")
        print(data)
        print("===============================================")
        # 创建一个字典，用于存储股票名称与其代码和上市日期的对应关系
        name_dict = dict()

        # 遍历每一行数据，填充name_dict
        for index, row in data.iterrows():
            information_list = list()
            information_list.append(row['code'])  # 添加股票代码
            information_list.append(row['上市日期'])  # 添加上市日期
            name_dict[row['股票名']] = information_list  # 键为股票名称，值为信息列表

        return name_dict  # 返回股票信息字典
    
    @staticmethod
    def input_stockInformation():

        """
        交互式地获取用户想要回测的股票名称、回测起始日期和结束日期。
        :return: 用户选择的股票代码列表、回测起始日期和结束日期
        """
        # 显示股票代码列表并获取股票信息字典
        name_dict = DataIO.show_stock_codes()

        codes = list()  # 存储用户选择的股票代码
        names = list()  # 存储用户输入的股票名称
        print("请对应股票代码表输入，需要回测的股票名称,结束请输入“#” ")
        print("===============================================")
        # 循环获取用户输入的股票名称
        while True:
            name = input("请继续输入：\n").strip()
            if name == "#":
                break  # 输入'#'表示结束输入
            if name not in name_dict:
                print("输入股票名不存在，请重新输入")
                continue  # 如果股票名称不存在，提示重新输入
            names.append(name)  # 添加到名称列表中
        # 根据名称列表获取对应的股票代码
        for name in names:
            codes.append(name_dict[name][0])
        # 获取回测的起始日期和结束日期
        while True:
            if not names:
                break  # 如果没有选择任何股票，直接退出
            judge = True
            try:
                # 输入回测起始日期
                start_date = int(input("请按说明格式输入回测起始日期：\n（例如：若为2021年9月10日则应输入：20210910）\n").strip())
                if start_date == "":
                    print("输入为空！请重试！！！")
                    continue
            except ValueError:
                print("非法输入！请重试！！！")
                continue
            # 检查起始日期是否合法
            for name in names:
                if int(name_dict[name][1]) > start_date:
                    print("起始日期不可早于该股票上市日期,请重新输入！！！")
                    print(f"股票：{name},上市日期为：{name_dict[name][1]}")
                    judge = False
                    break
                if DataGet.get_date_from_int(start_date) > datetime.date.today():
                    print("起始日期不可晚于今日，请重新输入！！！")
                    judge = False
                    break

            if not judge:
                continue  # 如果起始日期不合法，重新输入
            while True:
                try:
                    # 输入回测结束日期
                    end_date = int(input("请按说明格式输入回测结束日期：\n（例如：若为2021年9月10日则应输入：20210910）\n").strip())
                    if DataGet.get_date_from_int(end_date) > datetime.date.today():
                        print("结束日期不可晚于今日，请重新输入！！！")
                        continue
                    if end_date < start_date:
                        print("结束日期不可早于起始日期！！！请重试！！！")
                        continue
                    break  # 结束日期输入正确，退出循环
                except ValueError:
                    print("非法输入！请重试！！！")
                    continue
            break  # 起始日期和结束日期均输入正确，退出循环
        
        return codes, start_date, end_date  # 返回股票代码列表和日期
    @staticmethod 
    def input_futureInformation():

        """
        交互式地获取用户想要回测的品种名称、回测起始日期和结束日期。
        :return: 用户选择的品种代码wh_code列表、回测起始日期和结束日期
        """
        # 显示股票代码列表并获取股票信息字典
        name_dict = DataIO.show_future_codes_from_mysql()
        wh_codes = list()  # 存储用户选择的股票文华代码
        names = list()  # 存储用户输入的股票名称
        print("请对应期货代码表输入，需要回测的期货名称,结束请输入“#” ")
        print("===============================================")
        # 循环获取用户输入的股票名称
        while True:
            name = input("请继续输入：\n").strip()
            if name == "#":
                break  # 输入'#'表示结束输入
            if name in name_dict:
                names.append(name)  # 添加到名称列表中
            else:
                print("输入期货不存在，请重新输入")
                continue  # 如果股票名称不存在，提示重新输入
        # 根据名称列表获取对应的股票文化码
        for name in names:
            wh_codes.append(name_dict[name][-1])

        # 选回测周期
        period_options = {"1": ('day', 'day'), "2": ('15min', 'min'),"3": ('5s', 's')}
        period_input = input("请选择回测周期：\n1.一天\n2.15分钟\n3.5秒钟\n").strip()
        if period_input not in period_options:
            print("无效选项，请重新运行程序并选择有效选项。")
            exit()
        period, has_time = period_options[period_input]

        def get_valid_date(prompt, has_time):
            while True:
                date_str = input(prompt).strip()
                date_full = DataGet.get_date_from_int(date_str, has_time=has_time)
                if has_time =='day':
                    try:
                        if date_full > datetime.date.today():
                            print("日期或时间不可晚于当前时间，请重新输入！！！")
                            continue
                        return date_str
                    except ValueError as e:
                        print(f"解析日期失败: {e}")
                        continue
                elif has_time =='min':
                    if not date_str.isdigit() or len(date_str) != 12:
                        print("非法输入！请确保输入为12位数字，格式为：YYYYMMDDHHMM")
                        continue
                    try:
                        if date_full > datetime.datetime.now():
                            print("日期或时间不可晚于当前时间，请重新输入！！！")
                            continue
                        return date_str
                    except ValueError as e:
                        print(f"解析日期失败: {e}")
                        continue
                elif has_time == 's':
                    if not date_str.isdigit() or len(date_str) != 14:
                        print("非法输入！请确保输入为14位数字，格式为：YYYYMMDDHHMMSS")
                        continue
                    try:
                        if date_full > datetime.datetime.now():
                            print("日期或时间不可晚于当前时间，请重新输入！！！")
                            continue
                        return date_str
                    except ValueError as e:
                        print(f"解析日期失败: {e}")
                        continue
        while True:
            start_date = get_valid_date(
                "请按说明格式输入回测起始日期或时间：\n（例如：若为2024年12月16日15点30分15秒则应输入：20241216153015）\n",
                has_time)

            end_date = get_valid_date(
                "请按说明格式输入回测结束日期或时间：\n（例如：若为2024年12月16日15点30分15秒则应输入：20241216153015）\n",
                has_time)
            if end_date < start_date:
                print("结束日期或时间不可早于起始日期或时间！！！请重试！！！")
            if end_date >= start_date:
                break


        DataIO.start_date=start_date
        DataIO.end_date=end_date
        return wh_codes,names, start_date, end_date, period, has_time  # 返回股票代码列表和日期
 
    @staticmethod
    def add_analysers(cerebro):
        """
        交互式地添加回测分析器，用户可以选择需要计算的回测指标。
        :param cerebro: Backtrader的Cerebro引擎实例
        """
        print("请选择需要计算的回测指标，并在下方输入选项前的数字标号：\n1.年化收益\n2.夏普比率\n3.权益回撤\n4.年化收益率")
        while True:
            # 获取用户输入的指标选项
            num = input("请输入：（输入”0“结束输入）\n")
            if num == "0":
                break  # 输入'0'表示结束输入
            elif num == "1":
                # 添加年化收益分析器
                cerebro.addanalyzer(AnnualReturn, _name='AnnualReturn')
            elif num == "2":
                # 添加夏普比率分析器
                cerebro.addanalyzer(SharpeRatio, timeframe=bt.TimeFrame.Years, _name='SharpeRatio')
            elif num == "3":
                # 添加权益回撤分析器
                cerebro.addanalyzer(DrawDown, _name='DrawDown')
            elif num == "4":
                # 添加年化收益率分析器
                cerebro.addanalyzer(TimeReturn, timeframe=bt.TimeFrame.Years, _name='TimeReturn')
            else:
                print("非法输入！请重试！！！")  # 输入不合法，提示重试

    @staticmethod
    def add_plotElements(cerebro):
        """
        交互式地添加可视化绘制的回测曲线，用户可以选择需要显示的曲线。
        :param cerebro: Backtrader的Cerebro引擎实例
        """
        # 添加买卖点观察器
        cerebro.addobserver(bt.observers.BuySell)
        print("请选择可视化绘制的回测曲线，并在下方输入选项前的数字标号\n1.收益曲线\n2.回撤曲线\n3.总体权益曲线")
        while True:
            # 获取用户输入的可视化选项
            num = input("请输入：（输入”0“结束输入）\n")
            if num == "0":
                break  # 输入'0'表示结束输入
            elif num == "1":
                # 添加收益曲线观察器
                cerebro.addobserver(bt.observers.TimeReturn)
            elif num == "2":
                # 添加回撤曲线观察器
                cerebro.addobserver(bt.observers.DrawDown)
            elif num == "3":
                # 添加总体权益曲线观察器
                cerebro.addobserver(bt.observers.FundValue)
            else:
                print("非法输入！请重试！！！")
                continue  # 输入不合法，提示重试

    @staticmethod
    def text_report(cerebro, strat):
        """
        输出回测的文本报告，包括期初权益、期末权益、收益、收益率等信息。
        :param cerebro: Backtrader的Cerebro引擎实例
        :param strat: 运行后的策略实例
        """
        endingcash = cerebro.broker.get_value()  # 获取期末权益
        #endingcash=shared_cash_pool_pointing.Shared_Cash_Pool_Pointing.getvalue()
        if endingcash <= 0:
            endingcash = 0
        # 输出期初和期末权益
        print(f"期初权益：{cerebro.broker.startingcash}")
        print(f"期末权益：{endingcash}")
        profit = endingcash - cerebro.broker.startingcash  # 计算收益
        print(f"收益:{round(profit, 2)}")
        # 计算收益率
        profit_percent = round(profit / cerebro.broker.startingcash, 2) * 100
        if profit < 0:
            profit_percent = -profit_percent
        print(f"收益率：{round(profit_percent, 2)}%")
        # 输出夏普比率
        if hasattr(strat.analyzers, "SharpeRatio"):
            sharpe_ratio = strat.analyzers.SharpeRatio.get_analysis().get('sharperatio', None)
            if sharpe_ratio is not None:
                print(f"夏普比率:{round(sharpe_ratio, 2)}")
        # 输出最大回撤信息
        if hasattr(strat.analyzers, "DrawDown"):
            drawdown = strat.analyzers.DrawDown.get_analysis()
            print(f"最大回撤率:{round(drawdown['max']['drawdown'], 2)}%")
            print(f"最大回撤资金:{round(-drawdown['max']['moneydown'], 2)}")
        # 输出年化平均收益率
        if hasattr(strat.analyzers, "AnnualReturn"):
            annual_returns = strat.analyzers.AnnualReturn.get_analysis()
            avg_annual_return = np.mean(list(annual_returns.values()))
            print(f"年化平均收益率:{round(float(avg_annual_return), 2) * 100}%")

    @staticmethod
    def input_OptInformation():
        """
        交互式地获取策略参数优化的信息，包括优化算法、优化次数、参数范围等。
        :return: 优化算法名称、优化次数、参数N1的范围列表、参数N2的范围列表
        """
        n1_list = []  # 存储参数N1的范围
        n2_list = []  # 存储参数N2的范围
        num = 0       # 优化次数
        name = ""     # 优化算法名称
        # 选择优化算法
        while True:
            try:
                print("*************************************************************************************")
                print("可用的参数优化算法:\n1.粒子群优化算法\n2.SOBOL序列\n3.随机搜索算法（耗时较久）\n4.CMA-ES\n5.网格搜索算法\n")
                name_choose = int(input("请选择优化算法并输入对应优化算法前的数字序号：\n"))
                if name_choose == 1:
                    name = "particle swarm"
                    break
                elif name_choose == 2:
                    name = "sobol"
                    break
                elif name_choose == 3:
                    name = "random search"
                    break
                elif name_choose == 4:
                    name = "cma-es"
                    break
                elif name_choose == 5:
                    name = "grid search"
                    break
                else:
                    print("不存在该选项！请重试！！！")
                    continue
            except ValueError:
                print("非法输入，请输入整数数字，请重试！")
                continue
        # 输入优化次数
        while True:
            try:
                num = int(input("请输入算法优化次数："))
                break
            except ValueError:
                print("请输入整数数字，请重试！")
                continue
        # 输入策略参数的优化范围
        while True:
            judge = True
            try:
                for i in range(2):  # 对于参数N1和N2
                    start = int(input(f"请输入参数{i + 1}的优化范围下限:\n"))
                    if start == "":
                        print("输入为空，请重试！")
                        judge = False
                        n1_list.clear()
                        n2_list.clear()
                        break
                    end = int(input(f"请输入参数{i + 1}的优化范围上限:\n"))
                    if end == "":
                        judge = False
                        print("输入为空，请重试！")
                        n1_list.clear()
                        n2_list.clear()
                        break
                    if start > end:
                        print("参数上限不可小于参数下限！请重新输入！")
                        n1_list.clear()
                        n2_list.clear()
                        judge = False
                        break
                    if i == 0:
                        n1_list.append(start)
                        n1_list.append(end)
                    else:
                        n2_list.append(start)
                        n2_list.append(end)
                if judge:
                    break  # 参数范围输入正确，退出循环
                else:
                    continue
            except ValueError:
                print("非法输入，请重试！")
                n1_list.clear()
                n2_list.clear()
                continue

        print(num, n1_list, n2_list)  # 输出优化次数和参数范围
        return name, num, n1_list, n2_list  # 返回优化信息

    @staticmethod
    def printOptParameters(name, optimal_pars):
        """
        打印参数优化后的最优参数信息。
        :param name: 优化算法名称
        :param optimal_pars: 最优参数的字典
        """
        print(f'采用{name}算法优化后的参数信息:')
        print('N1 = %.2f' % optimal_pars['N1'])
        print('N2 = %.2f' % optimal_pars['N2'])


    params = (
        ('target_percent', 0.05),  # 默认值为 5%
    )
    def __init__(self):
        self.target_percent=self.params.target_percent

    def change_target_percent(self):
        log.Log.log(self,f"Current Target percentage is {self.target_percent}.")
        change_flag = input("是否需要调整持仓比例(y/n): ").strip().lower()
        if change_flag=='y':
            DataIO.set_target_percent(self)

    def set_target_percent(self):
        """
        接收用户输入的目标持仓比例
        """
        while True:
            try:
                new_target_percent = float(input("Enter the new target percentage(or 'q' to exit): "))
                if new_target_percent == 'q':
                    break
                elif 0 <= new_target_percent <= 1:
                    self.target_percent = new_target_percent
                    log.Log.log(self,f"Target percentage updated to {new_target_percent:.2f}")
                    break
                else:
                    log.Log.Log.log(self,"Target percentage must be between 0 and 1.")
            except ValueError:
                log.Log.Log.log("Invalid input. Please enter a valid number.")

    def show_future_codes_from_mysql():
        """
        从MySQL数据库中读取所有上市交易的期货代码，并返回期货名称与代码、上市日期的对应字典。
        :return: 期货名称与其代码和上市日期的字典
        """
        connection = get_engine()
        # 使用pandas读取MySQL数据库中的表 future_codes
        query = "SELECT * FROM future_codes"
        data = pd.read_sql(query,con=connection)
        print(data.columns)

        # 设置Pandas显示选项，显示所有列和所有行
        pd.set_option('display.max_columns', None)
        pd.set_option('display.max_rows', None)

        # 打印期货品种代码列表
        print("===================期货品种代码列表===================")
        print(data.iloc[:, :4])  # 只展示前四列
        print("===============================================")

        # 创建一个字典，用于存储期货名称与其代码和上市日期的对应关系
        name_dict = dict()
        alias_to_name = {} # 用于期货名到别名的映射

        # 遍历每一行数据，填充name_dict # 和 alias_to_name
        for index, row in data.iterrows():
            information_list = [row['code'], row['期货名'],row['别名'],row['wh_code']]  # 假设表中有'code'和'期货名'这两列
            name_dict[row['期货名']] = information_list  # 键为期货名称，值为信息列表
            # if pd.notna(row['别名']):
            #     # 如果有别名，则将其映射到期货名
            #     alias_to_name[row['别名']] = row['期货名']

        return name_dict  # ,alias_to_name  # 返回期货信息字典及别名映射

    # @staticmethod
    # def show_future_codes():
    #     """
    #     显示所有上市交易的股票代码，并返回股票名称与代码、上市日期的对应字典。
    #     :return: 股票名称与其代码和上市日期的字典
    #     """
    #     # 设置Pandas显示选项，显示所有列和所有行
    #     pd.set_option('display.max_columns', None)
    #     pd.set_option('display.max_rows', None)
    #     # 读取之前保存的股票代码CSV文件
    #     data = pd.read_csv("datasets/future_codes.csv", index_col=0)
    #     # 重命名列名为中文
    #     # 打印股票代码列表
    #     print("===================期货品种代码列表===================")
    #     print(data)
    #     print("===============================================")
    #     # 创建一个字典，用于存储股票名称与其代码和上市日期的对应关系
    #     name_dict = dict()
    #
    #     # 遍历每一行数据，填充name_dict
    #     for index, row in data.iterrows():
    #         information_list = list()
    #         information_list.append(row['code'])  # 添加股票代码
    #         information_list.append(row['期货名'])
    #         name_dict[row['期货名']] = information_list  # 键为股票名称，值为信息列表
    #     return name_dict  # 返回股票信息字典


