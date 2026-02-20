#!/usr/bin/env python3
"""
ClearTrack Log Sync Script
Syncs the contribution log file to a remote Git repository.
"""

import sys
from pathlib import Path

# Ensure cleartrack can be imported when run from any working directory
lib_dir = Path(__file__).resolve().parent / "lib"
sys.path.insert(0, str(lib_dir))
from cleartrack import (
    load_config,
    sync_log_to_repository,
    clone_or_init_log_repository,
    diagnose_sync,
)


def main():
    """Sync the log file to the configured repository."""
    args = sys.argv[1:]
    do_test = "--test" in args
    verbose = "--verbose" in args or "-v" in args
    if "--help" in args or "-h" in args:
        print("Usage: python sync-log.py [--test] [--verbose|-v] [--help|-h]")
        print("  --test    Test connectivity to log repo (no sync, no changes)")
        print("  --verbose Show detailed output")
        sys.exit(0)

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

    if do_test:
        print("ClearTrack connectivity test (no changes made)")
        print("=" * 60)
        ok, msgs = diagnose_sync(config, verbose=True)
        for m in msgs:
            print(m)
        print("=" * 60)
        if ok:
            print("OK - Repository is reachable. Run without --test to sync.")
            sys.exit(0)
        else:
            print("FAIL - Fix errors above. Common: auth, wrong URL, network.", file=sys.stderr)
            sys.exit(1)

    repo_url = config['log_repo_url']
    print(f"Syncing log file to repository: {repo_url}")
    
    # Initialize repository if needed (with personal credentials)
    if not (log_file_path.parent / ".git").exists():
        print("Initializing Git repository...")
        personal_name = config.get('personal_name')
        personal_email = config.get('personal_email')
        repo_url = config['log_repo_url']
        if not clone_or_init_log_repository(log_file_path, repo_url, personal_name, personal_email, config):
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
