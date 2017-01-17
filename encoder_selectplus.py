#!/usr/bin/env python2
# -*- coding: utf-8 -*-
##################################################
# GNU Radio Python Flow Graph
# Title: Top Block
# Generated: Fri Dec 23 10:35:25 2016
##################################################

if __name__ == '__main__':
  import ctypes
  import sys
  if sys.platform.startswith('linux'):
    try:
      x11 = ctypes.cdll.LoadLibrary('libX11.so')
      x11.XInitThreads()
    except:
      print "Warning: failed to XInitThreads()"

from gnuradio import analog
from gnuradio import blocks
from gnuradio import eng_notation
from gnuradio import filter
from gnuradio import gr
from gnuradio import qtgui
from gnuradio.eng_option import eng_option
from gnuradio.fft import window
from gnuradio.filter import firdes
from gnuradio.wxgui import fftsink2
from gnuradio.wxgui import scopesink2
from grc_gnuradio import wxgui as grc_wxgui
from grc_gnuradio import blks2 as grc_blks2
from optparse import OptionParser
import osmosdr
import time
from PyQt4 import Qt
import sip
from decoders import encoder_selectplus
from grc_gnuradio import blks2 as grc_blks2
import protocols
from functools import partial

class top_block(gr.top_block, Qt.QWidget):

  def __init__(self, output_filename=None, freq_center=433920000):):
    gr.top_block.__init__(self, "Top Block")
    Qt.QWidget.__init__(self)
    self.setWindowTitle("Top Block")
    try:
      self.setWindowIcon(Qt.QIcon.fromTheme('gnuradio-grc'))
    except:
      pass
    self.top_scroll_layout = Qt.QVBoxLayout()
    self.setLayout(self.top_scroll_layout)
    self.top_scroll = Qt.QScrollArea()
    self.top_scroll.setFrameStyle(Qt.QFrame.NoFrame)
    self.top_scroll_layout.addWidget(self.top_scroll)
    self.top_scroll.setWidgetResizable(True)
    self.top_widget = Qt.QWidget()
    self.top_scroll.setWidget(self.top_widget)
    self.top_layout = Qt.QHBoxLayout(self.top_widget)
    self.top_grid_layout = Qt.QGridLayout()
    self.top_layout.addLayout(self.top_grid_layout)

    self.settings = Qt.QSettings("GNU Radio", "top_block")
    self.restoreGeometry(self.settings.value("geometry").toByteArray())

    ##################################################
    # Variables
    ##################################################
    self.samp_rate = samp_rate = 2000000
    self.freq_transition = freq_transition = 10000
    self.freq_cutoff = freq_cutoff = 50000
    self.freq_center = freq_center

    ##################################################
    # Blocks
    ##################################################
    vbox = Qt.QVBoxLayout()
    hbox1 = Qt.QHBoxLayout()
    _variable_qtgui_push_button_0_push_button = Qt.QPushButton("dingdong")
    _variable_qtgui_push_button_0_push_button.pressed.connect(self.button_pressed)
    _variable_qtgui_push_button_0_push_button.released.connect(self.button_released)
    hbox1.addWidget(_variable_qtgui_push_button_0_push_button)
    vbox.addLayout(hbox1)
    vbox.addStretch(1)
    self.top_layout.addLayout(vbox)
    self.qtgui_time_sink_x_0 = qtgui.time_sink_f(
    	10240, #size
    	samp_rate, #samp_rate
    	"", #name
    	1 #number of inputs
    )
    self.qtgui_time_sink_x_0.set_update_time(0.01)
    self.qtgui_time_sink_x_0.set_y_axis(-0.1, 1.1)

    self.qtgui_time_sink_x_0.set_y_label("Amplitude", "")

    self.qtgui_time_sink_x_0.enable_tags(-1, True)
    self.qtgui_time_sink_x_0.set_trigger_mode(qtgui.TRIG_MODE_FREE, qtgui.TRIG_SLOPE_POS, 0.0, 0, 0, "")
    self.qtgui_time_sink_x_0.enable_autoscale(False)
    self.qtgui_time_sink_x_0.enable_grid(False)
    self.qtgui_time_sink_x_0.enable_control_panel(False)

    if not True:
      self.qtgui_time_sink_x_0.disable_legend()

    labels = ["", "", "", "", "",
              "", "", "", "", ""]
    widths = [1, 1, 1, 1, 1,
              1, 1, 1, 1, 1]
    colors = ["blue", "red", "green", "black", "cyan",
              "magenta", "yellow", "dark red", "dark green", "blue"]
    styles = [1, 1, 1, 1, 1,
              1, 1, 1, 1, 1]
    markers = [-1, -1, -1, -1, -1,
               -1, -1, -1, -1, -1]
    alphas = [1.0, 1.0, 1.0, 1.0, 1.0,
              1.0, 1.0, 1.0, 1.0, 1.0]

    for i in xrange(1):
      if len(labels[i]) == 0:
        self.qtgui_time_sink_x_0.set_line_label(i, "Data {0}".format(i))
      else:
        self.qtgui_time_sink_x_0.set_line_label(i, labels[i])
      self.qtgui_time_sink_x_0.set_line_width(i, widths[i])
      self.qtgui_time_sink_x_0.set_line_color(i, colors[i])
      self.qtgui_time_sink_x_0.set_line_style(i, styles[i])
      self.qtgui_time_sink_x_0.set_line_marker(i, markers[i])
      self.qtgui_time_sink_x_0.set_line_alpha(i, alphas[i])

    self._qtgui_time_sink_x_0_win = sip.wrapinstance(self.qtgui_time_sink_x_0.pyqwidget(), Qt.QWidget)
    self.top_layout.addWidget(self._qtgui_time_sink_x_0_win, 1)

    if output_filename is None:
      self.osmosdr_sink_0 = osmosdr.sink( args="numchan=" + str(1) + " " + "" )
      self.osmosdr_sink_0.set_sample_rate(samp_rate)
      self.osmosdr_sink_0.set_center_freq(freq_center, 0)
      self.osmosdr_sink_0.set_freq_corr(0, 0)
      self.osmosdr_sink_0.set_gain(14, 0)
      self.osmosdr_sink_0.set_if_gain(47, 0)
      self.osmosdr_sink_0.set_bb_gain(0, 0)
      self.osmosdr_sink_0.set_antenna("", 0)
      self.osmosdr_sink_0.set_bandwidth(0, 0)
    else:
      self.file_sink_0 = blocks.file_sink(gr.sizeof_gr_complex*1, "encoder_out", False)

    self.low_pass_filter_0 = filter.fir_filter_ccf(1, firdes.low_pass(1, samp_rate, 15000, 15000, firdes.WIN_BLACKMAN, 6.76))
    self.blocks_float_to_complex_0 = blocks.float_to_complex(1)
    self.analog_const_source_x_0 = analog.sig_source_f(0, analog.GR_CONST_WAVE, 0, 0, 0)
    self.encoder = encoder_selectplus(samp_rate)

    ##################################################
    # Connections
    ##################################################
    self.connect((self.analog_const_source_x_0, 0), (self.blocks_float_to_complex_0, 1))
    self.connect((self.encoder, 0), (self.blocks_float_to_complex_0, 0))
    self.connect((self.blocks_float_to_complex_0, 0), (self.low_pass_filter_0, 0))
    self.connect((self.encoder, 0), (self.qtgui_time_sink_x_0, 0))
    if output_filename is None:
      self.connect((self.low_pass_filter_0, 0), (self.osmosdr_sink_0, 0))
    else:
      self.connect((self.encoder, 0), (self.file_sink_0, 0))

  def closeEvent(self, event):
    self.settings = Qt.QSettings("GNU Radio", "top_block")
    self.settings.setValue("geometry", self.saveGeometry())
    event.accept()

  def set_variable_qtgui_range_0(self, variable_qtgui_range_0):
    self.variable_qtgui_range_0 = variable_qtgui_range_0

  def button_pressed(self):
    #self.encoder.code = str(protocols.protocol_dio(7117250, 0, 1, self.variable_qtgui_range_0, btn))
    self.encoder.start_sending()

  def button_released(self):
    self.encoder.stop_sending()

  def get_samp_rate(self):
    return self.samp_rate

  def set_samp_rate(self, samp_rate):
    self.samp_rate = samp_rate
    self.analog_sig_source_x_0.set_sampling_freq(self.samp_rate)
    self.osmosdr_sink_0.set_sample_rate(self.samp_rate)
    self.low_pass_filter_0.set_taps(firdes.low_pass(1, self.samp_rate, self.freq_cutoff, self.freq_transition, firdes.WIN_HAMMING, 6.76))
    self.encoder.set_sample_rate(self.samp_rate)
    self.wxgui_scopesink2_0.set_sample_rate(self.samp_rate)

  def get_freq_transition(self):
    return self.freq_transition

  def set_freq_transition(self, freq_transition):
    self.freq_transition = freq_transition
    self.low_pass_filter_0.set_taps(firdes.low_pass(1, self.samp_rate, self.freq_cutoff, self.freq_transition, firdes.WIN_HAMMING, 6.76))

  def get_freq_cutoff(self):
    return self.freq_cutoff

  def set_freq_cutoff(self, freq_cutoff):
    self.freq_cutoff = freq_cutoff
    self.low_pass_filter_0.set_taps(firdes.low_pass(1, self.samp_rate, self.freq_cutoff, self.freq_transition, firdes.WIN_HAMMING, 6.76))

  def get_freq_center(self):
    return self.freq_center

  def set_freq_center(self, freq_center):
    self.freq_center = freq_center
    self.osmosdr_sink_0.set_center_freq(self.freq_center, 0)

def main(top_block_cls=top_block, options=None):
  from distutils.version import StrictVersion
  if StrictVersion(Qt.qVersion()) >= StrictVersion("4.5.0"):
      style = gr.prefs().get_string('qtgui', 'style', 'raster')
      Qt.QApplication.setGraphicsSystem(style)
  qapp = Qt.QApplication(sys.argv)

  parser = OptionParser()
  parser.add_option("-o", "--output-filename", type="string", default=None, help="specify output-filename [default=%default]")
  parser.add_option("--freq-center", type="int", default=433920000, help="specify freq-center [default=%default]")
  (options, args) = parser.parse_args()
  tb = top_block_cls(options.output_filename, options.freq_center)
  tb.start()
  tb.show()

  def quitting():
      tb.stop()
      tb.wait()
  qapp.connect(qapp, Qt.SIGNAL("aboutToQuit()"), quitting)
  qapp.exec_()


if __name__ == '__main__':
  main()
