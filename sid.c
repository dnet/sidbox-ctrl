#include <stdio.h>
#include <unistd.h>
#include <sys/io.h>

#define LATCH 0x00
#define SIDCS 0x01
#define PEACE 0x02

#define PDATA 0x0378
#define PSTAT 0x037A

int pwrite(char addr, char data) {
	outb(PEACE, PSTAT);
	outb(addr, PDATA);
	outb(LATCH, PSTAT);
	outb(PEACE, PSTAT);
	outb(data, PDATA);
	outb(PEACE | SIDCS, PSTAT);
	usleep(1);
	outb(PEACE, PSTAT);
}

int pinit() {
	ioperm(PSTAT, 1, 1);
	ioperm(PDATA, 1, 1);
	outb(0x08, PSTAT);
	usleep(10);
	outb(0x02, PSTAT);
}

int main() {
	pinit();
	pwrite(0x18, 0x0F);
	pwrite(0x01, 0x10);
	pwrite(0x05, 0x0C);
	pwrite(0x06, 0x04);
	pwrite(0x04, 0x21);
	return 0;
}
