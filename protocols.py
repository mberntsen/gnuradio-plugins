# -*- coding: utf-8 -*-
##################################################
# GNU Radio HomeEasy Remote decoder
# Author: Martijn Berntsen
#
##################################################
class protocol_dio():
  def __init__(self, address=0, glob=0, state=0, slider=0, button=0):
    self.address = address
    self.glob = glob
    self.state = state
    self.slider = slider
    self.button = button

  def __str__(self):
    a = "{0:026b}{1:01b}{2:01b}{3:02b}{4:02b}".format( \
      self.address,
      self.glob,
      self.state,
      self.slider,
      self.button)
    b = ''
    for c in a:
      if (c == '1'):
        b = b + '10'
      else:
        b = b + '01'

    return b

  def fromstring(self, string):
    string = string[::2] #manchester style
    self.addres = int(string[0:26], 2)
    self.glob   = int(string[26:27], 2)
    self.state  = int(string[27:28], 2)
    self.slider = int(string[28:30], 2)
    self.button = int(string[30:32], 2)


class protocol_impuls():
  def __init__(self, address=0, button=0, off=0, on=0):
    self.address = address
    self.button = button
    self.off = off
    self.on = on

  def __str__(self):
    a = "{0:05b}".format( \
      self.address ^ 0b11111)
    b = "{0:05b}{1:01b}{2:01b}".format( \
      self.button,
      self.off,
      self.on)
    out = ''
    for c in a:
      out = out + c + '0'
    out = out + '1'
    for c in b:
      out = out + c + '1'
    return out

  def __len__(self):
    return 25

  def __eq__(self, other):
    if isinstance(other, self.__class__):
      return (self.address == other.address) and (self.button == other.button) and (self.on == other.on) and (self.off == other.off)
    else:
      return False

  def __ne__(self, other):
    return not self.__eq__(other)

  @classmethod
  def fromstring(cls, string):
    address = int(string[0:10][::2], 2) ^ 0b11111
    button = int(string[11:21][::2], 2)
    off = int(string[21])
    on = int(string[23])
    return cls(address, button, off, on)

class protocol_easywave():
  def __init__(self, address=0, switch=0, button=0):
    self.address = address
    self.switch = switch
    self.button = button

  def __str__(self):
    #{'a': 23, 'b': 24}
    a = "{0:20b}{1:02b}{2:010b}".format( \
      self.address,
      self.switch,
      self.button)
    return a
#    for c in a:
#      out = out + c + '0'
#    out = out + '1'
#    for c in b:
#      out = out + c + '1'
#    return out

  def __len__(self):
    return len(str(self))

  def tostring(self):
    a = "{{'address': {0:d}, 'switch': {1:d}, 'button': {2:d}}}".format( \
      self.address,
      self.switch,
      self.button)
    out = '11111111110'
    for c in a:
      if (c == '1'):
        out = out + '10'
      else:
        out = out + '01'
    return out


  def __eq__(self, other):
    if isinstance(other, self.__class__):
      return (self.address == other.address) and (self.button == other.button) and (self.switch == other.switch)
    else:
      return False

  def __ne__(self, other):
    return not self.__eq__(other)

  @classmethod
  def fromstring(cls, string):
    string = string[::2]
    address = int(string[:20], 2)
    switch = int(string[20:22], 2)
    button = int(string[22:32], 2)
    return cls(address, switch, button)
