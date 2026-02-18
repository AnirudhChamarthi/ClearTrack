#!/usr/bin/env python3
"""
ClearTrack Uninstall Script
Removes ClearTrack from your system: Git alias, wrapper scripts, and optionally config.
Does not delete your contribution log file. Keeps only your contribution data.
"""

import json
import subprocess
import sys
from pathlib import Path
import platform

CONFIG_FILE = ".cleartrack_config.json"
CLEARTRACK_FOLDER = ".cleartrack"  # Wrapper scripts folder


def get_config_path():
    """Path to the config file in the user's home directory."""
    return Path.home() / CONFIG_FILE


def load_config():
    """Load config if it exists (to get log path and script dir before removal)."""
    path = get_config_path()
    if path.exists():
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return None


def get_cleartrack_folder():
    """Path to the .cleartrack folder (wrappers live here)."""
    return Path.home() / CLEARTRACK_FOLDER


def get_batch_wrapper_path():
    """Path to the Windows batch wrapper (in .cleartrack)."""
    return get_cleartrack_folder() / "cleartrack_push.bat"


def get_bash_wrapper_path():
    """Path to the Unix bash wrapper (in .cleartrack)."""
    return get_cleartrack_folder() / "cleartrack_push.sh"


def get_legacy_batch_path():
    """Old location (pre-.cleartrack). Remove for migration."""
    return Path.home() / "cleartrack_push.bat"


def get_legacy_bash_path():
    """Old location (pre-.cleartrack). Remove for migration."""
    return Path.home() / ".cleartrack_push.sh"


def remove_git_alias(uninstalled):
    """Remove the global push-tracked alias. Appends to uninstalled list."""
    try:
        result = subprocess.run(
            ["git", "config", "--global", "--get", "alias.push-tracked"],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            return True
        subprocess.run(
            ["git", "config", "--global", "--unset", "alias.push-tracked"],
            check=True,
            capture_output=True,
        )
        uninstalled.append("Git alias: push-tracked")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Warning: Could not remove Git alias: {e}", file=sys.stderr)
        return False


def remove_cleartrack_wrappers(uninstalled):
    """Remove only ClearTrack wrapper files from .cleartrack. Never deletes the
    entire folder - user may have other files there. Graceful if folder missing.
    """
    folder = get_cleartrack_folder()
    if not folder.exists():
        print(f"ClearTrack folder not found at {folder}. Skipping.")
        return
    wrappers = [
        folder / "cleartrack_push.bat",
        folder / "cleartrack_push.sh",
    ]
    for path in wrappers:
        if path.exists() and path.is_file():
            try:
                path.unlink()
                uninstalled.append(str(path))
            except OSError as e:
                print(f"Warning: Could not remove {path}: {e}", file=sys.stderr)
    # Remove folder only if it is now empty (no other user files)
    try:
        if folder.exists() and not any(folder.iterdir()):
            folder.rmdir()
            uninstalled.append(str(folder) + " (empty folder removed)")
    except OSError:
        pass  # Folder not empty or permission issue - leave it


def remove_legacy_wrappers(uninstalled):
    """Remove wrappers from old locations (pre-.cleartrack migration)."""
    for path in (get_legacy_batch_path(), get_legacy_bash_path()):
        if path.exists():
            try:
                path.unlink()
                uninstalled.append(str(path) + " (legacy)")
            except OSError as e:
                print(f"Warning: Could not remove {path}: {e}", file=sys.stderr)


def remove_config(uninstalled):
    """Remove the config file. Appends to uninstalled list if removed."""
    path = get_config_path()
    if not path.exists():
        return True
    try:
        path.unlink()
        uninstalled.append(str(path))
        return True
    except OSError as e:
        print(f"Warning: Could not remove config: {e}", file=sys.stderr)
        return False


def main():
    uninstalled = []

    # Load config first (before we might remove it) to get paths for summary
    config = load_config()
    log_file_path = None
    if config and "log_file_path" in config:
        log_file_path = config["log_file_path"]

    script_dir = None
    if config and "install_script_dir" in config:
        script_dir = config["install_script_dir"]
    if not script_dir:
        script_dir = str(Path(__file__).resolve().parent)

    print("ClearTrack Uninstall")
    print("=" * 60)

    remove_git_alias(uninstalled)
    remove_cleartrack_wrappers(uninstalled)
    remove_legacy_wrappers(uninstalled)

    config_path = get_config_path()
    if config_path.exists():
        response = input(
            f"Remove config file at {config_path}? (yes/no, default: yes): "
        ).strip().lower()
        if response not in ("no", "n"):
            remove_config(uninstalled)
        else:
            print("Config file kept.")
    else:
        print("No config file found.")

    # Summary: Record of uninstalled files
    print("\n")
    print("=" * 60)
    print("  RECORD OF UNINSTALLED ITEMS")
    print("=" * 60)
    if uninstalled:
        for item in uninstalled:
            print(f"  - {item}")
    else:
        print("  (Nothing was removed)")
    print("=" * 60)

    # What remains: contribution files
    print("\n")
    print("=" * 60)
    print("  KEPT (your contribution data)")
    print("=" * 60)
    if log_file_path:
        print(f"  Contribution log file: {log_file_path}")
        print("  (Delete manually if you no longer need it)")
    else:
        print("  Contribution log: (path unknown - check your config if kept)")
    print("=" * 60)

    # Where to delete ClearTrack source code (if user wants to remove it too)
    print("\n")
    print("=" * 60)
    print("  TO REMOVE CLEARTRACK SOURCE CODE, DELETE THIS FOLDER:")
    print("=" * 60)
    print()
    print(f"  >>>  {script_dir}  <<<")
    print()
    print("  This folder contains install.py, uninstall.py, sync-log.py,")
    print("  lib/ (cleartrack.py, git-push-wrapper.py), and other files.")
    print("=" * 60)
    print("\nUninstall complete.")


if __name__ == "__main__":
    main()
