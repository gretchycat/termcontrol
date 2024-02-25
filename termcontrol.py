#!/usr/bin/python3
import sys, os, fcntl, select, asyncio, termios, tty, logging, pyte, re, icat

"""
         0   1   2   3   4   5   6   7   8   9   A   B   C   D   E   F
U+250x   ─   ━   │   ┃   ┄   ┅   ┆   ┇   ┈   ┉   ┊   ┋   ┌   ┍   ┎   ┏
U+251x   ┐   ┑   ┒   ┓   └   ┕   ┖   ┗   ┘   ┙   ┚   ┛   ├   ┝   ┞   ┟
U+252x   ┠   ┡   ┢   ┣   ┤   ┥   ┦   ┧   ┨   ┩   ┪   ┫   ┬   ┭   ┮   ┯
U+253x   ┰   ┱   ┲   ┳   ┴   ┵   ┶   ┷   ┸   ┹   ┺   ┻   ┼   ┽   ┾   ┿
U+254x   ╀   ╁   ╂   ╃   ╄   ╅   ╆   ╇   ╈   ╉   ╊   ╋   ╌   ╍   ╎   ╏

         0   1   2   3   4   5   6   7   8   9   A   B   C   D   E   F
U+255x   ═   ║   ╒   ╓   ╔   ╕   ╖   ╗   ╘   ╙   ╚   ╛   ╜   ╝   ╞   ╟
U+256x   ╠   ╡   ╢   ╣   ╤   ╥   ╦   ╧   ╨   ╩   ╪   ╫   ╬   ╭   ╮   ╯
U+257x   ╰   ╱   ╲   ╳   ╴   ╵   ╶   ╷   ╸   ╹   ╺   ╻   ╼   ╽   ╾   ╿

         0   1   2   3   4   5   6   7   8   9   A   B   C   D   E   F
U+258x   ▀   ▁   ▂   ▃   ▄   ▅   ▆   ▇   █   ▉   ▊   ▋   ▌   ▍   ▎   ▏
U+259x   ▐   ░   ▒   ▓   ▔   ▕   ▖   ▗   ▘   ▙   ▚   ▛   ▜   ▝   ▞   ▟
"""

grchr={}
grchr['ascii']={'hline':'-', 'vline':'|',
                'TH':'^', 'BH':'o',
                'B0':' ', 'B25':':', 'BN60':'$', 'B75':'#', 'B100':'@',
                'BLC':'\\', 'TLC':'/', 'BRC':'/', 'TRC':'\\',
                'BLB':'+', 'TLB':'+', 'BRB':'+', 'TRB':'+',
                'TBR':'|', 'TBL':'|', 'BLR':'-', 'TLR':'-', 'TBLR':'+',
                }

grchr['utf8']={ 'hline':'\u2500', 'vline':'\u2502',
                'TH':'\u2580', 'BH':'\u2584',
                'B0':' ', 'B25':'\u2591', 'B50':'\u2593', 'B75':'\u2593', 'B100':'\u2588',
                'BLC':'\u256E', 'TLC':'\u256F', 'BRC':'\u256D', 'TRC':'\u2570',
                'BLB':'\u2510', 'TLB':'\u2518', 'BRB':'\u250C', 'TRB':'\u2514',
                'TBR':'\u251C', 'TBL':'\u2524', 'BLR':'\u252C', 'TLR':'\u2534', 'TBLR':'\u253C',
               }

theme={}
theme['inside']={
        'TL': 'BH', 'TC': 'BH', 'TR': 'BH',
        'ML': 'B100', 'MC': 'B75', 'MR': 'B100',
        'BL': 'TH', 'BC': 'TH', 'BR': 'TH'
        }

theme['outside']={
        'TL': 'B100', 'TC': 'TH', 'TR': 'B100',
        'ML': 'B100', 'MC': 'B0', 'MR': 'B100',
        'BL': 'B100', 'BC': 'BH', 'BR': 'B100'
        }

theme['curve']={
        'TL': 'BRC', 'TC': 'hline', 'TR': 'BLC',
        'ML': 'vline', 'MC': 'B0', 'MR': 'vline',
        'BL': 'TRC', 'BC': 'hline', 'BR': 'TLC'
        }

rgb_file_path = '/usr/share/X11/rgb.txt'

