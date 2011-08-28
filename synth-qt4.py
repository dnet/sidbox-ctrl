#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# synth-qt4.py - SIDbox synthesizer written using the QT4 framework
#
# Copyright (c) 2010 András Veres-Szentkirályi
#
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation
# files (the "Software"), to deal in the Software without
# restriction, including without limitation the rights to use,
# copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following
# conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
# OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
# OTHER DEALINGS IN THE SOFTWARE.

from sid import SID
from PyQt4 import QtGui, QtCore
from optparse import OptionParser
from threading import Thread
from ConfigParser import RawConfigParser
from itertools import imap, ifilter
import sys
import time
import uuid

class FourBitSlider(QtGui.QSlider):
	def __init__(self, default, reporter, parent = None):
		QtGui.QSlider.__init__(self, QtCore.Qt.Vertical, parent)
		self.resize(32, 64)
		self.setMinimum(0)
		self.setMaximum(15)
		self.setValue(default)
		self.setTracking(True)
		self.setTickPosition(QtGui.QSlider.TicksRight)
		self.setFocusPolicy(QtCore.Qt.NoFocus)
		self.connect(self, QtCore.SIGNAL('valueChanged(int)'), reporter)

class PwSlider(FourBitSlider):
	def __init__(self, default, reporter, parent = None):
		FourBitSlider.__init__(self, 0, reporter, parent)
		self.setMaximum(4095)
		self.setTickInterval(256)
		self.setValue(default)

attackrates = { # attack rates in msec (decay/release is three times this)
	0: 2,	1: 8,	2: 16,	3: 24,
	4: 38,	5: 56,	6: 68,	7: 80,
	8: 100,	9: 250,	10: 500,	11: 800,
	12: 1000,	13: 3000,	14: 5000,	15: 8000
}

class AdsrWidget(QtGui.QLabel):
	MAX = 31
	def __init__(self, voice, parent = None):
		QtGui.QLabel.__init__(self, parent)
		self.setMinimumSize(64, AdsrWidget.MAX + 1)
		self.voice = voice
		voice.notifylist += [self.repaint]

	def paintEvent(self, event):
		self.data = [self.voice.attack, self.voice.decay, 16, self.voice.release]
		slev = int(round(self.voice.sustain * AdsrWidget.MAX / 16))
		self.levels = [0, AdsrWidget.MAX, slev, slev, 0]
		paint = QtGui.QPainter()
		paint.begin(self)

		paint.setPen(QtGui.QColor(0, 0, 0))
		i = 0
		pos = 0
		for d in self.data:
			paint.drawLine(pos, AdsrWidget.MAX - self.levels[i],
				pos + self.data[i], AdsrWidget.MAX - self.levels[i + 1])
			pos += self.data[i]
			i += 1

		paint.end()

class PianoInput(QtGui.QLineEdit):
	DESC = 'piano input'
	NOTES = ['a', 'w', 's', 'e', 'd', 'f', 't', 'g', 'z', 'h', 'u', 'j', 'k']
	NOTESTART = 60
	def __init__(self, output, parent = None):
		QtGui.QLineEdit.__init__(self, parent)
		self.output = output
		self.resize(25, 25)
		self.config = {}

	def keyReleaseEvent(self, event):
		if not event.isAutoRepeat():
			self.output.ungate()

	def keyPressEvent(self, event):
		if event.isAutoRepeat():
			return
		try:
			keyindex = PianoInput.NOTES.index(chr(event.key()).lower())
		except:
			return
		self.output.gatemidinote(PianoInput.NOTESTART + keyindex)

	def setMenu(self, menu):
		pass

