# -*- coding: utf-8 -*-
##################################################
# GNU Radio HomeEasy Remote decoder
# Author: Martijn Berntsen
#
##################################################

from gnuradio import gr
import numpy as np
import sys
from string import maketrans
import json
import protocols

class decoder_base(gr.basic_block):
    def __init__(self, name='base decoder', threshold=0.1):  # only default arguments here
        super(decoder_base, self).__init__(
            name=name,
            in_sig=[np.float32],
            out_sig=[]
        )
        self.counts = 0
        self.oldcode = None
        self.pulsecounter = 0
        self.lastlevel = False
        self.code = ''
        self.threshold = threshold

    def stop(self):
        if self.oldcode is not None:
          print ''
        return True

    def set_sample_rate(self, samp_rate):
        self.sample_rate = sample_rate

    def find_edges(self, input_items):
        b = input_items[0] > self.threshold
        c = np.concatenate(([self.lastlevel], b))
        d = np.diff(c)
        indexes = np.arange(len(input_items[0]), dtype=np.int)
        self.lastlevel = b[-1]
        return [(b[i], i) for i in indexes[d]]

    def newCode(self):
        if self.oldcode <> self.code:
          self.counts = 0
          print ''
        self.counts = self.counts + 1
        sys.stdout.write('\r%s : %s x %d' % (len(self.code), self.code, self.counts))
        sys.stdout.flush()
        self.oldcode = self.code

class decoder_base_fsk(gr.basic_block):
    def __init__(self, name='base fsk decoder', threshold=0.1, threshold2=0.1):  # only default arguments here
        super(decoder_base_fsk, self).__init__(
            name=name,
            in_sig=[np.float32, np.float32],
            out_sig=[]
        )
        self.counts = 0
        self.oldcode = None
        self.pulsecounter = 0
        self.lastlevel = False
        self.code = ''
        self.threshold = threshold
        self.threshold2 = threshold2
        self.signalvalid = False

    def stop(self):
        if self.oldcode is not None:
          print ''
        return True

    def set_sample_rate(self, samp_rate):
        self.sample_rate = sample_rate

    def find_edges(self, input_items):
        length = min(len(input_items[0]), len(input_items[1]))
        in1 = input_items[0][:length]
        in2 = input_items[1][:length]
        in1 = in1[in2 > self.threshold2]
        self.signalvalid = len(in1) > 0
        if len(in1) > 0:
          #self.threshold = (np.min(in1) + np.max(in1)) / 2
          b = in1 > self.threshold
          c = np.concatenate(([self.lastlevel], b))
          d = np.diff(c)
          indexes = np.arange(len(in1), dtype=np.int)
          self.lastlevel = b[-1]
          return [(b[i], i) for i in indexes[d]]
        else:
          return []

    def newCode(self):
        if self.oldcode <> self.code:
          self.counts = 0
          print ''
        self.counts = self.counts + 1
        sys.stdout.write('\r%s : %s x %d' % (len(self.code), self.code, self.counts))
        sys.stdout.flush()
        self.oldcode = self.code

class decoder_base_debug(decoder_base):
  def __init__(self, name='base debug decoder', threshold=0.1):
    super(decoder_base_debug, self).__init__(
      name=name,
      threshold = threshold
    )
    self.wh = np.empty((0), np.int)
    self.wl = np.empty((0), np.int)

  def stop(self):
    np.save('workfileh.npy', self.wh)
    np.save('workfilel.npy', self.wl)
    return super(decoder_base_debug, self).stop()

  def find_edges(self, input_items):
    edges = super(decoder_base_debug, self).find_edges(input_items)
    oldi = self.pulsecounter
    for v, i in edges:
      length = i - oldi
      if v == True:
        #space finished
        self.wl = np.append(self.wl, [length])
      else:
        self.wh = np.append(self.wh, [length])
      oldi = i
    return edges

class decoder_base_fsk_debug(decoder_base_fsk):
  def __init__(self, name='base fsk debug decoder', threshold=0.1):
    super(decoder_base_fsk_debug, self).__init__(
      name=name,
      threshold = threshold
    )
    self.wh = np.empty((0), np.int)
    self.wl = np.empty((0), np.int)

  def stop(self):
    np.save('workfileh.npy', self.wh)
    np.save('workfilel.npy', self.wl)
    return super(decoder_base_fsk_debug, self).stop()

  def find_edges(self, input_items):
    edges = super(decoder_base_fsk_debug, self).find_edges(input_items)
    oldi = self.pulsecounter
    for v, i in edges:
      length = i - oldi
      if v == True:
        #space finished
        self.wl = np.append(self.wl, [length])
      else:
        self.wh = np.append(self.wh, [length])
      oldi = i
    return edges

