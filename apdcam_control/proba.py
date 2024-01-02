import copy

class Parent:
    class Child:
        def __init__(self,parent,value):
            self.parent = parent
            self.value  = value

    def __init__(self,value1, value2):
        self.value = value1
        self.child = self.Child(self,value2)

    def show(self):
        print("self value: " + str(self.value))
        print("child value: " + str(self.child.value))

print(0xab)
