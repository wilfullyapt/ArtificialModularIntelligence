
// test/mocks.h
#ifndef MOCKS_H
#define MOCKS_H

#include <stdio.h>
#include <stddef.h>
#include <dirent.h>
#include <sys/stat.h>
#include <unistd.h>

// Mock functions for testing
int system(const char *command);
int mkdir(const char *pathname, mode_t mode);
int chdir(const char *path);
int access(const char *pathname, int mode);
FILE *fopen(const char *path, const char *mode);
int fclose(FILE *fp);
int fprintf(FILE *fp, const char *format, ...);
char *getcwd(char *buf, size_t size);
DIR *opendir(const char *name);
struct dirent *readdir(DIR *dirp);
int closedir(DIR *dirp);

// Test-specific mock functions
int repo_exists(const char *user_repo);
void reset_system_mock(void);
const char *get_last_system_cmd(void);

#endif // MOCKS_H
