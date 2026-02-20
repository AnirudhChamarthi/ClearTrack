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


def _path_under_home(path_str):
    """Return True if path is under user's home. Prevents writing outside home."""
    try:
        home = Path.home().resolve()
        path = Path(path_str).expanduser().resolve()
        path.relative_to(home)
        return True
    except (ValueError, OSError, RuntimeError):
        return False


def load_config():
    """Load configuration from the user's home directory."""
    config_path = get_config_path()
    if config_path.exists():
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            # Security: Reject config with log path outside home
            if "log_file_path" in config and not _path_under_home(config["log_file_path"]):
                return None
            return config
        except (json.JSONDecodeError, IOError):
            return None
    return None


def save_config(config):
    """Save configuration to the user's home directory."""
    config_path = get_config_path()
    try:
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2)
        return True
    except IOError:
        return False


# Git exit code 128 = fatal error (auth, repo not found, etc.)
GIT_EXIT_128_HINTS = {
    "Authentication failed": "Check credentials. Use SSH keys or a personal access token.",
    "repository not found": "Verify the repo URL exists and you have access.",
    "Permission denied": "Check SSH key or HTTPS token permissions.",
    "Could not resolve host": "Check network connectivity and URL.",
    "Connection refused": "Check if the host/port is correct.",
    "denied": "Access denied. Check credentials.",
}


def _get_log_repo_env(config):
    """Return env dict with GIT_SSH_COMMAND for log repo operations.
    Uses personal_ssh_key_path from config so work repo credentials are unaffected.
    Returns None if no key configured or key file does not exist.
    """
    if not config:
        return None
    key_path = config.get('personal_ssh_key_path')
    if not key_path:
        return None
    path = Path(key_path).expanduser().resolve()
    if not path.exists():
        return None
    env = os.environ.copy()
    env['GIT_SSH_COMMAND'] = f'ssh -i "{path}" -o IdentitiesOnly=yes'
    return env


def _run_git(cmd, cwd=None, capture=True, env=None):
    """Run a git command. If capture=True and it fails, return (returncode, stdout, stderr).
    Use capture=False to stream output (for user-facing commands).
    If env is provided, use it for the subprocess (e.g. GIT_SSH_COMMAND for log repo).
    """
    result = subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=capture,
        text=True,
        env=env,
    )
    return result


def _report_git_error(cmd, result, context="Git command"):
    """Print a helpful error message when a git command fails."""
    err = (result.stderr or "").strip()
    out = (result.stdout or "").strip()
    print(f"\n{context} failed (exit code {result.returncode})", file=sys.stderr)
    if err:
        print(err, file=sys.stderr)
    if out and out != err:
        print(out, file=sys.stderr)
    if result.returncode == 128 and err:
        for keyword, hint in GIT_EXIT_128_HINTS.items():
            if keyword.lower() in err.lower():
                print(f"\nHint: {hint}", file=sys.stderr)
                break


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


def get_git_user_info(repo_path=None):
    """Get Git user name and email from the current repository context.
    
    Returns (name, email) tuple, checking local config first, then global.
    """
    try:
        # Try local config first (repo-specific)
        name_result = subprocess.run(
            ['git', 'config', '--local', 'user.name'],
            cwd=repo_path,
            capture_output=True,
            text=True
        )
        email_result = subprocess.run(
            ['git', 'config', '--local', 'user.email'],
            cwd=repo_path,
            capture_output=True,
            text=True
        )
        
        # If local config exists, use it
        if name_result.returncode == 0 and email_result.returncode == 0:
            return (name_result.stdout.strip(), email_result.stdout.strip())
        
        # Fall back to global config
        name_result = subprocess.run(
            ['git', 'config', '--global', 'user.name'],
            capture_output=True,
            text=True
        )
        email_result = subprocess.run(
            ['git', 'config', '--global', 'user.email'],
            capture_output=True,
            text=True
        )
        
        if name_result.returncode == 0 and email_result.returncode == 0:
            return (name_result.stdout.strip(), email_result.stdout.strip())
        
        return (None, None)
    except (subprocess.CalledProcessError, FileNotFoundError):
        return (None, None)


