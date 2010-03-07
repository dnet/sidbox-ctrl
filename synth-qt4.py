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
import sys
import time

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
		self.connect(self, QtCore.SIGNAL('textEdited(QString)'), self.playnote)

	def playnote(self, text):
		self.clear()
		self.output.playmidinote(
			PianoInput.NOTESTART + PianoInput.NOTES.index(text[0]), 0.1)
	
	def setMenu(self, menu):
		pass

class SequencerInput(QtGui.QLineEdit):
	DESC = 'sequencer input'
	def __init__(self, output, parent = None):
		QtGui.QLineEdit.__init__(self, parent)
		self.output = output
		self.thread = None
		self.setContextMenuPolicy(3) # Qt::CustomContextMenu
		self.connect(self,
			QtCore.SIGNAL('customContextMenuRequested(QPoint)'), self.cmr)

	def cmr(self, point):
		self.menu.exec_(self.mapToGlobal(point))

	def setMenu(self, menu):
		self.menu = menu
	
	def playmidinote(self, note, delay):
		if self.thread != None:
			self.thread.join()
		self.thread = SequencerThread(self.text(), self.output, note)
		self.thread.start()

class SequencerThread(Thread):
	def __init__(self, sequence, output, base):
		Thread.__init__(self)
		self.output = output
		self.sequence = sequence
		self.base = base
	
	def run(self):
		for seq in self.sequence.split(','):
			data = seq.split('-')
			try:
				delay = float(data[1]) / 1000
				try:
					self.output.playmidinote(
						self.base + int(data[0]), delay)
				except:
					time.sleep(delay)
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
		self.setContextMenuPolicy(3) # Qt::CustomContextMenu
		self.connect(self,
			QtCore.SIGNAL('customContextMenuRequested(QPoint)'), self.cmr)

	def cmr(self, point):
		self.menu.exec_(self.mapToGlobal(point))

	def setMenu(self, menu):
		self.menu = menu
	
	def playmidinote(self, note, delay):
		self.output.playmidinote(note + self.value(), delay)

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
			'W': { 'rep': self.setW, 'txt': 'Pulse width',
				'val': int(self.voice.pulse_width * 4095) },
			'A': { 'rep': self.setA, 'txt': 'Attack rate',
				'val': self.voice.attack },
			'D': { 'rep': self.setD, 'txt': 'Decay rate',
				'val': self.voice.decay },
			'S': { 'rep': self.setS, 'txt': 'Sustain level',
				'val': self.voice.sustain },
			'R': { 'rep': self.setR, 'txt': 'Release rate',
				'val': self.voice.release }
		}
		
		waveforms = QtGui.QComboBox(self)
		waveforms.addItems(VoiceWidget.WAVEFORMS.keys())
		waveforms.setCurrentIndex(VoiceWidget.WAVEFORMS.values().index(self.voice.waveform))
		self.connect(waveforms, QtCore.SIGNAL('activated(int)'), self.set_waveform)

		hbox = QtGui.QHBoxLayout()
		hbox.addWidget(QtGui.QLabel('<b>%d</b>' % self.voice.voicenum, self))

		wfbox = QtGui.QVBoxLayout()
		wfbox.addStretch(1)
		wfbox.addWidget(QtGui.QLabel('<div align="center">Waveform:</div>'))
		wfbox.addWidget(waveforms)
		hbox.addLayout(wfbox)

		for text in ['W', 'A', 'D', 'S', 'R']:
			data = self.sliders[text]
			label = QtGui.QLabel(self)
			labAbox = QtGui.QVBoxLayout()
			labAbox.addStretch(1)
			labAbox.addWidget(QtGui.QLabel(data['txt'], self))
			labAbox.addWidget(label)
			if text != 'W':
				s = FourBitSlider(data['val'], data['rep'], self)
			else:
				s = PwSlider(data['val'], data['rep'], self)
			hbox.addWidget(s)
			hbox.addLayout(labAbox)
			data['label'] = label
		
		self.voice.notifylist += [self.updateLabels]
		self.updateLabels()

		hbox.addWidget(AdsrWidget(self.voice, self))
		hbox.addStretch(1)

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
		self.lthread = None
		self.connect(self, QtCore.SIGNAL('clicked()'), self.clickd)
	
	def clickd(self):
		self.lthread.stop_at_next()
		self.lthread = None
		self.setMenu(self._tmpmenu)
		self.setText('Looper')
	
	def playmidinote(self, note, delay):
		if self.lthread != None:
			self.lthread.stop_at_next()
			self.lthread.join()
		else:
			self._tmpmenu = self.menu()
			self.setMenu(None)
			self.setText('Stop')
		self.lthread = LooperThread(self.output, note, delay)
		self.lthread.start()

class LooperThread(Thread):
	def __init__(self, output, note, delay):
		Thread.__init__(self)
		self.output = output
		self.note = note
		self.delay = delay
		self._san = False

	def stop_at_next(self):
		self._san = True

	def run(self):
		while not self._san:
			self.output.playmidinote(self.note, self.delay)

class VoiceSink(QtGui.QPushButton):
	def __init__(self, voice, parent = None):
		QtGui.QPushButton.__init__(self, 'Voice %d' % voice.voicenum, parent)
		self.resize(100, 25)
		self.output = None
		self.voice = voice
	
	def playmidinote(self, note, delay):
		self.voice.playmidinote(note, delay)

class RouterWidget(QtGui.QLabel):
	PADDING = 8
	def __init__(self, voices, parent = None):
		QtGui.QLabel.__init__(self, parent)
		self.components = []
		for v in sid.voices:
			self.init_widget(VoiceSink(v, self))
		self.arrange()

	def init_widget(self, widget):
		actions = [PianoInput, NoteShifter, SequencerInput, LooperEffect]
		menu = QtGui.QMenu(self)
		for a in actions:
			menu.addAction(AddAction(a, self, widget, menu))
		widget.setMenu(menu)
		self.components.append(widget)

	def comp_callback(self, aclass, sink):
		c = aclass(sink, self)
		c.setVisible(True)
		self.init_widget(c)
		self.arrange()
		self.repaint()

	def arrange(self, cpos = 0, right = 0, scomp = None):
		for c in self.components:
			if c.output == scomp:
				c.move(self.width() - right - c.width(), cpos)
				cpos = max(cpos + c.height(),
					self.arrange(cpos, right + c.width() + RouterWidget.PADDING, c))
		if (scomp == None):
			leftmost = min(map(lambda x: x.geometry().left(), self.components))
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

class MainWindow(QtGui.QWidget):
	def __init__(self, parent = None):
		QtGui.QWidget.__init__(self, parent)
		self.setWindowTitle('SIDbox synthesizer')
		self.setWindowIcon(QtGui.QIcon('sidbox.png'))
		
		effects = QtGui.QGroupBox('Sources', self)
		eff_hbox = QtGui.QHBoxLayout()
		eff_hbox.addStretch(1)
		eff_hbox.addWidget(RouterWidget(sid.voices, effects))
		effects.setLayout(eff_hbox)

		voices = QtGui.QGroupBox('Voices', self)
		voicebox = QtGui.QVBoxLayout()
		for v in sid.voices:
			voicebox.addWidget(VoiceWidget(v, voices))
		voicebox.addStretch(1)
		voices.setLayout(voicebox)

		vbox = QtGui.QVBoxLayout()
		vbox.addStretch(1)
		vbox.addWidget(effects)
		vbox.addWidget(voices)

		self.setLayout(vbox)
		self.resize(640, 600)
		self.center()

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
