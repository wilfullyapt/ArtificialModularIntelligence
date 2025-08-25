#ifndef MOCKS_H
#define MOCKS_H

#include <stdio.h>
#include <stddef.h>
#include <dirent.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <unistd.h>

// Test utility functions
void reset_system_mock(void);
const char* get_last_system_cmd(void);
int repo_exists(const char *user_repo);

// Global test counters (defined in mocks.c)
extern int tests_run;
extern int tests_failed;

#endif // MOCKS_H