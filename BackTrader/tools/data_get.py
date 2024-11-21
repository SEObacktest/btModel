import backtrader as bt
import tushare as ts
import datetime
import pandas as pd

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
        token = '7c15d8db9ccc0383e40eb7487930fa9eb88eaca08573fe1da440aa54'
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
            df = pro.daily(ts_code=f"{code}", start_date=start_date, end_date=end_date)  # 获取日线数据
            df['trade_date'] = pd.to_datetime(df['trade_date'])  # 转换交易日期为日期类型
            df.set_index('trade_date', inplace=True)  # 将交易日期设为索引
            df['openinterest'] = 0  # 初始化持仓量为0
            df = df[['open', 'high', 'low', 'close', 'vol', 'openinterest']].rename(columns={'vol': 'volume'})  # 重命名列
            df = df.sort_index()  # 按日期排序数据
            data = bt.feeds.PandasData(dataname=df)  # 转换为Backtrader的Pandas数据格式
            cerebro.adddata(data, name=code)  # 将数据添加到回测引擎中
