#include "plugin.h"
#include "error.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <dirent.h>
#include <sys/stat.h>
#include <unistd.h>
#include <errno.h>
#include <yaml.h>
#include <curl/curl.h>
#include <ctype.h>

extern char *g_plugins_dir;
extern char *g_config_path;

static char *expand_path(const char *path) {
    if (path[0] != '~') {
        return strdup(path);
    }
    char *home = getenv("HOME");
    char *full = malloc(strlen(home) + strlen(path) + 1);
    sprintf(full, "%s%s", home, path + 1);
    return full;
}

static int load_config(yaml_document_t *doc) {
    char *config = expand_path(g_config_path);
    FILE *fp = fopen(config, "r");
    free(config);
    if (!fp) {
        return 1;  // No config
    }
    yaml_parser_t parser;
    if (!yaml_parser_initialize(&parser)) {
        fclose(fp);
        return 1;
    }
    yaml_parser_set_input_file(&parser, fp);
    if (!yaml_parser_load(&parser, doc)) {
        yaml_parser_delete(&parser);
        fclose(fp);
        return 1;
    }
    yaml_parser_delete(&parser);
    fclose(fp);
    return 0;
}

static int save_config(yaml_document_t *doc) {
    char *config = expand_path(g_config_path);
    FILE *fp = fopen(config, "w");
    free(config);
    if (!fp) {
        return 1;
    }
    yaml_emitter_t emitter;
    if (!yaml_emitter_initialize(&emitter)) {
        fclose(fp);
        return 1;
    }
    yaml_emitter_set_output_file(&emitter, fp);
    yaml_emitter_dump(&emitter, doc);
    yaml_emitter_delete(&emitter);
    fclose(fp);
    return 0;
}

static void remove_key(yaml_document_t *doc, yaml_node_t *mapping, const char *key_name) {
    yaml_node_pair_t *pair = mapping->data.mapping.pairs.start;
    while (pair < mapping->data.mapping.pairs.top) {
        yaml_node_t *key = yaml_document_get_node(doc, pair->key);
        if (key->type == YAML_SCALAR_NODE && strcmp((char *)key->data.scalar.value, key_name) == 0) {
            // Shift remaining pairs
            memmove(pair, pair + 1, (mapping->data.mapping.pairs.top - (pair + 1)) * sizeof(yaml_node_pair_t));
            mapping->data.mapping.pairs.top--;
            continue;
        }
        pair++;
    }
}

static int set_plugin_status(const char *name, const char *status) {
    yaml_document_t doc;
    int loaded = load_config(&doc);
    if (loaded != 0) {
        yaml_document_initialize(&doc, NULL, NULL, NULL, 1, 1);
    }
    yaml_node_t *root = yaml_document_get_root_node(&doc);
    if (!root || root->type != YAML_MAPPING_NODE) {
        yaml_node_t *new_root = yaml_document_add_mapping(&doc, NULL, YAML_BLOCK_MAPPING_STYLE);
        if (loaded == 0) yaml_document_delete(&doc);  // Error handling
        root = new_root;
    }
    remove_key(&doc, root, name);
    yaml_node_t *key_node = yaml_document_add_scalar(&doc, NULL, (yaml_char_t *)name, -1, YAML_PLAIN_SCALAR_STYLE);
    yaml_node_t *val_node = yaml_document_add_scalar(&doc, NULL, (yaml_char_t *)status, -1, YAML_PLAIN_SCALAR_STYLE);
    yaml_document_append_mapping_pair(&doc, root, key_node, val_node);
    int ret = save_config(&doc);
    yaml_document_delete(&doc);
    return ret;
}

int cmd_plugin_enable(const char *name) {
    if (set_plugin_status(name, "true") != 0) {
        log_error("Failed to enable plugin");
        return 1;
    }
    return 0;
}

int cmd_plugin_disable(const char *name) {
    if (set_plugin_status(name, "false") != 0) {
        log_error("Failed to disable plugin");
        return 1;
    }
    return 0;
}

static const char *get_status(yaml_document_t *doc, const char *name) {
    yaml_node_t *root = yaml_document_get_root_node(doc);
    if (!root || root->type != YAML_MAPPING_NODE) return "unknown";
    for (yaml_node_pair_t *pair = root->data.mapping.pairs.start; pair < root->data.mapping.pairs.top; pair++) {
        yaml_node_t *key = yaml_document_get_node(doc, pair->key);
        if (key->type == YAML_SCALAR_NODE && strcmp((char *)key->data.scalar.value, name) == 0) {
            yaml_node_t *val = yaml_document_get_node(doc, pair->value);
            if (val->type == YAML_SCALAR_NODE) {
                if (strcmp((char *)val->data.scalar.value, "true") == 0) return "enabled";
                if (strcmp((char *)val->data.scalar.value, "false") == 0) return "disabled";
            }
        }
    }
    return "unknown";
}

