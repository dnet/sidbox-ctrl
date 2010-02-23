#!/usr/bin/env python
# -*- coding: utf-8 -*-

from subprocess import Popen, PIPE
import time

class SID(object):
	NOISE = 0x80
	SQUARE = 0x40
	RAMP = 0x20
	TRIANGLE = 0x10
	def __init__(self):
		self.process = Popen(['./cat'], stdin=PIPE)
		self.voice = 0
		self.waveform = SID.RAMP
		self._attack = 0
		self._decay = 12
		self._sustain = 0
		self._release = 4
		self.first_play = True

	def update_attack_decay(self):
		self.rawrite(self.voice * 7 + 5, ((self._attack & 0x0F) << 4) | (self._decay & 0x0F))

	def update_sustain_release(self):
		self.rawrite(self.voice * 7 + 6, ((self._sustain & 0x0F) << 4) | (self._release & 0x0F))

	@property
	def attack(self):
		return self._attack

	@property
	def decay(self):
		return self._decay

	@property
	def sustain(self):
		return self._sustain

	@property
	def release(self):
		return self._release

	@attack.setter
	def attack(self, value):
		self._attack = value
		self.update_attack_decay()

	@decay.setter
	def decay(self, value):
		self._decay = value
		self.update_attack_decay()

	@sustain.setter
	def sustain(self, value):
		self._sustain = value
		self.update_sustain_release()

	@release.setter
	def release(self, value):
		self._release = value
		self.update_sustain_release()

	def rawrite(self, addr, data):
		self.process.stdin.write(chr(addr) + chr(data))

	def playfreq(self, freq, delay):
		if self.first_play:
			self.first_play = False
			self.update_attack_decay()
			self.update_sustain_release()
		self.rawrite(self.voice * 7, freq & 0xFF)
		self.rawrite(self.voice * 7 + 1, (freq >> 8) & 0xFF)
		self.rawrite(self.voice * 7 + 4, 0x00)
		self.rawrite(self.voice * 7 + 4, self.waveform | 0x01)
		time.sleep(delay)

	def playmidinote(self, note, delay):
		self.playfreq(int(round(274 * (1.05946309436 ** (note - 12)))), delay)
