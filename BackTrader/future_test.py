import pandas as pd
from .tools import DataGet
from .config import Config
class FutureTest:
    def __init__(self):
        self.name=FutureTest
        self.pro=DataGet.login_ts()
        self.exchanges=["CFFEX","DCE","CZCE","SHFE","INE","GFEX"]
        self.config=Config() 
    def get_data(self):
        dfs=[]
        for exchange in self.exchanges:
         df =self.pro.fut_basic(exchange='INE', fut_type='2', fields='ts_code,symbol,name,list_date,delist_date')
         dfs.append(df)
        return dfs
    def export_to_csv(self):
        dfs=[]
        com_df=pd.DataFrame()
        #Sry guys, wait for top-up.So let's set API limit =2 per min
        for item in self.exchanges:
            df = self.pro.fut_basic(exchange=item, fut_type='1', fields='ts_code,symbol,name,list_date,delist_date')
            df['exchange']=item
            com_df=pd.concat([com_df,df])
            
            
            
        com_df.to_csv("test.csv")
ft=FutureTest()

ft.export_to_csv()
