#include "mocks.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/stat.h>
#include <dirent.h>

static char last_system_cmd[1024] = {0};

void reset_system_mock(void) {
    memset(last_system_cmd, 0, sizeof(last_system_cmd));
}

const char* get_last_system_cmd(void) {
    return last_system_cmd;
}

int system_mock(const char* cmd) {
    if (cmd) {
        strncpy(last_system_cmd, cmd, sizeof(last_system_cmd) - 1);
    }
    return 0;  // Always succeed in tests
}

// Add other mock definitions (e.g., for dirent functions, repo_exists)
int repo_exists(const char *user_repo) {
    return 1;  // Fake valid repo
}

DIR *opendir(const char *name) { 
    (void)name; // Suppress unused parameter warning
    return (DIR *)1; 
}

struct dirent *readdir(DIR *dirp) { 
    (void)dirp; // Suppress unused parameter warning
    return NULL;  // Empty dir
}

int closedir(DIR *dirp) {
    (void)dirp; // Suppress unused parameter warning
    return 0;
}