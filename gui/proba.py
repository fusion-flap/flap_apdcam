from functools import partial

class A:
    def __init__(self):
        self.value = 1

    def f(self,arg):
        print(self.value)
        print(arg)
        print("")


a = A()
a.value = 2
b = A()
b.value = 10

f = partial(a.f,123)
f()
