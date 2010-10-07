#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
from datetime import datetime
import re
import time as time_module
try:
    import curses
except ImportError:
    curses = None
try:
    import termcolor
    colored_orig = termcolor.colored
    _normal_esc_seq = colored_orig('>', 'grey').split('>')[1]
    def colored(color, typ):
        if color == 'black':
            color = 'grey'
        if typ == 'bg':
            fg_color = None
            bg_color = 'on_' + color
        elif typ == 'fg':
            fg_color = color
            bg_color = None
        return colored_orig('>', fg_color, bg_color).split('>')[0]

    def formatted(typ):
        try:
            return colored_orig('>', attrs=[typ]).split('>')[0]
        except KeyError:
            if typ == 'normal':
                return _normal_esc_seq
            else:
                return ''
except ImportError:
    termcolor = None
    colored = lambda color, typ: ''
    formatted = lambda typ: ''

######################################################################

# Basic constants
_epoch = datetime(2009, 10, 8, 13, 1, 34)
_one_alp = 2 ** 18
_hexalp_divide = 2 ** 14
_qvalp_divide = 2 ** 12
_salp_divide = 2 ** 8
_talp_divide = 2 ** 4

# Date formats
## one '*' in the end prepends a zero if length of str(number) is < 2
## one '#' in the end returns the number in hex
## Available "units":
### seconds, seconds_since_epoch, alp, hexalp, qvalp, salp, talp, second

_default_hex_date_format = '\
%(bold)#(cyan)$(yellow)&(alp)\
#(blue)$(white)/\
#(black)$(red)&(hexalp#)\
$(yellow)&(qvalp)\
$(green)&(salp#)\
$(blue)&(talp#)\
$(magenta)&(second#)'
         # e.g. 2403/93EC2

_default_dec_date_format = '\
%(bold)#(cyan)$(yellow)&(alp)\
#(blue)$(white)/\
#(black)$(red)&(hexalp*)\
$(yellow)&(qvalp)\
$(green)&(salp*)\
$(blue)&(talp*)\
$(magenta)&(second*)'
         # e.g. 2403/093141202

_date_format_unit_regex = re.compile(r'&\((.+?)\)')

######################################################################

class _AlpTime(object):
    """The Alp time object"""

    def __init__(self):
        self.update()

    def get_seconds_since_epoch(self, date=None):
        if date is None:
            date = datetime.now()
        diff = (date - _epoch)
        return diff.days * 86400 + diff.seconds

    def update(self, date=None):
        passed = self.get_seconds_since_epoch(date)
        seconds_total = passed % _one_alp
        alp = passed / _one_alp
        seconds_left = seconds_total
        hexalp = seconds_left / _hexalp_divide
        seconds_left -= hexalp * _hexalp_divide
        qvalp = seconds_left / _qvalp_divide
        seconds_left -= qvalp * _qvalp_divide
        salp = seconds_left / _salp_divide
        seconds_left -= salp * _salp_divide
        talp = seconds_left / _talp_divide
        seconds_left -= talp * _talp_divide
        second = seconds_left

        self.seconds_since_epoch = passed
        self.alp = alp
        self.seconds = seconds_total
        self.hexalp = hexalp
        self.qvalp = qvalp
        self.salp = salp
        self.talp = talp
        self.second = second

    def _format_replace(self, obj):
        unit = obj.groups(1)[0]
        zero_prepend = unit.endswith('*')
        as_hex = unit.endswith('#')
        if zero_prepend or as_hex:
            unit = unit[:-1]
        value = self.__dict__[unit]
        if zero_prepend:
            return '%02d' % value
        elif as_hex:
            return hex(value)[2:].upper()
        else:
            return str(value)

    def format(self, date_format=None):
        if date_format is None:
            date_format=_default_hex_date_format
        return _date_format_unit_regex.sub(self._format_replace, date_format)

    def __str__(self):
        return 'AlpTime{alp: %d, hexalp: %d, qvalp: %d, \
salp: %d, talp: %d, second: %d}' % (self.alp, self.hexalp, self.qvalp,
                                 self.salp, self.talp, self.second)

time = _AlpTime()
update = time.update
format = time.format

######################################################################

# Using curses without initscr
_curses_colors = ('BLUE', 'GREEN', 'CYAN', 'RED', 'MAGENTA', 'YELLOW',
                  'WHITE', 'BLACK')

_curses_controls = {
    'bol': 'cr', 'up': 'cuu1', 'down': 'cud1', 'left': 'cub1',
    'right': 'cuf1', 'clear_screen': 'clear', 'clear_eol': 'el',
    'clear_bol': 'el1', 'clear_eos': 'ed', 'bold': 'bold', 'blink':
    'blink', 'dim': 'dim', 'reverse': 'rev', 'underline': 'smul',
    'normal': 'sgr0', 'hide_cursor': 'civis', 'show_cursor': 'cnorm'
}

_curses_control_regex = re.compile(r'%\((.+?)\)')
_curses_bg_color_regex = re.compile(r'#\((.+?)\)')
_curses_fg_color_regex = re.compile(r'\$\((.+?)\)')

