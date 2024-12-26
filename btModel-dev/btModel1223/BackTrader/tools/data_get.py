import backtrader as bt
import tushare as ts
import datetime
import pandas as pd
from tools.db_mysql import get_engine
from sqlalchemy import text
from concurrent.futures import ThreadPoolExecutor, as_completed
import os
import pickle
class DataGet:
    _data_cache={}
    _db_access_count=0
    @staticmethod
    def _get_cache_key(code,period):
        return f"{code}_{period}"
    
    @staticmethod
    def _load_from_cache(cache_key):
        if cache_key in DataGet._data_cache:
            #print(f"Loading data from cache for {cache_key}")
            return DataGet._data_cache[cache_key]

        cache_dir="./data_cache"
        os.makedirs(cache_dir,exist_ok=True)
        cache_file=os.path.join(cache_dir,f"{cache_key}.pkl")
        if os.path.exists(cache_file):
            with open(cache_file,"rb") as f:
                DataGet._data_cache[cache_key]=pickle.load(f)
            return DataGet._data_cache[cache_key]
        return None

    @staticmethod
    def _save_to_cache(cache_key,data):
        DataGet._data_cache[cache_key]=data
        cache_dir="./data_cache"
        os.makedirs(cache_dir,exist_ok=True)
        cache_file=os.path.join(cache_dir,f"{cache_key}.pkl")
        with open(cache_file,"wb") as f:
            pickle.dump(data,f)

    @staticmethod
    def get_str_to_datetime(date_str):
        """
        将日期字符串格式（yyyyMMdd、yyyyMMddHHmm、yyyyMMddHHmmss）转换为日期对象。
        :param date_str: 日期的字符串表示
        :return: 格式化后的日期字符串
        """
        # 清理输入中的非数字字符
        if isinstance(date_str, str):
            date_str = ''.join(filter(str.isdigit, date_str))
        try:
            date_len = len(date_str)

            if date_len == 8:  #yyyymmdd
                fmt = "%Y%m%d"
                return datetime.datetime.strptime(date_str, fmt).date()
            elif date_len == 10:  # yyyymmddHH (假设没有 mm 分钟部分)
                raise ValueError("Invalid length for time. Expected HHMM or HHMMSS.")
            elif date_len == 12:  # yyyymmddHHmm
                fmt = "%Y%m%d%H%M"
            elif date_len == 14:  # yyyymmddHHmmss
                fmt = "%Y%m%d%H%M%S"
            else:
                raise ValueError(f"Unexpected date length {date_len}. Expected 8, 12, or 14 digits.")
            return datetime.datetime.strptime(date_str, fmt)
        except ValueError as e:
            raise ValueError(f"Invalid date format or value provided: {e}")

    @staticmethod
    def get_date_from_int(date_str):
        """
        将日期的字符串格式（yyyyMMdd）转换为日期对象
        :param date_str: 日期的字符串表示
        :return: 转换后的日期对象
        """
        # 获取日期
        date_str = DataGet.get_str_to_datetime(date_str)
        # if has_time=='min':
        #     # 假设输入格式为 yyyyMMddHHmm
        #     date_min = date_str
        #     return date_min
        # elif has_time=='s':
        #     # 假设输入格式为 yyyyMMddHHmmss
        #     date_s = date_str
        #     return date_s
        # elif has_time=='day':
        #     # 假设输入格式为 yyyyMMdd
        #     date_full = date_str
        return date_str

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

    '''def get_fut_data(codes: list, cerebro: bt.Cerebro, period):
        """
            从MySQL数据库中获取期货日线数据并添加到Backtrader回测引擎中
            :param codes: 合约wh_code列表
            :param cerebro: Backtrader 回测引擎实例
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
                                  AND table_name LIKE '{code}_{period}'
                            """
                tables_result = pd.read_sql(text(query_tables), con=connection)
                if tables_result.empty:
                    print(f"No tables found for wh_code {code}.")
                    break
                # print(tables_result.columns)
                for table_name in tables_result['TABLE_NAME']:
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
                print(f"Failed to load data for {code}: {e}")'''

    # def get_fut_data(codes:list, cerebro:bt.Cerebro, period):
    #     """
    #         从MySQL数据库中获取期货数据并添加到Backtrader回测引擎中
    #         :param codes: 合约wh_code列表
    #         :param cerebro: Backtrader 回测引擎实例
    #         :param period: 数据周期（例如 'day', '15min' 等）
    #     """
    #     # 创建数据库连接引擎
    #     connection = get_engine()
    #     code_list = codes if isinstance(codes, list) else [codes]  # 确保codes是列表形式
    #
    #     # 构建一个查询，用于找到所有符合条件的表
    #     placeholders = ', '.join([f"'{code}_{period}'" for code in code_list])
    #     # print(placeholders)
    #     query_tables = f"""
    #             SELECT table_name
    #             FROM information_schema.tables
    #             WHERE table_schema = 'future'
    #               AND table_name IN ({placeholders})
    #         """
    #
    #     tables_result = pd.read_sql(text(query_tables), con=connection)
    #
    #     if tables_result.empty:
    #         print("No tables found for the specified codes and period.")
    #         return
    #
    #     def load_and_process_table(table_name):
    #         try:
    #             # 从每个匹配的表中加载数据
    #             query_data = f"SELECT * FROM `{table_name}`"
    #             df = pd.read_sql(text(query_data), con=connection)
    #
    #             # 数据预处理
    #             df['trade_date'] = pd.to_datetime(df['trade_date'])  # 转换交易日期为日期类型
    #             df.set_index('trade_date', inplace=True)  # 将交易日期设为索引
    #             df['openinterest'] = 0  # 初始化持仓量为0
    #             df = (df[['open', 'high', 'low', 'close', 'vol', 'openinterest']]
    #                   .rename(columns={'vol': 'volume'}))  # 重命名列
    #             df = df.sort_index()  # 按日期排序数据
    #
    #             # 获取合约代码
    #             code = table_name.rsplit('_', 1)[0]
    #             data = bt.feeds.PandasData(dataname=df)
    #             cerebro.adddata(data, name=code)
    #
    #         except Exception as e:
    #             print(f"Failed to load data for {table_name}: {e}")
    #
    #     # 使用线程池并发加载和处理表格
    #     with ThreadPoolExecutor(max_workers=4) as executor:
    #         # print((tables_result))
    #         futures = {executor.submit(load_and_process_table, table_name): table_name for table_name in
    #                    tables_result['table_name']}
    #         for future in as_completed(futures):
    #             table_name = futures[future]
    #             try:
    #                 future.result()
    #             except Exception as exc:
    #                 print(f"{table_name} generated an exception: {exc}")


    '''def get_fut_data(codes: list, cerebro: bt.Cerebro, period):
        """
            从MySQL数据库中获取期货数据并添加到Backtrader回测引擎中
            :param codes: 合约wh_code列表
            :param cerebro: Backtrader 回测引擎实例
            :param period: 数据周期（例如 'day', '15min' 等）
        """
        # 创建数据库连接引擎
        connection = get_engine()
        code_list = codes if isinstance(codes, list) else [codes]  # 确保codes是列表形式



        # 构建一个查询，用于找到所有符合条件的表
        placeholders = ', '.join([f"'{code}_{period}'" for code in code_list])
        # print(placeholders)
        query_tables = f"""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'future'
                AND table_name IN ({placeholders})
            """

        tables_result = pd.read_sql(text(query_tables), con=connection)

        if tables_result.empty:
            print("No tables found for the specified codes and period.")
            return

        def load_and_process_table(table_name):
            try:
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

                # 获取合约代码
                code = table_name.rsplit('_', 1)[0]



                data = bt.feeds.PandasData(dataname=df)
                cerebro.adddata(data, name=code)
                #cerebro.adddata(data,name=name)

            except Exception as e:
                print(f"Failed to load data for {table_name}: {e}")

        # 使用线程池并发加载和处理表格
        with ThreadPoolExecutor(max_workers=4) as executor:
            # print((tables_result))
            futures = {executor.submit(load_and_process_table, table_name): table_name for table_name in
                    tables_result['table_name']}
            for future in as_completed(futures):
                table_name = futures[future]
                try:
                    future.result()
                except Exception as exc:
                    print(f"{table_name} generated an exception: {exc}")'''

    @staticmethod
    def get_fut_data(cerebro, codes, period):
        """获取期货数据并添加到cerebro"""
        code_list = codes if isinstance(codes, list) else [codes]
        
        for code in code_list:
            cache_key = DataGet._get_cache_key(code, period)
            df = DataGet._load_from_cache(cache_key)
            
            if df is None:
                DataGet._db_access_count += 1  # 记录数据库访问次数
                print(f"从数据库加载数据 ({DataGet._db_access_count}): {code}")
                
                connection = get_engine()
                query = f"SELECT * FROM `{code}_{period}`"
                df = pd.read_sql(text(query), con=connection)
                
                # 数据预处理
                df['trade_date'] = pd.to_datetime(df['trade_date'])
                df.set_index('trade_date', inplace=True)
                df['openinterest'] = 0
                df = df[['open', 'high', 'low', 'close', 'vol', 'openinterest']].rename(columns={'vol': 'volume'})
                df = df.sort_index()
                
                # 保存到缓存
                DataGet._save_to_cache(cache_key, df)
            else:
                #df.index=df.index.floor('S')
                print(f"从缓存加载数据: {code}")
            
            # 转换为Backtrader数据格式并添加到cerebro
            data = bt.feeds.PandasData(dataname=df)
            cerebro.adddata(data, name=code)


    @staticmethod
    def clear_cache():
        """清理所有缓存"""
        DataGet._data_cache.clear()
        cache_dir = "./data_cache"
        if os.path.exists(cache_dir):
            for file in os.listdir(cache_dir):
                os.remove(os.path.join(cache_dir, file))