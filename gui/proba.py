#!/usr/bin/python3


class Register:
    def __init__(self,a,b):
        self.a = a
        self.b = b

class A:
    AAA = Register(1,2)
    BBB = Register(3,4)

print(A.AAA)    
