from functools import partial

class A:
    def __init__(self):
        self.value = 1
        def fff():
            print(self.value)
        self.f = fff


a = A()
a.value = 2
b = A()
b.value = 10

a.f()
b.f()
