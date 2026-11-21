#include "commands.h"
#include "error.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <dirent.h>
#include <sys/stat.h>
#include <unistd.h>
#include <errno.h>

#define AMI_HOME "~/.ami"
#define PLUGINS_DIR "~/.ami/plugins"
#define CONFIG_PATH "~/.ami/ami_config.yaml"
#define SERVICE_PATH "~/.config/systemd/user/ami.service"

extern const char *source_dir;  // From -DSOURCE_DIR

static char *expand_path(const char *path) {
    char *home = getenv("HOME");
    char *full = malloc(strlen(home) + strlen(path) + 1);
    sprintf(full, "%s%s", home, path + 1);  // Skip ~
    return full;
}

void cmd_run(void) {
    char cmd[1024];
    /* Package entry is ami.main — not a root ami.py */
    snprintf(cmd, sizeof(cmd),
             "cd %s && python3 -m ami.main", source_dir);
    if (system(cmd) != 0) {
        log_error("Failed to run Python application (python3 -m ami.main)");
    }
}

void cmd_update(void) {
    char cmd[1024];
    /* Thin sketch: no release plane / rollback yet — see docs/APPLIANCE_SPINE.md */
    snprintf(cmd, sizeof(cmd),
             "git -C %s fetch && git -C %s checkout $(git -C %s describe --tags --abbrev=0) && make -C %s test",
             source_dir, source_dir, source_dir, source_dir);
    if (system(cmd) != 0) {
        log_error("Update failed (no auto-rollback)");
    }
}

void cmd_gethead(const char *user_repo) {
    char *plugins = expand_path(PLUGINS_DIR);
    char cmd[1024];
    snprintf(cmd, sizeof(cmd), "mkdir -p %s && git clone https://github.com/%s %s/%s",
             plugins, user_repo, plugins, strrchr(user_repo, '/') + 1);
    if (system(cmd) != 0) {
        log_error("Failed to download headspace");
    }
    free(plugins);
}

void cmd_autostart_enable(void) {
    char *service = expand_path(SERVICE_PATH);
    FILE *fp = fopen(service, "w");
    if (!fp) {
        log_error("Failed to create service file");
        return;
    }
    fprintf(fp, "[Unit]\nDescription=AMI\n[Service]\nExecStart=%s run\n[Install]\nWantedBy=default.target\n", getcwd(NULL, 0));  // Use current binary path for ExecStart
    fclose(fp);
    system("systemctl --user daemon-reload");
    if (system("systemctl --user enable --now ami.service") != 0) {
        log_error("Failed to enable autostart");
    }
    free(service);
}

void cmd_autostart_disable(void) {
    if (system("systemctl --user disable --now ami.service") != 0) {
        log_error("Failed to disable autostart");
    }
    char *service = expand_path(SERVICE_PATH);
    remove(service);
    system("systemctl --user daemon-reload");
    free(service);
}

void cmd_plugin_list(void) {
    char cmd[1024];
    snprintf(cmd, sizeof(cmd), "cd %s && python3 -m ami.cli plugin list", source_dir);
    if (system(cmd) != 0) {
        log_error("plugin list failed (python -m ami.cli)");
    }
}

void cmd_plugin_enable(const char *name) {
    char cmd[1024];
    snprintf(cmd, sizeof(cmd), "cd %s && python3 -m ami.cli plugin enable %s", source_dir, name);
    if (system(cmd) != 0) {
        log_error("plugin enable failed (python -m ami.cli)");
    }
}

void cmd_plugin_disable(const char *name) {
    char cmd[1024];
    snprintf(cmd, sizeof(cmd), "cd %s && python3 -m ami.cli plugin disable %s", source_dir, name);
    if (system(cmd) != 0) {
        log_error("plugin disable failed (python -m ami.cli)");
    }
}

void cmd_help(void) {
    printf("Usage: ami <command>\n");
    printf("Commands:\n");
    printf("  run                       Run python3 -m ami.main from source tree\n");
    printf("  update                    Checkout latest git tag + make test (no rollback yet)\n");
    printf("  gethead <user>/<repo>     git clone headspace into ~/.ami/plugins/\n");
    printf("  autostart enable          Create systemd user service for auto-startup\n");
    printf("  autostart disable         Stop and disable systemd service\n");
    printf("  plugin list|enable|disable  Delegates to python3 -m ami.cli (enabled_headspaces)\n");
}