class termcontrol:
    def __init__(self):
        self.x11_colors = self.parse_rgb_file(rgb_file_path)
        self.image_support=[]
        self.img_cache={}
        term=os.environ.get('TERM', '')
        konsole_ver=os.environ.get('KONSOLE_VERSION', '')
        if 'kitty' in term:
            self.image_support.append('kitty')
        if 'vt340' in term or len(konsole_ver or '')>0:
            self.image_support.append('sixel')

    def enable_mouse(self, utf8=True):
        if(utf8):
            return "\x1b[?1005h"
        return "\x1b[?1000h"

    def disable_mouse(self, utf8=True):
        if(utf8):
            return "\x1b[?1005l"
        return "\x1b[?1000l"

    def enable_cursor(self):
        return "\x1b[?25h"

    def disable_cursor(self):
        return "\x1b[?25l"

    def normal_screen(self):
        return "\x1b[?1049l"

    def alt_screen(self):
        return "\x1b[?1049h"

    def set_title(self, title):
        return f"\x1b]0;{title}\\a"

    def pause_terminal_output(self):
        sys.stdout.flush()
        os.system('stty -icanon -echo')

    def resume_terminal_output(self):
        sys.stdout.flush()
        os.system('stty icanon echo')

    def parse_rgb_file(self, file_path):
        colors = {}
        if not os.path.isfile(file_path):
            return colors
        return colors
        with open(file_path, 'r') as file:
            for line in file:
                if not line.startswith('!'):
                    parts = line.strip().split('\t')
                    if len(parts) >= 4:
                        name = parts[3].lower()
                        red, green, blue = int(parts[0]), int(parts[1]), int(parts[2])
                        colors[name] = {'red':red, 'green':green, 'blue':blue}
        return colors

    def pause(self):
        print ('[pause]')
        return sys.stdin.readline()

    def get_terminal_size(self):
        import array, fcntl, sys, termios
        buf = array.array('H', [0, 0, 0, 0])
        fcntl.ioctl(sys.stdout, termios.TIOCGWINSZ, buf)
        # Create a dictionary with meaningful keys
        window_info = {
            "rows": buf[0],
            "columns": buf[1],
            "width": buf[2],
            "height": buf[3]
        }
        return window_info

    def color(self, color):
        if type(color)==int:
            return color
        co={
                'black'  : 0,
                'red'    : 1,
                'green'  : 2,
                'yellow' : 3,
                'brown'  : 3,
                'blue'   : 4,
                'magenta': 5,
                'cyan'   : 6,
                'white'  : 7,
                'brightblack'  : 8,
                'brightred'    : 9,
                'brightgreen'  : 10,
                'brightbrown'  : 11,
                'brightyellow' : 11,
                'brightblue'   : 12,
                'brightmagenta': 13,
                'brightcyan'   : 14,
                'brightwhite'  : 15,
            }
        if type(color)==str:
            regex = r'^([A-Fa-f0-9]{6})$'
            if re.match(regex, color) is not None:
                color={
                        'red'  :int(color[0:2], 16),
                        'green':int(color[2:4], 16),
                        'blue' :int(color[4:6], 16),
                      }
                return color
            regex = r'^([A-Fa-f0-9]{3})$'
            if re.match(regex, color) is not None:
                color={
                        'red'  :int(color[0:1], 16)*16,
                        'green':int(color[1:2], 16)*16,
                        'blue' :int(color[2:3], 16)*16,
                      }
                return color
            regex = r'^#([A-Fa-f0-9]{6})$'
            if re.match(regex, color) is not None:
                color={
                        'red'  :int(color[1:3], 16),
                        'green':int(color[3:5], 16),
                        'blue' :int(color[5:7], 16),
                      }
                return color
            regex = r'^#([A-Fa-f0-9]{3})$'
            if re.match(regex, color) is not None:
                color={
                        'red'  :int(color[1:2], 16)*16,
                        'green':int(color[2:3], 16)*16,
                        'blue' :int(color[3:4], 16)*16,
                      }
                return color
            if co.get(color):
                return co.get(color)
            return self.x11_colors.get(color)
        return None

    def getRGB(self, c):
        color=self.color(c)
        if type(color)==dict:
            return color
        if type(color)==int:
            pass #FIXME
        return {'red':127, 'green':127, 'blue':127}

    def ansicolor(self, fg=7, bg=None,
                  bold=False, dim=False, italic=False, underline=False,
                  strike=False, blink=False, blink2=False, reverse=False,
                  bold_is_bright=False):
        if fg=='default':
            fg=7
        if bg=='default':
            bg=None
        fg=self.color(fg)
        bg=self.color(bg)
        fgs=""
        bgs=""
        if type(fg)==int:
            if fg<16:
                if fg<8:
                    if bold_is_bright:
                        fgs=f"{fg+90}"
                    else:
                        fgs=f"{fg+30}"
                else:
                    fgs=f"{(fg-8)+90}"
            else:
                fgs=f'38;5;{fg}'
        elif type(fg)==dict:
            fgs=f'38;2;{fg["red"]};{fg["green"]};{fg["blue"]}'
        if type(bg)==int:
            if bg<16:
                if bg<8:
                    bgs=f"{bg+40}"
                else:
                    bgs=f"{(bg-8)+100}"
            else:
                bgs=f'48;5;{bg}'
        elif type(bg)==dict:
            bgs=f'48;2;{bg["red"]};{bg["green"]};{bg["blue"]}'
        bo, bl, bl2, dm, it, ul, st, rv="","","","","","","", ""
        if bold:bo='1;'
        if dim:bdm='2;'
        if italic:it='3;'
        if underline:ul='4;'
        if blink:bl='5;'
        if blink2:bl2='6;'
        if reverse:rv='7;'
        ansi=""
        if len(bgs) and len(fgs):
            ansi=f'{fgs};{bgs}'
        elif len(bgs):
            ansi=bgs
        elif len(fgs):
            ansi=fgs
        if len(ansi)>0:
            return f"\x1b[{bo}{dm}{it}{ul}{bl}{bl2}{rv}{ansi}m"
        return ""

    def drawRuler(self,w,h):
        buffer=''
        for y in range(0,h):
            for x in range(0,int((w)/10)):
                buffer+=self.gotoxy(x*10+1,y)
                buffer+=f'({x*10+1},{y})'
        return buffer

    def pyte_render(self, x, y, screen, line=1,
                    fg='default', bg='default',
                    fg0='default', bg0='default',
                    bold_is_bright=False):
        bold=False
        blink=False
        w=screen.columns
        h=screen.screen_lines
        start_line=line-1
        if start_line<0:
            start_line=int(screen.cursor.y-h+2)
        if start_line<0:
            start_line=0
        if start_line>int(screen.cursor.y-h+2):
            start_line=int(screen.cursor.y-h+2)
        buffer = self.ansicolor(fg, bg, bold=bold, blink=blink)
        screen.cursor_position(screen.screen_lines+start_line, 1)
        for yy in range(start_line, start_line+h):
            buffer += self.gotoxy(x, y+yy-(start_line))
            buffer+=self.ansicolor(fg, bg)
            for xx in range(w):
                if screen.buffer[yy][xx].fg!=fg or screen.buffer[yy][xx].bold!=bold:
                    fg=screen.buffer[yy][xx].fg
                    bold=screen.buffer[yy][xx].bold
                    buffer += self.ansicolor(fg, None, bold=bold, bold_is_bright=bold_is_bright)
                if screen.buffer[yy][xx].bg!=bg or screen.buffer[yy][xx].blink!=blink:
                    bg=screen.buffer[yy][xx].bg
                    blink=screen.buffer[yy][xx].blink
                    buffer += self.ansicolor(None, bg, blink=blink)
                buffer += screen.buffer[yy][xx].data
            buffer+=self.ansicolor(fg0, bg0)
        return buffer

    def gotoxy(self, x, y):
        return f'\x1b[{int(y)};{int(x)}f'

    def clear(self):
        return '\x1b[2J'

    def reset(self):
        return '\x1b[0m'

    def setbg(self, c):
        return self.ansicolor(None, c)

    def setfg(self, c):
        return self.ansicolor(c, None)

    def up(self, n):
        return f'\x1b[{n}A'

    def down(self, n):
        return f'\x1b[{n}B'

    def left(self, n):
        return f'\x1b[{n}D'

    def right(self, n):
        return f'\x1b[{n}C'

    def clear_images(self):
        out=''
        if 'kitty' in self.image_support:
            out+='\x1b_Ga=d\x1b\\'
        if 'sixel' in self.image_support:
            pass
        return out

    def showImage(self, image, x=0, y=0, w=30, h=15, showInfo=False, mode='auto', charset='utf8'):
        desc=""
        imgX,imgY=0,0
        if(showInfo):
            try:
                img = Image.open(image)
                imgX,imgY=img.size
                img.close()
            except:
                pass
                #logging.WARNING(f"can't open {image} as an image.")
            filename=os.path.basename(image)
            desc=f'({imgX}x{imgY}) {filename}'[:w]
            descX=int(x+(w/2)-(len(desc)/2))+1
            descY=int(y+h)-1
            desc=f'\x1b[s\x1b[48;5;245;30m\x1b[{descY};{descX}H{desc}\n'
        start_pos = f'\x1b[{y};{x+1}H'
        if not self.img_cache.get(image):
            ic=ICat(w=int(w), h=int(h), zoom='aspect', f=True, x=int(0), y=int(0), place=True, mode=mode, charset=charset)
            self.img_cache[image]=ic.print(image)
        return f'{start_pos}{self.img_cache[image]}{desc}'

