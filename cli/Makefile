CC = gcc
CFLAGS = -Wall -Wextra -std=c99 -Iinclude -DSOURCE_DIR=\"$(PWD)/../\"
LDFLAGS = -lyaml -lcurl

SRCDIR = source
TESTDIR = test
INCDIR = include
BUILDDIR = build

SOURCES = $(wildcard $(SRCDIR)/*.c)
OBJECTS = $(SOURCES:$(SRCDIR)/%.c=$(BUILDDIR)/%.o)
TEST_SOURCES = $(wildcard $(TESTDIR)/*.c)
TEST_OBJECTS = $(TEST_SOURCES:$(TESTDIR)/%.c=$(BUILDDIR)/test_%.o)

TARGET = ami
TEST_TARGET = test_runner

.PHONY: all clean test

all: $(TARGET)

$(TARGET): $(OBJECTS)
	$(CC) $(OBJECTS) -o $@ $(LDFLAGS)

$(BUILDDIR)/%.o: $(SRCDIR)/%.c | $(BUILDDIR)
	$(CC) $(CFLAGS) -c $< -o $@

$(BUILDDIR):
	mkdir -p $(BUILDDIR)

# Test build
test: $(TEST_TARGET)
	./$(TEST_TARGET)

$(TEST_TARGET): $(TEST_OBJECTS) $(filter-out $(BUILDDIR)/main.o, $(OBJECTS)) | $(BUILDDIR)
	$(CC) $(filter-out $(BUILDDIR)/main.o, $(OBJECTS)) $(TEST_OBJECTS) -o $@ $(LDFLAGS)

$(BUILDDIR)/test_%.o: $(TESTDIR)/%.c | $(BUILDDIR)
	$(CC) $(CFLAGS) -DTESTING -c $< -o $@

clean:
	rm -rf $(BUILDDIR) $(TARGET) $(TEST_TARGET)

install: $(TARGET)
	cp $(TARGET) /usr/local/bin/

.PRECIOUS: $(BUILDDIR)/%.o $(BUILDDIR)/test_%.o