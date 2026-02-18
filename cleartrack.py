#!/usr/bin/env python3
"""
ClearTrack - A privacy-focused contribution tracker for Git repositories.
Logs contributions without revealing project details.
"""

import os
import sys
import json
import subprocess
from datetime import datetime
from pathlib import Path
import platform

# Configuration file name
CONFIG_FILE = ".cleartrack_config.json"
LOG_FILE_NAME = "contributions.txt"


def get_config_path():
    """Get the path to the configuration file in the user's home directory."""
    home = Path.home()
    return home / CONFIG_FILE


def load_config():
    """Load configuration from the user's home directory."""
    config_path = get_config_path()
    if config_path.exists():
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return None
    return None


def save_config(config):
    """Save configuration to the user's home directory."""
    config_path = get_config_path()
    try:
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        return True
    except IOError:
        return False


def get_git_remote_url():
    """Get the remote URL of the current Git repository."""
    try:
        result = subprocess.run(
            ['git', 'config', '--get', 'remote.origin.url'],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def get_current_repo_path():
    """Get the absolute path of the current Git repository."""
    try:
        result = subprocess.run(
            ['git', 'rev-parse', '--show-toplevel'],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def get_current_branch():
    """Get the current Git branch name."""
    try:
        result = subprocess.run(
            ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def get_push_target():
    """Get the target repository URL from git push arguments."""
    # Git hook receives arguments: remote_name remote_url
    # We can also get it from git config
    if len(sys.argv) > 2:
        return sys.argv[2]  # remote_url from git hook
    else:
        # Fallback to remote.origin.url
        return get_git_remote_url()


def log_contribution(config):
    """Log a contribution to the central log file."""
    log_file_path = Path(config['log_file_path'])
    
    # Ensure the directory exists
    log_file_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Create log entry
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"{timestamp} - Contribution logged\n"
    
    # Append to log file
    try:
        with open(log_file_path, 'a', encoding='utf-8') as f:
            f.write(entry)
        return True
    except IOError as e:
        print(f"Error writing to log file: {e}", file=sys.stderr)
        return False


def confirm_with_user(current_repo_path, push_target_url):
    """Display information and confirm with the user."""
    print("\n" + "="*60)
    print("ClearTrack - Contribution Logger")
    print("="*60)
    print(f"Current Repository: {current_repo_path}")
    print(f"Push Target: {push_target_url}")
    print("="*60)
    print("\nThis will log a contribution without revealing project details.")
    
    while True:
        response = input("Proceed with logging? (yes/no): ").strip().lower()
        if response in ['yes', 'y']:
            return True
        elif response in ['no', 'n']:
            return False
        else:
            print("Please enter 'yes' or 'no'.")


def main():
    """Main entry point for ClearTrack."""
    # Check if we're in a Git repository
    current_repo_path = get_current_repo_path()
    if not current_repo_path:
        print("Error: Not in a Git repository.", file=sys.stderr)
        sys.exit(1)
    
    # Load configuration
    config = load_config()
    if not config or 'log_file_path' not in config:
        print("Error: ClearTrack not configured.")
        print("Please run the installation script first.")
        sys.exit(1)
    
    # Get push target
    push_target_url = get_push_target()
    if not push_target_url:
        print("Error: Could not determine push target.", file=sys.stderr)
        sys.exit(1)
    
    # Confirm with user
    if not confirm_with_user(current_repo_path, push_target_url):
        print("Logging cancelled by user.")
        sys.exit(0)
    
    # Log the contribution
    if log_contribution(config):
        print("Contribution logged successfully!")
        sys.exit(0)
    else:
        print("Error: Failed to log contribution.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
