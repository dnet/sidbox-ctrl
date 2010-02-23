#!/usr/bin/env python
# -*- coding: utf-8 -*-

from sid import SID
import sys
import csv
import termios, fcntl, os

sid = SID()
sid.rawrite(0x18, 0x04)

fd = sys.stdin.fileno()

oldterm = termios.tcgetattr(fd)
newattr = termios.tcgetattr(fd)
newattr[3] = newattr[3] & ~termios.ICANON & ~termios.ECHO
termios.tcsetattr(fd, termios.TCSANOW, newattr)

oldflags = fcntl.fcntl(fd, fcntl.F_GETFL)
fcntl.fcntl(fd, fcntl.F_SETFL, oldflags | os.O_NONBLOCK)

notes = ['a', 'w', 's', 'e', 'd', 'f', 't', 'g', 'z', 'h', 'u', 'j', 'k']
notestart = 60

if len(sys.argv) > 1:
	try:
		sid.voice = int(sys.argv)
	except: pass

sid.rawrite(sid.voice * 7 + 5, 0x0C)
sid.rawrite(sid.voice * 7 + 6, 0x04)

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
