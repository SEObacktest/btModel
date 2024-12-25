from sqlalchemy import create_engine


#                       数据库类型+数据库驱动选择：//用户名：密码@服务器地址：端口/数据库
#engine = create_engine('mysql+pymysql://root:1234@localhost:3306/future')
#engine = create_engine('mysql+pymysql://future:tl1109@39.106.68.189:3306/future')
engine = create_engine('mysql+pymysql://future:tl1009@180.76.152.14:3306/future')
def get_engine():
    return engine
