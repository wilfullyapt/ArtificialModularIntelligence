CC = gcc

REPO_DIR := $(abspath $(dir $(abspath $(lastword $(MAKEFILE_LIST))))..)
BASE_CFLAGS = -Wall -Wextra -std=c99 -I$(INCLUDE_DIR) -DSOURCE_DIR=\"$(REPO_DIR)\"
LDFLAGS = -lyaml -lcurl

PROD_CFLAGS = $(BASE_CFLAGS) -O3
PROD_LDFLAGS = $(LDFLAGS)

TEST_LDFLAGS = $(LDFLAGS) -g
TEST_CFLAGS = $(BASE_CFLAGS) -g -O0

SOURCE_DIR = source
TEST_DIR = test
INCLUDE_DIR = include
PROD_BUILDDIR = build/prod
TEST_BUILDDIR = build/test
VPATH = $(SOURCE_DIR):$(TEST_DIR)

SOURCES = $(wildcard $(SOURCE_DIR)/*.c)
PROD_OBJECTS = $(SOURCES:$(SOURCE_DIR)/%.c=$(PROD_BUILDDIR)/%.o)

TEST_SOURCES = $(filter-out $(SOURCE_DIR)/main.c, $(wildcard $(SOURCE_DIR)/*.c $(TEST_DIR)/*.c))
TEST_OBJECTS = $(patsubst %.c,$(TEST_BUILDDIR)/%.o,$(notdir $(TEST_SOURCES)))

TARGET = ami

.PHONY: all production install test valgrind clean settings

all: production

production: $(PROD_OBJECTS)
	$(CC) $(PROD_OBJECTS) -o $(TARGET) $(PROD_LDFLAGS)
	rm -rf $(PROD_BUILDDIR)

install:
	$(MAKE) production
	cp $(TARGET) $(HOME)/.local/bin/ami

$(PROD_BUILDDIR)/%.o: $(SOURCE_DIR)/%.c | $(PROD_BUILDDIR)
	$(CC) $(PROD_CFLAGS) -c $< -o $@

$(PROD_BUILDDIR):
	mkdir -p $(PROD_BUILDDIR)

# Update your test/valgrind targets to use $(TEST_OBJECTS) instead of separate groups
# For example:
test: $(TEST_OBJECTS)
	$(CC) $^ -o $(TARGET) $(TEST_LDFLAGS)
	./$(TARGET)

valgrind: $(TEST_OBJECTS)
	$(CC) $^ -o $(TARGET) $(TEST_LDFLAGS)
	valgrind --leak-check=full --show-leak-kinds=all --track-origins=yes ./$(TARGET)

$(TEST_BUILDDIR)/%.o: %.c | $(TEST_BUILDDIR)
	$(CC) $(TEST_CFLAGS) $(if $(findstring $(TESTDIR)/,$<),-DTESTING,) -c $< -o $@

coverage: test
	gcov $(SOURCES)
	# Or for HTML reports: Install lcov (sudo apt install lcov), then:
	# lcov --capture --directory . --output-file coverage.info
	# genhtml coverage.info --output-directory coverage_html
	# Open coverage_html/index.html in a browser

$(TEST_BUILDDIR):
	mkdir -p $(TEST_BUILDDIR)

clean:
	rm -rf build $(TARGET)

settings:
	@echo ""
	@echo "Repo Directory        => $(REPO_DIR)"
	@echo "Production Build      => $(CC) $(PROD_OBJECTS) -o $(TARGET) $(PROD_LDFLAGS)"
	@echo ""
	@echo "Sources               => $(SOURCES)"
	@echo "Objects               => $(PROD_OBJECTS)"
	@echo ""
	@echo "Test Sources          => $(TEST_SOURCES)"
	@echo "Test Objects     => $(TEST_OBJECTS)"
	@echo ""
