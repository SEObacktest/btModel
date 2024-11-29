import configparser
import os
import sys

start_date=None
end_date=None

CFG_FL_PATH="../sys.cfg"
USER_CFG_SECTION = "cerebro_config"
class Config:
    def __init__(self):
        config=configparser.ConfigParser()
    
        if not os.path.exists(CFG_FL_PATH):
            print("No configuration file (sys.cfg) found!")
            sys.exit(1)
        else:
            config.read(CFG_FL_PATH)
    
        self.INIT_BALANCE=config.get(USER_CFG_SECTION,'init_balance')
        self.API_KEY=config.get(USER_CFG_SECTION,'api_key')