def get_push_target():
    """Get the target repository URL from git push arguments."""
    # Git hook receives arguments: remote_name remote_url
    # We can also get it from git config
    if len(sys.argv) > 2:
        return sys.argv[2]  # remote_url from git hook
    else:
        # Fallback to remote.origin.url
        return get_git_remote_url()


def clone_or_init_log_repository(log_file_path, repo_url, personal_name=None, personal_email=None, config=None):
    """Clone the receiving repo if possible, else init. Ensures repo is set up for sync.
    
    Uses clone when the log directory doesn't exist (avoids merge conflicts with remote).
    Falls back to init for existing directories (e.g. custom paths, reinstall).
    Sets local Git config with personal credentials (separate from work repo credentials).
    If config contains personal_ssh_key_path, uses that key for clone (does not affect work repo).
    """
    log_dir = Path(log_file_path).parent
    git_dir = log_dir / ".git"
    log_env = _get_log_repo_env(config) if config else None

    try:
        if not git_dir.exists():
            if not log_dir.exists() and repo_url:
                # Clone: directory doesn't exist - clone creates it with remote history
                log_dir.parent.mkdir(parents=True, exist_ok=True)
                r = _run_git(['git', 'clone', repo_url, str(log_dir)], env=log_env)
                if r.returncode != 0:
                    _report_git_error(
                        ['git', 'clone', repo_url, str(log_dir)],
                        r,
                        "Clone of log repository",
                    )
                    return False
            else:
                # Init: directory exists (custom path) or no repo_url
                log_dir.mkdir(parents=True, exist_ok=True)
                r = _run_git(['git', 'init'], cwd=log_dir)
                if r.returncode != 0:
                    _report_git_error(['git', 'init'], r, "Initialize log repository")
                    return False

        # Set local Git config with personal credentials (separate from global/work config)
        if personal_name:
            _run_git(
                ['git', 'config', '--local', 'user.name', personal_name],
                cwd=log_dir,
            )
        if personal_email:
            _run_git(
                ['git', 'config', '--local', 'user.email', personal_email],
                cwd=log_dir,
            )

        # Ensure .gitignore only tracks the log file (overwrite if clone brought other rules)
        log_filename = Path(log_file_path).name
        gitignore_path = log_dir / ".gitignore"
        with open(gitignore_path, 'w', encoding='utf-8') as f:
            f.write("*\n")
            f.write(f"!{log_filename}\n")
            f.write("!.gitignore\n")

        return True
    except IOError as e:
        print(f"Error: Could not initialize Git repository: {e}", file=sys.stderr)
        return False


