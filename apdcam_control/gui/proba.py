#!/usr/bin/python3

V = 30
Vreg = int(V/0.12)
print("Value in register: " + str(Vreg))
mask = 2**12-1
Vreg2 = (Vreg*256) & mask
print("hahaha: " + str(Vreg2))