class _BaseControls(object):
    """A generic text formatting generator"""

    def _generate_part(self, attr, obj):
        return ''

    def generate(self, text, put=False):
        text = _curses_control_regex.sub(
            lambda obj: self._generate_part('controls', obj), text)
        text = _curses_bg_color_regex.sub(
            lambda obj: self._generate_part('bg_colors', obj), text)
        text = _curses_fg_color_regex.sub(
            lambda obj: self._generate_part('fg_colors', obj), text)
        if put:
            sys.stdout.write(text)
        return text

    def clear(self):
        self.generate('%(clear_eol)', True)

    def end(self):
        pass

class _CursesControls(_BaseControls):
    """
    A text formatting generator and a container of curses escape
    sequences
    """

    def __init__(self):
        if not sys.stdout.isatty():
            return
        try:
            curses.setupterm()
        except Exception, e:
            print e
        bg_seq = curses.tigetstr('setab') or curses.tigetstr('setb') or ''
        fg_seq = curses.tigetstr('setaf') or curses.tigetstr('setf') or ''

        self.bg_colors = {}
        self.fg_colors = {}
        self.controls = {}

        # Get escape sequences
        for color in _curses_colors:
            index = getattr(curses, 'COLOR_%s' % color)
            color = color.lower()
            self.bg_colors[color] = curses.tparm(bg_seq, index)
            self.fg_colors[color] = curses.tparm(fg_seq, index)
        for control in _curses_controls:
            self.controls[control] = curses.tigetstr(_curses_controls[control]) or ''

        self.cols = curses.tigetnum('cols')
        self.lines = curses.tigetnum('lines')

    def _generate_part(self, attr, obj):
        return self.__getattribute__(attr)[obj.groups(1)[0]]

    def end(self):
        print formatter.generate('%(normal)%(show_cursor)\n%(up)%(clear_eol)%(up)')

class _FakeCursesControls(_BaseControls):
    """A text formatting generator without curses"""

    def _generate_part(self, attr, obj):
        obj = obj.groups(1)[0]
        if attr == 'bg_colors':
            return colored(obj, 'bg')
        elif attr == 'fg_colors':
            return colored(obj, 'fg')
        elif attr == 'controls':
            return formatted(obj)
        # Else
        return ''

    def end(self):
        print formatter.generate('%(normal)')

formatter = None
def start_formatter(use_curses=True):
    global formatter, start_formatter
    if curses is None or not use_curses:
        formatter = _FakeCursesControls()
    else:
        formatter = _CursesControls()
    start_formatter = lambda *arg: True
    return formatter

######################################################################

# Virtual LEDs
_led_letters = 'abcdefghijklmnopqrs'

_default_led_layout = '''\
   a  b  c  d
e  g  h  i  j
f  k  l  m  n
o  p  q  r  s\
'''

class _Container(object):
    pass

class _Led(object):
    """A simulation of a LED lamp"""
    def __init__(self, **kwds):
        start_formatter()

        self.items = {
            True: _Container(), False: _Container()}
        for key, val in kwds.iteritems():
            if key[-1] in ('0', '1'):
                key_vals = bool(int(key[-1])),
                key = key[:-1]
            else:
                key_vals = True, False

            for x in key_vals:
                self.items[x].__setattr__(key, val)
        for x in self.items.values():
            d = x.__dict__
            if not 'letter' in d:
                x.letter = 'o'
            if not 'fg' in d:
                x.fg = None
            if not 'bg' in d:
                x.bg = None
            if not 'controls' in d:
                x.controls = None

    def generate(self, state):
        info = self.items[state]
        text = info.letter
        pre_esc = ''
        if info.bg:
            pre_esc += formatter.generate('#(%s)' % info.bg)
        if info.fg:
            pre_esc += formatter.generate('$(%s)' % info.fg)
        if info.controls:
            for x in info.controls:
                pre_esc += formatter.generate('%(' + x + ')')
        text = pre_esc + text
        if pre_esc:
            text += formatter.generate('%(normal)')
        return text

_led_formatting = {
    'a': _Led(bg='red', letter='O'),
    'b': _Led(fg='green', controls=['bold'], bg='red', letter0='·', letter1='O'),
    '*': _Led(letter0='.', letter1='o') # For eventual non-defined letters
}

def _get_led_formatting(obj):
    try:
        return _led_formatting[obj.groups(1)[0]].generate(True)
    except KeyError:
        return _led_formatting['*'].generate(True)

def get_led_text(led_layout=None):
    if led_layout is None:
        led_layout = _default_led_layout

    led_layout = re.sub(r'([' + _led_letters + '])',
                        _get_led_formatting, led_layout)

    return led_layout
    


######################################################################

# Convenience functions

def print_time_continously(date_format=None):
    start_formatter(False)
    formatter.generate('%(hide_cursor)', True)
    update()
    prev = time.seconds_since_epoch
    print get_led_text()

    while 1:
        update()
        now = time.seconds_since_epoch
        if now > prev:
            formatter.clear()
            print formatter.generate(format(date_format) + '%(up)%(normal)')
            prev = now
        time_module.sleep(0.1)

######################################################################

if __name__ == '__main__':
    start_formatter()
    try:
        print_time_continously()
    except (KeyboardInterrupt, EOFError):
        formatter.end()