##################################################
# Protocol timing HomeEasy:
# mark    short :   260 us
# space   short :   270 us
#         long  :  1280 us
#         xx    : 10040 us
##################################################
class decoder_homeeasy(decoder_base_debug):
    def __init__(self, sample_rate=32000):  # only default arguments here
        super(decoder_homeeasy, self).__init__(
            name='HomeEasy decoder',
            threshold = 0.1
        )
        self.sample_rate = sample_rate

    def set_sample_rate(self, samp_rate):
        self.sample_rate = sample_rate

    def general_work(self, input_items, output_items):
        oldi = self.pulsecounter
        for v, i in self.find_edges(input_items):
          length = i - oldi
          if v == True:
            #space finished
            if length < self.sample_rate * 0.0002:
              self.code = '' # code will be invalid, implementation could be better?
            if length < self.sample_rate * 0.0005:
              self.code = self.code + '0'
            elif length < self.sample_rate * 0.005:
              self.code = self.code + '1'
            else:
              self.code = ''
            if (len(self.code) == 57):
              self.newCode()
              self.code = ''
          oldi = i
        self.pulsecounter = oldi - len(input_items[0])

        self.consume(0, len(input_items[0]))
        return 0

##################################################
# Protocol timing SelectPlus:
# mark   short :   342 us
#         long  :  1069 us
# space   short :   397 us
#         long  :  1125 us
#         xx    :  7560 us
##################################################
class decoder_selectplus(decoder_base):
    def __init__(self, sample_rate=32000):  # only default arguments here
        super(decoder_selectplus, self).__init__(
            name='SelectPlus decoder',
            threshold = 0.5
        )
        self.sample_rate = sample_rate

    def set_sample_rate(self, samp_rate):
        self.sample_rate = sample_rate

    def general_work(self, input_items, output_items):
        oldi = self.pulsecounter
        for v, i in self.find_edges(input_items):
          length = i - oldi
          if v == True:
            if length > self.sample_rate * 0.0015:
              self.code = ''

          if v == False:
            #space finished
            #print length, self.sample_rate * 0.0007, self.sample_rate * 0.0015, self.code
            if length < self.sample_rate * 0.0007:
              self.code = self.code + '0'
            elif length < self.sample_rate * 0.0015:
              self.code = self.code + '1'
            #else:
            #  self.code = ''
            if (len(self.code) == 18):
              self.newCode()
              self.code = ''
          oldi = i
        self.pulsecounter = oldi - len(input_items[0])

        self.consume(0, len(input_items[0]))
        return 0

class encoder_selectplus(gr.basic_block):
  def __init__(self, sample_rate=32000):  # only default arguments here
    super(encoder_selectplus, self).__init__(
        name='SelectPlus encoder',
        in_sig=[],
        out_sig=[np.float32]
    )
    self.sample_rate = sample_rate
    self.code = '000010100000001111'
    self.samplesleft = 0
    self.state = 0
    self.code_index = 0
    self.oldstate = -1
    self.running = False

  def set_sample_rate(self, samp_rate):
    self.sample_rate = sample_rate

  def start_sending(self):
    self.running = True

  def stop_sending(self):
    self.running = False

  def general_work(self, input_items, output_items):
    out = output_items[0]
    i = 0
    while (i < len(out)):
      r = len(out) - i
      if (self.state == 0):
        if (self.running):
          self.state = 5
        else:
          out[i:] = [0] * r
          i = i + r
      elif (self.state == 5):
        if (self.code_index == len(self.code)):
          # code completed
          self.state = 100
        else:
          self.state = 10
      elif (self.state == 10):
        if (self.code[self.code_index] == '1'):
          self.samplesleft = int(self.sample_rate * 0.000344)
        else:
          self.samplesleft = int(self.sample_rate * 0.001136)
        self.state = 20
      elif (self.state == 20):
        if (r < self.samplesleft):
          # much more work
          out[i:] = [0] * r
          self.samplesleft = self.samplesleft - r
          i = i + r
        else:
          # bit more work
          out[i:i+self.samplesleft] = [0] *  self.samplesleft
          i = i + self.samplesleft
          self.state = 30
      elif (self.state == 30):
        if (self.code[self.code_index] == '1'):
          self.samplesleft = int(self.sample_rate * 0.001136)
        else:
          self.samplesleft = int(self.sample_rate * 0.000344)
        self.state = 40
      elif (self.state == 40):
        if (r < self.samplesleft):
          # much more work
          out[i:] = [1] * r
          self.samplesleft = self.samplesleft - r
          i = i + r
        else:
          # bit more work
          out[i:i+self.samplesleft] = [1] *  self.samplesleft
          i = i + self.samplesleft
          self.code_index = self.code_index + 1
          self.state = 5
      elif (self.state == 100):
        self.samplesleft = int(self.sample_rate * 0.005500)
        self.state = 110
      elif (self.state == 110):
        if (r < self.samplesleft):
          # much more work
          out[i:] = [0] * r
          self.samplesleft = self.samplesleft - r
          i = i + r
        else:
          # bit more work
          out[i:i+self.samplesleft] = [0] *  self.samplesleft
          i = i + self.samplesleft
          self.code_index = 0
          self.state = 0
      #if (self.state <> self.oldstate):
      #  print self.state
      #  self.oldstate = self.state

    return len(out)

