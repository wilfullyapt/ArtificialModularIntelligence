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
    snprintf(cmd, sizeof(cmd), "python3 %s/ami.py", source_dir);  // Assume main Python at SOURCE_DIR/ami.py
    if (system(cmd) != 0) {
        log_error("Failed to run Python application");
    }
}

void cmd_update(void) {
    char cmd[1024];
    snprintf(cmd, sizeof(cmd), "git -C %s fetch && git -C %s checkout $(git -C %s describe --tags --abbrev=0) && make -C %s test", source_dir, source_dir, source_dir, source_dir);  // Checkout latest tag, run tests (assume 'make test' exists)
    if (system(cmd) != 0) {
        log_error("Update failed");
    }
}

void cmd_gethead(const char *user_repo) {
    char *plugins = expand_path(PLUGINS_DIR);
    char cmd[1024];
    snprintf(cmd, sizeof(cmd), "git clone https://github.com/%s %s/%s", user_repo, plugins, strrchr(user_repo, '/') + 1);
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
    char *plugins = expand_path(PLUGINS_DIR);
    DIR *dir = opendir(plugins);
    if (!dir) {
        log_error("Failed to open plugins dir");
        free(plugins);
        return;
    }
    struct dirent *entry;
    while ((entry = readdir(dir))) {
        if (entry->d_type == DT_DIR && entry->d_name[0] != '.') {
            // Get status from YAML
            char status[10] = "unknown";
            char *config = expand_path(CONFIG_PATH);
            FILE *fp = fopen(config, "r");
            if (fp) {
                char line[512];
                char target[512];
                snprintf(target, sizeof(target), "  %s: ", entry->d_name);
                while (fgets(line, sizeof(line), fp)) {
                    if (strstr(line, target)) {
                        if (strstr(line, "true")) strcpy(status, "enabled");
                        else if (strstr(line, "false")) strcpy(status, "disabled");
                        break;
                    }
                }
                fclose(fp);
            }
            free(config);
            printf("Plugin: %s - Status: %s\n", entry->d_name, status);
        }
    }
    closedir(dir);
    free(plugins);
}

void cmd_plugin_enable(const char *name) {
    // Note: Assuming enable sets to true (your description says "Disable" but seems like a typo; adjust if needed)
    char *config = expand_path(CONFIG_PATH);
    FILE *fp = fopen(config, "r");
    if (!fp) {
        log_error("Failed to open config");
        free(config);
        return;
    }
    char temp_file[] = "/tmp/ami_config_temp.yaml";
    FILE *temp = fopen(temp_file, "w");
    if (!temp) {
        log_error("Failed to create temp file");
        fclose(fp);
        free(config);
        return;
    }
    char line[256];
    char target[256];
    snprintf(target, sizeof(target), "  %s: false", name);
    int found = 0;
    while (fgets(line, sizeof(line), fp)) {
        if (strstr(line, target)) {
            fprintf(temp, "  %s: true\n", name);
            found = 1;
        } else {
            fputs(line, temp);
        }
    }
    if (!found) {
        fprintf(temp, "  %s: true\n", name);  // Add if not found
    }
    fclose(fp);
    fclose(temp);
    rename(temp_file, config);
    free(config);
}

void cmd_plugin_disable(const char *name) {
    // Similar to enable, but set to false (your description says "Enable" but seems typo)
    char *config = expand_path(CONFIG_PATH);
    FILE *fp = fopen(config, "r");
    if (!fp) {
        log_error("Failed to open config");
        free(config);
        return;
    }
    char temp_file[] = "/tmp/ami_config_temp.yaml";
    FILE *temp = fopen(temp_file, "w");
    if (!temp) {
        log_error("Failed to create temp file");
        fclose(fp);
        free(config);
        return;
    }
    char line[256];
    char target[256];
    snprintf(target, sizeof(target), "  %s: true", name);
    int found = 0;
    while (fgets(line, sizeof(line), fp)) {
        if (strstr(line, target)) {
            fprintf(temp, "  %s: false\n", name);
            found = 1;
        } else {
            fputs(line, temp);
        }
    }
    if (!found) {
        fprintf(temp, "  %s: false\n", name);  // Add if not found
    }
    fclose(fp);
    fclose(temp);
    rename(temp_file, config);
    free(config);
}

void cmd_help(void) {
    printf("Usage: ami <command>\n");
    printf("Commands:\n");
    printf("  run                       Execute the main Python application\n");
    printf("  update                    Update source repository to latest tag and run tests\n");
    printf("  gethead <user>/<repo>     Download headspace plugins from GitHub\n");
    printf("  autostart enable          Create systemd user service for auto-startup\n");
    printf("  autostart disable         Stop and disable systemd service\n");
    printf("  plugin list               List the Plugin name and its status\n");
    printf("  plugin enable <name>      Enable the Plugin in config.yaml\n");
    printf("  plugin disable <name>     Disable the Plugin in config.yaml\n");
}