class SequencerInput(QtGui.QLineEdit):
	DESC = 'sequencer input'
	def __init__(self, output, parent = None):
		QtGui.QLineEdit.__init__(self, parent)
		self.output = output
		self.thread = None
		self.record_mode = False
		self.last_note = None
		self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
		self.connect(self,
			QtCore.SIGNAL('customContextMenuRequested(QPoint)'), self.cmr)

	def get_config(self):
		return {'value': self.text()}

	def set_config(self, value):
		self.setText(value['value'])

	config = property(get_config, set_config)

	def cmr(self, point):
		self.menu.exec_(self.mapToGlobal(point))

	def setMenu(self, menu):
		self.menu = menu
		menu.addSeparator()
		a = menu.addAction('Record mode')
		a.setCheckable(True)
		self.connect(a, QtCore.SIGNAL('toggled(bool)'), self._record_toggled)

	def _record_toggled(self, checked):
		self.record_mode = checked
		self.base_note = None
	
	def ungate(self):
		if self.record_mode:
			oldtext = self.text()
			if oldtext != '':
				self.setText(oldtext + str(int((time.time() - self.last_note) * 1000)))
			self.last_note = time.time()
		elif self.thread != None:
			self.thread.stop_at_next = True

	def gatemidinote(self, note):
		if self.record_mode:
			if self.base_note == None:
				self.clear()
				self.base_note = note
			else:
				oldtext = self.text()
				if (oldtext != ''):
					oldtext += ','
				self.setText(oldtext + 'p-%d,%d-' %
					((time.time() - self.last_note) * 1000,
					note - self.base_note))
			self.last_note = time.time()
		else:
			if self.thread != None and self.thread.isAlive():
				self.thread.base = note
				self.thread.stop_at_next = False
			else:
				self.thread = SequencerThread(self, self.output, note)
				self.thread.start()

class SequencerThread(Thread):
	def __init__(self, sequencer, output, base):
		Thread.__init__(self)
		self.output = output
		self.sequencer = sequencer
		self.base = base
		self.stop_at_next = False
	
	def run(self):
		while not self.stop_at_next:
			nbase = self.base
			for seq in self.sequencer.text().split(','):
				data = seq.split('-')
				try:
					delay = float(data[1]) / 1000
					try:
						self.output.gatemidinote(
							nbase + int(data[0]))
					except:
						pass
					time.sleep(delay)
					self.output.ungate()
				except:
					pass

class NoteShifter(QtGui.QSpinBox):
	DESC = 'note shifter'
	def __init__(self, output, parent = None):
		QtGui.QSpinBox.__init__(self, parent)
		self.output = output
		self.setMaximum(100)
		self.setMinimum(-100)
		self.setValue(0)
		self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
		self.connect(self,
			QtCore.SIGNAL('customContextMenuRequested(QPoint)'), self.cmr)

	def get_config(self):
		return {'value': self.value()}

	def set_config(self, value):
		self.setValue(int(value['value']))

	config = property(get_config, set_config)

	def cmr(self, point):
		self.menu.exec_(self.mapToGlobal(point))

	def setMenu(self, menu):
		self.menu = menu

	def ungate(self):
		self.output.ungate()

	def gatemidinote(self, note):
		self.output.gatemidinote(note + self.value())