##################################################
# Protocol timing Elro ab440r:
# mark   short :   460 us
#         long  :  1113 us
# space   short :   188 us
#         long  :   838 us
#         xx    : 10000 us
##################################################
class decoder_elro_ab440r(decoder_base):
    def __init__(self, sample_rate=32000):  # only default arguments here
        super(decoder_elro_ab440r, self).__init__(
            name='Elro ab440r decoder',
            threshold = 0.1
        )
        self.sample_rate = sample_rate

    def set_sample_rate(self, samp_rate):
        self.sample_rate = sample_rate

    def general_work(self, input_items, output_items):
        oldi = self.pulsecounter
        for v, i in self.find_edges(input_items):
          length = i - oldi
          if v == True:
            #space finished
            if length < self.sample_rate * 0.0007:
              self.code = self.code + '1'
            elif length < self.sample_rate * 0.0015:
              self.code = self.code + '0'
            else:
              if (len(self.code) == 17):
                self.newCode()
              self.code = ''
          oldi = i
        self.pulsecounter = oldi - len(input_items[0])
        #check if ongoing space is long enough for closure
        if (self.pulsecounter < self.sample_rate * -0.0015) and \
           (self.lastlevel == False):
          if (len(self.code) == 17):
            self.newCode()
          self.code = ''

        self.consume(0, len(input_items[0]))
        return 0

        b = np.round(input_items[0] * 10000).astype(np.int)
        self.buffer = np.append(self.buffer, b)

        refvalue = (np.min(b) + np.max(b)) // 2

        indexes = np.arange(len(self.buffer), dtype=np.int)
        # get indexes with low values
        i_l = indexes[self.buffer < refvalue]
        # get holes in low signal (= pulses)
        steps_l = np.diff(i_l)

        min_width_h = self.sample_rate * 0.0002

        indexes = np.arange(len(steps_l))
        i2_l = indexes[steps_l > min_width_h]

        last_sample = None
        if len(i2_l) > 0:
          # get edge starting points
          t_lh = i_l[i2_l]
          # get edge ending points
          t_hl = i_l[i2_l + 1]

          # calculate pulse widths
          width_h = t_hl - t_lh# / (bitrate / 1000)
          width_l = t_lh[1:] - t_hl[0:-1]# / (bitrate / 1000)

          s = ''
          oldi = 0
          last_sample = 0
          for i, ph in enumerate(width_h):
            if i < len(width_l):
              pl = width_l[i]
              if ph < self.sample_rate * 0.0007:
                s = s + '1'
              else:
                s = s + '0'
              if pl > self.sample_rate * 0.005:
                if len(s) == 25:
                  self.newCode(s)
                self.wh = np.append(self.wh, width_h[oldi:i])
                self.wl = np.append(self.wl, width_l[oldi:i])
                oldi = i
                s = ''
                last_sample = t_hl[i]
          if (len(self.buffer) - t_hl[-1]) > self.sample_rate * 0.005:
            ph = width_h[-1]
            if ph < self.sample_rate * 0.0007:
              s = s + '1'
            else:
              s = s + '0'
            if len(s) == 25:
              self.newCode(s)
            self.wh = np.append(self.wh, width_h[oldi:-1])
            self.wl = np.append(self.wl, width_l[oldi:-1])
            last_sample = t_hl[-1]
        i = int(max(last_sample, len(self.buffer) - self.max_buffer_size))
        self.buffer = self.buffer[i:]
        self.consume(0, len(input_items[0]))
        return 0

