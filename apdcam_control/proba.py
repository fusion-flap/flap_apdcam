class A:
    aa = 1
    def __init__(self):
        print(self.aa)
        print(self.bb)
    bb = 2

class B(A):
    cc = 3

a = A()
print("---")
b = B()
