from .main_controller import MainController
import sys
if __name__=='__main__':
  try:
    def main():
        MainController.start()
  except Exception as e:
      print(e)
      sys.exit(1)
