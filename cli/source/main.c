#include "commands.h"
#include "types.h"
#include "error.h"
#include <stdio.h>
#include <string.h>

const char *source_dir = SOURCE_DIR;  // Embedded at compile time

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
    }
    if (strcmp(argv[1], "help") == 0) return CMD_HELP;
    return CMD_INVALID;
}

int main(int argc, char *argv[]) {
    Command cmd = parse_command(argc, argv);
    switch (cmd) {
        case CMD_RUN:
            cmd_run();
            break;
        case CMD_UPDATE:
            cmd_update();
            break;
        case CMD_GETHEAD:
            if (argc < 3) {
                log_error("gethead requires <user>/<repo>");
                return 1;
            }
            cmd_gethead(argv[2]);
            break;
        case CMD_AUTOSTART_ENABLE:
            cmd_autostart_enable();
            break;
        case CMD_AUTOSTART_DISABLE:
            cmd_autostart_disable();
            break;
        case CMD_PLUGIN_LIST:
            cmd_plugin_list();
            break;
        case CMD_PLUGIN_ENABLE:
            if (argc < 4) {
                log_error("plugin enable requires <name>");
                return 1;
            }
            cmd_plugin_enable(argv[3]);
            break;
        case CMD_PLUGIN_DISABLE:
            if (argc < 4) {
                log_error("plugin disable requires <name>");
                return 1;
            }
            cmd_plugin_disable(argv[3]);
            break;
        case CMD_HELP:
            cmd_help();
            break;
        default:
            log_error("Unknown command");
            cmd_help();
            return 1;
    }

    return 0;
}
