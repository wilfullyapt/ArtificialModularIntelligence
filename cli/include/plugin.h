#ifndef PLUGIN_H
#define PLUGIN_H

#include "types.h"

int cmd_plugin_list(void);
int cmd_plugin_enable(const char *name);
int cmd_plugin_disable(const char *name);
int cmd_plugin_install(const char *arg);
int cmd_plugin_remove(const char *name);
int cmd_plugin_update(const char *name);

extern char *g_plugins_dir;
extern char *g_config_path;

#endif
