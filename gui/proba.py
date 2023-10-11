#!/usr/bin/python3

from sys import getrefcount


a = bytearray(10)
print(getrefcount(a))
b = a[0:2]
print(getrefcount(a))

