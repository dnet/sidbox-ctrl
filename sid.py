#!/usr/bin/env python
# -*- coding: utf-8 -*-

from subprocess import Popen, PIPE
import time

class SID:
	NOISE = 0x80
	SQUARE = 0x40
	RAMP = 0x20
	TRIANGLE = 0x10
	def __init__(self):
		self.process = Popen(['./cat'], stdin=PIPE)
		self.voice = 0
		self.waveform = SID.RAMP

	def rawrite(self, addr, data):
		self.process.stdin.write(chr(addr) + chr(data))

	def playfreq(self, freq, delay):
		self.rawrite(self.voice * 7, freq & 0xFF)
		self.rawrite(self.voice * 7 + 1, (freq >> 8) & 0xFF)
		self.rawrite(self.voice * 7 + 4, 0x00)
		self.rawrite(self.voice * 7 + 4, self.waveform | 0x01)
		time.sleep(delay)

	def playmidinote(self, note, delay):
		self.playfreq(int(round(274 * (1.05946309436 ** (note - 12)))), delay)
