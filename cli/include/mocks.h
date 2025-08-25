// test/mocks.h
#ifndef MOCKS_H
#define MOCKS_H

#include <stdio.h>
#include <stddef.h>
#include <dirent.h>

// Mock functions for testing
int system(const char *command);
int mkdir(const char *pathname, int mode);
int chdir(const char *path);
int access(const char *pathname, int mode);
FILE *fopen(const char *path, const char *mode);
int fclose(FILE *fp);
int fprintf(FILE *fp, const char *format, ...);
char *getcwd(char *buf, size_t size);

// System mock functions
void reset_system_mock(void);
const char* get_last_system_cmd(void);
int system_mock(const char* cmd);

// Override system() calls in tests
#ifdef TESTING
#define system(cmd) system_mock(cmd)
#endif

#endif