def clean(input_string):
    # Use regular expressions to replace consecutive whitespace characters with a single space
    cleaned_string = re.sub(r'\s+', ' ', input_string)
    # Remove leading and trailing spaces
    return cleaned_string.strip()

class pyteLogger(logging.Logger):
    def __init__(self, refresh_class=None):
        logging.__init__('pyte')
        self.refresh_class=refresh_class

    def debug(self, msg, *args, **kwargs):
        logging.debug(clean(msg), *args, **kwargs)
        if self.refresh_class: self.refresh_class.refresh()

    def info(self, msg, *args, **kwargs):
        logging.info(clean(msg), *args, **kwargs)
        if self.refresh_class: self.refresh_class.refresh()

    def warning(self, msg, *args, **kwargs):
        logging.warning(clean(msg), *args, **kwargs)
        if self.refresh_class: self.refresh_class.refresh()

    def error(self, msg, *args, **kwargs):
        logging.error(clean(msg), *args, **kwargs)
        if self.refresh_class: self.refresh_class.refresh()

    def critical(self, msg, *args, **kwargs):
        logging.critical(clean(msg), *args, **kwargs)
        if self.refresh_class: self.refresh_class.refresh()
        exit()

class boxDraw:
    def __init__(self, bgColor=24,
                bg0=0, fg0=7,
                chars="",
                frameColors=[],
                title="", statusBar='',
                mode='auto', charset='utf8',
                style='inside',
                ):
        self.term=termcontrol()
        self.fg0, self.bg0=fg0, bg0
        self.bgColor=bgColor
        if len(chars)!=9:
            cd=grchr['utf8']
            if charset.lower() in ['utf8', 'utf-8']:
                cd=grchr['utf8']
            else:
                cd=grchr['ascii']
            self.chars=f'{cd[theme[style]["TL"]]}{cd[theme[style]["TC"]]}{cd[theme[style]["TR"]]}'\
                        f'{cd[theme[style]["ML"]]}{cd[theme[style]["MC"]]}{cd[theme[style]["MR"]]}'\
                        f'{cd[theme[style]["BL"]]}{cd[theme[style]["BC"]]}{cd[theme[style]["BR"]]}'
        else:
            self.chars=chars
        fr=False
        if len(frameColors)!=9:
            fr=True
        if mode in ['sixel', 'kitty', '24bit', '24-bit', 'auto']:
            if fr:
                self.frameColors=['#FFF', '#AAA','#777','#AAA', 0, '#555', '#777','#555','#333']
            if type(bgColor)==int and bgColor>255:
                self.bgColor=0
            else:
                self.bgColor=bgColor
        elif mode in ['8bit', '8-bit', '256color', '8bitgrey', 'grey', '8bitbright']:
            if fr:
                self.frameColors=[255, 245, 240, 245, 0, 237, 240, 237, 235]
            if type(bgColor)!=int or bgColor>255:
                self.bgColor=0
            else:
                self.bgColor=bgColor
        elif mode in ['4bit', '4-bit', '16color', '4bitgrey']:
            if fr:
                self.frameColors=[15, 7, 8, 7, 0, 8, 7, 8, 0]
            if type(bgColor)!=int or bgColor>15:
                self.bgColor=0
            else:
                self.bgColor=bgColor
        else:
            if fr:
                self.frameColors=[7, 7, 7, 7, 0, 7, 7, 7, 7]
            self.bgColor=0
        self.tinted=None
        self.title=title
        self.statusBar=statusBar

    def setColors(self, bgcolor, frameColors):
        self.bgColor=bgColor
        self.frameColors=frameColors

    def tintFrame(self, color):
        if color==None:
            self.tinted=None
            return
        c=self.term.getRGB(color)
        r, g, b=c['red'], c['green'], c['blue']
        r=r/255.0
        g=g/255.0
        b=b/255.0
        self.tinted=[]
        for i in range(0, len(self.frameColors)):
            c=self.term.getRGB(i)
            fr,fg,fb=c['red'], c['green'], c['blue']
            fr=int(fr/16*r)
            fg=int(fg/16*g)
            fb=int(fb/16*b)
            self.tinted.append(F"#{fr:X}{fg:X}{fb:X}")

    def unTintFrame(self):
        self.tinted=None

    def setCharacters(self):
        self.chars=chars

    def invert(self, cl):
        c=cl.copy()
        for i in range(0, len(cl)):
            c[i]=cl[8-i]
        return c

    def draw(self, x, y, w, h, fill=True, invert=False):
        if(w<3): w=3
        if(h<3): h=3
        colors=self.frameColors
        if(self.tinted):
            colors=self.tinted
        if invert:
            colors=self.invert(colors)
            pass
        buff=self.term.gotoxy(x,y)
        buff+=self.term.ansicolor(colors[0], self.bg0)+self.chars[0]
        buff+=self.term.ansicolor(colors[1], self.bg0)+self.chars[1]*(w-2)
        buff+=self.term.ansicolor(colors[2], self.bg0)+self.chars[2]
        buff+=self.term.ansicolor(self.fg0, self.bg0)
        for i in range(1,h-1):
            buff+=self.term.gotoxy(x,y+i)+\
                self.term.ansicolor(colors[3], self.bg0)+self.chars[3]
            if(fill):
                buff+=self.term.ansicolor(colors[4], self.bgColor)+self.chars[4]*(w-2)
            else:
                buff+=self.term.ansicolor(colors[4], self.bgColor)
                buff+=F"\x1b[{w-2}C"
            buff+=self.term.ansicolor(colors[5], self.bg0)+self.chars[5]
            buff+=self.term.ansicolor(self.fg0, self.bg0)
        buff+=self.term.gotoxy(x,y+h-1)
        buff+=self.term.ansicolor(colors[6], self.bg0)+self.chars[6]
        buff+=self.term.ansicolor(colors[7], self.bg0)+self.chars[7]*(w-2)
        buff+=self.term.ansicolor(colors[8], self.bg0)+self.chars[8]
        buff+=self.term.ansicolor(self.fg0, self.bg0)
        if self.title!='':
            desc=self.title
            descX=int(x+(w/2)-(len(desc)/2))+1
            descY=int(y)
            descPos=self.move(descX, descY)
            descColor=self.term.ansicolor(16, colors[1])
            buff+=f'{descPos}{descColor}{desc}'
            buff+=self.term.ansicolor(self.fg0, self.bg0)
        if self.statusBar!='':
            pass
        return buff

