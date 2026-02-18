#!/usr/bin/env python3
"""
ClearTrack Log Sync Script
Syncs the contribution log file to a remote Git repository.
"""

import sys
from pathlib import Path
from cleartrack import load_config, sync_log_to_repository, init_log_repository


def main():
    """Sync the log file to the configured repository."""
    # Load configuration
    config = load_config()
    if not config or 'log_file_path' not in config:
        print("Error: ClearTrack not configured.")
        print("Please run the installation script first.")
        sys.exit(1)
    
    log_file_path = Path(config['log_file_path'])
    
    # Check if repository URL is configured
    if 'log_repo_url' not in config or not config['log_repo_url']:
        print("Error: No repository URL configured for log syncing.")
        print("\nTo set up repository syncing:")
        print("1. Create a repository on GitHub/GitLab/etc. (or use an existing one)")
        print("2. Run: python install.py")
        print("   Or manually edit ~/.cleartrack_config.json and add:")
        print('   "log_repo_url": "https://github.com/yourusername/your-repo.git"')
        sys.exit(1)
    
    repo_url = config['log_repo_url']
    print(f"Syncing log file to repository: {repo_url}")
    
    # Initialize repository if needed (with personal credentials)
    if not (log_file_path.parent / ".git").exists():
        print("Initializing Git repository...")
        personal_name = config.get('personal_name')
        personal_email = config.get('personal_email')
        if not init_log_repository(log_file_path, personal_name, personal_email):
            print("Error: Could not initialize Git repository.", file=sys.stderr)
            sys.exit(1)
    
    # Sync to repository
    if sync_log_to_repository(config):
        print("Log file synced successfully!")
    else:
        print("Warning: Sync completed with errors. Check the output above.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
