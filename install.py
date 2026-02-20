#!/usr/bin/env python3
"""
ClearTrack Installation Script
Sets up ClearTrack for use across all Git repositories.

Windows note: Git aliases on Windows do not handle paths with spaces or quotes
well when invoking Python directly. We create a batch file (cleartrack_push.bat)
in the user's home directory and set the alias to that file instead. The batch
file then invokes Python with the real wrapper script.

Requires: Python 3.6+
"""

import os
import sys
import json
import subprocess
from pathlib import Path
import platform
from datetime import datetime


CONFIG_FILE = ".cleartrack_config.json"
CLEARTRACK_FOLDER = ".cleartrack"  # Wrapper scripts live here (easy to find, easy to uninstall)

# Optional config keys added in updates. On --reload, missing keys are added with these defaults.
# Preserves existing user values; only adds keys not yet in config.
CONFIG_OPTIONAL_DEFAULTS = {
    "personal_ssh_key_path": None,
    # Add future optional keys here, e.g. "new_feature_option": None,
}


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
    
    # Get log file location (relative paths resolve from home, not CWD)
    home = Path.home()
    default_log_path = home / "cleartrack_logs" / "contributions.txt"
    
    print(f"\nWhere should contributions be logged?")
    print(f"Default: {default_log_path}")
    log_path_input = input("Enter path (press Enter for default): ").strip()
    
    if log_path_input:
        p = Path(log_path_input).expanduser()
        if not p.is_absolute():
            log_file_path = (home / p).resolve()
        else:
            log_file_path = p.resolve()
    else:
        log_file_path = default_log_path.resolve()

    # Security: Ensure log path is under user's home (do not touch system or other paths)
    home_resolved = Path.home().resolve()
    try:
        log_resolved = log_file_path.resolve()
        log_resolved.relative_to(home_resolved)  # Raises ValueError if not under home
    except ValueError:
        print(
            f"Error: Log path must be inside your home directory ({home_resolved})",
            file=sys.stderr,
        )
        return None
    except (OSError, RuntimeError):
        print("Error: Could not resolve log path.", file=sys.stderr)
        return None

    # Ensure the directory exists
    log_file_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Get repository URL (required)
    print("\n" + "="*60)
    print("Repository Setup (Required)")
    print("="*60)
    print("\nClearTrack requires a Git repository to sync your contribution logs.")
    print("This should be a PERSONAL GitHub account repository.")
    print("This should NOT be the same repository. Please create a new repository to act as a receiver, such as ClearTrackReceiver.")
    print("If you already have a Receiver repository, you do not have to create a new one.")
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
    personal_name = input("\nYour name (for committing to the ClearTrack log repo): ").strip()
    if not personal_name:
        print("Error: Name is required for Git commits.", file=sys.stderr)
        return None
    
    personal_email = input("Your email (for committing to the ClearTrack log repo): ").strip()
    if not personal_email:
        print("Error: Email is required for Git commits.", file=sys.stderr)
        return None
    
    # Personal SSH key for the log repo (keeps work repo credentials separate)
    print("\n" + "-"*60)
    print("Personal SSH Key for Receiver Repo")
    print("-"*60)
    print("To push to your personal receiver repo,")
    print("specify the path to your personal SSH key (e.g. ~/.ssh/id_cleartrack_personal).")
    print("Leave blank to use your default Git/SSH credentials.")
    ssh_key_input = input("\nPath to personal SSH key (press Enter to skip): ").strip()
    personal_ssh_key_path = None
    if ssh_key_input:
        p = Path(ssh_key_input).expanduser().resolve()
        personal_ssh_key_path = str(p)
        if not p.exists():
            print(f"Warning: Key not found at {p}. Create it before first sync.", file=sys.stderr)
    
    # Create config with repository URL and personal credentials
    script_dir = Path(__file__).resolve().parent
    cleartrack_folder = Path.home() / CLEARTRACK_FOLDER
    config = {
        "log_file_path": str(log_file_path),
        "log_repo_url": repo_url,
        "personal_name": personal_name,
        "personal_email": personal_email,
        "installed_at": str(datetime.now().isoformat()),
        "install_script_dir": str(script_dir),
        "cleartrack_folder": str(cleartrack_folder),
    }
    if personal_ssh_key_path:
        config["personal_ssh_key_path"] = personal_ssh_key_path
    
    # Save config (restrictive permissions: sensitive data)
    try:
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2)
        # Restrict config to owner only (Unix); no-op on Windows
        try:
            os.chmod(config_path, 0o600)
        except (OSError, AttributeError):
            pass
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
    return script_dir / "lib" / "git-push-wrapper.py"


