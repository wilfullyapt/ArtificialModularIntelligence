
#ifndef MOCKS_H
#define MOCKS_H

// System mock functions
void reset_system_mock(void);
const char* get_last_system_cmd(void);
int system_mock(const char* cmd);

// Override system() calls in tests
#ifdef TESTING
#define system(cmd) system_mock(cmd)
#endif

#endif
