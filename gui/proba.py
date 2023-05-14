
class A:
    def __init__(self):
        class B:
            pass
        self.a = B()
        self.a.a = 1
        self.a.b  ="egy"


a = A()
print(a.a.a)
print(a.a.b)