class termKeyboard:
    def __init__(self):
        self.kbtimeout=0.25
        self.keymap={"\x1b[A":"Up", "\x1b[B":"Down",\
                 "\x1b[C":"Right", "\x1b[D":"Left",\
                 "\x7f":"Backspace", "\x09":"Tab",\
                 "\x0a":"Enter", "\x1b\x1b":"Esc",\
                 "\x1b[H":"Home", "\x1b[F":"End",\
                 "\x1b[5~":"PgUp", "\x1b[6~":"PgDn",\
                 "\x1b[2~":"Ins", "\x1b[3~":"Del",\
                 "\x1bOP":"F1", "\x1bOQ":"F2",\
                 "\x1bOR":"F3", "\x1bOS":"F4",\
                 "\x1b[15~":"F5", "\x1b[17~": "F6",\
                 "\x1b[18~":"F7", "\x1b[19~": "F8",\
                 "\x1b[20~":"F9", "\x1b[21~": "F10",\
                 "\x1b[23~":"F11", "\x1b[24~": "F12",\
                 "\x1b[32~":"SyRq", "\x1b[34~": "Brk",
                 "\x1b[Z":"Shift Tab"}

    def disable_keyboard_echo(self): # Get the current terminal attributes
        attributes = termios.tcgetattr(sys.stdin)
        # Disable echo flag
        attributes[3] = attributes[3] & ~termios.ECHO
        # Apply the modified attributes
        termios.tcsetattr(sys.stdin, termios.TCSANOW, attributes)

    def enable_keyboard_echo(self): # Get the current terminal attributes
        attributes = termios.tcgetattr(sys.stdin)
        # Enable echo flag
        attributes[3] = attributes[3] | termios.ECHO
        # Apply the modified attributes
        termios.tcsetattr(sys.stdin, termios.TCSANOW, attributes)

    def read(self, bin=False):
        rlist, _, _ = select.select([sys.stdin], [], [], self.kbtimeout)
        if rlist:
            if not bin:
                try:
                    return sys.stdin.read(1)
                except:
                    return sys.stdin.buffer.read(1)
            else:
                return sys.stdin.buffer.read(1)
        return ''

    def ord(self, d):
        if(type(d)==int):
            return d
        if(type(d)==str):
            return ord(d[0])
        if(type(d)==bytes):
            return int.from_bytes(d)
        return int(d)

    def read_keyboard_input(self): # Get the current settings of the terminal
        flags = fcntl.fcntl(sys.stdin.fileno(), fcntl.F_GETFL)
        fcntl.fcntl(sys.stdin.fileno(), fcntl.F_SETFL, flags | os.O_NONBLOCK)
        filedescriptors = termios.tcgetattr(sys.stdin)
        # Set the terminal to cooked mode
        tty.setcbreak(sys.stdin)
        char = self.read()
        buffer=char
        # Check if the character is an arrow key or a function key
        if char == "\x1b":
            char = self.read()
            buffer+=char
            if(char=='O'):      #special key F1-F4
                char = self.read()
                buffer+=char
            elif char=='[':     #special key or mouse
                char = self.read()
                buffer+=char
                if char=='M':   #mouse
                    b = self.ord(self.read(bin=True))-32
                    x = self.ord(self.read(bin=True))-32
                    y = self.ord(self.read(bin=True))-32
                    buffer+=f'\x1b[M{b};{x};{y}'
                    mouse=[b, x, y]
                else:           #other ansi sequence
                    while char>='0' and char<='9' or char==';':
                        char = self.read()
                        buffer+=char
        # Restore the original settings of the terminal
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, filedescriptors)
        fcntl.fcntl(sys.stdin.fileno(), fcntl.F_SETFL, flags & ~os.O_NONBLOCK)
        key=self.keymap.get(str(buffer))
        return key or str(buffer)

