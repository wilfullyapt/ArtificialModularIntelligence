#ifndef ERROR_H
#define ERROR_H

#include <stdarg.h>

void init_logging(const char *program_name, int use_syslog_flag);
void close_logging();
static void log_message(int priority, const char *format, va_list args);

void log_error(const char *message,...);
void log_info(const char *message,...);

#endif