def get_cleartrack_folder():
    """Get the path to the .cleartrack folder (wrappers live here)."""
    return Path.home() / CLEARTRACK_FOLDER


def get_batch_wrapper_path():
    """Get the path to the Windows batch wrapper inside .cleartrack."""
    return get_cleartrack_folder() / "cleartrack_push.bat"


def get_bash_wrapper_path():
    """Get the path to the Unix bash wrapper inside .cleartrack."""
    return get_cleartrack_folder() / "cleartrack_push.sh"


def setup_git_alias():
    """Set up a Git alias for git push that uses ClearTrack wrapper."""
    wrapper_script = get_wrapper_script_path()
    python_exe = sys.executable

    # Create platform-specific command
    if platform.system() == 'Windows':
        # On Windows, Git has trouble with quotes and spaces in alias paths.
        # We use a batch wrapper so the alias is just: !C:/Users/.../cleartrack_push.bat
        cleartrack_folder = get_cleartrack_folder()
        batch_wrapper = get_batch_wrapper_path()
        if not cleartrack_folder.exists():
            ensure_cleartrack_folder()  # Create folder if missing
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
                f"ClearTrack folder: {cleartrack_folder}",
                file=sys.stderr,
            )
            print(
                "Run the installer again; it will create the wrapper.",
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
    """Informational: ClearTrack uses a Git alias, not hooks.
    Git does not support post-push hooks; the wrapper approach is used instead.
    """
    print("\nNote: Git doesn't support post-push hooks natively.")
    print("ClearTrack uses a wrapper script approach instead.")
    return True


def ensure_cleartrack_folder():
    """Create .cleartrack folder if it does not exist. Returns the path."""
    folder = get_cleartrack_folder()
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def create_shell_wrapper():
    """Create platform-specific shell wrapper scripts in .cleartrack folder."""
    wrapper_script = get_wrapper_script_path()
    python_exe = sys.executable

    # Ensure .cleartrack folder exists (avoids "randomly breaking" if manually deleted)
    cleartrack_folder = ensure_cleartrack_folder()

    # Remove legacy wrappers from home root (migration from pre-.cleartrack installs)
    for legacy in (Path.home() / "cleartrack_push.bat", Path.home() / ".cleartrack_push.sh"):
        if legacy.exists():
            try:
                legacy.unlink()
            except OSError:
                pass

    # Create bash/zsh wrapper for Unix-like systems
    if platform.system() != 'Windows':
        bash_wrapper = get_bash_wrapper_path()
        bash_content = f"""#!/bin/bash
# ClearTrack Git Push Wrapper
{python_exe} "{wrapper_script}" "$@"
"""
        try:
            with open(bash_wrapper, 'w', encoding='utf-8') as f:
                f.write(bash_content)
            os.chmod(bash_wrapper, 0o755)
            print(f"\nBash wrapper created: {bash_wrapper}")
            print(f"ClearTrack wrappers folder: {cleartrack_folder}")
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
            with open(batch_wrapper, "w", encoding='utf-8') as f:
                f.write(batch_content)
            print(f"\nBatch wrapper created: {batch_wrapper}")
            print(f"ClearTrack wrappers folder: {cleartrack_folder}")
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
    lib_dir = Path(__file__).resolve().parent / "lib"
    sys.path.insert(0, str(lib_dir))
    from cleartrack import clone_or_init_log_repository, sync_log_to_repository

    log_file_path = Path(config['log_file_path'])
    repo_url = config['log_repo_url']
    personal_name = config['personal_name']
    personal_email = config['personal_email']

    print("\n" + "="*60)
    print("Repository Setup")
    print("="*60)

    # Clone or initialize Git repository
    print("\nSetting up log repository (clone or init)...")
    if not clone_or_init_log_repository(log_file_path, repo_url, personal_name, personal_email, config):
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


def do_reload():
    """Reload ClearTrack: update wrappers and alias for users who git pull an update.
    Preserves existing config; only refreshes scripts and paths.
    """
    config_path = get_config_path()
    if not config_path.exists():
        print("Error: ClearTrack not configured.", file=sys.stderr)
        print("Run 'python install.py' first (without --reload).", file=sys.stderr)
        return False

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error: Could not read config: {e}", file=sys.stderr)
        return False

    if "log_file_path" not in config:
        print("Error: Config incomplete. Run 'python install.py' to reinstall.", file=sys.stderr)
        return False

    # Merge in new optional keys from updates (preserve existing values)
    for key, default in CONFIG_OPTIONAL_DEFAULTS.items():
        if key not in config:
            config[key] = default

    script_dir = Path(__file__).resolve().parent
    cleartrack_folder = Path.home() / CLEARTRACK_FOLDER
    config["install_script_dir"] = str(script_dir)
    config["cleartrack_folder"] = str(cleartrack_folder)
    try:
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)
    except IOError as e:
        print(f"Warning: Could not update config: {e}", file=sys.stderr)

    print("ClearTrack Reload")
    print("=" * 60)
    print("Updating wrappers and Git alias from current ClearTrack folder...")

    if not create_shell_wrapper():
        print("Error: Could not recreate wrapper scripts.", file=sys.stderr)
        return False

    if not setup_git_alias():
        print("Warning: Could not update Git alias.", file=sys.stderr)

    print("\nReload complete. Wrappers and alias updated. Existing config preserved; new optional keys merged.")
    return True