class VoiceWidget(QtGui.QWidget):
	WAVEFORMS = {
		'Triangle': SID.TRIANGLE,
		'Ramp': SID.RAMP,
		'Square': SID.SQUARE,
		'Noise': SID.NOISE
	}
	def __init__(self, voice, parent = None):
		QtGui.QWidget.__init__(self, parent)
		
		self.voice = voice
		self.sliders = {
			'W': { 'rep': self.setW, 'txt': 'Pulse width', 'class': PwSlider,
				'val': int(self.voice.pulse_width * 4095) },
			'A': { 'rep': self.setA, 'txt': 'Attack rate', 'class': FourBitSlider,
				'val': self.voice.attack },
			'D': { 'rep': self.setD, 'txt': 'Decay rate', 'class': FourBitSlider,
				'val': self.voice.decay },
			'S': { 'rep': self.setS, 'txt': 'Sustain level', 'class': FourBitSlider,
				'val': self.voice.sustain },
			'R': { 'rep': self.setR, 'txt': 'Release rate', 'class': FourBitSlider,
				'val': self.voice.release }
		}
		
		waveforms = QtGui.QComboBox(self)
		waveforms.addItems(VoiceWidget.WAVEFORMS.keys())
		waveforms.setCurrentIndex(VoiceWidget.WAVEFORMS.values().index(self.voice.waveform))
		self.connect(waveforms, QtCore.SIGNAL('activated(int)'), self.set_waveform)

		hbox = QtGui.QHBoxLayout()
		hbox.addWidget(QtGui.QLabel('<div align="center"><b>%d</b></div>' % self.voice.voicenum, self))

		wfbox = QtGui.QVBoxLayout()
		wfbox.addStretch(1)
		wfbox.addWidget(QtGui.QLabel('<div align="center">Waveform:</div>'))
		wfbox.addWidget(waveforms)
		hbox.addLayout(wfbox)

		for text in ['W', 'A', 'D', 'S', 'R']:
			data = self.sliders[text]
			data['label'] = QtGui.QLabel(self)
			labAbox = QtGui.QVBoxLayout()
			labAbox.addStretch(1)
			labAbox.addWidget(QtGui.QLabel(data['txt'], self))
			labAbox.addWidget(data['label'])
			hbox.addWidget(data['class'](data['val'], data['rep'], self))
			hbox.addLayout(labAbox)
		
		self.voice.notifylist += [self.updateLabels]
		self.updateLabels()

		hbox.addWidget(AdsrWidget(self.voice, self))

		self.setLayout(hbox)

	def set_waveform(self, value):
		self.voice.waveform = VoiceWidget.WAVEFORMS.values()[value]

	def updateLabels(self):
		self.updateLabel('W', str(self.voice.pulse_width * 4095) + "/4k\n"
			+ str(round(self.voice.pulse_width * 100)) + '%')
		self.updateLabel('A', str(self.voice.attack) + "/15\n"
			+ str(attackrates[self.voice.attack]) + ' ms')
		self.updateLabel('D', str(self.voice.decay) + "/15\n"
			+ str(attackrates[self.voice.decay] * 3) + ' ms')
		self.updateLabel('S', str(self.voice.sustain) + "/15\n"
			+ str(100 * self.voice.sustain / 15) + '%')
		self.updateLabel('R', str(self.voice.release) + "/15\n"
			+ str(attackrates[self.voice.release] * 3) + ' ms')

	def updateLabel(self, addr, value):
		self.sliders[addr]['label'].setText(value)

	def setW(self, value):
		self.voice.pulse_width = float(value) / 4095

	def setA(self, value):
		self.voice.attack = value

	def setD(self, value):
		self.voice.decay = value

	def setS(self, value):
		self.voice.sustain = value

	def setR(self, value):
		self.voice.release = value

class AddAction(QtGui.QAction):
	def __init__(self, aclass, router, sink, parent):
		QtGui.QAction.__init__(self, 'Add %s' % aclass.DESC, parent)
		self.aclass = aclass
		self.router = router
		self.sink = sink
		self.connect(self, QtCore.SIGNAL('triggered(bool)'), self.adder)
	
	def adder(self, b):
		self.router.comp_callback(self.aclass, self.sink)

class LooperEffect(QtGui.QPushButton):
	DESC = 'looper effect'
	def __init__(self, output, parent = None):
		QtGui.QPushButton.__init__(self, 'Looper', parent)
		self.resize(100, 25)
		self.output = output
		self._running = False
		self.config = {}
		self.connect(self, QtCore.SIGNAL('clicked()'), self.clickd)
	
	def clickd(self):
		self._running = False
		self.output.ungate()
		self.setMenu(self._tmpmenu)
		self.setText('Looper')

	def ungate(self):
		pass

	def gatemidinote(self, note):
		if self._running:
			self.output.ungate()
		else:
			self._tmpmenu = self.menu()
			self.setText('Stop')
			self.setMenu(None)
			self._running = True
		self.output.gatemidinote(note)

class VoiceSink(QtGui.QPushButton):
	POOL = {}
	def __init__(self, voice, parent = None):
		QtGui.QPushButton.__init__(self, 'Voice %d' % voice.voicenum, parent)
		self.resize(100, 25)
		self.output = None
		self.voice = voice
		self.config = {}
		VoiceSink.POOL[voice] = self
	
	def gatemidinote(self, note):
		self.voice.gatemidinote(note)

	def ungate(self):
		self.voice.ungate()

