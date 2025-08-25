
CC = gcc
SOURCE_DIR ?= $(shell pwd)/..
CFLAGS = -Wall -g -Iinclude -DSOURCE_DIR=\"$(SOURCE_DIR)\" -D_GNU_SOURCE
LDFLAGS = -lcurl -lyaml
SOURCE_OBJ = source/commands.o source/error.o source/plugin.o
OBJ = $(SOURCE_OBJ) source/main.o
TEST_OBJ = test/test_main.o test/test_commands.o test/test_plugin.o test/test_e2e.o test/mocks.o
TARGET = ami
TEST_TARGET = test_ami

all: $(TARGET)

install: $(TARGET)
	cp $(TARGET) $(HOME)/.local/bin/
check-install:
	ls -lt $(HOME)/.local/bin | grep ami

$(TARGET): $(OBJ)
	$(CC) $(OBJ) -o $(TARGET) $(LDFLAGS)

test: $(TARGET) $(TEST_TARGET)
	./$(TEST_TARGET)

$(TEST_TARGET): $(SOURCE_OBJ) $(TEST_OBJ)
	$(CC) $(SOURCE_OBJ) $(TEST_OBJ) -o $(TEST_TARGET) $(LDFLAGS)

source/main.o: source/main.c include/commands.h include/types.h include/error.h include/plugin.h
	$(CC) $(CFLAGS) -c source/main.c -o source/main.o

source/commands.o: source/commands.c include/commands.h include/error.h include/types.h include/plugin.h
	$(CC) $(CFLAGS) -c source/commands.c -o source/commands.o

source/error.o: source/error.c include/error.h
	$(CC) $(CFLAGS) -c source/error.c -o source/error.o

source/plugin.o: source/plugin.c include/plugin.h include/error.h include/types.h
	$(CC) $(CFLAGS) -c source/plugin.c -o source/plugin.o

test/test_main.o: test/test_main.c test/test_framework.h
	$(CC) $(CFLAGS) -c test/test_main.c -o test/test_main.o

test/test_commands.o: test/test_commands.c test/test_framework.h include/commands.h
	$(CC) $(CFLAGS) -c test/test_commands.c -o test/test_commands.o

test/test_plugin.o: test/test_plugin.c test/test_framework.h include/plugin.h
	$(CC) $(CFLAGS) -c test/test_plugin.c -o test/test_plugin.o

test/test_e2e.o: test/test_e2e.c test/test_framework.h
	$(CC) $(CFLAGS) -c test/test_e2e.c -o test/test_e2e.o

test/mocks.o: test/mocks.c include/mocks.h
	$(CC) $(CFLAGS) -c test/mocks.c -o test/mocks.o

clean:
	rm -f $(OBJ) $(TEST_OBJ) $(TARGET) $(TEST_TARGET) *.gcno *.gcda *.gcov

#Coverage: Compile with coverage flags, run tests, generate reports
coverage: CFLAGS += --coverage
coverage: clean test
	gcov source/*.c

.PHONY: all install check-install test clean coverage
