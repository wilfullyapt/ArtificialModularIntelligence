# systemd (user)

```bash
python -m ami.cli init
python -m ami.cli systemd install
systemctl --user daemon-reload
systemctl --user enable --now ami.service
# linger so kiosk survives logout (optional, needs root once):
# sudo loginctl enable-linger $USER
journalctl --user -u ami.service -f
```
