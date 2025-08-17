#include "commands.h"
#include "types.h"
#include "error.h"
#include "plugin.h"
#include <stdio.h>
#include <string.h>
#include <getopt.h>
#include <stdlib.h>

char *g_source_dir = SOURCE_DIR;  // Can be overridden
char *g_plugins_dir = "~/.ami/plugins";
char *g_config_path = "~/.ami/ami_config.yaml";
char *g_service_path = "~/.config/systemd/user/ami.service";

static struct option long_options[] = {
    {"source-dir", required_argument, NULL, 'd'},
    {"plugins-dir", required_argument, NULL, 'p'},
    {"config-path", required_argument, NULL, 'c'},
    {"service-path", required_argument, NULL, 's'},
    {NULL, 0, NULL, 0}
};

Command parse_command(int argc, char *argv[]) {
    if (argc < 2) return CMD_HELP;
    if (strcmp(argv[1], "run") == 0) return CMD_RUN;
    if (strcmp(argv[1], "update") == 0) return CMD_UPDATE;
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
            default:
                log_error("Unknown option");
                cmd_help();
                return 1;
        }
    }

    Command cmd = parse_command(argc - optind + 1, &argv[optind - 1]);
    int ret = 0;
    switch (cmd) {
        case CMD_RUN:
            ret = cmd_run();
            break;
        case CMD_UPDATE:
            ret = cmd_update();
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

    return ret;
}
