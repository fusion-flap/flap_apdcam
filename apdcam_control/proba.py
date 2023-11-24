class A:
    def func(self,a):
        print(a)

    def __init__(self):
        self.variable = "variable"
        self.func = lambda a: print("Overwritten func: " + str(a) + " " + str(self.variable) + str(B().aaa))

class B:
    aaa = "aaa"

a = A()
a.func("egy")
