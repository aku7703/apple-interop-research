#!/usr/bin/env python3
"""
iOS Selective Backup Tool

Streams a MobileBackup2 backup from a USB-connected iOS device and keeps only
files whose name/domain matches a regex. Non-matching payloads (photos, videos,
app data) are drained and not stored, so little disk space is needed.

Only use this on devices you own. Extracted files can contain sensitive data.
"""

import argparse
import asyncio
import getpass
import os
import re
import sys
from pathlib import Path

from pymobiledevice3.lockdown import create_using_usbmux
from pymobiledevice3.services.device_link import DeviceLink
from pymobiledevice3.services.mobilebackup2 import BackupFile, Mobilebackup2Service

DEFAULT_REGEX = r"(?i).*(bluetooth|wirelessradio).*"
PASSWORD_ENV = "IOS_BACKUP_PASSWORD"


def parse_args():
    parser = argparse.ArgumentParser(description="Selective iOS backup tool.")
    parser.add_argument("-o", "--output", default="./backup_output", help="Directory to save preserved files.")
    parser.add_argument(
        "-r",
        "--regex",
        default=DEFAULT_REGEX,
        help="Regex matching file/domain names to preserve. Default: Bluetooth and wireless-radio files. "
        "Matching 'keychain' is sensitive and must be requested explicitly.",
    )
    parser.add_argument(
        "-p",
        "--password",
        action="store_true",
        help=f"Prompt for the backup password (or set ${PASSWORD_ENV}). "
        "Passwords are never accepted on the command line, to keep them out of shell history.",
    )
    parser.add_argument("--virtual-tb", type=int, default=10, help="Virtual disk capacity (TB) reported to iOS.")
    return parser.parse_args()


def get_password(prompt_requested: bool) -> str:
    env_value = os.environ.get(PASSWORD_ENV, "")
    if env_value:
        return env_value
    if prompt_requested:
        return getpass.getpass("Backup password: ")
    return ""


def setup_disk_virtualization(capacity_tb: int):
    """
    Overrides DeviceLink host space checks so iOS does not abort when
    the device library exceeds actual free disk space on the host.
    """
    capacity_bytes = capacity_tb * (1024**4)

    async def fake_get_free_disk_space(self, _message):
        await self.status_response(0, status_dict=capacity_bytes)

    async def fake_purge_disk_space(self, _message):
        await self.status_response(0)

    DeviceLink.get_free_disk_space = fake_get_free_disk_space
    DeviceLink.purge_disk_space = fake_purge_disk_space


def build_filter(regex_pattern: str):
    compiled = re.compile(regex_pattern)
    stats = {"preserved": 0, "dropped": 0}

    def _filter(backup_file: BackupFile) -> bool:
        candidates = []
        if backup_file.device_name:
            candidates.append(backup_file.device_name)
        if backup_file.relative_path:
            candidates.append(backup_file.relative_path)
        if backup_file.domain:
            candidates.append(backup_file.domain)
            if backup_file.relative_path:
                candidates.append(f"{backup_file.domain}/{backup_file.relative_path}")

        if any(compiled.search(c) for c in candidates):
            stats["preserved"] += 1
            name = backup_file.device_name or backup_file.relative_path or "file"
            print(f"[PRESERVE] {name}")
            return True

        stats["dropped"] += 1
        if stats["dropped"] % 250 == 0:
            print(f"[DROPPED] {stats['dropped']} non-target files (not stored)...")
        return False

    return _filter, stats


async def main():
    args = parse_args()
    try:
        re.compile(args.regex)
    except re.error as exc:
        print(f"Error: invalid --regex: {exc}")
        return 2

    password = get_password(args.password)
    setup_disk_virtualization(args.virtual_tb)
    filter_fn, stats = build_filter(args.regex)

    output_path = Path(args.output).resolve()
    output_path.mkdir(parents=True, exist_ok=True)

    print("Connecting to device via usbmux...")
    try:
        ld = await create_using_usbmux()
    except Exception as e:
        print(f"Error connecting to device: {e}")
        return 1

    print(f"Connected to device [{ld.udid}] ({ld.product_type} {ld.product_version})")
    will_encrypt = await ld.get_value(domain="com.apple.mobile.backup", key="WillEncrypt")
    print(f"Device backup encryption status: {will_encrypt}")

    if will_encrypt and not password:
        print(f"Error: Device backup encryption is enabled. Use --password or set ${PASSWORD_ENV}.")
        return 1

    def progress_callback(pct):
        print(f"Overall Progress: {pct}%")

    print(f"Starting selective backup to: {output_path}")
    print(f"Filter regex: {args.regex}")

    exit_code = 0
    async with Mobilebackup2Service(ld) as client:
        try:
            await client.backup(
                full=True,
                backup_directory=str(output_path),
                progress_callback=progress_callback,
                filter_callback=filter_fn,
                password=password,
                unback=False,
            )
            print("\nBackup session completed successfully.")
        except Exception as e:
            print(f"\nSession terminated: {e}")
            exit_code = 1

    print("\n--- Summary ---")
    print(f"Files preserved on disk : {stats['preserved']}")
    print(f"Files dropped (not stored): {stats['dropped']}")
    return exit_code


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
