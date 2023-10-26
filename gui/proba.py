#!/usr/bin/python3

class A:
        

a = A()

pattern = [0,1,2,3,4,5,6,7,8,9,10]
signals = [9,10,0,1,2,3,4,5,6,7,8,9,10,0]

full,matches = a.match_pattern(signals,pattern)

print(full)
print(matches)
    
