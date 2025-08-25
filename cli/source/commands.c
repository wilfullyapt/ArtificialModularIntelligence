#include "commands.h"
#include "error.h"
#include "plugin.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdbool.h>
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

static char *capture_output(const char *cmd) {
    FILE *fp = popen(cmd, "r");
    if (!fp) return NULL;
    char buf[1024];
    if (fgets(buf, sizeof(buf), fp) == NULL) {
        pclose(fp);
        return NULL;
    }
    pclose(fp);
    buf[strcspn(buf, "\n")] = '\0';
    return strdup(buf);
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

int cmd_safe_update(void) {
    char ami_home[1024];
    snprintf(ami_home, sizeof(ami_home), "%s/.ami", getenv("HOME"));
    if (access(ami_home, F_OK) != 0) {
        if (mkdir(ami_home, 0755) != 0) {
            log_error("Failed to create ~/.ami directory");
            return 1;
        }
    }
    char *last_good_path = expand_path("~/.ami/last_good_tag");
    char git_cmd[1024];
    snprintf(git_cmd, sizeof(git_cmd), "git -C %s describe --tags --abbrev=0", g_source_dir);
    char *current_tag = capture_output(git_cmd);
    if (!current_tag) {
        log_error("Failed to get current tag");
        free(last_good_path);
        return 1;
    }
    FILE *fp = fopen(last_good_path, "w");
    if (!fp) {
        log_error("Failed to write last good tag");
        free(current_tag);
        free(last_good_path);
        return 1;
    }
    fprintf(fp, "%s", current_tag);
    fclose(fp);

    snprintf(git_cmd, sizeof(git_cmd), "git -C %s fetch --tags", g_source_dir);
    if (system(git_cmd) != 0) {
        log_error("Failed to fetch tags");
        free(current_tag);
        free(last_good_path);
        return 1;
    }
    snprintf(git_cmd, sizeof(git_cmd), "git -C %s tag -l --sort=-version:refname | head -n 1", g_source_dir);
    char *latest_tag = capture_output(git_cmd);
    if (!latest_tag) {
        log_error("Failed to get latest tag");
        free(current_tag);
        free(last_good_path);
        return 1;
    }
    if (strcmp(current_tag, latest_tag) == 0) {
        log_info("Already on latest tag");
        free(current_tag);
        free(latest_tag);
        free(last_good_path);
        return 0;
    }
    snprintf(git_cmd, sizeof(git_cmd), "git -C %s checkout %s", g_source_dir, latest_tag);
    if (system(git_cmd) != 0) {
        log_error("Failed to checkout latest tag");
        cmd_rollback();
        free(current_tag);
        free(latest_tag);
        free(last_good_path);
        return 1;
    }
    char cli_dir[1024];
    if (getcwd(cli_dir, sizeof(cli_dir)) == NULL) {
        log_error("Failed to get CLI directory");
        cmd_rollback();
        free(current_tag);
        free(latest_tag);
        free(last_good_path);
        return 1;
    }
    bool needs_recompile = false;
    snprintf(git_cmd, sizeof(git_cmd), "git -C %s diff %s..HEAD -- cli/source/ cli/include/ Makefile | wc -l", g_source_dir, current_tag);
    char *diff_count_str = capture_output(git_cmd);
    if (diff_count_str) {
        int diff_count = atoi(diff_count_str);
        free(diff_count_str);
        if (diff_count > 0) {
            needs_recompile = true;
        }
    } else {
        log_error("Failed to check diff for CLI files");
        cmd_rollback();
        free(current_tag);
        free(latest_tag);
        free(last_good_path);
        return 1;
    }
    bool recompiled = false;
    if (needs_recompile) {
        char *backup_cmd = NULL;
        int len = asprintf(&backup_cmd, "cp %s/ami %s/ami_prev", cli_dir, cli_dir);
        if (len == -1) {
            log_error("Failed to allocate memory for backup command");
            cmd_rollback();
            free(current_tag);
            free(latest_tag);
            free(last_good_path);
            return 1;
        }
        if (system(backup_cmd) != 0) {
            log_error("Failed to backup binary");
            free(backup_cmd);
            cmd_rollback();
            free(current_tag);
            free(latest_tag);
            free(last_good_path);
            return 1;
        }
        free(backup_cmd);
        if (system("make clean && make") != 0) {
            log_error("Failed to recompile binary");
            char *rollback_cmd = NULL;
            int len = asprintf(&rollback_cmd, "%s/ami_prev rollback", cli_dir);
            if (len == -1) {
                log_error("Failed to allocate memory for rollback command");
                free(current_tag);
                free(latest_tag);
                free(last_good_path);
                return 1;
            }
            system(rollback_cmd);
            free(rollback_cmd);
            free(current_tag);
            free(latest_tag);
            free(last_good_path);
            return 1;
        }
        recompiled = true;
    }
    char test_cmd[1024];
    snprintf(test_cmd, sizeof(test_cmd), "make -C %s test", g_source_dir);
    if (system(test_cmd) != 0) {
        log_error("Tests failed");
        if (recompiled) {
            char *rollback_cmd = NULL;
            int len = asprintf(&rollback_cmd, "%s/ami_prev rollback", cli_dir);
            if (len == -1) {
                log_error("Failed to allocate memory for rollback command");
                free(current_tag);
                free(latest_tag);
                free(last_good_path);
                return 1;
            }
            system(rollback_cmd);
            free(rollback_cmd);
        } else {
            cmd_rollback();
        }
        free(current_tag);
        free(latest_tag);
        free(last_good_path);
        return 1;
    }
    fp = fopen(last_good_path, "w");
    if (fp) {
        fprintf(fp, "%s", latest_tag);
        fclose(fp);
    } else {
        log_error("Failed to update last good tag (non-fatal)");
    }
    free(current_tag);
    free(latest_tag);
    free(last_good_path);
    return 0;
}

int cmd_rollback(void) {
    char *last_good_path = expand_path("~/.ami/last_good_tag");
    FILE *fp = fopen(last_good_path, "r");
    if (!fp) {
        log_error("No last good tag found");
        free(last_good_path);
        return 1;
    }
    char prev_tag[1024];
    if (fgets(prev_tag, sizeof(prev_tag), fp) == NULL) {
        log_error("Failed to read last good tag");
        fclose(fp);
        free(last_good_path);
        return 1;
    }
    fclose(fp);
    prev_tag[strcspn(prev_tag, "\n")] = '\0';
    char *git_cmd = NULL;
    int len = asprintf(&git_cmd, "git -C %s checkout %s", g_source_dir, prev_tag);
    if (len == -1) {
        log_error("Failed to allocate memory for git command.");
        free(last_good_path);
        return 1;
    }
    if (system(git_cmd) != 0) {
        log_error("Failed to checkout previous tag");
        free(git_cmd);
        free(last_good_path);
        return 1;
    }
    free(git_cmd);
    if (system("make clean && make") != 0) {
        log_error("Failed to rebuild binary after rollback");
        free(last_good_path);
        return 1;
    }
    char cli_dir[1024];
    if (getcwd(cli_dir, sizeof(cli_dir)) != NULL) {
        char *prev_bin = NULL;
        int len =asprintf(&prev_bin, "%s/ami_prev", cli_dir);
        if (len == -1) {
            log_error("Failed to allocate memory for previous binary path");
            free(prev_bin);
            return 1;
        }
        if (access(prev_bin, F_OK) == 0) {
            remove(prev_bin);
        }
        free(prev_bin);
    }
    free(last_good_path);
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
    printf("  safe-update               Safely update to latest tag with rollback on failure\n");
    printf("  rollback                  Rollback to last good tag\n");
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
