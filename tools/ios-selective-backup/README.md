# iOS Selective Backup Utility

A lightweight CLI tool that streams files from an iOS device over Apple's `MobileBackup2` protocol while selectively writing only matching target files to disk.

---

## Why This Exists

Standard iOS backups through iTunes, Finder, or `pymobiledevice3` are monolithic: backing up a 256 GB or 512 GB phone requires allocating equivalent storage on the host computer and can take hours.

This utility uses two techniques to solve this:
1. **Virtual Host Disk Reporting**: Overrides `DeviceLink.get_free_disk_space` to report virtualized free capacity, preventing iOS from rejecting the backup or demanding disk purges (`DLMessagePurgeDiskSpace`).
2. **In-Flight Stream Dropping**: As file streams arrive over the USB link, payloads matching `--regex` are written to disk; non-matching payloads (photos, videos, app sandboxes) are discarded in memory, writing **0 bytes to host storage**.

---

## Usage

```bash
pip install -r requirements.txt
```

### Extracting Bluetooth & Pairing Plists (default):
```bash
python selective_backup.py -o ./bluetooth_output
```

### Encrypted backups
If the device has backup encryption enabled, the tool prompts for the password (or reads `IOS_BACKUP_PASSWORD`). Passwords are not accepted as command-line arguments, which keeps them out of shell history.
```bash
python selective_backup.py -p -o ./secure_output
```

### Custom filters
The default filter matches Bluetooth and wireless-radio files only. Matching `keychain` data is sensitive, so you must ask for it explicitly:
```bash
python selective_backup.py -p -r "(?i).*(keychain|bluetooth).*" -o ./secure_output
```

## Notes

- `--virtual-tb` makes the tool report a large amount of free host disk space to the device so it does not abort the backup. Non-matching payloads are read and discarded, not stored.
- The tool patches `pymobiledevice3` internals (`DeviceLink.get_free_disk_space` / `purge_disk_space`). It was checked against pymobiledevice3 9.30.0 and the current development branch, but could break on future releases. It has not been tested against a physical device.
- Exit code is non-zero if the connection or backup session fails.

## Security and Privacy Notice

Files such as keychain and pairing plists contain sensitive credentials. Use this only on devices you own. Do not publish or commit extracted files (`backup_output/` is git-ignored by default).