def sync_log_to_repository(config):
    """Commit and push the log file to the remote repository if configured."""
    log_file_path = Path(config['log_file_path'])
    log_dir = log_file_path.parent
    log_env = _get_log_repo_env(config)
    
    # Check if repository URL is configured
    if 'log_repo_url' not in config or not config['log_repo_url']:
        return True  # No repository configured, skip sync
    
    repo_url = config['log_repo_url']
    
    try:
        # Check if remote is already configured
        result = _run_git(['git', 'remote', 'get-url', 'origin'], cwd=log_dir)

        # If remote doesn't exist or is different, set it up
        if result.returncode != 0 or result.stdout.strip() != repo_url:
            if result.returncode != 0:
                r = _run_git(
                    ['git', 'remote', 'add', 'origin', repo_url],
                    cwd=log_dir,
                )
                if r.returncode != 0:
                    _report_git_error(
                        ['git', 'remote', 'add', 'origin', repo_url],
                        r,
                        "Add remote origin",
                    )
                    return False
            else:
                _run_git(
                    ['git', 'remote', 'set-url', 'origin', repo_url],
                    cwd=log_dir,
                )
        
        # Ensure log file exists (create empty if it doesn't)
        if not log_file_path.exists():
            log_file_path.parent.mkdir(parents=True, exist_ok=True)
            log_file_path.touch()
        
        # Add the log file
        log_filename = log_file_path.name
        result = _run_git(['git', 'add', log_filename], cwd=log_dir)

        if result.returncode != 0:
            # If git add fails, it might be because file is not tracked yet
            gitignore_path = log_dir / ".gitignore"
            if gitignore_path.exists():
                _run_git(['git', 'add', '.gitignore'], cwd=log_dir)
            result = _run_git(['git', 'add', log_filename], cwd=log_dir)
            if result.returncode != 0:
                _report_git_error(
                    ['git', 'add', log_filename], result, "Add log file"
                )
                return False

        # Check if there are changes to commit
        result = _run_git(['git', 'diff', '--cached', '--quiet'], cwd=log_dir)

        if result.returncode != 0:  # There are changes
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            commit_message = f"Update contributions log - {timestamp}"
            r = _run_git(
                ['git', 'commit', '-m', commit_message],
                cwd=log_dir,
            )
            if r.returncode != 0:
                _report_git_error(
                    ['git', 'commit', '-m', commit_message], r, "Commit"
                )
                return False

            # Push to remote (force push - log repo is single source of truth)
            push_succeeded = False
            last_push_error = None
            for branch in ['main', 'master']:
                r = _run_git(
                    ['git', 'push', '--force', '-u', 'origin', branch],
                    cwd=log_dir,
                    env=log_env,
                )
                if r.returncode == 0:
                    push_succeeded = True
                    break
                last_push_error = r

            if not push_succeeded:
                r = _run_git(
                    ['git', 'push', '--force', '-u', 'origin', 'HEAD'],
                    cwd=log_dir,
                    env=log_env,
                )
                if r.returncode == 0:
                    push_succeeded = True
                else:
                    last_push_error = r

            if not push_succeeded and last_push_error:
                _report_git_error(
                    ['git', 'push', '--force', '-u', 'origin', 'origin/HEAD'],
                    last_push_error,
                    "Push to log repository (exit 128 = auth/repo access)",
                )
                return False

        return True

    except FileNotFoundError as e:
        print(
            f"Error: Git not found. Is Git installed and in PATH? {e}",
            file=sys.stderr,
        )
        return False


def log_contribution(config, quiet=False):
    """Log a contribution to the central log file and sync to repository.

    If quiet=True, suppresses verbose output (paths, URLs, account info).
    """
    log_file_path = Path(config['log_file_path'])
    
    # Ensure the directory exists
    log_file_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Clone or init repository if configured (with personal credentials)
    if 'log_repo_url' in config and config['log_repo_url']:
        personal_name = config.get('personal_name')
        personal_email = config.get('personal_email')
        repo_url = config['log_repo_url']
        clone_or_init_log_repository(log_file_path, repo_url, personal_name, personal_email, config)
    
    # Create log entry
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"{timestamp} - Contribution logged\n"
    
    # Append to log file
    try:
        with open(log_file_path, 'a', encoding='utf-8') as f:
            f.write(entry)
        
        # Always sync to repository if configured
        if 'log_repo_url' in config and config['log_repo_url']:
            if not quiet:
                sync_name = config.get('personal_name', 'Unknown')
                sync_email = config.get('personal_email', 'Unknown')
                sync_repo = config.get('log_repo_url', 'Unknown')
                print(f"\n📥 Syncing to personal repository...")
                print(f"   Account: {sync_name} <{sync_email}>")
                print(f"   Repo:    {sync_repo}")

            if sync_log_to_repository(config):
                if not quiet:
                    print("✅ Log synced successfully to personal repository!")
            else:
                print("⚠️  Warning: Sync had errors. Run 'python sync-log.py' to retry.", file=sys.stderr)
        
        return True
    except IOError as e:
        print(f"Error writing to log file: {e}", file=sys.stderr)
        return False


