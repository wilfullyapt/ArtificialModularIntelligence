#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <ctype.h>

#ifndef SOURCE_DIR
#define SOURCE_DIR "."
#endif

void print_usage() {
    printf("Usage: ami [-v|--verbose] <command>\n");
    printf("Commands:\n");
    printf("  run                    Run the Python program\n");
    printf("  install_plugin <user>/<repo>  Install a plugin from GitHub\n");
    printf("  update                 Update the source repository and run tests\n");
}

int is_valid_repo(const char *repo) {
    char *slash = strchr(repo, '/');
    if (slash == NULL || slash == repo || slash[1] == '\0') {
        return 0;
    }
    if (strchr(slash + 1, '/') != NULL) {
        return 0;
    }
    for (const char *p = repo; *p; p++) {
        if (*p != '/' && !isalnum((unsigned char)*p) && *p != '-' && *p != '_') {
            return 0;
        }
    }
    return 1;
}

char *get_repo_name(const char *repo) {
    char *slash = strrchr(repo, '/');
    if (slash) {
        return slash + 1;
    }
    return NULL;
}

void run_python(int verbose) {
    if (verbose) {
        printf("Running Python program from source directory: %s\n", SOURCE_DIR);
    }
    char cmd[1024];
    snprintf(cmd, sizeof(cmd), "uv run --directory %s python -m ami.main", SOURCE_DIR);
    int ret = system(cmd);
    if (ret != 0) {
        fprintf(stderr, "Failed to run Python program\n");
        exit(1);
    }
}

void install_plugin(const char *repo, const char *home, int verbose) {
    char plugins_dir[1024];
    snprintf(plugins_dir, sizeof(plugins_dir), "%s/.ami/plugins", home);

    char url[1024];
    snprintf(url, sizeof(url), "https://github.com/%s.git", repo);

    char *repo_name = strrchr(repo, '/');
    if (repo_name) repo_name++;
    else repo_name = (char *)repo;

    size_t mkdir_cmd_len = strlen("mkdir -p ") + strlen(plugins_dir) + 1;
    char *mkdir_cmd = malloc(mkdir_cmd_len);
    if (!mkdir_cmd) {
        fprintf(stderr, "Memory allocation failed for mkdir_cmd\n");
        exit(1);
    }
    snprintf(mkdir_cmd, mkdir_cmd_len, "mkdir -p %s", plugins_dir);

    if (verbose) {
        printf("Creating plugins directory: %s\n", plugins_dir);
    }
    int ret = system(mkdir_cmd);
    free(mkdir_cmd);
    if (ret != 0) {
        fprintf(stderr, "Failed to create plugins directory\n");
        exit(1);
    }

    size_t clone_cmd_len = strlen("git clone ") + strlen(url) + strlen(" ") +
                           strlen(plugins_dir) + strlen("/") + strlen(repo_name) + 1;
    char *clone_cmd = malloc(clone_cmd_len);
    if (!clone_cmd) {
        fprintf(stderr, "Memory allocation failed for clone_cmd\n");
        exit(1);
    }
    snprintf(clone_cmd, clone_cmd_len, "git clone %s %s/%s", url, plugins_dir, repo_name);

    if (verbose) {
        printf("Cloning repository: %s into %s/%s\n", url, plugins_dir, repo_name);
    }
    ret = system(clone_cmd);
    free(clone_cmd);
    if (ret != 0) {
        fprintf(stderr, "Failed to clone repository\n");
        exit(1);
    }
}

char *get_home() {
    char *home = getenv("HOME");
    if (!home) {
        fprintf(stderr, "HOME environment variable not set\n");
        exit(1);
    }

    return home;
}

void update_source(int verbose) {

    if (verbose) {
        printf("Updating source in directory: %s\n", SOURCE_DIR);
    }
    if (chdir(SOURCE_DIR) != 0) {
        fprintf(stderr, "Failed to change to source directory\n");
        exit(1);
    }

    if (verbose) {
        printf("Fetching tags\n");
    }
    system("git fetch --tags");
    FILE *fp = popen("git tag -l | sort -V | tail -n 1", "r");
    if (!fp) {
        fprintf(stderr, "Failed to get latest tag\n");
        exit(1);
    }
    char latest_tag[256];
    if (fgets(latest_tag, sizeof(latest_tag), fp) == NULL) {
        fprintf(stderr, "No tags found\n");
        pclose(fp);
        exit(1);
    }
    pclose(fp);
    latest_tag[strcspn(latest_tag, "\n")] = 0;

    if (verbose) {
        printf("Latest tag: %s\n", latest_tag);
    }
    char cmd[1024];
    snprintf(cmd, sizeof(cmd), "git checkout %s", latest_tag);

    if (verbose) {
        printf("Checking out tag: %s\n", latest_tag);
    }
    int ret = system(cmd);
    if (ret != 0) {
        fprintf(stderr, "Failed to checkout latest tag\n");
        exit(1);
    }
    snprintf(cmd, sizeof(cmd), "uv run pytest");

    if (verbose) {
        printf("Running tests\n");
    }
    ret = system(cmd);
    if (ret != 0) {
        fprintf(stderr, "Tests failed\n");
        exit(1);
    }
}

int main(int argc, char *argv[]) {

    int verbose = 0;
    if (argc > 1 && (strcmp(argv[1], "-v") == 0 || strcmp(argv[1], "--verbose") == 0)) {
        verbose = 1;
        argc--;
        argv++;
    }

    if (argc < 2) {
        print_usage();
        exit(1);
    }

    if (strcmp(argv[1], "run") == 0) {
        if (argc != 2) {
            print_usage();
            exit(1);
        }
        run_python(verbose);

    } else if (strcmp(argv[1], "install_plugin") == 0) {
        if (argc != 3) {
            print_usage();
            exit(1);
        }
        if (!is_valid_repo(argv[2])) {
            fprintf(stderr, "Invalid repository format\n");
            exit(1);
        }
        install_plugin(argv[2], get_home(), verbose);

    } else if (strcmp(argv[1], "update") == 0) {
        if (argc != 2) {
            print_usage();
            exit(1);
        }
        update_source(verbose);

    } else {
        print_usage();
        exit(1);
    }

    return 0;
}
