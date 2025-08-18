#include "unity.h"
#include "commands.h"  // Include headers for functions to test
#include "plugin.h"

// Mock any externs if needed, e.g., extern char *g_source_dir = "/mock";

void setUp(void) {}  // Setup before each test
void tearDown(void) {}  // Cleanup after each test

void test_expand_path(void) {
    char *result = expand_path("~/.test");
    TEST_ASSERT_NOT_NULL(result);
    // Assume HOME=/home/user, check prefix
    TEST_ASSERT_TRUE(strncmp(result, "/home/", 6) == 0);  // Adjust for your env
    free(result);
}

void test_valid_user_repo(void) {
    TEST_ASSERT_TRUE(valid_user_repo("user/repo"));
    TEST_ASSERT_FALSE(valid_user_repo("user//repo"));
    TEST_ASSERT_FALSE(valid_user_repo("user/repo!"));
}

// Add more: test_capture_output (mock popen), set_plugin_status (mock files), etc.

int main(void) {
    UNITY_BEGIN();
    RUN_TEST(test_expand_path);
    RUN_TEST(test_valid_user_repo);
    // Add all tests
    return UNITY_END();
}
