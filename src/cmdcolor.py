from colorama import init as _init
from colorama import Fore, Back, Style

# Fore
FBLACK = Fore.BLACK
FRED = Fore.RED
FGREEN = Fore.GREEN
FYELLOW = Fore.YELLOW
FBULE = Fore.BLUE
FMAGENTA = Fore.MAGENTA
FCYAN = Fore.CYAN
FWHITE = Fore.WHITE
FRESET = Fore.RESET

# Back
BBLACK = Back.BLACK
BRED = Back.RED
BGREEN = Back.GREEN
BYELLOW = Back.YELLOW
BBLUE = Back.BLUE
BMAGENTA = Back.MAGENTA
BCYAN = Back.CYAN
BWHITE = Back.WHITE
BRESET = Back.RESET

# Style
SDIM =Style.DIM
SNORMAL = Style.NORMAL
SBRIGHT = Style.BRIGHT
SRESET_ALL = Style.RESET_ALL

ENABLE = False

def init(enable=True, autoreset=False):
    global ENABLE
    ENABLE = enable
    _init(autoreset=False)

def cmdstr(message, keywords=None, color=None):
    if ENABLE is True:
        if color is not None:
            if keywords is not None:
                if isinstance(keywords, list) or isinstance(keywords, tuple):
                    if isinstance(color, list) or isinstance(color, tuple):
                        _color = color[:len(keywords)] if len(keywords) <= len(color) \
                                 else [_ for _ in color] + [FRESET for _ in range(len(keywords) - len(color))]
                        _keywords = ["%s%s%s" % (_color[i], keywords[i], SRESET_ALL) for i in range(len(keywords))]
                    else:
                        _keywords = ["%s%s%s" % (color, keywords[i], SRESET_ALL) for i in range(len(keywords))]
                    return (message % tuple(_keywords))
                else:
                    _keywords = "%s%s%s" % (color, keywords, SRESET_ALL)
                    return (message % _keywords)
            else:
                return ("%s%s%s" % (color, message, SRESET_ALL))
        else:
            return (message % tuple(keywords)) if keywords is not None else message
    else:
        if isinstance(keywords, list) or isinstance(keywords, tuple):
            return (message % tuple(keywords))
        else:
            return message if keywords is None else message % keywords

def cmdprint(message, end="\n", keywords=None, color=None):
    print(cmdstr(message, keywords=keywords, color=color), end=end)

def cmdinput(prompt, keywords=None, color=None):
    cmdprint(prompt, end="", keywords=keywords, color=color)
    return input()


if __name__ == "__main__":
    init()
    cmdprint("I'm %s %s!", keywords=("Super", "Man"), color=FRED)
    cmdprint("I'm %s %s!", keywords=("Super", "Man"), color=None)
    cmdprint("I'm %s!", keywords=("Super",), color=FRED)
    cmdprint("I'm %s!", keywords=("Super"), color=FRED)
    cmdprint("I'm Man!", keywords=None, color=FRED)
    print(cmdinput("I'm %s %s? ", keywords=("Super", "Man"), color=(FRED, FBULE)))
    input()
