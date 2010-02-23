#include <stdio.h>
#include "sid.h"

int main() {
	int addr, data;

	if (sid_init()) return 1;
	while (1) {
		if (((addr = getchar()) == EOF)
			|| ((data = getchar()) == EOF)) break;
		sid_write(addr, data);
	}
	return 0;
}
