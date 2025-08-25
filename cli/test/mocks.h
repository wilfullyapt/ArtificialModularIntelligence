
// test/mocks.h
#ifndef MOCKS_H
#define MOCKS_H

#include <stdio.h>
#include <stddef.h>
#include <dirent.h>
#include <sys/stat.h>
#include <unistd.h>

// Test utility functions
void reset_system_mock(void);
const char* get_last_system_cmd(void);
int repo_exists(const char *user_repo);

#endif // MOCKS_H
