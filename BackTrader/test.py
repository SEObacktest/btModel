class class1():
    def __init__(self):
        self.number1=1
    def call_c2(self):
        class2.print1(self)

class class2():
    def __init__(self):
        self.number1=2
    def print1(self):
        print(self.number1)
    def print2(num):
        print(num)

obj=class1()
ob=class2()
ob.print1()