#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# sid.py - managed native interface to the SIDbox in Python
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

from subprocess import Popen, PIPE
import time

# Voice class -- an instance represents one of the tree voices in a SID chip
class Voice(object):
	def __init__(self, sid, voice):
		self.notifylist = []
		self._voice = voice
		self._sid = sid
		self._waveform = SID.RAMP
		self._attack = 0
		self._decay = 12
		self._sustain = 0
		self._release = 4
		self.update_attack_decay()
		self.update_sustain_release()

	def _notify(self):
		for i in self.notifylist: i()

	def update_attack_decay(self):
		self._notify()
		self.rawrite(self._voice * 7 + 5, ((self._attack & 0x0F) << 4) | (self._decay & 0x0F))

	def update_sustain_release(self):
		self._notify()
		self.rawrite(self._voice * 7 + 6, ((self._sustain & 0x0F) << 4) | (self._release & 0x0F))

	def get_waveform(self):
		return self._waveform
	
	def set_waveform(self, value):
		self._waveform = value
		self._notify()

	def get_attack(self):
		return self._attack

	def get_decay(self):
		return self._decay

	def get_sustain(self):
		return self._sustain

	def get_release(self):
		return self._release

	def set_attack(self, value):
		self._attack = value
		self.update_attack_decay()

	def set_decay(self, value):
		self._decay = value
		self.update_attack_decay()

	def set_sustain(self, value):
		self._sustain = value
		self.update_sustain_release()

	def set_release(self, value):
		self._release = value
		self.update_sustain_release()

	def get_voicenum(self):
		return self._voice

	waveform = property(get_waveform, set_waveform)
	attack = property(get_attack, set_attack)
	decay = property(get_decay, set_decay)
	sustain = property(get_sustain, set_sustain)
	release = property(get_release, set_release)
	voicenum = property(get_voicenum)
	def playfreq(self, freq, delay):
		self.rawrite(self._voice * 7, freq & 0xFF)
		self.rawrite(self._voice * 7 + 1, (freq >> 8) & 0xFF)
		self.rawrite(self._voice * 7 + 4, 0x00)
		self.rawrite(self._voice * 7 + 4, self.waveform | 0x01)
		time.sleep(delay)

	def rawrite(self, addr, data):
		self._sid.rawrite(addr, data)

	# play a note using MIDI values (69 = A4 [440 Hz], +- 1 / half note)
	def playmidinote(self, note, delay):
		self.playfreq(int(round(274 * (1.05946309436 ** (note - 12)))), delay)

# SID class -- an instance represents the whole SID chip
class SID(object):
	NOISE = 0x80
	SQUARE = 0x40
	RAMP = 0x20
	TRIANGLE = 0x10
	def __init__(self, catpath = './cat'):
		self.process = Popen(catpath, stdin = PIPE)
		self.volume = 15
		self.voices = [
			Voice(self, 0),
			Voice(self, 1),
			Voice(self, 2)
		]

	def get_volume(self):
		return _volume

	def set_volume(self, value):
		self._volume = value
		self.update_volume()

	volume = property(get_volume, set_volume)

	def update_volume(self):
		self.rawrite(0x18, self._volume & 0x0F)

	def rawrite(self, addr, data):
		self.process.stdin.write(chr(addr) + chr(data))
