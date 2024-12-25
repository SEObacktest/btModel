import backtrader as bt
import codecs
import datetime
'''class Log():
    @staticmethod
    def log(self, txt, dt=None,log_file="log.txt"):
        """ 日志记录函数 """
        dt = dt or self.datetime.date(0)
        log_message = f'{dt.isoformat()} {txt}'
        print(f'{dt.isoformat()} {txt}')

        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(log_message + '\n')'''

class Log():
    @staticmethod
    def log(txt, dt=None, log_file="log.txt"):
        """ 日志记录函数，将日志输出到控制台并写入文件（UTF-8编码） """
        dt = dt or datetime.datetime.now()
        log_message = f'{dt.isoformat()} {txt}'

        # 输出到控制台
        print(log_message)

        # 使用 codecs 模块打开文件并写入 UTF-8 编码
        # with codecs.open(log_file, 'a', encoding='utf-8') as f:
        #     f.write(log_message + '\n')

# class Log():
#     @staticmethod
#     def log(self,txt, dt=None, log_file="log.txt"):
#         """ 日志记录函数，将日志输出到控制台并写入文件（UTF-8编码） """
#         dt = dt or self.datetime.now()
#         log_message = f'{dt.isoformat()} {txt}'
#
#         # 输出到控制台
#         print(log_message)
#
#         # 使用 codecs 模块打开文件并写入 UTF-8 编码
#         with codecs.open(log_file, 'a', encoding='utf-8') as f:
#             f.write(log_message + '\n')
