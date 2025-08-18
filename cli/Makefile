
CC = gcc
SOURCE_DIR ?= $(shell pwd)/..
#CFLAGS = -Wall -g -Iinclude -DSOURCE_DIR=\"$(SOURCE_DIR)\" -I test/unity/src
CFLAGS = -Wall -g -Iinclude -DSOURCE_DIR=\"$(SOURCE_DIR)\" -I test/unity/src -D_GNU_SOURCE
LDFLAGS = -lcurl -lyaml
OBJ = source/main.o source/commands.o source/error.o source/plugin.o
TEST_OBJ = test/unit_tests.o test/unity/src/unity.o
TARGET = ami
TEST_TARGET = test_ami

all: $(TARGET)

install: $(TARGET)
	cp $(TARGET) $(HOME)/.local/bin/
check-install:
	ls -lt $(HOME)/.local/bin | grep ami

$(TARGET): $(OBJ)
	$(CC) $(OBJ) -o $(TARGET) $(LDFLAGS)

source/main.o: source/main.c include/commands.h include/types.h include/error.h include/plugin.h
	$(CC) $(CFLAGS) -c source/main.c -o source/main.o

source/commands.o: source/commands.c include/commands.h include/error.h include/types.h include/plugin.h
	$(CC) $(CFLAGS) -c source/commands.c -o source/commands.o

source/error.o: source/error.c include/error.h
	$(CC) $(CFLAGS) -c source/error.c -o source/error.o

source/plugin.o: source/plugin.c include/plugin.h include/error.h include/types.h
	$(CC) $(CFLAGS) -c source/plugin.c -o source/plugin.o

test/unit_tests.o: test/unit_tests.c
	$(CC) $(CFLAGS) -c test/unit_tests.c -o test/unit_tests.o

test/unity/src/unity.o: test/unity/src/unity.c
	$(CC) $(CFLAGS) -c test/unity/src/unity.c -o test/unity/src/unity.o

$(TEST_TARGET): $(OBJ) $(TEST_OBJ)
	$(CC) $(OBJ) $(TEST_OBJ) -o $(TEST_TARGET) $(LDFLAGS)

test: $(TEST_TARGET)
	./$(TEST_TARGET)
	./test/integration.sh

check-deps:
	@command -v git >/dev/null 2>&1 || echo "Missing git: sudo apt install git"
	@command -v systemctl >/dev/null 2>&1 || echo "Missing systemd: Already on Pop!_OS"
	@pkg-config --exists libyaml-0.1 >/dev/null 2>&1 || echo "Missing libyaml: sudo apt install libyaml-dev"

clean:
	rm -f $(OBJ) $(TEST_OBJ) $(TARGET) $(TEST_TARGET)

.PHONY: all clean check-deps test
