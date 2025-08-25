// test/test_main.c
#include "test_framework.h"

extern void run_commands_tests(void);
extern void run_plugin_tests(void);
extern void run_e2e_tests(void);

int main(void) {
    printf("Starting tests...\n");
    run_commands_tests();
    run_plugin_tests();
    run_e2e_tests();
    TEST_SUMMARY();
    return tests_failed > 0 ? 1 : 0;
}
