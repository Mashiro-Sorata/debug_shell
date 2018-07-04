from cmd import Cmd
import os
import sys
from types import FunctionType
import usb_receive as _usb
from time import time, sleep
from functools import wraps
import numpy as np
import pylab as plt
import ms_random as random
import cmdcolor as _cmd


class CmdException(Exception):
    def __init__(self, *args, level=None):
        super().__init__(*args)
        if level is None:
            self.level = ERROR
        else:
            self.level = level

ERROR = "Error"
WARN = "Warning"
HEAD = """Debug-Shell (v1.2.0, Apr  27 2018, 15:18:24)
Powered by @Mashiro_Sorata                  
Type <?> or <help> for more information.    """
NODEV_WARN = CmdException("Device not found! Please do 'init' first!", level=WARN)

ERROR_COLOR = _cmd.FRED
WARN_COLOR = _cmd.FYELLOW
HEAD_COLOR = _cmd.FWHITE + _cmd.SBRIGHT
SYS_COLOR = _cmd.FGREEN + _cmd.SBRIGHT
INFO_COLOR = _cmd.FYELLOW + _cmd.SBRIGHT

def hann(N):
    x = np.arange(0, N, 1.0)
    return 0.5 * (1 - np.cos(2 * np.pi * x / (N - 1)))

def average_fft(x, fft_size):
    n = len(x) // fft_size * fft_size
    tmp = x[:n].reshape(-1, fft_size)
    tmp *= hann(fft_size)
    xf = np.abs(np.fft.rfft(tmp)/fft_size)
    avgf = np.average(xf, axis=0)
    return 20*np.log10(avgf)

def NOPARAM_ERROR(line):
    return CmdException("Invalid params: '%s'!" % line)

def chk_input(prompt, check=None):
    if isinstance(check, FunctionType):
        res = _cmd.cmdinput(prompt)
        chk = check(res)
        while chk is not True:
            if isinstance(chk, str):
                _cmd.cmdprint("%s: %s", keywords=("Input Error", chk), color=(ERROR_COLOR, INFO_COLOR))
            res = _cmd.cmdinput(prompt)
            chk = check(res)
        return res
    elif check is None:
        return _cmd.cmdinput(prompt)
    else:
        raise TypeError("Invalid Type: %s check" % type(check))


def check(s):
    if s:
        for each in s:
            if each not in "0123456789XxAaBbCcDdEeFf":
                return "Invalid data: %s!" % s
        return True
    return True

def list_check(x):
    try:
        data = eval(x)
    except Exception as e:
        return str(e)
    else:
        if isinstance(data, list):
            if len(data) <= 1024:
                return True
            else:
                return "Data length must <= 1024!"
        else:
            return "Data must be <list> type!"


def init_ids(**kws):
    file = r"usb_id.info"
    if kws.get("f"):
        if os.path.isfile(file):
            with open(file, "rt") as f:
                ids = [_.split("=")[1].strip("\n ") for _ in f.readlines()]
            vid = int(ids[0], 16) if ids[0] else None
            pid = int(ids[1], 16) if ids[1] else None
            file_name = ids[2] if ids[2] else "Data.dat"
            return vid, pid, file_name
        else:
            _cmd.cmdprint("%s: %s", keywords=(WARN, "No such a file: %s!"%file),
                          color=(WARN_COLOR, INFO_COLOR))
            if input("Do you want to creat that file?(Y/N):") in "yY":
                vid = chk_input("VID(hex):", check)
                pid = chk_input("PID(hex):", check)
                with open(file, "wt") as f:
                    f.write("VID = %s\nPID = %s\nFILE_NAME = Data.dat" % (vid, pid))
                vid = int(vid, 16) if vid else None
                pid = int(pid, 16) if pid else None
                return vid, pid
            return None
    elif kws.get("n") or kws.get("s"):
        vid = chk_input("VID(hex):", check)
        pid = chk_input("PID(hex):", check)
        if kws.get("s"):
            with open(file, "wt") as f:
                f.write("VID = %s\nPID = %s" % (vid, pid))
        vid = int(vid, 16) if vid else None
        pid = int(pid, 16) if pid else None
        return vid, pid
    elif kws.get("r"):
        return None
    else:
        raise CmdException("init_ids: Unknown syntax: %s" % kws)


