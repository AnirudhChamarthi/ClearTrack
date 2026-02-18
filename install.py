#!/usr/bin/env python3
"""
ClearTrack Installation Script
Sets up ClearTrack for use across all Git repositories.
"""

import os
import sys
import json
import subprocess
from pathlib import Path
import platform
from datetime import datetime


CONFIG_FILE = ".cleartrack_config.json"
GIT_TEMPLATE_DIR = ".git_template"
HOOKS_DIR = "hooks"
POST_PUSH_HOOK = "post-push"


def get_config_path():
    """Get the path to the configuration file in the user's home directory."""
    home = Path.home()
    return home / CONFIG_FILE


def get_cleartrack_script_path():
    """Get the absolute path to the cleartrack.py script."""
    # Get the directory where this install script is located
    script_dir = Path(__file__).parent.absolute()
    return script_dir / "cleartrack.py"


def setup_config():
    """Set up the configuration file."""
    config_path = get_config_path()
    
    print("\nClearTrack Configuration")
    print("="*60)
    
    # Get log file location
    home = Path.home()
    default_log_path = home / "cleartrack_contributions.txt"
    
    print(f"\nWhere should contributions be logged?")
    print(f"Default: {default_log_path}")
    log_path_input = input("Enter path (press Enter for default): ").strip()
    
    if log_path_input:
        log_file_path = Path(log_path_input).expanduser().absolute()
    else:
        log_file_path = default_log_path
    
    # Ensure the directory exists
    log_file_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Create config
    config = {
        "log_file_path": str(log_file_path),
        "installed_at": str(datetime.now().isoformat())
    }
    
    # Save config
    try:
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        print(f"\nConfiguration saved to: {config_path}")
        print(f"Log file will be: {log_file_path}")
        return True
    except IOError as e:
        print(f"Error saving configuration: {e}", file=sys.stderr)
        return False


def get_wrapper_script_path():
    """Get the absolute path to the git-push-wrapper.py script."""
    script_dir = Path(__file__).parent.absolute()
    return script_dir / "git-push-wrapper.py"


def setup_git_alias():
    """Set up a Git alias for git push that uses ClearTrack wrapper."""
    wrapper_script = get_wrapper_script_path()
    python_exe = sys.executable
    
    # Create platform-specific command
    if platform.system() == 'Windows':
        # On Windows, use Python to run the script
        alias_command = f'!{python_exe} "{wrapper_script}"'
    else:
        # On Unix-like systems
        alias_command = f'!{python_exe} "{wrapper_script}"'
    
    try:
        # Set up the alias
        subprocess.run(
            ['git', 'config', '--global', 'alias.push-tracked', alias_command],
            check=True,
            capture_output=True
        )
        print(f"\nGit alias 'push-tracked' configured.")
        print("Use 'git push-tracked' instead of 'git push' to log contributions.")
        print("\nTo use ClearTrack automatically, you can:")
        print("  1. Use 'git push-tracked' instead of 'git push'")
        print("  2. Or set up a shell alias/function (see README)")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Warning: Could not configure Git alias: {e}", file=sys.stderr)
        return False


def setup_git_hooks():
    """Set up Git hooks to use ClearTrack (for pre-push hook)."""
    home = Path.home()
    git_template_dir = home / GIT_TEMPLATE_DIR
    hooks_dir = git_template_dir / HOOKS_DIR
    
    # Create template directory structure
    hooks_dir.mkdir(parents=True, exist_ok=True)
    
    # Get the path to wrapper script
    wrapper_script = get_wrapper_script_path()
    
    # Determine Python executable
    python_exe = sys.executable
    
    # Note: Git doesn't have post-push hook, so we'll use a different approach
    # We'll set up a git alias instead (handled in setup_git_alias)
    print("\nNote: Git doesn't support post-push hooks natively.")
    print("ClearTrack uses a wrapper script approach instead.")
    
    return True


def create_shell_wrapper():
    """Create platform-specific shell wrapper scripts."""
    wrapper_script = get_wrapper_script_path()
    python_exe = sys.executable
    home = Path.home()
    
    # Create bash/zsh wrapper for Unix-like systems
    if platform.system() != 'Windows':
        bash_wrapper = home / ".cleartrack_push.sh"
        bash_content = f"""#!/bin/bash
# ClearTrack Git Push Wrapper
{python_exe} "{wrapper_script}" "$@"
"""
        try:
            with open(bash_wrapper, 'w') as f:
                f.write(bash_content)
            os.chmod(bash_wrapper, 0o755)
            print(f"\nBash wrapper created: {bash_wrapper}")
            print("Add this to your ~/.bashrc or ~/.zshrc:")
            print(f"  alias git-push='{bash_wrapper}'")
            print("  # Or override git push:")
            print(f"  # alias push='{bash_wrapper}'")
            return True
        except IOError as e:
            print(f"Warning: Could not create bash wrapper: {e}", file=sys.stderr)
            return False
    else:
        # Windows: Create a batch file
        batch_wrapper = home / "cleartrack_push.bat"
        batch_content = f"""@echo off
REM ClearTrack Git Push Wrapper
"{python_exe}" "{wrapper_script}" %*
"""
        try:
            with open(batch_wrapper, 'w') as f:
                f.write(batch_content)
            print(f"\nBatch wrapper created: {batch_wrapper}")
            print("You can create a shortcut or add to PATH to use 'cleartrack-push'")
            return True
        except IOError as e:
            print(f"Warning: Could not create batch wrapper: {e}", file=sys.stderr)
            return False


def main():
    """Main installation function."""
    print("ClearTrack Installation")
    print("="*60)
    
    # Setup configuration
    if not setup_config():
        print("Installation failed during configuration.", file=sys.stderr)
        sys.exit(1)
    
    # Setup Git hooks (informational)
    setup_git_hooks()
    
    # Setup Git alias
    setup_git_alias()
    
    # Create shell wrapper
    create_shell_wrapper()
    
    print("\n" + "="*60)
    print("Installation complete!")
    print("="*60)
    print("\nClearTrack is now configured.")
    print("\nUsage:")
    print("  - Use 'git push-tracked' instead of 'git push'")
    print("  - Or set up a shell alias (see instructions above)")
    print("\nTo test, run 'git push-tracked' in any Git repository.")


if __name__ == "__main__":
    main()
