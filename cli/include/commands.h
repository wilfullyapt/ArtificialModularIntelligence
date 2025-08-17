#ifndef COMMANDS_H
#define COMMANDS_H

#include "types.h"

int cmd_run(void);
int cmd_update(void);
int cmd_gethead(const char *user_repo);
int cmd_autostart_enable(void);
int cmd_autostart_disable(void);
int cmd_help(void);

extern char *g_source_dir;
extern char *g_service_path;

#endif