##################################################
# Protocol timing DIO:
# mark    short :   229 us
# space   short :   306 us = 0
#         long  :  1306 us = 1
#         xl    :  2661 us = start
#         xxl   : 10096 us = message spacing
#
# code seems sort of manchester, every data-bit consists of a set of 2 bits
##################################################
class decoder_dio(decoder_base):
    def __init__(self, sample_rate=32000):  # only default arguments here
        super(decoder_dio, self).__init__(
            name='DIO decoder',
            threshold = 0.1
        )
        self.sample_rate = sample_rate

    def set_sample_rate(self, samp_rate):
        self.sample_rate = sample_rate

    def general_work(self, input_items, output_items):
        oldi = self.pulsecounter
        for v, i in self.find_edges(input_items):
          length = i - oldi
          if v == True:
            #space finished
            if length < self.sample_rate * 0.0005:
              self.code = self.code + '0'
            elif length < self.sample_rate * 0.002:
              self.code = self.code + '1'
            elif length < self.sample_rate * 0.005:
              self.code = ''
            if (len(self.code) == 64):
              #print self.code;
              #self.code = self.code[::2] #manchester style
              #self.code = {'address': int(self.code[0:26], 2),
              #             'global' : int(self.code[26:27], 2),
              #             'state'  : int(self.code[27:28], 2),
              #             'slider' : int(self.code[28:30], 2),
              #             'button' : int(self.code[30:32], 2)}
              self.code = protocols.protocol_dio.fromstring(self.code)
              self.newCode()
              self.code = ''
          oldi = i
        self.pulsecounter = oldi - len(input_items[0])

        self.consume(0, len(input_items[0]))
        return 0

class encoder_dio(gr.basic_block):
  def __init__(self, sample_rate=32000):
    super(encoder_dio, self).__init__(
        name='test',
        in_sig=[],
        out_sig=[np.float32]
    )
    self.sample_rate = sample_rate
    self.code = '0101011010011010010110010110100101101010010101011001011001010101'
    self.samplesleft = 0
    self.state = 0
    self.code_index = 0
    self.oldstate = -1
    self.running = False

  def set_sample_rate(self, samp_rate):
    self.sample_rate = sample_rate

  def start_sending(self):
    self.running = True

  def stop_sending(self):
    self.running = False

  def general_work(self, input_items, output_items):
    out = output_items[0]
    i = 0
    while (i < len(out)):
      r = len(out) - i
      if (self.state == 0):
        if (self.running):
          self.state = 1
        else:
          out[i:] = [0] * r
          i = i + r
      elif (self.state == 1):
        # start first pulse
        self.samplesleft = int(self.sample_rate * 0.000229)
        self.state = 2
      elif (self.state == 2):
        # wait for first pulse to finish
        if (r < self.samplesleft):
          # much more work
          out[i:] = [1] * r
          self.samplesleft = self.samplesleft - r
          i = i + r
        else:
          # bit more work
          out[i:i+self.samplesleft] = [1] * self.samplesleft
          i = i + self.samplesleft
          self.state = 4
      elif (self.state == 4):
        # start begin mark
        self.samplesleft = int(self.sample_rate * 0.002661)
        self.state = 6
      elif (self.state == 6):
        if (r < self.samplesleft):
          # much more work
          out[i:] = [0] * r
          self.samplesleft = self.samplesleft - r
          i = i + r
        else:
          # bit more work
          out[i:i+self.samplesleft] = [0] * self.samplesleft
          i = i + self.samplesleft
          self.state = 8
      if (self.state == 8):
        # start pulse
        self.samplesleft = int(self.sample_rate * 0.000229)
        self.state = 9
      elif (self.state == 9):
        # wait for pulse to finish
        if (r < self.samplesleft):
          # much more work
          out[i:] = [1] * r
          self.samplesleft = self.samplesleft - r
          i = i + r
        else:
          # bit more work
          out[i:i+self.samplesleft] = [1] * self.samplesleft
          i = i + self.samplesleft
          self.state = 10
      elif (self.state == 10):
        if (self.code_index == len(self.code)):
          # code completed
          self.state = 100
        else:
          # code bits remaining
          if (self.code[self.code_index] == '0'):
            self.samplesleft = int(self.sample_rate * 0.000306)
          else:
            self.samplesleft = int(self.sample_rate * 0.001306)
          self.state = 12
      elif (self.state == 12):
        if (r < self.samplesleft):
          # much more work
          out[i:] = [0] * r
          self.samplesleft = self.samplesleft - r
          i = i + r
        else:
          # bit more work
          out[i:i+self.samplesleft] = [0] *  self.samplesleft
          i = i + self.samplesleft
          self.code_index = self.code_index + 1
          self.state = 8
      elif (self.state == 100):
        self.samplesleft = int(self.sample_rate * 0.01)
        self.state = 102
      elif (self.state == 102):
        if (r < self.samplesleft):
          # much more work
          out[i:] = [0] * r
          self.samplesleft = self.samplesleft - r
          i = i + r
        else:
          # bit more work
          out[i:i+self.samplesleft] = [0] *  self.samplesleft
          i = i + self.samplesleft
          self.code_index = 0
          self.state = 0
      #if (self.state <> self.oldstate):
      #  print self.state
      #  self.oldstate = self.state

    #return produced
    return len(out)