def param_check(plist, params):
    for each in plist:
        if each not in params:
            raise NOPARAM_ERROR(each)
    return True

def report(times, err, time):
    print("""Report:
    Total time: %s s
    Success times: %s
    Failed times: %s""" % (time, times - len(err), len(err)))
    if len(err) and input("Print Failed Data?(Y/N):") in "Yy":
        if len(err) > 5:
            print("Too many error data, please input the range of data to print!")
            num = int(chk_input("Num: ",
                    lambda x: True if int(x) < len(err) else "Num must <= %s" % len(err)))
        else:
            num = len(err)
        print("Failed at:")
        for i in range(num):
            print("At: @%s\nData: %s\n" % (str(err[i][0]), str(err[i][1])))

def key_interrupt(f):
    @wraps(f)
    def indef(*args, **kws):
        try:
            return f(*args, **kws)
        except KeyboardInterrupt:
            _cmd.cmdprint("\nUser KeyboardInterrupt Quit!", color=WARN_COLOR)
    return indef

def usberr(prompt=None):
    @wraps(usberr)
    def dec(f):
        @wraps(f)
        def indef(*args, **kws):
            try:
                res = f(*args, **kws)
            except CmdException as cmde:
                if cmde.level == ERROR:
                    _cmd.cmdprint("%s: %s", keywords=(cmde.level, cmde), color=(ERROR_COLOR, INFO_COLOR))
                elif cmde.level == WARN:
                    _cmd.cmdprint("%s: %s", keywords=(cmde.level, cmde), color=(WARN_COLOR, INFO_COLOR))
            except Exception as e:
                try:
                    _cmd.cmdprint("%s: %s %s %s",
                                  keywords=("USBError", "Errno", e.errno, e.strerror.decode("gbk")),
                                  color=(ERROR_COLOR, INFO_COLOR, INFO_COLOR, INFO_COLOR))
                except Exception:
                    _cmd.cmdprint("%s: %s", keywords=("Error", e), color=(ERROR_COLOR, INFO_COLOR))
            else:
                if prompt is not None:
                    _cmd.cmdprint("$%s\n" % prompt, color=SYS_COLOR)
        return indef
    return dec

def cmdinfo(message):
    _cmd.cmdprint(message, color=INFO_COLOR)
                    

