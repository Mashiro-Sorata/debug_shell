import usb
import struct
import data


class USBError(ValueError):
    pass


class USB:
    NO_DEV = -1             # 实例化无参数时的device
    RD_END_POINT = 0x86     # 读功能EndPoint
    WR_END_POINT = 0x02     # 写功能EndPoint
    READ_BYTES_NUM = 1024
    WRITE_BYTES_NUM = 1024
    NULL = 0
    CONST = data.Const()
    CONST.new(
        "TYPES", {"CHAR": "!1024b",
                  "UCHAR": "!1024B",
                  "SHORT": "!512h",
                  "USHORT": "!512H",
                  "INT": "!256i",
                  "UINT": "!256I",
                  "LONGLONG": "!128q",
                  "ULONGLONG": "!128Q",
                  "FLOAT": "!256f",
                  "DOUBLE": "!128d"
                  }
    )

    def __init__(self, vid=None, pid=None):
        self.device = self.NO_DEV
        self.configuration = None
        self.read_end_point = None
        self.write_end_point = None
        if vid or pid:
            self.init_device(vid, pid)

    def config(self, read_bytes_num):
        if read_bytes_num % 512:
            raise ValueError("READ_BYTES_NUM must be an integer multiple of 512, not %s" % read_bytes_num)
        if read_bytes_num != self.READ_BYTES_NUM:
            self.READ_BYTES_NUM = read_bytes_num
            if hasattr(self.CONST, "TYPES"):
                delattr(self.CONST, "TYPES")

            def _fun(length, _type):
                return "!" + str(self.READ_BYTES_NUM // length) + _type
            self.CONST.new(
                "TYPES", {"CHAR": _fun(1, "b"),
                          "UCHAR": _fun(1, "B"),
                          "SHORT": _fun(2, "h"),
                          "USHORT": _fun(2, "H"),
                          "INT": _fun(4, "i"),
                          "UINT": _fun(4, "I"),
                          "LONGLONG": _fun(8, "q"),
                          "ULONGLONG": _fun(8, "Q"),
                          "FLOAT": _fun(4, "f"),
                          "DOUBLE": _fun(8, "d")}
            )

    def init_device(self, vid=None, pid=None):
        if self.device is self.NO_DEV:
            if vid is None and pid is None:
                raise ValueError("Lack of device information: vid & pid!")
            elif vid is None:
                self.device = usb.core.find(idProduct=pid)
            elif pid is None:
                self.device = usb.core.find(idVendor=vid)
            else:
                self.device = usb.core.find(idVendor=vid, idProduct=pid)
            if self.device is None:
                raise ValueError("Device not found!")
            self.device.set_configuration()
            self.configuration = self.device.get_active_configuration()
            self.read_end_point = self.__get_end_point(self.RD_END_POINT)
            self.write_end_point = self.__get_end_point(self.WR_END_POINT)
        else:
            raise USBError("USB device can not be changed!")

    def __get_end_point(self, address):
        _ep = usb.util.find_descriptor(
            self.configuration[(0, 0)],
            # match the endpoint with address
            custom_match=lambda e: e.bEndpointAddress == address)
        return _ep

    def info(self):
        if self.device != -1:
            print(self.device)
        else:
            print("No Device!")

    def read(self, types=None):
        """byte_num 单次读usb的bytes数, 应为512的整数倍, 默认1024
           按types返回格式化数据:
                CHAR: char, 1 byte;
                UCHAR: unsigned char, 1 byte;
                SHORT: short, 2 byte;
                USHORT: unsigned short, 2 byte;
                INT: int, 4 byte;
                UINT: unsigned int, 4 byte;
                LONGLONG: long long, 8 byte;
                ULONGLONG: unsigned long long, 8 byte;
                FLOAT: float, 4 byte;
                DOUBLE: double, 8 byte
        """
        if types is None:
            return self.read_end_point.read(self.READ_BYTES_NUM)
        elif types in self.CONST.TYPES.keys():
            _data = bytes(self.read_end_point.read(self.READ_BYTES_NUM))
            return struct.unpack(self.CONST.TYPES[types], _data)
        else:
            raise ValueError("No such types: %s" % types)

    def __exfill(self, data, length):
        m = length % self.WRITE_BYTES_NUM
        i = length // self.WRITE_BYTES_NUM
        if not m and not i:
            return bytes([self.NULL for _ in range(self.WRITE_BYTES_NUM)])
        elif i and not m:
            return bytes(data[:])
        elif isinstance(data, list):
            _data = data[:]
            _data.extend([self.NULL for _ in range(self.WRITE_BYTES_NUM - m)])
            return bytes(_data)
        elif isinstance(data, tuple):
            _data = list(data)
            _data.extend([self.NULL for _ in range(self.WRITE_BYTES_NUM - m)])
            return bytes(_data)
        elif isinstance(data, str):
            return bytes(data, "ascii") + bytes([self.NULL for _ in range(self.WRITE_BYTES_NUM - m)])
        elif isinstance(data, bytes):
            return data + bytes([self.NULL for _ in range(self.WRITE_BYTES_NUM - m)])
        else:
            raise ValueError("Data must be 'list', 'tuple' or 'str' type, not %s" % type(data))

    def base_write(self, data):
        if isinstance(data, bytes):
            self.write_end_point.write(data, len(data))
        else:
            raise TypeError("Data must be 'bytes' not %s" % type(data))

    def write(self, data):
        r"""写数据, data为列表,元组或字符类型.
当所给data长度小于1024时, 自动以0x00补全, data数据范围为range(0, 256)."""
        _data = self.__exfill(data, len(data))
        for i in range(len(_data)//self.WRITE_BYTES_NUM):
            # print(len(_data[i*self.WRITE_BYTES_NUM:(i+1)*self.WRITE_BYTES_NUM]))
            self.write_end_point.write(_data[i*self.WRITE_BYTES_NUM:(i+1)*self.WRITE_BYTES_NUM], self.WRITE_BYTES_NUM)
    
    def print(self, types=None):
        print(self.read(types))

    def save2file(self, name, m_bytes=1, _ascii=False):
        """name: 文件路径, m_bytes: 文件大小(MB), byte_num: 单次读usb的bytes数, _ascii: 是否以ascii保存8位二进制数"""
        _num = int(1024 * 1024 * m_bytes / self.READ_BYTES_NUM)
        if _ascii:
            with open(name, "wt") as f:
                for i in range(_num):
                    _data = self.read()
                    f.writelines([bin(_)[2:].rjust(8, "0") for _ in _data])
        else:
            with open(name, "wb") as f:
                for i in range(_num):
                    _data = self.read()
                    f.write(bytes(_data))
        return True


if __name__ == "__main__":
    VID = 0x04b4
    PID = 0x8613
    #usb_ins = USB(vid=VID, pid=PID)
    usb_ins = USB()
    # usb_ins.write([_%256 for _ in range(3*1024+1)])
    #usb_ins.info()
    # usb_test(usb_ins)
    # usb_ins.print()
    # usb_ins.write(bytes([255,255]))
