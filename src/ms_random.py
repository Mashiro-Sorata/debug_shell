import numpy as np


class Random:
    def __init__(self, usb_instance):
        self.usb = usb_instance
        self.generator = self.random_generator_01()
        self.style = "base"

    def random_generator_01(self):
        while 1:
            data_pack = self.usb.read("ULONGLONG")
            for i in data_pack:
                yield i * (1 / 18446744073709551616)

    def random_generator_char(self):
        while 1:
            data_pack = self.usb.read("UCHAR")
            for i in data_pack:
                yield i

    def set_generator(self, style="base"):
        if self.style != style:
            if style == "base":
                self.style = "base"
                self.generator = self.random_generator_01()
            elif style == "uchar":
                self.style = "uchar"
                self.generator = self.random_generator_char()
            else:
                raise ValueError("No such style: %s" % style)

    def random(self):
        return next(self.generator)

    def choice(self, lists):
        self.set_generator("base")
        return lists[int(self.random() * len(lists))]

    def randnp(self, pack_num):
        gen = self.random_generator_01() 
        return np.array([next(gen) for i in range(pack_num * 1024)])
        