class DebugShell(Cmd):
    SPLIT_KEY = "-"
    def __init__(self):
        super().__init__()
        _cmd.init(True, True)
        self.initialized = False
        self.prompt = _cmd.cmdstr(">>>", color=SYS_COLOR)
        self.usb = None
        self.rdtype = "UCHAR"
        self.Bpr = 1024
        self.vid = None
        self.pid = None
        self.__set_params = {"c": lambda x: self.__config(int(x)),
                             "t": lambda x: self.__rdtype(x),
                             "n": lambda x: self.__rename(x)}
        self.type_list = ["CHAR", "UCHAR", "SHORT", "USHORT", "INT",
                          "UINT", "LONGLONG", "ULONGLONG", "FLOAT", "DOUBLE"]
        file = r"usb_id.info"
        if os.path.isfile(file):
            with open(file, "rt") as f:
                ids = [_.split("=")[1].strip("\n ") for _ in f.readlines()]
            self.file_name = ids[2] if ids[2] else "Data.dat"
        else:
            self.file_name = "Data.dat"
    
    def emptyline(self):
        pass

    @key_interrupt
    def cmdloop(self, intro=None):
        self.preloop()
        if self.use_rawinput and self.completekey:
            try:
                import readline
                self.old_completer = readline.get_completer()
                readline.set_completer(self.complete)
                readline.parse_and_bind(self.completekey+": complete")
            except ImportError:
                pass
        try:
            if intro is not None:
                self.intro = intro
            if self.intro:
                self.stdout.write(str(self.intro)+"\n")
            stop = None
            while not stop:
                if self.cmdqueue:
                    line = self.cmdqueue.pop(0)
                else:
                    if self.use_rawinput:
                        line = _cmd.cmdinput(self.prompt, color=SYS_COLOR)
                    else:
                        line = _cmd.cmdinput(self.prompt)
                        if not len(line):
                            line = 'EOF'
                        else:
                            line = line.rstrip('\r\n')
                line = self.precmd(line)
                stop = self.onecmd(line)
                stop = self.postcmd(stop, line)
            self.postloop()
        finally:
            if self.use_rawinput and self.completekey:
                try:
                    import readline
                    readline.set_completer(self.old_completer)
                except ImportError:
                    pass

    def default(self, line):
        _cmd.cmdprint("%s: %s", keywords=("*** Unknown syntax", line), color=(ERROR_COLOR, INFO_COLOR))
    
    @usberr("Device initialized successfully! Type 'info' to see details.")
    def do_init(self, line):
        r"""Function: Initialize with usb's id(hex) and to get usb handle.
    Parameter(s):| f, n, s, r | Default: f
        f: Id(s) from file("usb_id.info"), other param will not work if it exists;
        n: New id(s) entered manually for temporary test;
        s: New id(s) entered manually will be saved in file("usb_id.info").
        r: Reset usb device when it was already initialized.

You can edit the file("usb_id.info") in current location.
Please do with param(r) if you want to update usb device(If SPLIT_KEY is '-'):
Wrong eg.
    |>>>init -f
    |>>>read
    |>>>init -f
    |Error:....
    This condition will raise Error, because the device is alread being used.
Right eg.
    |>>>init
    |>>>read
    |>>>init -f -r
"""
        params = ["f", "n", "s", "r"]
        cmd = "".join(line.split())
        kws = {}
        if not cmd:
            kws["f"] = True
        else:
            plist = cmd.split(self.SPLIT_KEY)[1:]
            param_check(plist, params)
            if "r" in plist:
                kws["r"] = True
            if "f" in plist:
                kws["f"] = True
            else:
                if "n" in plist:
                    kws["n"] = True
                if "s" in plist:
                    kws["s"] = True
        if kws:
            if kws.get("r"):
                if self.usb is not None:
                    self.usb.device.reset()
                    sleep(0.2)
                else:
                    if self.initialized is not True:
                        raise CmdException("No device yet, can't reset!", level=WARN)
            ids = init_ids(**kws)
            if ids is not None:
                self.vid = ids[0]
                self.pid = ids[1]
                if len(ids) == 3:
                    self.file_name = ids[2]
                self.usb = _usb.USB(vid=ids[0], pid=ids[1])
                if self.usb.device is self.usb.NO_DEV:
                    self.usb.init_device(ids[0], ids[1])
                if self.usb is not None:
                    if self.initialized is False:
                        self.initialized = True
                    else:
                        self.__config(self.Bpr)
                else:
                    raise CmdException("Device not found! Please retry with new ids!", level=WARN)

    def __rdtype(self, rdtype):
        if rdtype in self.type_list:
            self.rdtype = rdtype if rdtype else None
        else:
            raise CmdException("No such type: %s, see more with '?set'" % rdtype)

    def __rename(self, file_name):
        with open(r"usb_id.info", "rt") as f:
            vid = f.readline()
            pid = f.readline()
        with open(r"usb_id.info", "wt") as f:
            f.writelines([vid, pid, "FILE_NAME = %s" % file_name])
        self.file_name = file_name if file_name else "Data.dat"

    @usberr("Setting done!")
    def do_set(self, line):
        r"""Function: Set usb parameters, see details in params.
    Parameter(s):| c, t, n | No default param
    (If SPLIT_KEY is '-'):
         c: Format:|>>>set 1024-c |. 
            Set the number of bytes in each read method;
            The number could be set to 512, 2048...
            It must be an integer multiple of 512!
            
         t: Format:|>>>set UCHAR-t |.
            Set data's type from read method.
            Type List:
                CHAR: char, 1 byte;
                UCHAR: unsigned char, 1 byte;
                SHORT: short, 2 byte;
                USHORT: unsigned short, 2 byte;
                INT: int, 4 byte;
                UINT: unsigned int, 4 byte;
                LONGLONG: long long, 8 byte;
                ULONGLONG: unsigned long long, 8 byte;
                FLOAT: float, 4 byte;
                DOUBLE: double, 8 byte.
        
         n: Format: |>>>set Data.dat-n |.
            Set file's name used for data saving.

Set method only works with one param!"""
        plist = "".join(line.split()).split(self.SPLIT_KEY)
        if len(plist) == 2:
            param_check([plist[1]], self.__set_params.keys())
            self.__set_params[plist[1]](plist[0])
        else:
            raise NOPARAM_ERROR(line)

    @key_interrupt
    @usberr("Reading done!")
    def do_read(self, line):
        r"""Function: Read data from usb.
    Parameter(s):| times | Default: times = 1
        times: Format:|>>>read 6 |.
               Call read method 6 times."""
        if self.usb is not None:
            if line:
                for i in range(int(line)):
                    self.usb.print(self.rdtype)
            else:
                self.usb.print(self.rdtype)
        else:
            raise NODEV_WARN

    @key_interrupt
    @usberr("Reading done!")
    def do_readwait(self, line):
        r"""Function: Wait for read data. 'ctrl+c' to exit.
    No Parameter(s)."""
        if self.usb is not None:
            while True:
                try:
                    self.usb.print(self.rdtype)
                except Exception:
                    pass
        else:
            raise NODEV_WARN


    @key_interrupt
    @usberr("Saving done!")
    def do_save(self, line):
        r"""Function: Saving data to file.
    Parameter(s):| MB, ascii | Default: MB = 1
    (If SPLIT_KEY is '-')
        MB: Format:|>>>save 2 |.
            Declaration of file's size.(Unit: M Bytes)

        ascii: Format:|>>>save 2 -ascii |.
               Data would be saved as a sequence char of '0' and '1' if param '-ascii' were given."""
        params = ["ascii"]
        if self.usb is not None:
            if line:
                if self.SPLIT_KEY in line:
                    plist = "".join(line.split()).split(self.SPLIT_KEY)
                    if len(plist) == 2:
                        param_check([plist[1]], params)
                        mb = int(plist[0]) if plist[0] else 1
                        self.usb.save2file(self.file_name, mb, True)
                    else:
                        raise NOPARAM_ERROR(line)
                else:
                    mb = int(line)
                    self.usb.save2file(self.file_name, mb)
            else:
                self.usb.save2file(self.file_name)
        else:
            raise NODEV_WARN

    def __wr_file(self, name):
        with open(name, "rb") as f:
            return f.read()

    @usberr("Writing done!")
    def do_write(self, line):
        r"""Function: Write data to usb device.
    Parameter(s):| s, l, f | Default: s
    (If SPLIT_KEY is '-')
        s: Format:|>>>write hello-s | or |>>>write hello world! |
           Write 'hello'<string> to usb device. This param is default one when param is not given.

        l: Format:|>>>write [104, 101, 108, 108, 111] -l |
           Write 'hello'(ascii) to usb device by <list>.

        f: Format:|>>>write file_name.dat -f |
           Write data in file_name.dat file. Data must be binary."""
        method = {"s": lambda x: x,
                  "l": lambda x: eval(x),
                  "f": lambda x: self.__wr_file(x)}
        name = {"s": "string", "l": "list", "f": "bytes"}
        if self.usb is not None:
            plist = line.split(self.SPLIT_KEY)
            if len(plist) == 2:
                param_check([plist[1]], method.keys())
                print("Written data<%s>:\n%s" % (name[plist[1]] ,method[plist[1]](plist[0])))
                self.usb.write(method[plist[1]](plist[0]))
            elif len(plist) == 1:
                if "[" in plist[0] and "]" in plist[0]:
                    _cmd.cmdprint("%s: %s", keywords=(WARN, "Detected type like <list>, but written as <string>!"),
                                  color=(WARN_COLOR, INFO_COLOR))
                    if input("Do you want to change the type to <list>?(Y/N)") in "Yy":
                        print("Written data<list>:\n%s" % method["l"](plist[0]))
                        self.usb.write(method["l"](plist[0]))
                    else:
                        print("Written data<string>:\n%s" % plist[0])
                        self.usb.write(plist[0])
                else:
                    print("Written data<string>:\n%s" % plist[0])
                    self.usb.write(plist[0])
            else:
                raise NOPARAM_ERROR(line)
        else:
            raise NODEV_WARN

    def __loop_test(self):
        cmdinfo("Loop Test Running...")
        content = eval(chk_input("Send Data(<list> required): ", list_check))
        if len(content) <= 512:
            write_times = 2
            content = (content[:]+[0 for _ in range(512-len(content))])
            res_con = content[:] + content[:]
        elif len(content) <= 1024:
            write_times = 1
            content = (content[:] + [0 for _ in range(1024-len(content))])
            res_con = content[:]
        else:
            raise CmdException("Send Data<list> length must <= 1024")
        times = int(input("Loop Times: "))
        err = []
        cmdinfo("Loading...(Interrupt with <ctrl+c>!)")
        start = time()
        for i in range(times):
            for j in range(write_times):
                self.usb.base_write(bytes(content))
            res = list(self.usb.read())
            if res != res_con:
                err.append((i+1, res))
        end = time()
        report(times, err[:], end-start)
        cmdinfo("Loop Test End!")


    def __read_test(self):
        cmdinfo("Read Test Running...")
        content = eval(chk_input("Read Data(<list> required): ", list_check))
        if len(content) <= 1024:
            content = (content[:] + [0 for _ in range(1024-len(content))])
        else:
            raise CmdException("Read Data<list> length must <= 1024")
        times = int(input("Loop Times: "))
        err = []
        cmdinfo("Loading...(Interrupt with <ctrl+c>!)")
        start = time()
        for i in range(times):
            res = list(self.usb.read())
            if res != content:
                err.append(i+1, res)
        end = time()
        report(times, err[:], end-start)
        cmdinfo("Read Test End!")

    def __speed_test(self):
        cmdinfo("Speed Test Running...")
        num = int(input("Test Times: "))
        if num > 0:
            cmdinfo("Loading...(Interrupt with <ctrl+c>!)")
            begin = time()
            for _ in range(num):
                self.usb.read()
            end = time()
            data_size = num * 8 * self.Bpr
            dt = end - begin
            v = data_size / (dt * 1000000)
            print("Test Result:\n>>Total Size: %s bit\n>>Total Time: %s s\n>>Velocity: %s Mb/s\n"
                  % (data_size, dt, v))
            cmdinfo("Speed Test End!")
        else:
            raise CmdException("Test times must > 0 !")

    def __fft_test(self):
        cmdinfo("FFT Test Running...")
        dnum = int(input("Read Num: "))
        fft_size = int(input("FFT Size: "))
        if input("Data as random?(Y/N)") in "Yy":
            cmdinfo("Loading...(Interrupt with <ctrl+c>!)")
            begin = time()
            r = random.Random(self.usb)
            data = r.randnp(dnum) - 0.5
        else:
            data = []
            cmdinfo("Loading...(Interrupt with <ctrl+c>!)")
            begin = time()
            for i in range(dnum):
                data += list(self.usb.read())
            data = np.array(data, dtype="float64")
        xf = average_fft(data, fft_size)
        end = time()
        print("Report:\n")
        print("Used Time: %s s" % (end - begin))
        print("Result:")
        print("%s" % xf)
        if input("Plot result?(Y/N)") in "Yy":
            plt.plot(xf)
            plt.show()
        cmdinfo("FFT Test End!")
        
    @key_interrupt
    @usberr("Test Successful!")
    def do_Test(self, line):
        r"""Function: Usb test.
    No Parameter(s)."""
        if self.usb is not None:
            self.__config(1024)
            Test = [self.__loop_test, self.__read_test,
                    self.__speed_test, self.__fft_test]
            if line:
                NOPARAM_ERROR(line)
            else:
                cmdinfo("Choose the number of the test that you want to do:\n" +
                            "\t1.Loop Test: Test for usb loop back.\n"+
                            "\t2.Read Test: Test read data.\n" +
                            "\t3.Speed Test: Test speed of usb read.\n" +
                            "\t4.FFT Test: Test FFT of read data.\n")
                num = int(input("Test Number:"))
                Test[num-1]()
        else:
            raise NODEV_WARN
            

    def __config(self, bytes_num):
        if self.usb is not None:
            self.usb.config(bytes_num)
            self.Bpr = bytes_num
        else:
            raise NODEV_WARN

    @usberr()
    def do_cls(self, line):
        r"""Function: Clear Dos Shell.
    No parameter(s)."""
        if line:
            NOPARAM_ERROR(line)
        else:
            os.system("cls")
            _cmd.cmdprint(HEAD, color=HEAD_COLOR)

    def __shell_info(self):
        cmdinfo("\nShell Info:")
        vid = hex(self.vid) if self.vid is not None else "None"
        pid = hex(self.pid) if self.pid is not None else "None"
        print("""    VID -> %s
    PID -> %s
    Read Type -> %s
    Bytes per Read -> %s
    File Name -> %s""" % (vid, pid, self.rdtype, self.Bpr, self.file_name))

    def __info(self, param):
        if param == "d":
            if self.usb is not None:
                self.usb.info()
            else:
                raise NODEV_WARN
        elif param == "s":
            self.__shell_info()
        elif param == "a":
            cmdinfo("Device Info:")
            if self.usb is not None:
                self.usb.info()
            else:
                print("    No Device yet!")
            self.__shell_info()

    @usberr("Info done!")
    def do_info(self, line):
        r"""Function: Show infomation.
    Parameter(s):| d, s, a| Default: s
        d: The information of usb device;
        s: The information of this shell's configuration;
        a: The information of all."""
        params = ["d", "s", "a"]
        if line:
            plist = "".join(line.split()).split(self.SPLIT_KEY)
            if len(plist) == 2 and plist[0] == "":
                param_check([plist[1]], params)
                self.__info(plist[1])
            else:
                raise NOPARAM_ERROR(line)
        else:
            self.__info("s")

    @usberr()
    def do_all(self, line):
        r"""Function: Show all method and help.
Type 'all' for more infomation!"""
        if line:
            raise NOPARAM_ERROR(line)
        else:
            cmdinfo(r"""
<!!!TIPS!!!>
<!!!If you want to add param(s) after method, please add '%s' before param(s)!!!>
<!!!You can type <ctrl+c> to quit some transition(s)!!!>
See more details by help:
    Format: |>>>help init
            |......
            
        or: |>>>?init
            |......
""" % self.SPLIT_KEY)

    def __restart(self, enable):
        _cmd.init(enable)
        self.prompt = _cmd.cmdstr(">>>", color=SYS_COLOR)
    
    @usberr("Restart done!")
    def do_restart(self, line):
        r"""Function: Restart shell with param(s).
    Parameter(s):| c | Defualt: on
    (If SPLIT_KEY is '-')
        c: Format:|>>>restart on-c | or |>>>restart off-c |
            Enable or disable ANSI escape sequences, which provide variety colors for cmd frame.
            If messy codes appeared, try to turn it off.
        
"""
        params = ["c"]
        if line:
            plist = "".join(line.split()).split(self.SPLIT_KEY)
            if len(plist) == 2 and plist[0] != "":
                param_check([plist[1]], params)
                if plist[0] == "on":
                    self.__restart(True)
                elif plist[0] == "off":
                    self.__restart(False)
                else:
                    raise NOPARAM_ERROR(line)
            else:
                raise NOPARAM_ERROR(line)
        else:
            self.__restart(True)

    def do_exit(self, line):
        r"""Function: Exit this shell.
    No Parameter(s)."""
        if line:
            raise NOPARAM_ERROR(line)
        else:
            os._exit(0)

if __name__ == "__main__":
    debug = DebugShell()
    _cmd.cmdprint(HEAD, color=HEAD_COLOR)
    while True:
        debug.cmdloop()
        if chk_input(_cmd.cmdstr("%s(Y/N): ", keywords="Quit Shell?", color=SYS_COLOR),
                     lambda x: True if x in "YyNn" else "Unknown Input: '%s'!" % x) in "Yy":
            break
