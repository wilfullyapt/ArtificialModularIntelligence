
#include "test_framework.h"
#include <stdio.h>
#include <string.h>

TEST(test_ami_help) {
    FILE *fp = popen("./ami help", "r");
    char buf[1024] = {0};
    fread(buf, 1, sizeof(buf) - 1, fp);
    pclose(fp);
    const char *expected = "Usage: ami [options] <command>\n"
    "Options:\n"
    "  --source-dir <path>       Set source directory (default: compile-time)\n"
    "  --plugins-dir <path>      Set plugins directory (default: ~/.ami/plugins)\n"
    "  --config-path <path>      Set config path (default: ~/.ami/ami_config.yaml)\n"
    "  --service-path <path>     Set service path (default: ~/.config/systemd/user/ami.service)\n"
    "Commands:\n"
    "  run                       Execute the main Python application\n"
    "  update                    Update source repository to latest tag and run tests\n"
    "  safe-update               Safely update to latest tag with rollback on failure\n"
    "  rollback                  Rollback to last good tag\n"
    "  gethead <user>/<repo>     Download headspace plugins from GitHub\n"
    "  autostart enable          Create systemd user service for auto-startup\n"
    "  autostart disable         Stop and disable systemd service\n"
    "  plugin list               List the Plugin name and its status\n"
    "  plugin enable <name>      Enable the Plugin in config.yaml\n"
    "  plugin disable <name>     Disable the Plugin in config.yaml\n"
    "  plugin install <url>      Install plugin from URL (or GitHub user/repo)\n"
    "  plugin remove <name>      Remove plugin\n"
    "  plugin update <name>      Update plugin via git pull\n";
    ASSERT_STRING_EQUAL(expected, buf, "help output correct");
}

void run_e2e_tests(void) {
    RUN_TEST(test_ami_help);
}
