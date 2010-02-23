TEST_OBJECTS=test.o sid.o
CAT_OBJECTS=cat.o sid.o

all: cat test

cat: $(CAT_OBJECTS)
	$(CC) $(CAT_OBJECTS) -o $@

test: $(TEST_OBJECTS)
	$(CC) $(TEST_OBJECTS) -o $@

%.o: %.c
	$(CC) $< -c -o $@ -O

clean:
	rm -f test cat *.o

.PHONY: clean all
