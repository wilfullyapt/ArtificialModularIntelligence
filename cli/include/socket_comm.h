#ifndef SOCKET_COMM_H
#define SOCKET_COMM_H

extern int g_socket_fd;

int init_socket_connection(const char *socket_path);
int send_event_if_connected(const char *event, const char *message, const char *data_json);
void close_socket_connection(void);

#endif