class widget():
    def __init__(self, x=1, y=1, w=1, h=1, fg=7, bg=0, key=None, action=None):
        self.fg0=7
        self.bg0=0
        self.invert=False
        self.key=key
        self.action=action
        self.minW=1
        self.minH=1
        self.t=termcontrol()
        self.kb=termKeyboard()
        self.setSize(x, y, w, h)
        self.setColors(fg, bg)
        self.widgetList=[]
        self.outstream=None #sys.stdout
        self.focus=None
        self.parent=None

    def __del__(self):
        pass

    def checkWidgetEvents(self, key, w):
        if key!='':
            esc='\x1b'
            print(f'{self.t.gotoxy(10,19)}  {key.replace(esc, "<")}         ')
        if w.key==key:
            if f'{type(self.action)}' in [ "function", "<class 'method'>" ]:
                self.invert=True
                self.action()
            else:
                print(f'{self.t.gotoxy(10,20)}invalid action for "{key}" type: {type(self.action)}             ')
        for cw in w.widgetList:
            cw.checkWidgetEvents(key, cw)

    def guiLoop(self):
        go=True
        self.t.disable_cursor()
        self.t.enable_mouse()
        buffercache=""
        while go:
            buffer=self.draw()
            if buffer != buffercache:
                buffercache=buffer
                print(buffer, end='')
            #print("\n"*3)
            key=self.kb.read_keyboard_input()
            self.checkWidgetEvents(key, self)
        self.t.enable_cursor()
        self.t.disable_mouse()

    def quit(self):
        exit(0)

    def setColors(self, fg, bg):
        self.fg, self.bg=fg, bg

    def setSize(self, x, y, w, h): #should always be okay
        if x<1:
            x=1
        if y<1:
            y=1
        scr=self.t.get_terminal_size()
        if w<self.minW:
            w=self.minW
        if h<self.minH:
            h=self.minH
        if x>scr['columns']-self.minW:
            x=scr['columns']-self.minW
        if y>scr['rows']-self.minH:
            y=scr['rows']-self.minH
        if w>scr['columns']-x+1:
            w=scr['columns']-x+1
        if h>scr['rows']-y+1:
            h=scr['rows']-y+1
        self.x=x
        self.y=y
        self.w=w
        self.h=h

    def addWidget(self, widget):
        widget.parent=self
        widget.fg0=self.fg
        widget.bg0=self.bg
        self.widgetList.append(widget)
        return self.widgetList[-1]

    def resize(self):
        for w in self.widgetList:
            w.resize()

    def drawChildren(self):
        buffer=''
        for w in self.widgetList:
            buffer+=w.draw()
        return buffer

    def draw(self):
        buffer=self.drawChildren()
        if self.outstream:
            self.outstream.write(buffer)
        return buffer

    def setFocus(self):
        pas

    def onFocus(self):
        pass

    def onDeFocus(self):
        pass

    def mouseEvent(self, x, y, buttons):
        pass

    def kbEvent(self, ch):
        pass

    def save(self, f):
        pass

    def load(self, f):
        pass

