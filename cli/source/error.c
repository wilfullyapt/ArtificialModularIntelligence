#include "error.h"
#include <syslog.h>
#include <stdarg.h>
#include <stdio.h>  // For fallback if needed
#include <time.h>   // For timestamps if not using syslog

// Global flag to determine logging method: 0 for stderr/stdout, 1 for syslog
static int use_syslog = 1;

// Initialize logging system
void init_logging(const char *program_name, int use_syslog_flag) {
    use_syslog = use_syslog_flag;
    if (use_syslog) {
        openlog(program_name, LOG_PID | LOG_CONS, LOG_USER);
    }
}

// Cleanup logging
void close_logging() {
    if (use_syslog) {
        closelog();
    }
}

// Helper function for formatted logging
static void log_message(int priority, const char *format, va_list args) {
    char buffer[1024];
    vsnprintf(buffer, sizeof(buffer), format, args);

    if (use_syslog) {
        syslog(priority, "%s", buffer);
    } else {
        // Fallback to console with timestamp
        time_t now = time(NULL);
        struct tm *tm = localtime(&now);
        char time_str[32];
        strftime(time_str, sizeof(time_str), "%Y-%m-%d %H:%M:%S", tm);

        FILE *out = (priority == LOG_ERR) ? stderr : stdout;
        fprintf(out, "[%s] %s: %s\n", time_str, (priority == LOG_ERR) ? "Error" : "Info", buffer);
    }
}

void log_error(const char *message, ...) {
    va_list args;
    va_start(args, message);
    log_message(LOG_ERR, message, args);
    va_end(args);
}

void log_info(const char *message, ...) {
    va_list args;
    va_start(args, message);
    log_message(LOG_INFO, message, args);
    va_end(args);
}
