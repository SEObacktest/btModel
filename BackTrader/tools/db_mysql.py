from sqlalchemy import create_engine

engine = create_engine('mysql+pymysql://root:1234@localhost:3306/future')

def get_engine():
    return engine