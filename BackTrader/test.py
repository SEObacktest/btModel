from config import Config

class car():
    def __init__(self):
      self.config=Config()
    
    def print_conf(self):
       print(self.config.INIT_BALANCE)

c=car()
c.print_conf()