##################################################
# Protocol timing Smart key fob:
# mark    short :   250 us = 1
#         long  :   500 us = 11
#         xl    :  2000 us = start
# space   short :   250 us = 0
#         long  :   500 us = 00
#         xl    :  3000 us = message spacing
#         xxl   :  3250 us = (message spacing with additional 0?)
#
# the signal starts with about 325 high/low pulses, but these are removed
# by filtering op the keycode length (104 bytes manchester)
##################################################
class decoder_smart(decoder_base_fsk):
    def __init__(self, sample_rate=32000):  # only default arguments here
        super(decoder_smart, self).__init__(
            name='Smart key fob decoder',
            threshold = 0,
            threshold2 = 0.005
        )
        self.sample_rate = sample_rate
        self.is_decoding = False

    def set_sample_rate(self, samp_rate):
        self.sample_rate = sample_rate

    def general_work(self, input_items, output_items):
        samp_length = min(len(input_items[0]), len(input_items[1]))
        oldi = self.pulsecounter
        if self.signalvalid and not self.is_decoding:
          self.is_decoding = True
          self.code = ''
        for v, i in self.find_edges(input_items):
          length = i - oldi
          if length > 200:
            if (v == True) and self.is_decoding:
              #space finished
              if length < self.sample_rate * 0.000375:
                self.code = self.code + '0'
              elif length < self.sample_rate * 0.001:
                self.code = self.code + '00'
            elif (v == False):
              #mark finished
              if length < self.sample_rate * 0.000375:
                if self.is_decoding:
                  self.code = self.code + '1'
              elif length < self.sample_rate * 0.001:
                if self.is_decoding:
                  self.code = self.code + '11'
              else:
                self.code = ''
          oldi = i
        self.pulsecounter = oldi - len(input_items[0])
        if (not self.signalvalid) and (self.is_decoding):
          self.is_decoding = False
          self.code = self.code[::2]
          if (len(self.code) == 104):
            self.code = {'address': int(self.code[:48], 2),
                         'key'    : int(self.code[48:56], 2),
                         'rolling': int(self.code[56:104], 2)}
            self.newCode()
          self.code = ''

        self.consume(0, samp_length)
        self.consume(1, samp_length)
        return 0

##################################################
# Protocol timing DIO:
# mark    short :   146 us = 1
#         long  :   438 us = 0
# space   short :   146 us
#         long  :   438 us
#         xl    :  4000 us = message spacing
#
# short mark is followed by long space and viceversa (?)
##################################################
class decoder_impuls(decoder_base):
    def __init__(self, sample_rate=32000):  # only default arguments here
        super(decoder_impuls, self).__init__(
            name='DIO decoder',
            threshold = 0.1
        )
        self.sample_rate = sample_rate

    def set_sample_rate(self, samp_rate):
        self.sample_rate = sample_rate

    def general_work(self, input_items, output_items):
        oldi = self.pulsecounter
        for v, i in self.find_edges(input_items):
          length = i - oldi
          if v == True:
            if length > self.sample_rate * 0.003:
              self.code = ''
          else:
            if length < self.sample_rate * 0.0001:
              pass
            elif length < self.sample_rate * 0.0003:
              self.code = self.code + '1'
            else:
              self.code = self.code + '0'
            if (len(self.code) == 25):
              self.code = protocols.protocol_impuls.fromstring(self.code)
              #address = int(self.code[0:10][::2], 2) ^ 0b11111
              #keys = int(self.code[11:21][::2], 2)
              #off = int(self.code[21])
              #on = int(self.code[23])
              #self.code = {'address': address,
              #             'keys'    : keys,
              #             'off'    : off,
              #             'on'  : on}
              self.newCode()
              self.code = ''
          oldi = i
        self.pulsecounter = oldi - len(input_items[0])

        self.consume(0, len(input_items[0]))
        return 0

