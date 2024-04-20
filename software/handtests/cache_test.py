from dataclasses import dataclass
from functools import cache, cached_property


class Test:
    def __init__(self):
        self.foo = 5

    @cache
    def calc(self):
        print("Calculating")
        return self.foo + 1


test = Test()
print(test.calc())
print(test.calc())
print(" --- ")
test.foo = 500
print(test.calc())



print(" ================================== ")



class Data:
    def __init__(self, foo, bar):
        self.foo = foo
        self.bar = bar

    #def __eq__(self, other):
    #   return self.foo == other.foo and self.bar == other.bar

    def __hash__(self):
        return hash((self.foo, self.bar))

class Processor:

    @cache
    def process(self, data):
        print("processing")
        return data.foo + data.bar + 1


data = Data(1, 10)
processor = Processor()

print(processor.process(data))
print(processor.process(data))
print(" --- ")
data = Data(2, 20)
print(processor.process(data))
print(processor.process(data))

data.foo = 3
data.bar = 30
print(processor.process(data))
print(processor.process(data))

