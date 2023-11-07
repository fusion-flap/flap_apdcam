class register_bits:
    def __init__(self, firstBit, lastBit, shortName, description):
        self.firstBit = firstBit
        self.lastBit  = lastBit
        self.shortName = shortName
        self.description = description

class register:
    def __init__(self,bits):
        self.bits = bits

class register_table:
    b = register_bits
    R1 = register(b(1,2,"short","desc"))

regtable = register_table()
print(regtable.R1.bits.firstBit)
print(regtable.R1.bits.lastBit)
print(regtable.R1.bits.shortName)
print(regtable.R1.bits.description)
