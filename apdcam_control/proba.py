class A:
    a = 1

class B(A):
    b = 2

b = B()
print(isinstance(b,int))
