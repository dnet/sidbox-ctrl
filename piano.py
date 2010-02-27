#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# piano.py - simple piano application using the SID object
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
import sys
import termios, fcntl, os
from optparse import OptionParser

notes = ['a', 'w', 's', 'e', 'd', 'f', 't', 'g', 'z', 'h', 'u', 'j', 'k']
notestart = 60

parser = OptionParser()
parser.add_option('-v', '--voice', dest='voice', help='select SID voice (0-2)')
parser.add_option('-w', '--waveform', dest='waveform', help='select SID waveform (noise, square, ramp, triangle)')
parser.add_option('-s', '--sustain', dest='sustain', help='set sustain value (0-15)')
parser.add_option('-d', '--decay', dest='decay', help='set decay value (0-15)')
parser.add_option('-r', '--release', dest='release', help='set release value (0-15)')
parser.add_option('-a', '--attack', dest='attack', help='set attack value (0-15)')
parser.add_option('-c', '--catpath', dest='catpath', help='set \'cat\' path')
(options, args) = parser.parse_args()

try:
	voice = int(options.voice)
except:
	voice = 0

try:
	sidobj = SID(options.catpath)
except:
	sidobj = SID()

sid = sidobj.voices[voice]

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

# thx to http://pyfaq.infogami.com/how-do-i-get-a-single-keypress-at-a-time
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