class RouterWidget(QtGui.QLabel):
	PADDING = 8
	SINGLETON = None
	COMPONENTS = [PianoInput, NoteShifter, SequencerInput, LooperEffect]
	def __init__(self, voices, parent = None):
		QtGui.QLabel.__init__(self, parent)
		RouterWidget.SINGLETON = self
		self.components = []
		for v in sid.voices:
			self.init_widget(VoiceSink(v, self))
		self.arrange()

	def init_widget(self, widget):
		menu = QtGui.QMenu(self)
		for a in RouterWidget.COMPONENTS:
			menu.addAction(AddAction(a, self, widget, menu))
		widget.setMenu(menu)
		self.components.append(widget)

	def comp_callback(self, aclass, sink):
		c = aclass(sink, self)
		c.setVisible(True)
		self.init_widget(c)
		self.arrange()
		self.repaint()
		return c

	def arrange(self, cpos = 0, right = 0, scomp = None):
		for c in ifilter(lambda x: x.output == scomp, self.components):
			c.move(self.width() - right - c.width(), cpos)
			cpos = max(cpos + c.height(),
				self.arrange(cpos, right + c.width() + RouterWidget.PADDING, c))
		if (scomp == None):
			leftmost = min(imap(lambda x: x.geometry().left(), self.components))
			self.setMinimumSize(self.width() - leftmost, cpos)
			for c in self.components:
				c.move(c.geometry().left() - leftmost, c.geometry().top())
		return cpos

	def paintEvent(self, event):
		paint = QtGui.QPainter()
		paint.begin(self)

		paint.setPen(QtGui.QPen(QtGui.QBrush(QtGui.QColor(0, 0, 0)), 3))
		
		for c in self.components:
			if c.output == None:
				continue
			p1 = c.geometry().center()
			p2 = c.output.geometry().center()
			paint.drawLine(p1, p2)

		paint.end()

class SidStatusBox(QtGui.QGroupBox):
	def __init__(self, sid, parent = None):
		QtGui.QGroupBox.__init__(self, 'Status', parent)
		self.sid = sid
		self.statlab = QtGui.QLabel(self)
		hbox = QtGui.QHBoxLayout()
		hbox.addWidget(FourBitSlider(sid.volume, self.setV, self))
		hbox.addWidget(self.statlab)
		self.sid.notifylist += [self.update_label]
		self.sid.track_bw = True
		self.update_label()
		self.setLayout(hbox)

	def setV(self, value):
		self.sid.volume = value

	def update_label(self):
		vol = self.sid.volume
		self.statlab.setText('Volume\n%d%%\n%d/15\n\nThroughput\n%d Bps' %
			(100 * vol / 15, vol, self.sid.used_bw))

