adcPllFreqs = []
for mult in range(1,10):
    for div in range(1,10):
        adcPllFreqs.append([20.0*mult/div,mult,div])
adcPllFreqs.sort()

i=1
print(len(adcPllFreqs))
while i<len(adcPllFreqs):
    if adcPllFreqs[i][0] == adcPllFreqs[i-1][0]:
        adcPllFreqs.pop(i)
    else:
        i=i+1

for f in adcPllFreqs:
    print(f[0],f[1],f[2])
