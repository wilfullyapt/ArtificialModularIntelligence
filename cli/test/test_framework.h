
// test/test_framework.h
#ifndef TEST_FRAMEWORK_H
#define TEST_FRAMEWORK_H

#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <stdarg.h>

// Global test counters
extern int tests_run;
extern int tests_failed;

#define TEST(name) void name(void)
#define RUN_TEST(name) do { \
    printf("Running %s...\n", #name); \
    tests_run++; \
    name(); \
} while (0)

#define ASSERT_EQUAL_INT(expected, actual, message) do { \
    if ((expected) != (actual)) { \
        tests_failed++; \
        printf("FAIL: %s: %s (expected %d, got %d)\n", __func__, message, expected, actual); \
    } else { \
        printf("PASS: %s\n", __func__); \
    } \
} while (0)

#define ASSERT_STRING_EQUAL(expected, actual, message) do { \
    if (strcmp(expected, actual) != 0) { \
        tests_failed++; \
        printf("FAIL: %s: %s (expected '%s', got '%s')\n", __func__, message, expected, actual); \
    } else { \
        printf("PASS: %s\n", __func__); \
    } \
} while (0)

#define TEST_SUMMARY() do { \
    printf("\nTest Summary: %d run, %d passed, %d failed\n", \
           tests_run, tests_run - tests_failed, tests_failed); \
} while (0)

#endif // TEST_FRAMEWORK_H