class MainWindow(QtGui.QMainWindow):
	def __init__(self, parent = None):
		QtGui.QWidget.__init__(self, parent)
		self.setWindowTitle('SIDbox synthesizer')
		self.setWindowIcon(QtGui.QIcon('sidbox.png'))
		self.build_menu()

		effects = QtGui.QGroupBox('Sources', self)
		eff_hbox = QtGui.QHBoxLayout()
		eff_hbox.addStretch(1)
		eff_hbox.addWidget(RouterWidget(sid.voices, effects))
		effects.setLayout(eff_hbox)

		voices = QtGui.QGroupBox('Voices', self)
		voicebox = QtGui.QVBoxLayout()
		for v in sid.voices:
			voicebox.addWidget(VoiceWidget(v, voices))
		voices.setLayout(voicebox)

		stat_eff_hbox = QtGui.QHBoxLayout()
		stat_eff_hbox.addWidget(SidStatusBox(sid, self))
		stat_eff_hbox.addWidget(effects)

		vbox = QtGui.QVBoxLayout()
		vbox.addLayout(stat_eff_hbox)
		vbox.addWidget(voices)

		w = QtGui.QWidget(self)
		w.setLayout(vbox)
		self.setCentralWidget(w)
		self.resize(640, 600)
		self.center()

	def build_menu(self):
		menubar = self.menuBar()
		m_file = menubar.addMenu('&File')
		load = QtGui.QAction('&Load state...', self)
		load.setShortcut('Ctrl+L')
		self.connect(load, QtCore.SIGNAL('triggered()'), self.load_state)
		m_file.addAction(load)
		save = QtGui.QAction('&Save state...', self)
		save.setShortcut('Ctrl+S')
		self.connect(save, QtCore.SIGNAL('triggered()'), self.save_state)
		m_file.addAction(save)

	def save_state(self):
		fn = QtGui.QFileDialog.getSaveFileName(self, 'Save state')
		if fn == '':
			return
		f = open(fn, 'w+')
		cp = RawConfigParser()
		sn = 'main'
		cp.add_section(sn)
		cp.set(sn, 'volume', sid.volume)
		for v in sid.voices:
			sn = 'voice%d' % v.voicenum
			cp.add_section(sn)
			cp.set(sn, 'waveform', v.waveform)
			cp.set(sn, 'pulse_width', v.pulse_width)
			cp.set(sn, 'attack', v.attack)
			cp.set(sn, 'decay', v.decay)
			cp.set(sn, 'sustain', v.sustain)
			cp.set(sn, 'release', v.release)
			self.save_sink_state(VoiceSink.POOL[v], cp, sn)
		cp.write(f)
		f.close()

	def save_sink_state(self, sink, cp, sn):
		oid = str(uuid.uuid4())
		if cp.has_option(sn, 'sources'):
			src = '%s,%s' % (cp.get(sn, 'sources'), oid)
		else:
			src = oid
		cp.set(sn, 'sources', src)
		cp.add_section(oid)
		cp.set(oid, 'class', sink.__class__.__name__)
		for k, v in sink.config.iteritems():
			cp.set(oid, k, v)
		for i in RouterWidget.SINGLETON.components:
			if i.output == sink:
				self.save_sink_state(i, cp, oid)

	def load_state(self):
		fn = QtGui.QFileDialog.getOpenFileName(self, 'Load state')
		if fn == '':
			return
		cp = RawConfigParser()
		cp.read([fn])
		sid.volume = cp.getint('main', 'volume')
		for v in sid.voices:
			sn = 'voice%d' % v.voicenum
			v.waveform = cp.getint(sn, 'waveform')
			v.pulse_width = cp.getfloat(sn, 'pulse_width')
			v.attack = cp.getint(sn, 'attack')
			v.decay = cp.getint(sn, 'decay')
			v.sustain = cp.getint(sn, 'sustain')
			v.release = cp.getint(sn, 'release')
			try:
				sn = cp.get(cp.get(sn, 'sources'), 'sources')
				self.load_sink_state(VoiceSink.POOL[v], cp, sn)
			except:
				pass

	def load_sink_state(self, sink, cp, sns):
		for sn in sns.split(','):
			cn = cp.get(sn, 'class')
			c = ifilter(lambda x: x.__name__ == cn, RouterWidget.COMPONENTS)
			comp = RouterWidget.SINGLETON.comp_callback(next(c), sink)
			config = {}
			for i in ifilter(lambda x: x not in ('class', 'sources'),
				cp.options(sn)): config[i] = cp.get(sn, i)
			comp.config = config
			try:
				self.load_sink_state(comp, cp, cp.get(sn, 'sources'))
			except:
				pass

	def center(self):
		screen = QtGui.QDesktopWidget().screenGeometry()
		size = self.geometry()
		self.move((screen.width() - size.width()) / 2, (screen.height() - size.height()) / 2)

parser = OptionParser()
parser.add_option('-c', '--catpath', dest='catpath', help='set \'cat\' path')
(options, args) = parser.parse_args()

try:
	sid = SID(options.catpath)
except:
	sid = SID()

app = QtGui.QApplication(sys.argv)

w = MainWindow()
w.show()

sys.exit(app.exec_())
