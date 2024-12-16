from sqlalchemy import create_engine


#                       数据库类型+数据库驱动选择：//用户名：密码@服务器地址：端口/数据库
# engine = create_engine('mysql+pymysql://root:3330a34da165eb85@39.106.68.189:3306/future')
engine = create_engine('mysql+pymysql://future:tl1109@39.106.68.189:3306/future')

def get_engine():
    return engine
