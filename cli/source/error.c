
#include "error.h"
#include <stdio.h>

void log_error(const char *message) {
    fprintf(stderr, "Error: %s\n", message);
}

void log_info(const char *message) {
    printf("Info: %s\n", message);
}
