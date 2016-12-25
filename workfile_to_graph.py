#!/usr/bin/python

import struct
import numpy as np
import operator
import time
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec

wh = np.round(np.load('workfileh.npy') / 2)
wl = np.round(np.load('workfilel.npy') / 2)

a = [2500]
b = [100000]

#plt.xkcd(randomness=2)

fig = plt.figure(1, facecolor='white')
gs = gridspec.GridSpec(2, max(len(a), len(b)))

tplt = fig.add_subplot(gs[0, :])
bc = np.bincount(wh[wh < a[0]])
nz = np.nonzero(bc)[0]
start = nz[0]
y = np.trim_zeros(bc)
x = range(start, start + len(y))
tplt.plot(x, y)
tplt.set_ylabel('frequency high')
tplt.set_yscale('log')

oldi = 0
bc = np.bincount(wl[wl > 100])
nz = np.nonzero(bc)[0]
bplt = []
for c, i in enumerate(b):
  start = nz[0]
  y = np.trim_zeros(bc[oldi:i])
  x = range(start, start + len(y))
  nz = nz[nz > i]
  oldi = i
  
  bplt.append(fig.add_subplot(gs[1, c]))
  bplt[c].plot(x, y)
  if c == 0:
    bplt[c].set_ylabel('frequency low')
  bplt[c].set_yscale('log')

plt.savefig('workfiles.png')
  
plt.show()

