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


def init_log_repository(log_file_path, personal_name=None, personal_email=None):
    """Initialize a Git repository in the log file's directory if not already initialized.
    
    Sets local Git config with personal credentials (separate from work repo credentials).
    """
    log_dir = Path(log_file_path).parent
    git_dir = log_dir / ".git"
    
    try:
        # Initialize Git repository if it doesn't exist
        if not git_dir.exists():
            subprocess.run(
                ['git', 'init'],
                cwd=log_dir,
                check=True,
                capture_output=True
            )
        
        # Set local Git config with personal credentials (separate from global/work config)
        if personal_name:
            subprocess.run(
                ['git', 'config', '--local', 'user.name', personal_name],
                cwd=log_dir,
                check=True,
                capture_output=True
            )
        
        if personal_email:
            subprocess.run(
                ['git', 'config', '--local', 'user.email', personal_email],
                cwd=log_dir,
                check=True,
                capture_output=True
            )
        
        # Create .gitignore to ignore everything except the log file
        gitignore_path = log_dir / ".gitignore"
        if not gitignore_path.exists():
            log_filename = Path(log_file_path).name
            with open(gitignore_path, 'w') as f:
                f.write("*\n")
                f.write(f"!{log_filename}\n")
                f.write("!.gitignore\n")
        
        return True
    except (subprocess.CalledProcessError, IOError) as e:
        print(f"Warning: Could not initialize Git repository: {e}", file=sys.stderr)
        return False


def sync_log_to_repository(config):
    """Commit and push the log file to the remote repository if configured."""
    log_file_path = Path(config['log_file_path'])
    log_dir = log_file_path.parent
    
    # Check if repository URL is configured
    if 'log_repo_url' not in config or not config['log_repo_url']:
        return True  # No repository configured, skip sync
    
    repo_url = config['log_repo_url']
    
    try:
        # Check if remote is already configured
        result = subprocess.run(
            ['git', 'remote', 'get-url', 'origin'],
            cwd=log_dir,
            capture_output=True,
            text=True
        )
        
        # If remote doesn't exist or is different, set it up
        if result.returncode != 0 or result.stdout.strip() != repo_url:
            if result.returncode != 0:
                # Add remote
                subprocess.run(
                    ['git', 'remote', 'add', 'origin', repo_url],
                    cwd=log_dir,
                    check=True,
                    capture_output=True
                )
            else:
                # Update remote URL
                subprocess.run(
                    ['git', 'remote', 'set-url', 'origin', repo_url],
                    cwd=log_dir,
                    check=True,
                    capture_output=True
                )
        
        # Ensure log file exists (create empty if it doesn't)
        if not log_file_path.exists():
            log_file_path.parent.mkdir(parents=True, exist_ok=True)
            log_file_path.touch()
        
        # Add the log file
        log_filename = log_file_path.name
        result = subprocess.run(
            ['git', 'add', log_filename],
            cwd=log_dir,
            check=False,
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            # If git add fails, it might be because file is not tracked yet
            # Try adding .gitignore first if it exists
            gitignore_path = log_dir / ".gitignore"
            if gitignore_path.exists():
                subprocess.run(
                    ['git', 'add', '.gitignore'],
                    cwd=log_dir,
                    check=False,
                    capture_output=True
                )
            # Try adding the log file again
            result = subprocess.run(
                ['git', 'add', log_filename],
                cwd=log_dir,
                check=False,
                capture_output=True,
                text=True
            )
            if result.returncode != 0:
                raise subprocess.CalledProcessError(
                    result.returncode, 
                    ['git', 'add', log_filename],
                    result.stderr
                )
        
        # Check if there are changes to commit
        result = subprocess.run(
            ['git', 'diff', '--cached', '--quiet'],
            cwd=log_dir,
            capture_output=True
        )
        
        if result.returncode != 0:  # There are changes
            # Commit changes
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            commit_message = f"Update contributions log - {timestamp}"
            subprocess.run(
                ['git', 'commit', '-m', commit_message],
                cwd=log_dir,
                check=True,
                capture_output=True
            )
            
            # Push to remote (try main branch first, then master)
            for branch in ['main', 'master']:
                try:
                    subprocess.run(
                        ['git', 'push', '-u', 'origin', branch],
                        cwd=log_dir,
                        check=True,
                        capture_output=True
                    )
                    return True
                except subprocess.CalledProcessError:
                    continue
            
            # If neither branch worked, try pushing current branch
            try:
                subprocess.run(
                    ['git', 'push', '-u', 'origin', 'HEAD'],
                    cwd=log_dir,
                    check=True,
                    capture_output=True
                )
            except subprocess.CalledProcessError as e:
                print(f"Warning: Could not push to repository: {e}", file=sys.stderr)
                return False
        
        return True
        
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"Warning: Could not sync to repository: {e}", file=sys.stderr)
        return False


def log_contribution(config):
    """Log a contribution to the central log file and sync to repository."""
    log_file_path = Path(config['log_file_path'])
    
    # Ensure the directory exists
    log_file_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Initialize Git repository if configured (with personal credentials)
    if 'log_repo_url' in config and config['log_repo_url']:
        personal_name = config.get('personal_name')
        personal_email = config.get('personal_email')
        init_log_repository(log_file_path, personal_name, personal_email)
    
    # Create log entry
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"{timestamp} - Contribution logged\n"
    
    # Append to log file
    try:
        with open(log_file_path, 'a', encoding='utf-8') as f:
            f.write(entry)
        
        # Always sync to repository if configured
        if 'log_repo_url' in config and config['log_repo_url']:
            sync_name = config.get('personal_name', 'Unknown')
            sync_email = config.get('personal_email', 'Unknown')
            sync_repo = config.get('log_repo_url', 'Unknown')
            
            print(f"\n📥 Syncing to personal repository...")
            print(f"   Account: {sync_name} <{sync_email}>")
            print(f"   Repo:    {sync_repo}")
            
            if sync_log_to_repository(config):
                print("✅ Log synced successfully to personal repository!")
            else:
                print("⚠️  Warning: Sync had errors. Run 'python sync-log.py' to retry.")
        
        return True
    except IOError as e:
        print(f"Error writing to log file: {e}", file=sys.stderr)
        return False


def confirm_with_user(current_repo_path, push_target_url, config=None):
    """Display information and confirm with the user.
    
    Shows which account is used for the push and which for the sync.
    """
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
