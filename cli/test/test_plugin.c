// test/test_plugin.c
#include "test_framework.h"
#include "../include/mocks.h"
#include "../include/plugin.h"
#include <string.h>

// Mock globals
char *g_plugins_dir = "/fake/plugins";
char *g_config_path = "/fake/config.yaml";

// No local mocks needed; use global mocks from mocks.c

TEST(test_plugin_list) {
    reset_system_mock();
    int ret = cmd_plugin_list();
    ASSERT_EQUAL_INT(0, ret, "plugin list should succeed");
}

TEST(test_plugin_enable) {
    reset_system_mock();
    int ret = cmd_plugin_enable("test-plugin");
    ASSERT_EQUAL_INT(0, ret, "plugin enable should succeed");
}

TEST(test_plugin_disable) {
    reset_system_mock();
    int ret = cmd_plugin_disable("test-plugin");
    ASSERT_EQUAL_INT(0, ret, "plugin disable should succeed");
}

void run_plugin_tests(void) {
    printf("Running plugin tests...\n");
    RUN_TEST(test_plugin_list);
    RUN_TEST(test_plugin_enable);
    RUN_TEST(test_plugin_disable);
}
