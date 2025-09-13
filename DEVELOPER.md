# Information for Developers



## Logging


### Python AMI


### Binary AMI

**Relivent C Code**:

```c
void init_logging(const char *program_name, int use_syslog_flag) {
    if (use_syslog) {
        openlog(program_name, LOG_PID | LOG_CONS, LOG_USER);
    }
}
static void log_message(int priority, const char *format, va_list args) {
    if (use_syslog) {
        syslog(priority, "%s", buffer);
    }
}
```

**Logging Setup in Debian System**:
*This is what we did to make sure the system works the way we want it to.*

1. Create the rsyslog Config File (requires root access):
    - `sudo nano /etc/rsyslog.d/10-ami.conf`
    - Add the following content:
```
if $programname == "ami" then {
    action(type="omfile" file="/var/log/ami.log")
    stop
}
```

2. (**Optional**) Check and validate the logging config
	- `sudo rsyslogd -f /etc/rsyslog.conf -N1`

3. Set Permissions and Ownership for the Log File:
    - `rsyslog` runs as root or a dedicated user (often `syslog:adm`), so it can create/write to `/var/log/ami.log` automatically.
    - To ensure it's created with proper permissions (readable by your user for debugging) run these commands
    - `sudo touch /var/log/ami.log`
    - `sudo chown syslog:adm /var/log/ami.log`  *Adjust if your distro uses a different user/group (check with `ps aux | grep rsyslog`)*
    - `sudo chmod 644 /var/log/ami.log`
        
4. Restart rsyslog to Apply Changes:
	- `sudo systemctl restart rsyslog`

