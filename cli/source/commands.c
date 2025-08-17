#include "commands.h"
#include "error.h"
#include "plugin.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <dirent.h>
#include <sys/stat.h>
#include <unistd.h>
#include <errno.h>

extern char *g_source_dir;
extern char *g_service_path;

static char *expand_path(const char *path) {
    if (path[0] != '~') {
        return strdup(path);
    }
    char *home = getenv("HOME");
    char *full = malloc(strlen(home) + strlen(path) + 1);
    sprintf(full, "%s%s", home, path + 1);  // Skip ~
    return full;
}

int cmd_run(void) {
    char cmd[1024];
    snprintf(cmd, sizeof(cmd), "python3 %s/ami.py", g_source_dir);  // Assume main Python at SOURCE_DIR/ami.py
    if (system(cmd) != 0) {
        log_error("Failed to run Python application");
        return 1;
    }
    return 0;
}

int cmd_update(void) {
    char cmd[1024];
    snprintf(cmd, sizeof(cmd), "git -C %s fetch && git -C %s checkout $(git -C %s describe --tags --abbrev=0) && make -C %s test", g_source_dir, g_source_dir, g_source_dir, g_source_dir);  // Checkout latest tag, run tests (assume 'make test' exists)
    if (system(cmd) != 0) {
        log_error("Update failed");
        return 1;
    }
    return 0;
}

int cmd_gethead(const char *user_repo) {
    return cmd_plugin_install(user_repo);
}

int cmd_autostart_enable(void) {
    char *service = expand_path(g_service_path);
    FILE *fp = fopen(service, "w");
    if (!fp) {
        log_error("Failed to create service file");
        free(service);
        return 1;
    }
    char cwd[1024];
    if (getcwd(cwd, sizeof(cwd)) == NULL) {
        log_error("Failed to get current working directory");
        fclose(fp);
        free(service);
        return 1;
    }
    fprintf(fp, "[Unit]\nDescription=AMI\n[Service]\nExecStart=%s/ami run\n[Install]\nWantedBy=default.target\n", cwd);
    fclose(fp);
    system("systemctl --user daemon-reload");
    if (system("systemctl --user enable --now ami.service") != 0) {
        log_error("Failed to enable autostart");
        free(service);
        return 1;
    }
    free(service);
    return 0;
}

int cmd_autostart_disable(void) {
    if (system("systemctl --user disable --now ami.service") != 0) {
        log_error("Failed to disable autostart");
        return 1;
    }
    char *service = expand_path(g_service_path);
    remove(service);
    system("systemctl --user daemon-reload");
    free(service);
    return 0;
}

int cmd_help(void) {
    printf("Usage: ami [options] <command>\n");
    printf("Options:\n");
    printf("  --source-dir <path>       Set source directory (default: compile-time)\n");
    printf("  --plugins-dir <path>      Set plugins directory (default: ~/.ami/plugins)\n");
    printf("  --config-path <path>      Set config path (default: ~/.ami/ami_config.yaml)\n");
    printf("  --service-path <path>     Set service path (default: ~/.config/systemd/user/ami.service)\n");
    printf("Commands:\n");
    printf("  run                       Execute the main Python application\n");
    printf("  update                    Update source repository to latest tag and run tests\n");
    printf("  gethead <user>/<repo>     Download headspace plugins from GitHub\n");
    printf("  autostart enable          Create systemd user service for auto-startup\n");
    printf("  autostart disable         Stop and disable systemd service\n");
    printf("  plugin list               List the Plugin name and its status\n");
    printf("  plugin enable <name>      Enable the Plugin in config.yaml\n");
    printf("  plugin disable <name>     Disable the Plugin in config.yaml\n");
    printf("  plugin install <url>      Install plugin from URL (or GitHub user/repo)\n");
    printf("  plugin remove <name>      Remove plugin\n");
    printf("  plugin update <name>      Update plugin via git pull\n");
    return 0;
}
