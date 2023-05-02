from enum import Enum


class GuiMode(Enum):
    simple = 1
    expert = 2
    factory = 3

a = {GuiMode.simple: 1, GuiMode.expert: 10}

if GuiMode.expert in a:
    print(a[GuiMode.expert])