def do_change_repo():
    """Change the remote sync repo. Runs repocheck with new URL; updates config only if repocheck succeeds."""
    config_path = get_config_path()
    if not config_path.exists():
        print("Error: ClearTrack not configured.", file=sys.stderr)
        print("Run 'python install.py' first.", file=sys.stderr)
        return False

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error: Could not read config: {e}", file=sys.stderr)
        return False

    if "log_file_path" not in config or "log_repo_url" not in config:
        print("Error: Config incomplete. Run 'python install.py' to reinstall.", file=sys.stderr)
        return False

    old_url = config["log_repo_url"]
    print("\nChange Sync Repository")
    print("=" * 60)
    print(f"Current receiver repo: {old_url}")
    print("=" * 60)
    new_url = input("\nEnter new repository URL: ").strip()
    if not new_url:
        print("No change (empty input).")
        return True
    if new_url == old_url:
        print("URL unchanged.")
        return True

    # Basic URL validation
    if not (new_url.startswith("http://") or new_url.startswith("https://") or
            new_url.startswith("git@") or new_url.endswith(".git")):
        print("Warning: URL format may be incorrect.", file=sys.stderr)

    # Test with new URL via repocheck (without saving config yet)
    lib_dir = Path(__file__).resolve().parent / "lib"
    sys.path.insert(0, str(lib_dir))
    from cleartrack import log_repocheck, _run_git

    config_test = dict(config)
    config_test["log_repo_url"] = new_url

    print("\nRunning repocheck with new URL...")
    if log_repocheck(config_test):
        config["log_repo_url"] = new_url
        try:
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2)
            print("\nRepository URL updated successfully.")
            print(f"New receiver repo: {new_url}")
            return True
        except IOError as e:
            print(f"Error: Could not save config: {e}", file=sys.stderr)
            return False
    else:
        # Revert remote in log dir if it was changed
        log_dir = Path(config["log_file_path"]).parent
        git_dir = log_dir / ".git"
        if git_dir.exists():
            _run_git(
                ["git", "remote", "set-url", "origin", old_url],
                cwd=log_dir,
            )
        print("\nRepocheck failed. Config unchanged.", file=sys.stderr)
        return False


def main():
    """Main installation function."""
    if sys.version_info < (3, 6):
        print(
            "Error: ClearTrack requires Python 3.6 or higher.",
            file=sys.stderr,
        )
        print(
            f"Current version: {sys.version_info.major}.{sys.version_info.minor}",
            file=sys.stderr,
        )
        sys.exit(1)

    if "--help" in sys.argv or "-h" in sys.argv:
        print("Usage: python install.py [--reload|-r] [--change-repo|-c] [--help|-h]")
        print("  --reload      Update wrappers and alias after git pull (keeps your config)")
        print("  --change-repo Change the sync receiver repo (runs repocheck; updates only if successful)")
        sys.exit(0)

    if "--change-repo" in sys.argv or "-c" in sys.argv:
        if do_change_repo():
            sys.exit(0)
        sys.exit(1)

    if "--reload" in sys.argv or "-r" in sys.argv:
        if do_reload():
            sys.exit(0)
        sys.exit(1)

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
    cleartrack_folder = get_cleartrack_folder()
    print(f"\nClearTrack wrappers folder (easy to find): {cleartrack_folder}")
    print("\nClearTrack is now configured and ready to use.")
    print("\nUsage:")
    print("  - Use 'git push-tracked' instead of 'git push'")
    print("  - Contributions will be logged and automatically synced to your repository")
    print("\nTo test, run 'git push-tracked' in any Git repository.")


if __name__ == "__main__":
    main()
