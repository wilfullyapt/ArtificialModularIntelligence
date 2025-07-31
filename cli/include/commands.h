#ifndef COMMANDS_H
#define COMMANDS_H

#include "types.h"

void cmd_run(void);
void cmd_update(void);
void cmd_gethead(const char *user_repo);
void cmd_autostart_enable(void);
void cmd_autostart_disable(void);
void cmd_plugin_list(void);
void cmd_plugin_enable(const char *name);
void cmd_plugin_disable(const char *name);
void cmd_help(void);

#endif
