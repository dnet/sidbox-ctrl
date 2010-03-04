/*
 * cat-arduino.pde - cat-like LPT-USB interface for Arduino
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
 * Electrical connections
 * ======================
 *
 * SIDbox:  GND SID_CS LATCH D0 D1 D2 D3    D4 D5 D6 D7     R/W  RESET
 *              ______   __                                     ______
 * LPT:     GND STROBE   LF  D0 D1 D2 D3    D4 D5 D6 D7    INIT SELECT
 *           21    1     14   2  3  4  5     6  7  8  9     16    17
 *
 * Arduino: GND   13     12  11 10  9  8  |  7  6  5  4  |  GND   5V
 *
 */

#define SIDCS 13
#define LATCH 12

#define CSON LOW
#define CSOFF HIGH

#define LATCHON HIGH
#define LATCHOFF LOW

void setup() {
	for (char i = 4; i <= 13; i++) {
		pinMode(i, OUTPUT);
	}
	digitalWrite(SIDCS, CSOFF);
	digitalWrite(LATCH, LATCHOFF);
	Serial.begin(115200);
}

void loop() {
	while (!Serial.available());
	char addr = Serial.read();
	while (!Serial.available());
	char data = Serial.read();
	sid_write(addr, data);
}

void sid_datawrite(char data) {
	for (char i = 0; i <= 7; i++) {
		char wbit = (data & (1 << i)) == (1 << i) ? HIGH : LOW;
		digitalWrite(11 - i, wbit);
	}
}

void sid_write(char addr, char data) {
	sid_datawrite(addr);
	digitalWrite(LATCH, LATCHON);
	digitalWrite(LATCH, LATCHOFF);
	sid_datawrite(data);
	digitalWrite(SIDCS, CSON);
	delayMicroseconds(1);
	digitalWrite(SIDCS, CSOFF);
}

