#include <stdio.h>
#include <unistd.h>
#include <sys/io.h>

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
	outb(RESET, PSTAT);
	usleep(10);
	outb(PEACE, PSTAT);
	return 0;
}

int main() {
	if (sid_init()) return 1;
	sid_write(0x18, 0x0F);
	sid_write(0x01, 0x10);
	sid_write(0x05, 0x0C);
	sid_write(0x06, 0x04);
	sid_write(0x04, 0x21);
	return 0;
}
