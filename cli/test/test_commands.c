
// test/test_commands.c
#include "test_framework.h"
#include "../include/mocks.h"
#include "../include/commands.h"
#include <string.h>
#include <stdlib.h>
#include <stdio.h>
#include <unistd.h>

// External globals that commands.c expects
extern char *g_source_dir;
extern char *g_service_path;

// Mock globals for testing
char *g_source_dir = "/fake/source";
char *g_service_path = "/fake/service.service";

TEST(test_cmd_run) {
    reset_system_mock();
    int ret = cmd_run();
    ASSERT_EQUAL_INT(0, ret, "cmd_run should succeed");
    ASSERT_STRING_EQUAL("python3 /fake/source/ami.py", get_last_system_cmd(), "correct python command");
}

TEST(test_cmd_autostart_enable) {
    reset_system_mock();
    int ret = cmd_autostart_enable();
    ASSERT_EQUAL_INT(0, ret, "autostart enable should succeed");
    // Just check that some system command was called
    const char *last_cmd = get_last_system_cmd();
    ASSERT_EQUAL_INT(1, strlen(last_cmd) > 0, "system command was called");
}

TEST(test_cmd_safe_update_no_update_needed) {
    reset_system_mock();
    int ret = cmd_safe_update();
    ASSERT_EQUAL_INT(0, ret, "safe-update should succeed when on latest tag");
}

void run_commands_tests(void) {
    printf("Running command tests...\n");
    RUN_TEST(test_cmd_run);
    RUN_TEST(test_cmd_autostart_enable);
    RUN_TEST(test_cmd_safe_update_no_update_needed);
}
