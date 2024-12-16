import backtrader as bt
import tushare as ts
import datetime
import pandas as pd
from db_mysql import get_engine
from sqlalchemy import text
class DataGet:
    @staticmethod
    def get_str_date_from_int(date_int):
        """
        将日期的整数格式（yyyyMMdd）转换为字符串格式（yyyy-mm-dd）
        :param date_int: 日期的整数表示
        :return: 格式化后的日期字符串
        """
        try:
            date_int = int(date_int)
        except ValueError:
            date_int = int(date_int.replace("-", ""))
        year = date_int // 10000  # 获取年份
        month = (date_int % 10000) // 100  # 获取月份
        day = date_int % 100  # 获取日期

        return "%d-%02d-%02d" % (year, month, day)

    @staticmethod
    def get_date_from_int(date_int):
        """
        将日期的整数格式（yyyyMMdd）转换为日期对象
        :param date_int: 日期的整数表示
        :return: 转换后的日期对象
        """
        date_str = DataGet.get_str_date_from_int(date_int)
        return datetime.datetime.strptime(date_str, "%Y-%m-%d").date()

    @staticmethod
    def login_ts():
        """
        登录Tushare，获取pro_api接口
        :return: 返回Tushare pro_api实例
        """
        token = 'a4ef5bd632a83a568af0497fb9a21920ada0f4d013b79685bdce16ea'
        ts.set_token(token)  # 设置Tushare Token
        pro = ts.pro_api(token)  # 获取Tushare pro接口
        return pro

    @staticmethod
    def get_data(codes, cerebro, start_date, end_date):
        """
        获取指定股票/期货代码的数据，并将其添加到回测引擎（Cerebro）中
        :param codes: 股票/期货代码（可以是单个代码或多个代码的列表）
        :param cerebro: Backtrader回测引擎实例
        :param start_date: 回测开始日期
        :param end_date: 回测结束日期
        """
        pro = DataGet.login_ts()  # 登录Tushare接口
        code_list = codes if isinstance(codes, list) else codes.split()  # 确保codes是列表形式
        # 加载数据
        for code in code_list:
            #df = pro.daily(ts_code=f"{code}", start_date=start_date, end_date=end_date)  # 获取日线数据
            df = pro.daily(ts_code=f"{code}")  # 获取日线数据
            df['trade_date'] = pd.to_datetime(df['trade_date'])  # 转换交易日期为日期类型
            df.set_index('trade_date', inplace=True)  # 将交易日期设为索引
            df['openinterest'] = 0  # 初始化持仓量为0
            df = df[['open', 'high', 'low', 'close', 'vol', 'openinterest']].rename(columns={'vol': 'volume'})  # 重命名列
            df = df.sort_index()  # 按日期排序数据
            data = bt.feeds.PandasData(dataname=df)  # 转换为Backtrader的Pandas数据格式
            cerebro.adddata(data, name=code)  # 将数据添加到回测引擎中
    @staticmethod
    # def get_fut_data(codes:list,cerebro:bt.Cerebro,start_date,end_date):
    #
    #     pro = DataGet.login_ts()  # 登录Tushare接口
    #     code_list = codes if isinstance(codes, list) else codes.split()  # 确保codes是列表形式
    #     # 加载数据
    #     for code in code_list:
    #         df = pro.fut_daily(ts_code=code)  # 获取日线数据
    #         df['trade_date'] = pd.to_datetime(df['trade_date'])  # 转换交易日期为日期类型
    #         df.set_index('trade_date', inplace=True)  # 将交易日期设为索引
    #         df['openinterest'] = 0  # 初始化持仓量为0
    #         df = df[['open', 'high', 'low', 'close', 'vol', 'openinterest']].rename(columns={'vol': 'volume'})  # 重命名列
    #         df = df.sort_index()  # 按日期排序数据
    #         data = bt.feeds.PandasData(dataname=df)  # 转换为Backtrader的Pandas数据格式
    #         cerebro.adddata(data, name=code)  # 将数据添加到回测引擎中

    # def get_fut_data(names: list, cerebro: bt.Cerebro, start_date, end_date):
    #     """
    #         从MySQL数据库中获取期货日线数据并添加到Backtrader回测引擎中
    #         :param names: 合约名称列表
    #         :param cerebro: Backtrader 回测引擎实例
    #         :param start_date: 数据开始日期
    #         :param end_date: 数据结束日期
    #         """
    #     connection = get_engine()
    #     name_list = names if isinstance(names, list) else [names]  # 确保codes是列表形式
    #
    #     for name in name_list:
    #         # 构造SQL查询语句，选择特定合约代码的数据，并限制时间范围
    #         query = f"""
    #                    SELECT * FROM combined_day
    #                    WHERE name = '{name}'
    #                      AND trade_date BETWEEN '{start_date}' AND '{end_date}'
    #                """
    #         try:
    #             # 使用Pandas读取SQL查询结果
    #             df = pd.read_sql(query, con=connection)
    #
    #             # 如果DataFrame为空，则跳过该合约
    #             if df.empty:
    #                 print(f"No data found for {name} between {start_date} and {end_date}. Skipping...")
    #                 continue
    #
    #             # 数据预处理
    #             df['trade_date'] = pd.to_datetime(df['trade_date'])  # 转换交易日期为日期类型
    #             df.set_index('trade_date', inplace=True)  # 将交易日期设为索引
    #             df['openinterest'] = 0  # 初始化持仓量为0
    #             df = df[['open', 'high', 'low', 'close', 'vol', 'openinterest']].rename(columns={'vol': 'volume'})  # 重命名列
    #             df = df.sort_index()  # 按日期排序数据
    #
    #             # 转换为Backtrader的Pandas数据格式并添加到回测引擎中
    #             data = bt.feeds.PandasData(dataname=df)
    #             cerebro.adddata(data, name=name)
    #
    #         except Exception as e:
    #             print(f"Failed to load data for {name}: {e}")

    def get_fut_data(codes:list,cerebro:bt.Cerebro):
        """
            从MySQL数据库中获取期货日线数据并添加到Backtrader回测引擎中
            :param codes: 合约wh_code列表
            :param cerebro: Backtrader 回测引擎实例
            :param start_date: 数据开始日期
            :param end_date: 数据结束日期
        """
        # 创建数据库连接引擎
        connection = get_engine()
        # name_list = names if isinstance(names, list) else [names]  # 确保names是列表形式
        code_list = codes if isinstance(codes, list) else [codes]  # 确保codes是列表形式
        for code in code_list:
            try:
                # 查找所有表名中包含wh_code的表
                query_tables = f"""
                                SELECT table_name 
                                FROM information_schema.tables 
                                WHERE table_schema = 'future' 
                                  AND table_name LIKE '{code}%' 
                            """
                tables_result = pd.read_sql(text(query_tables), con=connection)
                if tables_result.empty:
                    print(f"No tables found for wh_code {code}.")
                    break
                for table_name in tables_result['table_name']:
                    # 从每个匹配的表中加载数据
                    query_data = f"SELECT * FROM `{table_name}`"
                    df = pd.read_sql(text(query_data), con=connection)

                    # 数据预处理
                    df['trade_date'] = pd.to_datetime(df['trade_date'])  # 转换交易日期为日期类型
                    df.set_index('trade_date', inplace=True)  # 将交易日期设为索引
                    df['openinterest'] = 0  # 初始化持仓量为0
                    df = (df[['open', 'high', 'low', 'close', 'vol', 'openinterest']]
                          .rename(columns={'vol': 'volume'}))  # 重命名列
                    df = df.sort_index()  # 按日期排序数据
                    # 转换为Backtrader的Pandas数据格式并添加到回测引擎中
                    data = bt.feeds.PandasData(dataname=df)
                    cerebro.adddata(data, name=code)

            except Exception as e:
                print(f"Failed to load data for {code}: {e}")
