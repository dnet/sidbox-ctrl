/*
 * sid.c - low-level SIDbox control primitives
 *
 * Copyright (c) 2010 András Veres-Szentkirályi
 *
 * Permission is hereby granted, free of charge, to any person
 * obtaining a copy of this software and associated documentation
 * files (the "Software"), to deal in the Software without
 * restriction, including without limitation the rights to use,
 * copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the
 * Software is furnished to do so, subject to the following
 * conditions:
 *
 * The above copyright notice and this permission notice shall be
 * included in all copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
 * EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
 * OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
 * NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
 * HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
 * WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
 * FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
 * OTHER DEALINGS IN THE SOFTWARE.
 *
 */

#include <stdio.h>
#include <unistd.h>
#include <sys/io.h>
#include "sid.h"

#define LATCH 0x00
#define SIDCS 0x01
#define PEACE 0x02
#define RESET 0x08

#define PDATA 0x0378
#define PSTAT 0x037A

void sid_write(char addr, char data) {
	outb(PEACE, PSTAT);
	outb(addr, PDATA);
	outb(LATCH, PSTAT);
	outb(PEACE, PSTAT);
	outb(data, PDATA);
	outb(PEACE | SIDCS, PSTAT);
	usleep(1);
	outb(PEACE, PSTAT);
}

int sid_init() {
	if (ioperm(PSTAT, 1, 1) || ioperm(PDATA, 1, 1)) {
		perror("Could not get permissions to LPT1");
		return 1;
	}
	return 0;
}

void sid_reset() {
	outb(RESET, PSTAT);
	usleep(10);
	outb(PEACE, PSTAT);
}