class encoder_impuls(gr.basic_block):
  def __init__(self, sample_rate=32000):
    super(encoder_impuls, self).__init__(
        name='test',
        in_sig=[],
        out_sig=[np.float32]
    )
    self.sample_rate = sample_rate
    self.code = '1000000010101010101110111'
    self.samplesleft = 0
    self.state = 0
    self.code_index = 0
    self.oldstate = -1
    self.running = False

  def set_sample_rate(self, samp_rate):
    self.sample_rate = sample_rate

  def start_sending(self):
    self.running = True

  def stop_sending(self):
    self.running = False

  def general_work(self, input_items, output_items):
    out = output_items[0]
    i = 0
    while (i < len(out)):
      r = len(out) - i
      if (self.state == 0):
        if (self.running):
          self.state = 1
        else:
          out[i:] = [0] * r
          i = i + r
      elif (self.state == 1):
        if (self.code_index == len(self.code)):
          # code completed
          self.state = 100
        else:
          self.state = 5
      elif (self.state == 5):
        if (self.code[self.code_index] == '1'):
          self.state = 10
        else:
          self.state = 20
      elif (self.state == 10):
        self.samplesleft = int(self.sample_rate * 0.000146)
        self.state = 12
      elif (self.state == 12):
        # wait for mark to finish
        if (r < self.samplesleft):
          # much more work
          out[i:] = [1] * r
          self.samplesleft = self.samplesleft - r
          i = i + r
        else:
          # bit more work
          out[i:i+self.samplesleft] = [1] * self.samplesleft
          i = i + self.samplesleft
          self.state = 14
      elif (self.state == 14):
        self.samplesleft = int(self.sample_rate * 0.000436)
        self.state = 16
      elif (self.state == 16):
        # wait for space to finish
        if (r < self.samplesleft):
          # much more work
          out[i:] = [0] * r
          self.samplesleft = self.samplesleft - r
          i = i + r
        else:
          # bit more work
          out[i:i+self.samplesleft] = [0] * self.samplesleft
          i = i + self.samplesleft
          self.code_index = self.code_index + 1
          self.state = 1
      elif (self.state == 20):
        self.samplesleft = int(self.sample_rate * 0.000436)
        self.state = 22
      elif (self.state == 22):
        # wait for mark to finish
        if (r < self.samplesleft):
          # much more work
          out[i:] = [1] * r
          self.samplesleft = self.samplesleft - r
          i = i + r
        else:
          # bit more work
          out[i:i+self.samplesleft] = [1] * self.samplesleft
          i = i + self.samplesleft
          self.state = 24
      elif (self.state == 24):
        self.samplesleft = int(self.sample_rate * 0.000146)
        self.state = 26
      elif (self.state == 26):
        # wait for space to finish
        if (r < self.samplesleft):
          # much more work
          out[i:] = [0] * r
          self.samplesleft = self.samplesleft - r
          i = i + r
        else:
          # bit more work
          out[i:i+self.samplesleft] = [0] * self.samplesleft
          i = i + self.samplesleft
          self.code_index = self.code_index + 1
          self.state = 1
      elif (self.state == 100):
        self.samplesleft = int(self.sample_rate * 0.004)
        self.state = 102
      elif (self.state == 102):
        if (r < self.samplesleft):
          # much more work
          out[i:] = [0] * r
          self.samplesleft = self.samplesleft - r
          i = i + r
        else:
          # bit more work
          out[i:i+self.samplesleft] = [0] *  self.samplesleft
          i = i + self.samplesleft
          self.code_index = 0
          self.state = 0
      #if (self.state <> self.oldstate):
      #  print self.state
      #  self.oldstate = self.state

    return len(out)

##################################################
# Protocol timing Smart key fob:
# mark    short :    66 us = 1
#         long  :   154 us = 11
# space   short :   106 us = 0
#         long  :   194 us = 00
##################################################
class decoder_volvo(decoder_base_fsk):
    def __init__(self, sample_rate=32000):  # only default arguments here
        super(decoder_volvo, self).__init__(
            name='Volvo key fob decoder',
            threshold = 0,
            threshold2 = 0.1
        )
        self.sample_rate = sample_rate
        self.is_decoding = False

    def set_sample_rate(self, samp_rate):
        self.sample_rate = sample_rate

    def general_work(self, input_items, output_items):
        samp_length = min(len(input_items[0]), len(input_items[1]))
        oldi = self.pulsecounter
        if self.signalvalid and not self.is_decoding:
          self.is_decoding = True
          self.code = ''
        for v, i in self.find_edges(input_items):
          length = i - oldi
          if (v == True):
            #space finished
            if length < self.sample_rate * 0.000050:
              self.code = self.code + '_'
            elif length < self.sample_rate * 0.000110:
              self.code = self.code + '0'
            elif length < self.sample_rate * 0.000250:
              self.code = self.code + '00'
            else:
              print 'X'
          elif (v == False):
            #mark finished
            if length < self.sample_rate * 0.000050:
              self.code = self.code + '_'
            elif length < self.sample_rate * 0.000150:
              self.code = self.code + '1'
            elif length < self.sample_rate * 0.000250:
              self.code = self.code + '11'
            else:
              print 'X'
          oldi = i
        self.pulsecounter = oldi - samp_length
        if (not self.signalvalid) and (self.is_decoding):
          self.is_decoding = False
          self.code = self.code[::2] # because manchester code
          lastbits = self.code[-2:]
          self.code = self.code[:-2] # bullshit part
          #rollingcode = self.code[-80:]
          #eycode = self.code[-112:-80]
          #address = self.code[-152:-112]
          #reverse = lastbits == '11'
          self.code = {'address': self.code[-152:-112],
                       'key'    : self.code[-112:-80],
                       'rolling': self.code[-80:],
                       'inversed': lastbits == '11'}
          self.newCode()
          self.code = ''
          #self.code = self.code[-154:] #start of non 101010101010 part
          #if (self.code[-200] == '1'):
          #  intab = "01"
          #  outtab = "10"
          #  trantab = maketrans(intab, outtab)
          #  self.code = self.code.translate(trantab)
            #print self.code[-82:-2], 'T' # rolling code part
          #else:
            #print self.code[-82:-2] # rolling code part
          #print self.code[-238:]
          #self.newCode()

        self.consume(0, samp_length)
        self.consume(1, samp_length)
        return 0

