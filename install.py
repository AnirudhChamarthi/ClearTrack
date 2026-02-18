#!/usr/bin/env python3
"""
ClearTrack Installation Script
Sets up ClearTrack for use across all Git repositories.

Windows note: Git aliases on Windows do not handle paths with spaces or quotes
well when invoking Python directly. We create a batch file (cleartrack_push.bat)
in the user's home directory and set the alias to that file instead. The batch
file then invokes Python with the real wrapper script.
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
    """Set up the configuration file with log path and repository URL."""
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
    
    # Get repository URL (required)
    print("\n" + "="*60)
    print("Repository Setup (Required)")
    print("="*60)
    print("\nClearTrack requires a Git repository to sync your contribution logs.")
    print("This should be your PERSONAL GitHub account repository.")
    print("Create a repository on GitHub, GitLab, or any Git hosting service.")
    print("Example: https://github.com/yourusername/cleartrack-logs.git")
    
    while True:
        repo_url = input("\nPersonal Repository URL: ").strip()
        if repo_url:
            # Basic URL validation
            if not (repo_url.startswith('http://') or repo_url.startswith('https://') or 
                    repo_url.startswith('git@') or repo_url.endswith('.git')):
                print("Warning: URL format may be incorrect. Continuing anyway...")
            break
        else:
            print("Repository URL is required. Please enter a valid Git repository URL.")
    
    # Get personal Git credentials for the log repository
    print("\n" + "="*60)
    print("Personal Git Credentials")
    print("="*60)
    print("\nThese credentials will be used ONLY for syncing contribution logs.")
    print("They are separate from your work repository credentials.")
    print("This preserves privacy - your work repos won't know about personal tracking.")
    
    # Get personal name and email
    personal_name = input("\nYour name (for Git commits): ").strip()
    if not personal_name:
        print("Error: Name is required for Git commits.", file=sys.stderr)
        return None
    
    personal_email = input("Your email (for Git commits): ").strip()
    if not personal_email:
        print("Error: Email is required for Git commits.", file=sys.stderr)
        return None
    
    # Create config with repository URL and personal credentials
    config = {
        "log_file_path": str(log_file_path),
        "log_repo_url": repo_url,
        "personal_name": personal_name,
        "personal_email": personal_email,
        "installed_at": str(datetime.now().isoformat())
    }
    
    # Save config
    try:
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        print(f"\nConfiguration saved to: {config_path}")
        print(f"Log file will be: {log_file_path}")
        print(f"Repository URL: {repo_url}")
        return config
    except IOError as e:
        print(f"Error saving configuration: {e}", file=sys.stderr)
        return None


def get_wrapper_script_path():
    """Get the absolute path to the git-push-wrapper.py script."""
    script_dir = Path(__file__).parent.absolute()
    return script_dir / "git-push-wrapper.py"


def get_batch_wrapper_path():
    """Get the path to the Windows batch wrapper (home/cleartrack_push.bat)."""
    return Path.home() / "cleartrack_push.bat"


def setup_git_alias():
    """Set up a Git alias for git push that uses ClearTrack wrapper."""
    wrapper_script = get_wrapper_script_path()
    python_exe = sys.executable

    # Create platform-specific command
    if platform.system() == 'Windows':
        # On Windows, Git has trouble with quotes and spaces in alias paths.
        # We use a batch wrapper so the alias is just: !C:/Users/.../cleartrack_push.bat
        batch_wrapper = get_batch_wrapper_path()
        if not batch_wrapper.exists():
            print(
                "\nError: Batch wrapper not found. The 'git push-tracked' alias requires it.",
                file=sys.stderr,
            )
            print(
                f"Expected: {batch_wrapper}",
                file=sys.stderr,
            )
            print(
                "Run this installer again; the wrapper is created in the previous step.",
                file=sys.stderr,
            )
            return False
        # Git on Windows accepts forward slashes in the path
        batch_wrapper_normalized = str(batch_wrapper).replace("\\", "/")
        alias_command = f"!{batch_wrapper_normalized}"
    else:
        # On Unix-like systems, use Python directly
        alias_command = f'!{python_exe} "{wrapper_script}"'

    try:
        subprocess.run(
            ["git", "config", "--global", "alias.push-tracked", alias_command],
            check=True,
            capture_output=True,
        )
        print("\nGit alias 'push-tracked' configured.")
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
        # Windows: Create a batch file so Git's alias can call it without quote issues
        batch_wrapper = get_batch_wrapper_path()
        batch_content = f"""@echo off
REM ClearTrack Git Push Wrapper
"{python_exe}" "{wrapper_script}" %*
"""
        try:
            with open(batch_wrapper, "w") as f:
                f.write(batch_content)
            print(f"\nBatch wrapper created: {batch_wrapper}")
            print("This wrapper is used by the 'git push-tracked' alias.")
            return True
        except IOError as e:
            print(
                f"Error: Could not create batch wrapper at {batch_wrapper}: {e}",
                file=sys.stderr,
            )
            print(
                "The 'git push-tracked' alias will not work without this file.",
                file=sys.stderr,
            )
            return False


def setup_repository(config):
    """Initialize Git repository with personal credentials and perform initial sync."""
    from cleartrack import init_log_repository, sync_log_to_repository
    
    log_file_path = Path(config['log_file_path'])
    repo_url = config['log_repo_url']
    personal_name = config['personal_name']
    personal_email = config['personal_email']
    
    print("\n" + "="*60)
    print("Repository Setup")
    print("="*60)
    
    # Initialize Git repository
    print("\nInitializing Git repository...")
    if not init_log_repository(log_file_path, personal_name, personal_email):
        print("Error: Could not initialize Git repository.", file=sys.stderr)
        return False
    
    print("Git repository initialized with personal credentials.")
    
    # Perform initial sync
    print("\nPerforming initial sync to repository...")
    if sync_log_to_repository(config):
        print("Initial sync completed successfully!")
        return True
    else:
        print("Warning: Initial sync had errors.", file=sys.stderr)
        print("You can run 'python sync-log.py' later to sync manually.", file=sys.stderr)
        return False


def main():
    """Main installation function."""
    print("ClearTrack Installation")
    print("="*60)
    
    # Setup configuration (requires repository URL)
    config = setup_config()
    if not config:
        print("Installation failed during configuration.", file=sys.stderr)
        sys.exit(1)
    
    # Setup Git hooks (informational)
    setup_git_hooks()
    
    # Create shell wrapper first (required on Windows for the Git alias)
    if not create_shell_wrapper():
        if platform.system() == "Windows":
            print(
                "Skipping Git alias: batch wrapper is required on Windows.",
                file=sys.stderr,
            )
            sys.exit(1)
    
    # Setup Git alias (on Windows this points to the batch wrapper)
    if not setup_git_alias():
        if platform.system() == "Windows":
            sys.exit(1)
    
    # Setup repository and perform initial sync
    setup_repository(config)
    
    print("\n" + "="*60)
    print("Installation complete!")
    print("="*60)
    print("\nClearTrack is now configured and ready to use.")
    print("\nUsage:")
    print("  - Use 'git push-tracked' instead of 'git push'")
    print("  - Contributions will be logged and automatically synced to your repository")
    print("\nTo test, run 'git push-tracked' in any Git repository.")


if __name__ == "__main__":
    main()