def log_repocheck(config):
    """Append 'repo checked' with timestamp to the log and push to the receiving repo."""
    log_file_path = Path(config["log_file_path"])

    log_file_path.parent.mkdir(parents=True, exist_ok=True)

    if "log_repo_url" in config and config["log_repo_url"]:
        personal_name = config.get("personal_name")
        personal_email = config.get("personal_email")
        repo_url = config["log_repo_url"]
        clone_or_init_log_repository(log_file_path, repo_url, personal_name, personal_email, config)

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"{timestamp} - repo checked\n"

    try:
        with open(log_file_path, "a", encoding="utf-8") as f:
            f.write(entry)

        if "log_repo_url" in config and config["log_repo_url"]:
            if not sync_log_to_repository(config):
                return False

        return True
    except IOError as e:
        print(f"Error writing to log file: {e}", file=sys.stderr)
        return False


def diagnose_sync(config, verbose=True):
    """Test connectivity to the log repository without pushing.
    Returns (success: bool, messages: list).
    """
    messages = []
    log_file_path = Path(config.get("log_file_path", ""))
    repo_url = config.get("log_repo_url")

    if not repo_url:
        messages.append("No log_repo_url configured.")
        return False, messages

    messages.append(f"Log repo: {repo_url}")
    messages.append(f"Log file: {log_file_path}")
    log_env = _get_log_repo_env(config)

    # Test 1: ls-remote (does not modify anything, tests auth and reachability)
    if verbose:
        messages.append("\nTesting connectivity (git ls-remote)...")
    r = _run_git(["git", "ls-remote", repo_url], env=log_env)
    if r.returncode != 0:
        messages.append(f"FAIL: ls-remote failed (exit {r.returncode})")
        if r.stderr:
            messages.append(r.stderr.strip())
        return False, messages
    messages.append("  OK - Repository is reachable")

    # Test 2: Log directory
    log_dir = log_file_path.parent
    if log_dir.exists():
        messages.append(f"\nLog directory exists: {log_dir}")
        git_dir = log_dir / ".git"
        if git_dir.exists():
            messages.append("  OK - Git repo initialized")
            # Check remote
            rr = _run_git(["git", "remote", "get-url", "origin"], cwd=log_dir)
            if rr.returncode == 0:
                messages.append(f"  Remote: {rr.stdout.strip()}")
        else:
            messages.append("  (Not yet cloned - will init on first sync)")
    else:
        messages.append(f"\nLog directory will be created: {log_dir}")

    return True, messages


def confirm_with_user(current_repo_path, push_target_url, config=None, quiet=False):
    """Display information and confirm with the user.

    Shows which account is used for the push and which for the sync.
    If quiet=True, shows only the confirmation prompt (no paths, URLs, or account info).
    """
    if not quiet:
        print("\n" + "="*60)
        print("ClearTrack - Contribution Logger")
        print("="*60)
        print(f"Current Repository: {current_repo_path}")
        print(f"Push Target: {push_target_url}")

        # Get account info for the push (current repo's Git config)
        push_name, push_email = get_git_user_info(current_repo_path)
        if push_name and push_email:
            print(f"\n📤 Push Account (work repo):")
            print(f"   Name:  {push_name}")
            print(f"   Email: {push_email}")
        else:
            print(f"\n📤 Push Account: (using default Git config)")

        # Get account info for the sync (personal account from config)
        if config:
            sync_name = config.get('personal_name')
            sync_email = config.get('personal_email')
            sync_repo = config.get('log_repo_url')

            if sync_name and sync_email:
                print(f"\n📥 Sync Account (personal log repo):")
                print(f"   Name:  {sync_name}")
                print(f"   Email: {sync_email}")
                if sync_repo:
                    print(f"   Repo:  {sync_repo}")
            else:
                print(f"\n📥 Sync Account: (not configured)")

        print("="*60)
        print("\nThis will log a contribution without revealing project details.")
        print("The push uses the work repo account; the log sync uses your personal account.")

    while True:
        response = input("\nProceed with logging? (yes/no): ").strip().lower()
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
