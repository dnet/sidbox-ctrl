#!/usr/bin/env python
# -*- coding: utf-8 -*-

from sid import SID
import sys
import csv
import termios, fcntl, os
from optparse import OptionParser

sid = SID()

notes = ['a', 'w', 's', 'e', 'd', 'f', 't', 'g', 'z', 'h', 'u', 'j', 'k']
notestart = 60

parser = OptionParser()
parser.add_option('-v', '--voice', dest='voice', help='select SID voice (0-2)')
parser.add_option('-w', '--waveform', dest='waveform', help='select SID waveform (noise, square, ramp, triangle)')
parser.add_option('-s', '--sustain', dest='sustain', help='set sustain value (0-15)')
parser.add_option('-d', '--decay', dest='decay', help='set decay value (0-15)')
parser.add_option('-r', '--release', dest='release', help='set release value (0-15)')
parser.add_option('-a', '--attack', dest='attack', help='set attack value (0-15)')
(options, args) = parser.parse_args()

try:
	sid.voice = int(options.voice)
except: pass

wfs = {
	'noise': SID.NOISE,
	'square': SID.SQUARE,
	'ramp': SID.RAMP,
	'triangle': SID.TRIANGLE
}

try:
	sid.waveform = wfs[options.waveform]
except: pass

try:
	sid.sustain = int(options.sustain)
except: pass

try:
	sid.decay = int(options.decay)
except: pass

try:
	sid.release = int(options.release)
except: pass

try:
	sid.attack = int(options.attack)
except: pass

fd = sys.stdin.fileno()

oldterm = termios.tcgetattr(fd)
newattr = termios.tcgetattr(fd)
newattr[3] = newattr[3] & ~termios.ICANON & ~termios.ECHO
termios.tcsetattr(fd, termios.TCSANOW, newattr)

oldflags = fcntl.fcntl(fd, fcntl.F_GETFL)
fcntl.fcntl(fd, fcntl.F_SETFL, oldflags | os.O_NONBLOCK)

try:
	while 1:
		try:
			c = sys.stdin.read(1)
			try:
				sid.playmidinote(notestart + notes.index(c), 0)
			except ValueError: pass
		except IOError: pass
finally:
	termios.tcsetattr(fd, termios.TCSAFLUSH, oldterm)
	fcntl.fcntl(fd, fcntl.F_SETFL, oldflags)
