
// test/test_plugin.c
#include "test_framework.h"
#include "plugin.h"
#include "mocks.h"
#include <string.h>
#include <stdlib.h>
#include <dirent.h>

// Mock globals
char *g_plugins_dir = NULL;
char *g_config_path = NULL;

// No local mocks needed; use global mocks from mocks.c
TEST(test_cmd_plugin_list_empty) {
    char template[] = "test/tmp/plugins_XXXXXX";
    if (mkdtemp(template) == NULL) {
        ASSERT_EQUAL_INT(0, 1, "mkdtemp failed");
    }
    char *temp_plugins = strdup(template);
    g_plugins_dir = temp_plugins;
    int ret = cmd_plugin_list();
    ASSERT_EQUAL_INT(0, ret, "plugin list should succeed on empty dir");
    free(temp_plugins);
    rmdir(template);
}

TEST(test_cmd_plugin_install) {
    char template[] = "test/tmp/plugins_XXXXXX";
    if (mkdtemp(template) == NULL) {
        ASSERT_EQUAL_INT(0, 1, "mkdtemp failed");
    }
    char *temp_plugins = strdup(template);
    g_plugins_dir = temp_plugins;
    reset_system_mock();
    int ret = cmd_plugin_install("user/repo");
    ASSERT_EQUAL_INT(0, ret, "plugin install should succeed");
    char expected[1024];
    snprintf(expected, sizeof(expected), "git clone https://github.com/user/repo %s/repo", template);
    ASSERT_STRING_EQUAL(expected, get_last_system_cmd(), "correct git clone command");
    reset_system_mock();
    free(temp_plugins);
    rmdir(template);
}

void run_plugin_tests(void) {
    RUN_TEST(test_cmd_plugin_list_empty);
    RUN_TEST(test_cmd_plugin_install);
}
