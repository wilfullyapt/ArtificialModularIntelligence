// test/test_mocks.c
#include <string.h>
#include <stdlib.h>

static char *last_system_cmd = NULL;
int system(const char *cmd) {
    last_system_cmd = strdup(cmd);
    return 0;  // Default: success; tests can override if needed
}

// Add a getter for tests to access last_system_cmd
char *get_last_system_cmd(void) {
    return last_system_cmd;
}

void reset_system_mock(void) {
    free(last_system_cmd);
    last_system_cmd = NULL;
}
