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
      pass

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
              self.code = self.code[::2] #manchester style
              self.code = {'address': int(self.code[0:26], 2),
                           'global' : int(self.code[26:27], 2),
                           'state'  : int(self.code[27:28], 2),
                           'slider' : int(self.code[28:30], 2),
                           'button' : int(self.code[30:32], 2)}
              self.newCode()
              self.code = ''
          oldi = i
        self.pulsecounter = oldi - len(input_items[0])
          
        self.consume(0, len(input_items[0]))
        return 0

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
# mark    short :   146 us = 0
#         long  :   438 us = 1
# space   short :   146 us
#         long  :   438 us
#         xl    :  4000 us = message spacing
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
              if (len(self.code) == 25):
                self.newCode()
              self.code = ''
          else:
            if length < self.sample_rate * 0.0001:
              pass
            elif length < self.sample_rate * 0.0003:
              self.code = self.code + '1'
            else:
              self.code = self.code + '0'
          oldi = i
        self.pulsecounter = oldi - len(input_items[0])
        #check if ongoing space is long enough for closure
        if (self.pulsecounter < self.sample_rate * -0.003) and \
           (self.lastlevel == False):
          if (len(self.code) == 25):
            self.newCode()
          self.code = ''
          
        self.consume(0, len(input_items[0]))
        return 0

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

