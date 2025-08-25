
// test/test_main.c
#include "test_framework.h"

extern void run_commands_tests(void);
extern void run_plugin_tests(void);
extern void run_e2e_tests(void);

int main(void) {
    // Initialize test counters
    tests_run = 0;
    tests_failed = 0;
    
    printf("Starting CLI tests...\n");
    
    run_commands_tests();
    run_plugin_tests();
    run_e2e_tests();
    
    TEST_SUMMARY();
    return tests_failed > 0 ? 1 : 0;
}
