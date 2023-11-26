
def loggerfunc(m):
    print(m)

logger = None

log = lambda m: logger(m) if (logger!=None) else 1


log("Hello")
