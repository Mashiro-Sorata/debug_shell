r"""定义了一些基本的数据类型
    Type List:
        Const: 常量.
"""

import random


class ConstError(TypeError):
    pass

class ConstDeepError(Exception):
    pass

class Const:
    r"""定义常量"""
    
    def __init__(self, deep=16):
        self.__dict__["_Const__ignore"] = ["_Const__left"]
        self.__dict__["_Const__deep"] = deep
        self.__dict__["_Const__data"] = []
        self.__dict__["_Const__left"] = [i for i in range(- pow(2, deep-1), pow(2, deep-1))]
        

    def new(self, name, value):
        r"""新建普通常量.
            name: 必需, 常量名, 必需全部大写.
            value: 必需, 常量值.
        """
        self.__setattr__(name, value)
        

    def News(self, name, value=None):
        r"""新建独特常量, 常量在所有常量中独一无二, 值为Int型.
            name: 必需, 常量名.
            value: 可选, 常量值, 为None则自动分配.
        """
        if value is None:
            length = len(self.__left)
            if not length:
                raise ConstDeepError("deep %s is not enough, can't set Const!" % self.__deep)
            index = random.randint(0, length-1)
            value = self.__left.pop(index)
        setattr(self, name, value)

    
    def __setattr__(self, name, val):
        if name not in self.__ignore:
            if name in self.__dict__:
                print(name)
                raise ConstError("Can't rebind const (%s)" % name)
            if not name.isupper():
                raise ConstError("Const name '%s' is not all uppercase" % name)
            self.__dict__[name] = val
            self.__data.append(val)
        else:
            self.__dict__[name] = val

class CONST:
    r"""常量定义"""
    _print = Const()
    _print.News("CENTER")    # CONST.CENTER
    _print.News("LEFT")      # CONST.LEFT
    _print.News("RIGHT")     # CONST.RIGHT
    pass

if __name__ == "__main__":
    c = Const()