class widgetScreen(widget):
    def __init__(self, x, y, w, h, fg=7, bg=None, style=None):
        super().__init__(x=x, y=y, w=w, h=h, fg=fg, bg=bg)
        if theme:
            self.box=boxDraw(style=style, bgColor=self.bg, bg0=self.bg0)
        else:
            self.box=None
        self.style=style
        self.resize()
        self.feed=self.stream.feed

    def resize(self):
        super().resize()
        self.minW=5
        self.minH=5
        if self.box:
            self.screen = pyte.Screen(self.w-4, self.h-2)
            self.screen.screen_lines=self.h-2
        else:
            self.screen = pyte.Screen(self.w, self.h)
            self.screen.screen_lines=self.h
        self.screen.mode.add(pyte.modes.LNM)
        self.screen.encoding='utf-8'
        self.stream = pyte.Stream(self.screen)
        self.stream.write=self.stream.feed

    def draw(self):
        self.fg0=7
        self.bg0=0
        if self.parent:
            self.fg0=self.parent.fg
            self.bg0=self.parent.bg
        if self.style in [ 'outside' ]:
            self.bg0=self.bg
        if self.style in [ 'inside' ]:
            self.box.chars=self.box.chars[:4]+' '+self.box.chars[5:]
        buffer=''
        if(self.box):
            self.box.bg0=self.bg0
            buffer+=self.box.draw(self.x, self.y, self.w, self.h)
        self.stream.feed(self.t.ansicolor(self.fg, self.bg))
        self.stream.feed(super().drawChildren())
        self.stream.feed(self.t.gotoxy(1, self.screen.screen_lines))
        if self.box:
            buffer+=self.t.pyte_render(self.x+2, self.y+1, self.screen, fg=self.fg, bg=self.bg)
        else:
            buffer+=self.t.pyte_render(self.x, self.y, self.screen, fg=self.fg, bg=self.bg)
        if self.outstream:
            self.outstream.write(buffer)
        return buffer

    def input(self, str, maxlen=50):
        if maxlen < 1:
            maxlen=1
        if self.box:
            buffer = self.t.gotoxy(self.screen.cursor.x+self.x+2, self.screen.cursor.y+self.y+1)
        else:
            buffer = self.t.gotoxy(self.screen.cursor.x+self.x, self.screen.cursor.y+self.y)
        buffer+=str
        buffer +=self.t.reset()+' '*maxlen+self.t.left(maxlen)
        return input(buffer) #, maxlen=maxlen)

    def onFocus(self):
        pass

    def onDeFocus(self):
        pass

    def mouseEvent(self, x, y, buttons):
        pass

    def kbEvent(self, ch):
        pass

