#define _GNU_SOURCE
#include "mocks.h"
#include "test_framework.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <dirent.h>

// Global test counters
int tests_run = 0;
int tests_failed = 0;

static char *last_system_cmd = NULL;

FILE *popen(const char *cmd, const char *type) {
    (void)type;  // Unused
    free(last_system_cmd);
    last_system_cmd = strdup(cmd);

    FILE *fp = tmpfile();  // Temporary file for simulated output
    if (!fp) return NULL;

    // Simulate outputs based on command patterns
    if (strstr(cmd, "describe --tags")) {
        fputs("v1.0\n", fp);  // Fake current tag
    } else if (strstr(cmd, "tag -l --sort")) {
        fputs("v1.0\n", fp);  // Fake latest tag (same as current)
    } else if (strstr(cmd, "diff") && strstr(cmd, "wc -l")) {
        fputs("0\n", fp);  // No changes, no recompile needed
    } else {
        // Default: empty output for unknown commands
        fputs("\n", fp);
    }

    rewind(fp);
    return fp;
}

int pclose(FILE *fp) {
    if (fp) fclose(fp);
    return 0;
}

// Mock system function
int system(const char *cmd) {
    if (cmd == NULL) {
        last_system_cmd = NULL;
        return -1;
    }
    free(last_system_cmd);
    last_system_cmd = strdup(cmd);
    return 0;  // Default: success
}

// Mock file operations
FILE *fopen(const char *path, const char *mode) {
    (void)path; (void)mode;
    return tmpfile();
}

int fclose(FILE *fp) {
    (void)fp;
    return 0;
}

int fprintf(FILE *fp, const char *format, ...) {
    (void)fp; (void)format;
    return 0;
}

char *getcwd(char *buf, size_t size) {
    if (buf) {
        strncpy(buf, "/fake/cwd", size - 1);
        buf[size - 1] = '\0';
        return buf;
    }
    return strdup("/fake/cwd");
}

// Mock directory operations
DIR *opendir(const char *name) {
    (void)name;
    return (DIR *)1;
}

struct dirent *readdir(DIR *dirp) {
    (void)dirp;
    return NULL;  // Empty directory
}

int closedir(DIR *dirp) {
    (void)dirp;
    return 0;
}

// Mock system operations
int mkdir(const char *pathname, mode_t mode) {
    (void)pathname; (void)mode;
    return 0;
}

int chdir(const char *path) {
    (void)path;
    return 0;
}

int access(const char *pathname, int mode) {
    (void)pathname; (void)mode;
    return 0;  // Always accessible
}

// Test utility functions
void reset_system_mock(void) {
    free(last_system_cmd);
    last_system_cmd = NULL;
}

const char* get_last_system_cmd(void) {
    return last_system_cmd ? last_system_cmd : "";
}

int repo_exists(const char *user_repo) {
    (void)user_repo;  // Mark parameter as used
    return 1;  // Fake valid repo
}
