#!/usr/bin/env python
# -*- coding: utf-8 -*-

from subprocess import Popen, PIPE
import time

class Voice(object):
	def __init__(self, sid, voice):
		self._voice = voice
		self._sid = sid
		self.waveform = SID.RAMP
		self._attack = 0
		self._decay = 12
		self._sustain = 0
		self._release = 4
		self.update_attack_decay()
		self.update_sustain_release()

	def update_attack_decay(self):
		self.rawrite(self._voice * 7 + 5, ((self._attack & 0x0F) << 4) | (self._decay & 0x0F))

	def update_sustain_release(self):
		self.rawrite(self._voice * 7 + 6, ((self._sustain & 0x0F) << 4) | (self._release & 0x0F))

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

	def playfreq(self, freq, delay):
		self.rawrite(self._voice * 7, freq & 0xFF)
		self.rawrite(self._voice * 7 + 1, (freq >> 8) & 0xFF)
		self.rawrite(self._voice * 7 + 4, 0x00)
		self.rawrite(self._voice * 7 + 4, self.waveform | 0x01)
		time.sleep(delay)

	def rawrite(self, addr, data):
		self._sid.rawrite(addr, data)

	def playmidinote(self, note, delay):
		self.playfreq(int(round(274 * (1.05946309436 ** (note - 12)))), delay)

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

	@property
	def volume(self):
		return _volume

	@volume.setter
	def volume(self, value):
		self._volume = value
		self.update_volume()

	def update_volume(self):
		self.rawrite(0x18, self._volume & 0x0F)

	def rawrite(self, addr, data):
		self.process.stdin.write(chr(addr) + chr(data))
