
// test/test_commands.c
#include "test_framework.h"
#include "commands.h"
#include "mocks.h"
#include <string.h>
#include <stdlib.h>
#include <stdio.h>
#include <unistd.h>

// Mock globals
char *g_source_dir = "/fake/source";
char *g_service_path = NULL;  // Set dynamically in tests

// No local mocks needed; use global mocks from mocks.c
TEST(test_cmd_run) {
    reset_system_mock();
    int ret = cmd_run();
    ASSERT_EQUAL_INT(0, ret, "cmd_run should succeed");
    ASSERT_STRING_EQUAL("python3 /fake/source/ami.py", get_last_system_cmd(), "correct python command");
    reset_system_mock();
}

TEST(test_cmd_autostart_enable) {
    char temp_template[] = "test/tmp/test_service_XXXXXX";  // Must be modifiable array, not pointer
    int fd = mkstemp(temp_template);  // Creates file and returns fd
    if (fd == -1) {
        ASSERT_EQUAL_INT(0, 1, "mkstemp failed");  // Fail test
    }
    close(fd);  // Close if not needed open
    char *service_path = strdup(temp_template);
    g_service_path = service_path;
    reset_system_mock();
    int ret = cmd_autostart_enable();
    ASSERT_EQUAL_INT(0, ret, "autostart enable should succeed");
    ASSERT_STRING_EQUAL("systemctl --user enable --now ami.service", get_last_system_cmd(), "enable called");
    reset_system_mock();
    free(service_path);
    unlink(temp_template);  // Clean up the temp file
}

TEST(test_cmd_safe_update_no_update_needed) {   // No local capture_output needed; use global mock
    int ret = cmd_safe_update();
    ASSERT_EQUAL_INT(0, ret, "safe-update should succeed when on latest tag");
    // Verify log_info called (requires mocking log_info for full check)
}

void run_commands_tests(void) {
    RUN_TEST(test_cmd_run);
    RUN_TEST(test_cmd_autostart_enable);
    RUN_TEST(test_cmd_safe_update_no_update_needed);
}
