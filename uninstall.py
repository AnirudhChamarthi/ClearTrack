#!/usr/bin/env python3
"""
ClearTrack Uninstall Script
Removes ClearTrack from your system: Git alias, wrapper scripts, and optionally config.
Does not delete your contribution log file unless you choose to.
"""

import subprocess
import sys
from pathlib import Path
import platform

CONFIG_FILE = ".cleartrack_config.json"


def get_config_path():
    """Path to the config file in the user's home directory."""
    return Path.home() / CONFIG_FILE


def get_batch_wrapper_path():
    """Path to the Windows batch wrapper."""
    return Path.home() / "cleartrack_push.bat"


def get_bash_wrapper_path():
    """Path to the Unix bash wrapper."""
    return Path.home() / ".cleartrack_push.sh"


def remove_git_alias():
    """Remove the global push-tracked alias."""
    try:
        result = subprocess.run(
            ["git", "config", "--global", "--get", "alias.push-tracked"],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            print("Git alias 'push-tracked' was not set. Skipping.")
            return True
        subprocess.run(
            ["git", "config", "--global", "--unset", "alias.push-tracked"],
            check=True,
            capture_output=True,
        )
        print("Removed Git alias 'push-tracked'.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Warning: Could not remove Git alias: {e}", file=sys.stderr)
        return False


def remove_wrappers():
    """Remove the platform-specific wrapper script."""
    removed = False
    if platform.system() == "Windows":
        path = get_batch_wrapper_path()
    else:
        path = get_bash_wrapper_path()

    if path.exists():
        try:
            path.unlink()
            print(f"Removed wrapper: {path}")
            removed = True
        except OSError as e:
            print(f"Warning: Could not remove {path}: {e}", file=sys.stderr)
    else:
        print(f"Wrapper not found at {path}. Skipping.")

    return removed or not path.exists()


def remove_config():
    """Remove the config file. Does not remove the log file."""
    path = get_config_path()
    if not path.exists():
        print(f"Config not found at {path}. Skipping.")
        return True
    try:
        path.unlink()
        print(f"Removed config: {path}")
        return True
    except OSError as e:
        print(f"Warning: Could not remove config: {e}", file=sys.stderr)
        return False


def main():
    print("ClearTrack Uninstall")
    print("=" * 60)

    remove_git_alias()
    remove_wrappers()

    config_path = get_config_path()
    if config_path.exists():
        response = input(
            f"Remove config file at {config_path}? (yes/no, default: yes): "
        ).strip().lower()
        if response not in ("no", "n"):
            remove_config()
        else:
            print("Config file kept.")
    else:
        print("No config file found.")

    print("\n" + "=" * 60)
    print("Uninstall complete.")
    print("=" * 60)
    print("\nYour contribution log file was not deleted.")
    print("You can delete it manually if you no longer need it.")
    print("The ClearTrack script files in this folder were not removed.")
    print("Delete the ClearTrack folder if you want to remove them.")


if __name__ == "__main__":
    main()
