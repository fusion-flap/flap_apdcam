import ctypes
import platform

# From Python 3.8 onwards, there is a reported bug in CDLL.__init__()
#mode = dict(winmode=0) if platform.python_version() >= '3.8' else dict()  


#lib = ctypes.CDLL('./libtest.so', **mode)
#lib = ctypes.cdll.LoadLibrary('./libtest.so', **mode)
#lib = ctypes.CDLL("./libtest.so",winmode=0)

# class Test(object):
#     def __init__(self, val: int):
#         # Declare input and output types for each method you intend to use
#         lib.init.argtypes = [ctypes.c_int]
#         lib.init.restype = ctypes.c_void_p

#         lib.setInt.argtypes = [ctypes.c_void_p, ctypes.c_int]
#         lib.setInt.restype = ctypes.c_void_p

#         lib.getInt.argtypes = [ctypes.c_void_p]
#         lib.getInt.restype = ctypes.c_int

#         lib.show.argtypes = [ctypes.c_void_p, ctypes.c_char_p]
#         lib.show.restype = ctypes.c_void_p

#         self.obj = lib.init(val)

#     def setInt(self, n):
#         lib.setInt(self.obj, n)
    
#     def getInt(self):
#         return lib.getInt(self.obj)

#     def show(self,s):
#         lib.show(self.obj,s.encode('ASCII'))


ArrayType = ( ctypes.c_bool * 8 ) * 2
a = ArrayType()

for i in range(2):
    for j in range(8):
        a[i][j] = True if (i+j)%2==0 else False
for i in range(2):
    for j in range(8):
        print(a[i][j])


# a = "hello"
# if isinstance(a,str):
#     print("IGEN")
# else:
#     print("NEM STR")
    
# exit(0)

# T1 = Test(12)
# print(T1.getInt())
# T1.setInt(32)
# print(T1.getInt())
# T1.show("Hello world")
