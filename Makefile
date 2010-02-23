TEST_OBJECTS=test.o sid.o

test: $(TEST_OBJECTS)
	$(CC) $(TEST_OBJECTS) -o $@

%.o: %.c
	$(CC) $< -c -o $@ -O

clean:
	rm -f test

.PHONY: clean
