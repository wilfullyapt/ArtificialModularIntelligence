// test/mocks.h
#ifndef MOCKS_H
#define MOCKS_H

extern char *mock_last_system_cmd;
extern int mock_system_ret;

// Declare the mock functions (no definitions here)
int system(const char *cmd);
FILE *fopen(const char *path, const char *mode);
int fclose(FILE *fp);
int fprintf(FILE *fp, const char *format, ...);
char *getcwd(char *buf, size_t size);
char *capture_output(const char *cmd);  // If needed for safe-update mocks
// Add other mocks as needed (e.g., opendir, readdir, repo_exists)

#endif
