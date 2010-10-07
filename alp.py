#!/usr/bin/env python

from datetime import datetime
import re
from termcolor import colored

_epoch = datetime(2009, 10, 8, 13, 1, 34)
_one_alp = 2 ** 18

# Date formats
 # a '*' in the end prepends a zero if length of str(number) is < 2
 # a '#' in the end returns the number in hex
_default_dec_date_format = '{alp}/{hexalp*}{qvalp}{salp*}{talp*}{second*}'
         # e.g. 2403/093141202
_default_hex_date_format = '{alp}/{hexalp#}{qvalp}{salp#}{talp#}{second#}'
         # e.g. 2403/93ec2

_unit_regex = re.compile(r'\{(.+?)\}')

# Virtual LEDs
_led_letters = 'abcdefghijklmnopqrs'

_led_layout = '''\
   a  b  c  d
e  g  h  i  j
f  k  l  m  n
o  p  q  r  s\
'''

_led_formatting = {
    'a': {'color': 'green'},
    'b': {'color': 'green'},
    'c': {'color': 'green'},
    'd': {'color': 'green'},
    'e': {'color': 'green'},
    'f': {'color': 'green'},
    'g': {'color': 'red'},
    'h': {'color': 'red'},
    'i': {'color': 'red'},
    'j': {'color': 'red'},
    'k': {'color': 'red'},
    'l': {'color': 'red'},
    'm': {'color': 'red'},
    'n': {'color': 'red'},
    'o': {'color': 'yellow'},
    'p': {'color': 'yellow'},
    'q': {'color': 'yellow'},
    'r': {'color': 'yellow'},
    's': {'color': 'yellow'}
}

######################################################################

class _AlpTime(object):
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
        hexalp = seconds_left / 2 ** 14
        seconds_left -= hexalp * 2 ** 14
        qvalp = seconds_left / 2 ** 12
        seconds_left -= qvalp * 2 ** 12
        salp = seconds_left / 2 ** 8
        seconds_left -= salp * 2 ** 8
        talp = seconds_left / 2 ** 4
        seconds_left -= talp * 2 ** 4
        second = seconds_left

        self.seconds_since_epoch = passed
        self.alp = alp
        self.seconds = seconds_total
        self.hexalp = hexalp
        self.qvalp = qvalp
        self.salp = salp
        self.talp = talp
        self.second = second

    def _format_replace(self, *o):
        unit = o[0].groups(1)[0]
        zero_prepend = unit.endswith('*')
        as_hex = unit.endswith('#')
        if zero_prepend or as_hex:
            unit = unit[:-1]
        value = self.__dict__[unit]
        if zero_prepend:
            return '%02d' % value
        elif as_hex:
            return hex(value)[2:]
        else:
            return str(value)

    def format(self, format=None):
        if format is None:
            format=_default_dec_date_format
        self.update()
        print _unit_regex.sub(self._format_replace, format)

    def __str__(self):
        return 'AlpTime{%d alp,%d hexalp, %d qvalp, \
%d salp, %d talp, %d second}' % (self.alp, self.hexalp, self.qvalp,
                                 self.salp, self.talp, self.second)

time = _AlpTime()
get_seconds_since_epoch = time.get_seconds_since_epoch
update = time.update
format = time.format

######################################################################

format()
