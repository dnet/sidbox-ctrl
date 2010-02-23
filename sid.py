#!/usr/bin/env python
# -*- coding: utf-8 -*-

from subprocess import Popen, PIPE
import time

class SID:
	def __init__(self):
		self.process = Popen(['./cat'], stdin=PIPE)

	def rawrite(self, addr, data):
		self.process.stdin.write(chr(addr) + chr(data))

	def playfreq(self, freq, delay):
		self.rawrite(0x00, freq & 0xFF)
		self.rawrite(0x01, (freq >> 8) & 0xFF)
		self.rawrite(0x04, 0x00)
		self.rawrite(0x04, 0x21)
		time.sleep(delay)

	def playmidinote(self, note, delay):
		self.playfreq(int(round(274 * (1.05946309436 ** (note - 12)))), delay)
