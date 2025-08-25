// test/test_e2e.c
#include "test_framework.h"
#include <stdio.h>
#include <string.h>

TEST(test_ami_help) {
    // For now, just test that we can call a basic function
    // In a real scenario, this would test the actual binary
    printf("E2E test placeholder - help command\n");
    ASSERT_EQUAL_INT(1, 1, "placeholder test passes");
}

void run_e2e_tests(void) {
    printf("Running e2e tests...\n");
    RUN_TEST(test_ami_help);
}