
CC = gcc
SOURCE_DIR ?= $(shell pwd)/..
CFLAGS = -Wall -g -Iinclude -DSOURCE_DIR=\"$(SOURCE_DIR)\"
LDFLAGS = -lcurl -luuid
OBJ = source/main.o source/commands.o source/error.o
TARGET = ami

all: $(TARGET)

$(TARGET): $(OBJ)
	$(CC) $(OBJ) -o $(TARGET) $(LDFLAGS)

source/main.o: source/main.c include/commands.h include/types.h include/error.h
	$(CC) $(CFLAGS) -c source/main.c -o source/main.o

source/commands.o: source/commands.c include/commands.h include/error.h include/types.h
	$(CC) $(CFLAGS) -c source/commands.c -o source/commands.o

source/error.o: source/error.c include/error.h
	$(CC) $(CFLAGS) -c source/error.c -o source/error.o

check-deps:
	@command -v git >/dev/null 2>&1 || echo "Missing git: sudo apt install git"
	@command -v systemctl >/dev/null 2>&1 || echo "Missing systemd: Already on Pop!_OS"

clean:
	rm -f $(OBJ) $(TARGET)

.PHONY: all clean check-deps
