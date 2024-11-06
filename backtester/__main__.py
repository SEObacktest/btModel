from .Backtrader_systemv3 import MainController
def main():
    MainController.start()
    
if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
