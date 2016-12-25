# -*- coding: utf-8 -*-
##################################################
# GNU Radio HomeEasy Remote decoder 
# Author: Martijn Berntsen
# 
##################################################

from gnuradio import gr
import numpy as np
import sys
import matplotlib.pyplot as plt

class decoder_base(gr.basic_block):
    def __init__(self, name='base decoder'):  # only default arguments here
        gr.basic_block.__init__(
            self,
            name=name,
            in_sig=[np.float32],
            out_sig=[]
        )
        self.counts = 0
        self.oldcode = None
        self.pulsecounter = 0
        self.lastlevel = False
        self.code = ''

    def stop(self):
        if self.oldcode is not None:
          print ''
        return True

    def set_sample_rate(self, samp_rate):
        self.sample_rate = sample_rate

    def find_edges(self, input_items):
        refvalue = 0.1        
        b = input_items[0] > refvalue
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
        sys.stdout.write('\r%s x %d' % (self.code, self.counts))
        sys.stdout.flush()
        self.oldcode = self.code

##################################################
# Protocol timing HomeEasy:
# pulse   short :   250 us
# space   short :   285 us
#         long  :  1293 us
#         xx    : 10164 us
##################################################
class decoder_homeeasy(decoder_base):
    def __init__(self, sample_rate=32000):  # only default arguments here
        decoder_base.__init__(
            self,
            name='HomeEasy decoder'
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
            elif length < self.sample_rate * 0.005:
              self.code = self.code + '1'
            else:
              if (len(self.code) == 57):
                self.newCode()
              self.code = ''
          oldi = i
        self.pulsecounter = oldi - len(input_items[0])
        #check if ongoing space is long enough for closure
        if (self.pulsecounter < self.sample_rate * -0.005) and \
           (self.lastlevel == False):
          if (len(self.code) == 57):
            self.newCode()
          self.code = ''
          
        self.consume(0, len(input_items[0]))
        return 0

class decoder_manchester(gr.basic_block):
    def __init__(self, sample_rate=32000, max_buffer_length=0.1, t_short=0.0004, t_long=0.0011, t_finish=0.0075, symbolcount=26):  # only default arguments here
        gr.basic_block.__init__(
            self,
            name='Manchester decoder',
            in_sig=[np.float32],
            out_sig=[]
        )
        self.sample_rate = sample_rate
        self.buffer = np.empty((0), dtype=np.int)
        self.counts = 0
        self.olds = None
        self.t_short = t_short
        self.t_long = t_long
        self.t_finish = t_finish
        self.s_shortlong = sample_rate * (t_short + t_long) * 0.5
        self.s_longfinish = sample_rate * (t_long + t_finish) * 0.5
        self.symbolcount = symbolcount
        self.bitcount = symbolcount * 2
        self.max_buffer_length = max_buffer_length
        self.max_buffer_size = sample_rate * max_buffer_length

    def stop(self):
        if self.olds is not None:
          print ''
        return True

    def set_sample_rate(self, samp_rate):
        self.sample_rate = sample_rate

    def general_work(self, input_items, output_items):
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
          last_sample = 0
          for i, ph in enumerate(width_h):
            if i < len(width_l):
              pl = width_l[i]
            
              if ph < self.s_shortlong:
                s = s + '0'
              else:
                s = s + '00'
              
              if pl < self.s_shortlong:
                s = s + '1'
              elif pl < self.s_longfinish:
                s = s + '11'
              else:
                if len(s) == self.bitcount:
                  self.newCode(s)
                s = ''
                last_sample = t_hl[i]
          if (len(self.buffer) - t_hl[-1]) > self.s_longfinish:
            ph = width_h[-1]
            if ph < self.s_shortlong:
              s = s + '0'
            else:
              s = s + '00'
            if len(s) == self.bitcount:
              self.newCode(s)
            last_sample = t_hl[-1]
        i = int(max(last_sample, len(self.buffer) - self.max_buffer_size))
        self.buffer = self.buffer[i:]
        self.consume(0, len(input_items[0]))
        return 0

    def newCode(self, s):
        self.counts = self.counts + 1
        if self.olds == s:
          sys.stdout.write('\r%s x %d' % (self.olds, self.counts))
          sys.stdout.flush()
        else:
          self.counts = 1                  
          self.olds = s
          sys.stdout.write('\n%s x %d' % (self.olds, self.counts))
          sys.stdout.flush()


##################################################
# Protocol timing SelectPlus:
# pulse   short :   342 us
#         long  :  1069 us
# space   short :   397 us
#         long  :  1125 us
#         xx    :  7560 us
##################################################
class decoder_selectplus(decoder_base):
    def __init__(self, sample_rate=32000):  # only default arguments here
        decoder_base.__init__(
            self,
            name='SelectPlus decoder'
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
# pulse   short :   460 us
#         long  :  1113 us
# space   short :   188 us
#         long  :   838 us
#         xx    : 10000 us
##################################################
class decoder_elro_ab440r(gr.basic_block):
    def __init__(self, sample_rate=32000, max_buffer_length=0.1):  # only default arguments here
        gr.basic_block.__init__(
            self,
            name='Elro ab440r decoder',
            in_sig=[np.float32],
            out_sig=[]
        )
        self.sample_rate = sample_rate
        self.buffer = np.empty((0), dtype=np.int)
        self.counts = 0
        self.olds = None
        self.max_buffer_length = max_buffer_length
        self.max_buffer_size = sample_rate * max_buffer_length
        self.wh = np.empty((0), dtype=np.int)
        self.wl = np.empty((0), dtype=np.int)

    def stop(self):
        if self.olds is not None:
          print ''
        np.save('workfileh.npy', self.wh)
        np.save('workfilel.npy', self.wl)
        return True

    def set_sample_rate(self, samp_rate):
        self.sample_rate = sample_rate

    def general_work(self, input_items, output_items):
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

    def newCode(self, s):
        s = s[1::2]
        self.counts = self.counts + 1
        if self.olds == s:
          sys.stdout.write('\r%s x %d' % (self.olds, self.counts))
          sys.stdout.flush()
        else:
          self.counts = 1                  
          self.olds = s
          sys.stdout.write('\n%s x %d' % (self.olds, self.counts))
          sys.stdout.flush()

