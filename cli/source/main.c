#include "commands.h"
#include "types.h"
#include "error.h"
#include "plugin.h"
#include "socket_comm.h"
#include <stdio.h>
#include <string.h>
#include <getopt.h>
#include <stdlib.h>

char *g_source_dir = SOURCE_DIR;
char *g_plugins_dir = "~/.ami/plugins";
char *g_config_path = "~/.ami/ami_config.yaml";
char *g_service_path = "~/.config/systemd/user/ami.service";

char *g_socket_path = NULL;
int g_socket_fd = -1;

static struct option long_options[] = {
    {"source-dir", required_argument, NULL, 'd'},
    {"plugins-dir", required_argument, NULL, 'p'},
    {"config-path", required_argument, NULL, 'c'},
    {"service-path", required_argument, NULL, 's'},
    {"socket-path", required_argument, NULL, 'k'},
    {NULL, 0, NULL, 0}
};

Command parse_command(int argc, char *argv[]) {
    if (argc < 2) return CMD_HELP;
    if (strcmp(argv[1], "wherepo") == 0) return CMD_WHEREPO;
    if (strcmp(argv[1], "run") == 0) return CMD_RUN;
    if (strcmp(argv[1], "update") == 0) return CMD_UPDATE;
    if (strcmp(argv[1], "safe-update") == 0) return CMD_SAFE_UPDATE;
    if (strcmp(argv[1], "rollback") == 0) return CMD_ROLLBACK;
    if (strcmp(argv[1], "gethead") == 0) return CMD_GETHEAD;
    if (strcmp(argv[1], "autostart") == 0 && argc > 2) {
        if (strcmp(argv[2], "enable") == 0) return CMD_AUTOSTART_ENABLE;
        if (strcmp(argv[2], "disable") == 0) return CMD_AUTOSTART_DISABLE;
    }
    if (strcmp(argv[1], "plugin") == 0 && argc > 2) {
        if (strcmp(argv[2], "list") == 0) return CMD_PLUGIN_LIST;
        if (strcmp(argv[2], "enable") == 0) return CMD_PLUGIN_ENABLE;
        if (strcmp(argv[2], "disable") == 0) return CMD_PLUGIN_DISABLE;
        if (strcmp(argv[2], "install") == 0) return CMD_PLUGIN_INSTALL;
        if (strcmp(argv[2], "remove") == 0) return CMD_PLUGIN_REMOVE;
        if (strcmp(argv[2], "update") == 0) return CMD_PLUGIN_UPDATE;
    }
    if (strcmp(argv[1], "help") == 0) return CMD_HELP;
    return CMD_INVALID;
}

int main(int argc, char *argv[]) {
    init_logging("ami", 1);

    char cmd_buf[4096] = {0};
    size_t len = 0;
    for (int i = 0; i < argc; i++) {
        size_t arg_len = strlen(argv[i]);
        if (len + arg_len + 2 > sizeof(cmd_buf)) {
            break;
        }
        if (i > 0) {
            cmd_buf[len++] = ' ';
        }
        memcpy(cmd_buf + len, argv[i], arg_len);
        len += arg_len;
    }
    cmd_buf[len] = '\0';
    log_info("Executed command: %s", cmd_buf);

    int opt;
    while ((opt = getopt_long(argc, argv, "", long_options, NULL)) != -1) {
        switch (opt) {
            case 'd':
                g_source_dir = optarg;
                break;
            case 'p':
                g_plugins_dir = optarg;
                break;
            case 'c':
                g_config_path = optarg;
                break;
            case 's':
                g_service_path = optarg;
                break;
            case 'k':
                g_socket_path = optarg;
                break;
            default:
                log_error("Unknown option");
                cmd_help();
                return 1;
        }
    }

    int socket_enabled = (g_socket_path != NULL && strlen(g_socket_path) > 0);
    if (socket_enabled) {
        if (init_socket_connection(g_socket_path) != 0) {
            log_error("Failed to initialize socket connection");
            return 1;
        }
        send_event_if_connected("start", "Command started", NULL);
    }

    Command cmd = parse_command(argc - optind + 1, argv + optind - 1);
    int ret = 0;
    switch (cmd) {
        case CMD_WHEREPO:
            ret = 0;
            printf("Source local Repo: %s\n", g_source_dir);
            break;
        case CMD_RUN:
            ret = cmd_run();
            break;
        case CMD_UPDATE:
            ret = cmd_update();
            break;
        case CMD_SAFE_UPDATE:
            ret = cmd_safe_update();
            break;
        case CMD_ROLLBACK:
            ret = cmd_rollback();
            break;
        case CMD_GETHEAD:
            if (argc - optind + 1 < 3) {
                log_error("gethead requires <user>/<repo>");
                return 1;
            }
            ret = cmd_gethead(argv[optind + 1]);
            break;
        case CMD_AUTOSTART_ENABLE:
            ret = cmd_autostart_enable();
            break;
        case CMD_AUTOSTART_DISABLE:
            ret = cmd_autostart_disable();
            break;
        case CMD_PLUGIN_LIST:
            ret = cmd_plugin_list();
            break;
        case CMD_PLUGIN_ENABLE:
            if (argc - optind + 1 < 4) {
                log_error("plugin enable requires <name>");
                return 1;
            }
            ret = cmd_plugin_enable(argv[optind + 2]);
            break;
        case CMD_PLUGIN_DISABLE:
            if (argc - optind + 1 < 4) {
                log_error("plugin disable requires <name>");
                return 1;
            }
            ret = cmd_plugin_disable(argv[optind + 2]);
            break;
        case CMD_PLUGIN_INSTALL:
            if (argc - optind + 1 < 4) {
                log_error("plugin install requires <url>");
                return 1;
            }
            ret = cmd_plugin_install(argv[optind + 2]);
            break;
        case CMD_PLUGIN_REMOVE:
            if (argc - optind + 1 < 4) {
                log_error("plugin remove requires <name>");
                return 1;
            }
            ret = cmd_plugin_remove(argv[optind + 2]);
            break;
        case CMD_PLUGIN_UPDATE:
            if (argc - optind + 1 < 4) {
                log_error("plugin update requires <name>");
                return 1;
            }
            ret = cmd_plugin_update(argv[optind + 2]);
            break;
        case CMD_HELP:
            ret = cmd_help();
            break;
        default:
            log_error("Unknown command");
            cmd_help();
            return 1;
    }

    if (socket_enabled) {
        if (ret == 0) {
            send_event_if_connected("success", "Command completed", NULL);
        } else {
            send_event_if_connected("error", "Command failed", NULL);
        }
        close_socket_connection();
    }

    close_logging();

    return ret;
}
