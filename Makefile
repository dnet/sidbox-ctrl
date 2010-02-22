sid: sid.c
	gcc sid.c -o sid -O

clean:
	rm -f sid

.PHONY: clean