int cmd_plugin_list(void) {
    char *plugins = expand_path(g_plugins_dir);
    DIR *dir = opendir(plugins);
    if (!dir) {
        log_error("Failed to open plugins dir");
        free(plugins);
        return 1;
    }
    yaml_document_t doc;
    int has_config = (load_config(&doc) == 0);
    struct dirent *entry;
    while ((entry = readdir(dir))) {
        if (entry->d_type == DT_DIR && entry->d_name[0] != '.') {
            const char *status = "unknown";
            if (has_config) {
                status = get_status(&doc, entry->d_name);
            }
            printf("Plugin: %s - Status: %s\n", entry->d_name, status);
        }
    }
    closedir(dir);
    if (has_config) yaml_document_delete(&doc);
    free(plugins);
    return 0;
}

static int valid_user_repo(const char *user_repo) {
    int slash_count = 0;
    for (const char *p = user_repo; *p; p++) {
        if (*p == '/') slash_count++;
        if (!isalnum(*p) && *p != '-' && *p != '_' && *p != '/') return 0;
    }
    return slash_count == 1;
}

static int repo_exists(const char *user_repo) {
    char url[1024];
    snprintf(url, sizeof(url), "https://github.com/%s", user_repo);
    CURL *curl = curl_easy_init();
    if (!curl) return 0;
    curl_easy_setopt(curl, CURLOPT_URL, url);
    curl_easy_setopt(curl, CURLOPT_NOBODY, 1L);
    curl_easy_setopt(curl, CURLOPT_FAILONERROR, 1L);
    CURLcode res = curl_easy_perform(curl);
    long http_code = 0;
    if (res == CURLE_OK) {
        curl_easy_getinfo(curl, CURLINFO_RESPONSE_CODE, &http_code);
    }
    curl_easy_cleanup(curl);
    return (res == CURLE_OK && http_code == 200);
}

int cmd_plugin_install(const char *arg) {
    char url[1024];
    if (strstr(arg, "://")) {
        strncpy(url, arg, sizeof(url) - 1);
    } else {
        snprintf(url, sizeof(url), "https://github.com/%s", arg);
    }
    const char *user_repo = NULL;
    if (strstr(url, "https://github.com/")) {
        user_repo = url + strlen("https://github.com/");
        if (!valid_user_repo(user_repo)) {
            log_error("Invalid user/repo format");
            return 1;
        }
        if (!repo_exists(user_repo)) {
            log_error("GitHub repo not found");
            return 1;
        }
    }
    // Extract repo_name
    char *repo_name = strdup(strrchr(url, '/') + 1);
    char *dot_git = strstr(repo_name, ".git");
    if (dot_git) *dot_git = '\0';
    char *plugins = expand_path(g_plugins_dir);
    char dir[1024];
    snprintf(dir, sizeof(dir), "%s/%s", plugins, repo_name);
    if (access(dir, F_OK) == 0) {
        log_error("Plugin directory already exists");
        free(repo_name);
        free(plugins);
        return 1;
    }
    char cmd[1024];
    snprintf(cmd, sizeof(cmd), "git clone %s %s", url, dir);
    if (system(cmd) != 0) {
        log_error("Failed to clone repository");
        free(repo_name);
        free(plugins);
        return 1;
    }
    free(repo_name);
    free(plugins);
    return 0;
}

int cmd_plugin_remove(const char *name) {
    char *plugins = expand_path(g_plugins_dir);
    char dir[1024];
    snprintf(dir, sizeof(dir), "%s/%s", plugins, name);
    if (access(dir, F_OK) != 0) {
        log_error("Plugin not found");
        free(plugins);
        return 1;
    }
    char cmd[1024];
    snprintf(cmd, sizeof(cmd), "rm -rf %s", dir);
    if (system(cmd) != 0) {
        log_error("Failed to remove plugin");
        free(plugins);
        return 1;
    }
    // Disable in config if exists
    cmd_plugin_disable(name);
    free(plugins);
    return 0;
}

int cmd_plugin_update(const char *name) {
    char *plugins = expand_path(g_plugins_dir);
    char dir[1024];
    snprintf(dir, sizeof(dir), "%s/%s", plugins, name);
    if (access(dir, F_OK) != 0) {
        log_error("Plugin not found");
        free(plugins);
        return 1;
    }
    char gitdir[1024];
    snprintf(gitdir, sizeof(gitdir), "%s/.git", dir);
    if (access(gitdir, F_OK) != 0) {
        log_error("Plugin is not a git repository");
        free(plugins);
        return 1;
    }
    char cmd[1024];
    snprintf(cmd, sizeof(cmd), "git -C %s pull", dir);
    if (system(cmd) != 0) {
        log_error("Failed to update plugin");
        free(plugins);
        return 1;
    }
    free(plugins);
    return 0;
}