##################################################
# Protocol timing Conrad BEL8006:
# mark    short :   146 us = 0
#         long  :   438 us = 1
# space   short :   146 us
#         long  :   438 us
#         xl    :  4000 us = message spacing
##################################################
class decoder_bel8006(decoder_base):
    def __init__(self, sample_rate=32000):  # only default arguments here
        super(decoder_bel8006, self).__init__(
            name='bel8006 decoder',
            threshold = 0.1
        )
        self.sample_rate = sample_rate
        self.code = []
        self.code2 = ''

    def set_sample_rate(self, samp_rate):
        self.sample_rate = sample_rate

    def bcd_to_int(self, bcd):
        return (bcd >> 4) * 10 + (bcd & 0x0F)

    def validate_checksum(self):
        c = 0
        for i in self.code[1:-2]:
          c = c ^ i
        return c == self.code[-1]


    def general_work(self, input_items, output_items):
        oldi = self.pulsecounter
        for v, i in self.find_edges(input_items):
          length = i - oldi
          if v == False: # high pulse
            if length < self.sample_rate * 0.0001:
              pass
            elif length < self.sample_rate * 0.0003:
              self.code2 = self.code2 + '0'
            elif length < self.sample_rate * 0.0005:
              self.code2 = self.code2 + '1'
            else:
              self.code2 = ''

            if len(self.code2) == 8:
              self.code.append(int(self.code2[0:8], 2))
              self.code2 = ''
              if self.code[0] == 169:
                if (len(self.code) == 14) and self.validate_checksum():
                  self.code = {
                    'opcode': self.code[0],
                    'seccode': self.bcd_to_int(self.code[1]) * 100 + self.bcd_to_int(self.code[2]),
                    'u1': self.code[3],
                    'u2': self.code[4],
                    'date': {
                      'd': self.bcd_to_int(self.code[5]),
                      'h': self.bcd_to_int(self.code[6]),
                      'm': self.bcd_to_int(self.code[7]),
                      's': self.bcd_to_int(self.code[8])
                    },
                    'cal': {
                      'd': self.bcd_to_int(self.code[9]),
                      'h': self.bcd_to_int(self.code[10]),
                      'm': self.bcd_to_int(self.code[11])
                    },
                    'valve': self.code[12]}
                  self.newCode()
                  self.code = []
              elif self.code[0] == 170:
                if len(self.code) == 20:
                  self.newCode()
                  self.code = []
          oldi = i
        self.pulsecounter = oldi - len(input_items[0])

        self.consume(0, len(input_items[0]))
        return 0

##################################################
# Protocol timing Symbol wireless barcode scanner:
#
# message starts with 010101010101010
##################################################
class decoder_symbol(decoder_base_fsk):
    def __init__(self, sample_rate=32000):  # only default arguments here
        super(decoder_symbol, self).__init__(
            name='symbol barcode scanner decoder',
            threshold = 0,
            threshold2 = 0.2
        )
        self.sample_rate = sample_rate
        self.is_decoding = False

    def set_sample_rate(self, samp_rate):
        self.sample_rate = sample_rate

    def general_work(self, input_items, output_items):
        samp_length = min(len(input_items[0]), len(input_items[1]))
        oldi = self.pulsecounter
        if self.signalvalid and not self.is_decoding:
          self.is_decoding = True
          self.code = ''
        for v, i in self.find_edges(input_items):
          length = i - oldi
          if v == True:
            self.code = self.code + '0' * int(round(length / 96.0))
          else:
            self.code = self.code + '1' * int(round(length / 105.0))
          oldi = i
        self.pulsecounter = oldi - len(input_items[0])
        if (not self.signalvalid) and (self.is_decoding):
          self.is_decoding = False
          print self.code

        self.consume(0, samp_length)
        self.consume(1, samp_length)
        return 0

