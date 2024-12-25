import ast
import os
import backtrader as bt
import tushare as ts
import datetime
import pandas as pd
from BackTrader.tools.db_mysql import get_engine
from sqlalchemy import text
from concurrent.futures import ThreadPoolExecutor, as_completed
from io import StringIO
import re

class DataGet:
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
            #输入的时间的长度
            date_len = len(date_str)
            #如果长度符号要求使用，datetime 的 strptime 方法将日期字符串解析为日期对象，并返回日期部分
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

    # def get_fut_data(codes: list, cerebro: bt.Cerebro, period):
    #     """
    #         从MySQL数据库中获取期货日线数据并添加到Backtrader回测引擎中
    #         :param codes: 合约wh_code列表
    #         :param cerebro: Backtrader 回测引擎实例
    #     """
    #     # 创建数据库连接引擎
    #     connection = get_engine()
    #     # name_list = names if isinstance(names, list) else [names]  # 确保names是列表形式
    #     code_list = codes if isinstance(codes, list) else [codes]  # 确保codes是列表形式
    #     for code in code_list:
    #         try:
    #             # 查找所有表名中包含wh_code的表
    #             query_tables = f"""
    #                             SELECT table_name
    #                             FROM information_schema.tables
    #                             WHERE table_schema = 'future'
    #                               AND table_name LIKE '{code}_{period}'
    #                         """
    #             tables_result = pd.read_sql(text(query_tables), con=connection)
    #             if tables_result.empty:
    #                 print(f"No tables found for wh_code {code}.")
    #                 break
    #             # print(tables_result.columns)
    #             for table_name in tables_result['TABLE_NAME']:
    #                 # 从每个匹配的表中加载数据
    #                 query_data = f"SELECT * FROM `{table_name}`"
    #                 df = pd.read_sql(text(query_data), con=connection)
    #
    #                 # 数据预处理
    #                 df['trade_date'] = pd.to_datetime(df['trade_date'])  # 转换交易日期为日期类型
    #                 df.set_index('trade_date', inplace=True)  # 将交易日期设为索引
    #                 df['openinterest'] = 0  # 初始化持仓量为0
    #                 df = (df[['open', 'high', 'low', 'close', 'vol', 'openinterest']]
    #                       .rename(columns={'vol': 'volume'}))  # 重命名列
    #                 df = df.sort_index()  # 按日期排序数据
    #                 # 转换为Backtrader的Pandas数据格式并添加到回测引擎中
    #                 data = bt.feeds.PandasData(dataname=df)
    #                 cerebro.adddata(data, name=code)
    #
    #         except Exception as e:
    #             print(f"Failed to load data for {code}: {e}")

    def get_fut_data(codes:list, cerebro:bt.Cerebro, period):
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
                    print(f"{table_name} generated an exception: {exc}")

    #本地sqlfile
    def get_fut_data(codes: list, cerebro: bt.Cerebro, period):
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
                    print(f"{table_name} generated an exception: {exc}")



    # def get_fut_data_from_file(file_path: str, codes: list, cerebro: bt.Cerebro, period: str):
    #     """
    #     从本地SQL文件加载期货数据并添加到Backtrader回测引擎中
    #
    #     :param file_path: SQL文本文件路径
    #     :param codes: 合约wh_code列表
    #     :param cerebro: Backtrader 回测引擎实例
    #     :param period: 数据周期（例如 'day', '15min' 等）
    #     """
    #     # 检查文件路径是否存在
    #     if not os.path.exists(file_path):
    #         print(f"File not found: {file_path}")
    #         return
    #
    #     # 确保 codes 是列表形式
    #     code_list = codes if isinstance(codes, list) else [codes]
    #     placeholders = [f"{code}_{period}" for code in code_list]
    #
    #     # 打开并读取SQL文件内容
    #     with open(file_path, 'r', encoding='utf-8') as file:
    #         sql_content = file.read()
    #
    #     # 替换 SQL 文件中的 NULL 为 None
    #     sql_content = sql_content.replace("NULL", "None")
    #
    #     def extract_insert_statements(sql_content, table_name):
    #         """
    #         提取SQL文件中与特定表相关的INSERT语句
    #
    #         :param sql_content: SQL文件内容
    #         :param table_name: 表名
    #         :return: 包含INSERT语句的列表
    #         """
    #         pattern = re.compile(rf"INSERT INTO `{table_name}` VALUES \((.+?)\);", re.DOTALL)
    #         matches = pattern.findall(sql_content)
    #         return matches
    #
    #     def parse_values_line(values_line):
    #         """
    #         安全解析INSERT语句中的VALUES数据
    #
    #         :param values_line: 单个VALUES数据行
    #         :return: 解析后的数据
    #         """
    #         try:
    #             return ast.literal_eval(values_line.strip("()"))
    #         except Exception as e:
    #             print(f"Failed to parse line: {values_line}. Error: {e}")
    #             return None
    #
        # def load_and_process_table(table_name):
        #     """
        #     加载并处理单个表的数据，并将其添加到Backtrader引擎
        #
        #     :param table_name: 表名
        #     """
        #     try:
        #         if table_name not in sql_content:
        #             print(f"Table {table_name} not found in the SQL file.")
        #             return
        #
        #         # 提取表的数据行
        #         data_lines = extract_insert_statements(sql_content, table_name)
        #         if not data_lines:
        #             print(f"No data found for table {table_name}. Check SQL file or extraction logic.")
        #             return
        #
        #         # 解析数据行并转换为DataFrame
        #         parsed_data = [parse_values_line(line) for line in data_lines if parse_values_line(line) is not None]
        #         if not parsed_data:
        #             print(f"No valid data parsed for table {table_name}. Ensure data format is correct.")
        #             return
        #
        #         # 动态创建DataFrame
        #         df = pd.DataFrame(parsed_data, columns=[
        #             'wh_code', 'trade_date', 'open', 'high', 'low', 'close', 'oi', 'vol',
        #             'settle', 'pre_close', 'pre_settle', 'change1', 'change2', 'name'
        #         ])
        #
        #         if 'trade_date' in df.columns:
        #             df['trade_date'] = pd.to_datetime(df['trade_date'])
        #             df.set_index('trade_date', inplace=True)
        #         else:
        #             print(f"Missing 'trade_date' column in {table_name}. Skipping...")
        #             return
        #
        #         # 适配 Backtrader 的列
        #         df['openinterest'] = 0
        #         df.rename(columns={'vol': 'volume'}, inplace=True)
        #         df = df[['open', 'high', 'low', 'close', 'volume', 'openinterest']].sort_index()
        #
        #         # 添加到Backtrader引擎
        #         code = table_name.rsplit('_', 1)[0]
        #         data = bt.feeds.PandasData(dataname=df)
        #         cerebro.adddata(data, name=code)
        #
        #     except Exception as e:
        #         print(f"Failed to load data for {table_name}: {e}")
        #
        # # 使用线程池并发加载和处理表格
        # with ThreadPoolExecutor(max_workers=4) as executor:
        #     futures = {executor.submit(load_and_process_table, table_name): table_name for table_name in placeholders}
        #     for future in as_completed(futures):
        #         table_name = futures[future]
        #         try:
        #             future.result()
        #         except Exception as exc:
        #             print(f"{table_name} generated an exception: {exc}")
    def get_fut_data_from_csv(codes: list, cerebro: bt.Cerebro, period, csv_file):
        """
            从单个CSV文件中获取期货数据并添加到Backtrader回测引擎中
            :param codes: 合约wh_code列表
            :param cerebro: Backtrader 回测引擎实例
            :param period: 数据周期（例如 'day', '15min' 等）
            :param csv_file: 包含所有期货数据的CSV文件路径
        """
        # 确保codes是列表形式
        code_list = codes if isinstance(codes, list) else [codes]

        try:
            # 从CSV文件加载数据，并指定数据类型
            dtype_spec = {
                'wh_code': str,
                'trade_date': str,
                'open': str,  # 暂时作为字符串读取，稍后处理
                'high': str,
                'low': str,
                'close': str,
                'oi': str,
                'vol': str,
                'settle': str,
                'pre_close': str,
                'pre_settle': str,
                'change1': str,
                'change2': str,
                'name': str
            }
            df = pd.read_csv(csv_file, dtype=dtype_spec, skip_blank_lines=True, low_memory=False)

            # 数据清洗：去除标题行或非数字行
            for col in ['open', 'high', 'low', 'close', 'oi', 'vol', 'settle', 'pre_close', 'pre_settle', 'change1',
                        'change2']:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            df = df.dropna(subset=['open', 'high', 'low', 'close', 'oi', 'vol'])

            # 数据预处理
            try:
                df['trade_date'] = pd.to_datetime(df['trade_date'], format='%Y%m%d', errors='coerce')  # 尝试解析日期
            except ValueError as e:
                print(f"Date parsing error: {e}")
                return

            # 丢弃无法解析日期的行
            df = df.dropna(subset=['trade_date'])
            df.set_index('trade_date', inplace=True)  # 将交易日期设为索引

            # 按所需列进行重命名和排序
            df['openinterest'] = df['oi'].astype(int)  # 使用 oi 列作为 openinterest
            df = (df[['wh_code', 'open', 'high', 'low', 'close', 'vol', 'openinterest']]
                  .rename(columns={'vol': 'volume'}))  # 重命名列
            df = df.sort_index()  # 按日期排序数据

            # 根据codes过滤数据并处理
            def process_code(code):
                code_df = df[df['wh_code'] == code]  # 根据合约代码筛选数据
                if code_df.empty:
                    print(f"No data found for code: {code}")
                    return

                data = bt.feeds.PandasData(dataname=code_df)
                cerebro.adddata(data, name=code)

            # 使用线程池并发处理每个合约代码
            with ThreadPoolExecutor(max_workers=4) as executor:
                futures = {executor.submit(process_code, code): code for code in code_list}
                for future in as_completed(futures):
                    code = futures[future]
                    try:
                        future.result()
                    except Exception as exc:
                        print(f"Processing code {code} generated an exception: {exc}")

        except Exception as e:
            print(f"Failed to load data from {csv_file}: {e}")







