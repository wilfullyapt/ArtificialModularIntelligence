#include "socket_comm.h"
#include "error.h"
#include <sys/socket.h>
#include <sys/un.h>
#include <unistd.h>
#include <string.h>
#include <errno.h>
#include <stdio.h>

extern int g_socket_fd;  // Defined in main.c or global.c; better to initialize here if possible.

int init_socket_connection(const char *socket_path) {
    struct sockaddr_un addr;
    g_socket_fd = socket(AF_UNIX, SOCK_STREAM, 0);
    if (g_socket_fd == -1) {
        log_error("Socket creation failed: %s", strerror(errno));
        return -1;
    }

    memset(&addr, 0, sizeof(addr));
    addr.sun_family = AF_UNIX;
    if (strlen(socket_path) >= sizeof(addr.sun_path)) {
        log_error("Socket path too long");
        close(g_socket_fd);
        g_socket_fd = -1;
        return -1;
    }
    strncpy(addr.sun_path, socket_path, sizeof(addr.sun_path) - 1);

    if (connect(g_socket_fd, (struct sockaddr*)&addr, sizeof(addr)) == -1) {
        log_error("Socket connect failed: %s", strerror(errno));
        close(g_socket_fd);
        g_socket_fd = -1;
        return -1;
    }
    return 0;
}

void send_event_if_connected(const char *event, const char *message, const char *data_json) {
    if (g_socket_fd == -1) {
        log_info("Socket not connected; falling back to log");
        return;
    }
    char buf[1024];
    int len;
    if (data_json) {
        len = snprintf(buf, sizeof(buf), "{\"event\": \"%s\", \"message\": \"%s\", \"data\": %s}\n", event, message, data_json);
    } else {
        len = snprintf(buf, sizeof(buf), "{\"event\": \"%s\", \"message\": \"%s\"}\n", event, message);
    }

    if (len <= 0 || (size_t)len >= sizeof(buf)) {
        log_error("Event message too long or formatting error");
        return;
    }

    ssize_t written = write(g_socket_fd, buf, len);
    if (written != len) {
        log_error("Failed to write to socket: %s", strerror(errno));
        return;
    }
}

void close_socket_connection(void) {
    if (g_socket_fd != -1) {
        close(g_socket_fd);
        g_socket_fd = -1;
    }
}
