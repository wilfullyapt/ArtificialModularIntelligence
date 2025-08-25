
#ifndef TEST_FRAMEWORK_H
#define TEST_FRAMEWORK_H

#include <stdio.h>
#include <string.h>
#include <stdlib.h>

extern int tests_passed;
extern int tests_failed;

#define TEST(test_name) void test_name(void)

#define RUN_TEST(test_func) do { \
    printf("Running %s... ", #test_func); \
    test_func(); \
    printf("PASSED\n"); \
    tests_passed++; \
} while(0)

#define ASSERT_EQUAL_INT(expected, actual, message) do { \
    if ((expected) != (actual)) { \
        printf("FAILED: %s (expected %d, got %d)\n", message, expected, actual); \
        tests_failed++; \
        return; \
    } \
} while(0)

#define ASSERT_STRING_EQUAL(expected, actual, message) do { \
    if (strcmp((expected), (actual)) != 0) { \
        printf("FAILED: %s (expected '%s', got '%s')\n", message, expected, actual); \
        tests_failed++; \
        return; \
    } \
} while(0)

#define TEST_SUMMARY() do { \
    printf("\nTest Summary: %d passed, %d failed\n", tests_passed, tests_failed); \
} while(0)

// Global test counters
int tests_passed = 0;
int tests_failed = 0;

#endif