class widgetProgressBar(widget):
    def __init__(self, x, y, w, h, fg=7, bg=0, p0='\u2591', p1='\u2588', note=''):
        super().__init__(x=x, y=y, w=w, h=h, fg=fg, bg=bg)
        self.p0, self.p1=p0,p1
        self.note=note

    def draw(self, progress, total):
        buffer=self.t.gotoxy(self.x, self.y)
        buffer+=self.t.ansicolor(self.fg, self.bg)
        buffer+=self.note
        pct=0
        if total>0:
            pct=progress/total
        w=self.w-len(self.note)
        buffer +=self.p1*int((pct)*w)
        buffer +=self.p0*int(w-((pct)*w))
        buffer +=f'{self.t.gotoxy(self.x+len(self.note)+int(w/2)-5,self.y)}{progress}/{total}'
        return buffer

class widgetSlider(widget):
    def __init__(self, x, y, w, min=0, max=100, bg=233, barColor=238, labelColor=244, labelType="int", sliderColor=27, key=None, action=None):
        super().__init__(x=x, y=y, w=w, h=1, bg=bg, key=key, action=action)
        self.slider='\u2561\u2592\u255e'
        self.bar='\u2560\u2550\u2563'
        self.pos=min
        self.min=min
        self.max=max
        self.barColor=barColor
        self.labelColor=labelColor
        self.labelType=labelType
        self.sliderColor=sliderColor

    def draw(self):
        def hmsf(s):
            s = int(s)
            minutes = s / 60
            seconds = s % 60
            return f"{int(minutes):02d}:{int(seconds):02d}"
        if self.parent:
            self.fg0=self.parent.fg
            self.bg0=self.parent.bg
        LLabel=""
        RLabel=""
        if self.labelType=='int':
            LLabel=f'{self.min}'
            RLabel=f'{self.max}'
        elif self.labelType=='time':
            LLabel=f'{hmsf(self.min)}'
            RLabel=f'{hmsf(self.max)}' 
        else:
            pass
        barw=self.w-len(LLabel)-len(RLabel)-2-len(self.slider)-2
        pos=0
        if (self.max-self.min)>0:
            pos=self.pos/(self.max-self.min)
        spos=int((barw)*pos)
        buffer=self.t.gotoxy(self.x, self.y)
        buffer+=self.t.ansicolor(self.labelColor, self.bg0)
        buffer+=LLabel
        buffer+=self.t.ansicolor(self.barColor)
        buffer+=self.bar[0]
        buffer+=self.bar[1]*(spos)
        buffer+=self.t.ansicolor(self.sliderColor)
        buffer+=self.slider
        buffer+=self.t.ansicolor(self.barColor)
        buffer+=self.bar[1]*((barw-spos))
        buffer+=self.bar[2]
        buffer+=self.t.ansicolor(self.labelColor)
        buffer+=RLabel
        if self.outstream:
            self.outstream.write(buffer)
        return buffer

    def setValue(self, value):
        if value>=self.min and value<=self.max:
            self.pos=value
        if value>self.max:
            self.pos=self.max
        if value<self.min:
            self.pos=self.min

    def setMin(self, value):
        self.min=value
        self.setValue(self.pos)

    def setMax(self, value):
        self.max=value
        self.setValue(self.pos)

class widgetButton(widget):
    def __init__(self, x, y, w, h, fg=7, bg=None, style='curve', caption='Button', key=None, action=None, toggle=None):
        super().__init__(x=x, y=y, w=w, h=h, fg=fg, bg=bg, key=key, action=action)
        self.bg0=0
        self.fg0=7
        self.invert=False
        if theme:
            if style:
                self.box=boxDraw(style=style, bgColor=self.bg, bg0=self.bg0)
        else:
            self.box=None
        self.tint=None
        self.style=style
        self.caption=caption

    def draw(self):
        if self.parent:
            self.fg0=self.parent.fg
            self.bg0=self.parent.bg
        buffer=""
        if self.box:
            self.box.bg0=self.bg0
            self.box.tintFrame(self.tint)
            buffer+=self.box.draw(self.x, self.y, self.w, self.h, invert=self.invert)
        self.invert=False
        buffer+=self.t.gotoxy(self.x+self.w//2-(len(self.caption)//2), self.y+1)
        buffer+=self.t.ansicolor(self.fg, self.bg)
        buffer+=self.caption
        if self.key:
            buffer +=self.t.gotoxy(self.x+self.w//2-((len(self.key)+2)//2), self.y+2)
            buffer+=f'[{self.key}]'
        return buffer

