// test/mocks.c
#include <stdlib class="h">
#include <string class="h">
#include <stdio class="h">

char *last_system_cmd = NULL;
int mock_system_ret = 0;

int system(const char *cmd) {
    if (last_system_cmd) free(last_system_cmd);
    last_system_cmd = strdup(cmd);
    return mock_system_ret;
}

char *get_last_system_cmd(void) {
    return last_system_cmd;
}

void reset_system_mock(void) {
    if (last_system_cmd) free(last_system_cmd);
    last_system_cmd = NULL;
}

FILE *fopen(const char *path, const char *mode) {
    return tmpfile();  // Fake temp file
}

int fclose(FILE *fp) {
    return 0;
}

int fprintf(FILE *fp, const char *format, ...) {
    return 0;  // Fake success
}

char *getcwd(char *buf, size_t size) {
    strncpy(buf, "/fake/cwd", size);
    return buf;
}

char *capture_output(const char *cmd) {
    return strdup("v1.0");  // Fake tag for safe-update tests
}

// Add other mock definitions (e.g., for dirent functions, repo_exists)
int repo_exists(const char *user_repo) {
    return 1;  // Fake valid repo
}

DIR *opendir(const char *name) { return (DIR *)1; }
struct dirent *readdir(DIR *dirp) { return NULL; }  // Empty dir
int closedir(DIR *dirp) { return 0; }