##################################################
# Protocol timing gate1:
# mark    short :   283 us = 1
#         long  :   566 us = 11
#         xl    :  2344 us
# space   short :   283 us = 0
#         long  :   566 us = 00
#         xl    :  2344 us
#
# message starts with 010101010101010
# then high (xl), low (xl)
##################################################
class decoder_gate1(decoder_base):
    def __init__(self, sample_rate=32000):  # only default arguments here
        super(decoder_gate1, self).__init__(
            name='gate1 decoder',
            threshold = 0.1
        )
        self.sample_rate = sample_rate

    def set_sample_rate(self, samp_rate):
        self.sample_rate = sample_rate

    def general_work(self, input_items, output_items):
        oldi = self.pulsecounter
        for v, i in self.find_edges(input_items):
          length = i - oldi
          if v == True: #end of low pulse
            if length < self.sample_rate * 0.0002:
              pass
            elif length < self.sample_rate * 0.0004:
              self.code = self.code + '0'
            elif length < self.sample_rate * 0.0008:
              self.code = self.code + '00'
            else:
              pass
          else:
            if length < self.sample_rate * 0.0002:
              pass
            elif length < self.sample_rate * 0.0004:
              self.code = self.code + '1'
            elif length < self.sample_rate * 0.0008:
              self.code = self.code + '11'
            else:
              if len(self.code) == 192:
                self.code = self.code[1:]
                self.code = self.code[::3]
                self.code = {
                  'serial': int(self.code[0:32], 2),
                  'rolling': int(self.code[32:64],)}
                self.newCode()
              self.code = ''
          oldi = i
        self.pulsecounter = oldi - len(input_items[0])
        #check if ongoing space is long enough for closure
        if (self.pulsecounter < self.sample_rate * -0.003) and \
           (self.lastlevel == False):
          if len(self.code) == 192:
            self.code = self.code[1:]
            self.code = self.code[::3]
            self.code = {
              'serial': int(self.code[0:32], 2),
              'rolling': int(self.code[32:64])}
            self.newCode()
          self.code = ''

        self.consume(0, len(input_items[0]))
        return 0

##################################################
# Protocol timing Niko Easywave:
# mark    short :   507 us = 1
#         long  :  1114 us = 11
# space   short :   507 us = 0
#         long  :  1114 us = 00
#         xl    :  5070 us = message spacing
##################################################
class decoder_easywave(decoder_base_fsk):
    def __init__(self, sample_rate=32000):  # only default arguments here
        super(decoder_easywave, self).__init__(
            name='Easywave remote decoder',
            threshold = 0,
            threshold2 = 0.1
        )
        self.sample_rate = sample_rate
        self.is_decoding = False

    def set_sample_rate(self, samp_rate):
        self.sample_rate = sample_rate

    def general_work(self, input_items, output_items):
        samp_length = min(len(input_items[0]), len(input_items[1]))
        oldi = self.pulsecounter
        if self.signalvalid and not self.is_decoding:
          self.is_decoding = True
          self.code = ''
        for v, i in self.find_edges(input_items):
          length = i - oldi
          if self.is_decoding:
            if (v == True) and self.is_decoding:
              #space finished
              if length < self.sample_rate * 0.000407:
                pass
              if length < self.sample_rate * 0.000750:
                self.code = self.code + '1'
              elif length < self.sample_rate * 0.001500:
                self.code = self.code + '11'
              else:
                self.code = ''
            elif (v == False):
              #mark finished
              if length < self.sample_rate * 0.000407:
                pass
              if length < self.sample_rate * 0.000750:
                self.code = self.code + '0'
              elif length < self.sample_rate * 0.001500:
                self.code = self.code + '00'
              #else:
              #  self.code = self.code + 'X'
            if len(self.code) == 64:
              self.code = self.code + '1'
            if len(self.code) == 65:
              self.code = self.code[1:]
              self.code = protocols.protocol_easywave.fromstring(self.code)
              self.newCode()
              self.code = ''
          oldi = i
        self.pulsecounter = oldi - len(input_items[0])
        if (not self.signalvalid) and (self.is_decoding):
          self.is_decoding = False

        self.consume(0, samp_length)
        self.consume(1, samp_length)
        return 0
