#!/usr/bin/env python3
"""
ClearTrack Log Repository Setup Script
Helps configure a Git repository for syncing contribution logs.
"""

import sys
import json
from pathlib import Path
from cleartrack import get_config_path, load_config, save_config, init_log_repository


def main():
    """Set up repository for log syncing."""
    print("ClearTrack Log Repository Setup")
    print("="*60)
    
    # Load existing config
    config = load_config()
    if not config:
        print("Error: ClearTrack not configured.")
        print("Please run 'python install.py' first.")
        sys.exit(1)
    
    log_file_path = Path(config['log_file_path'])
    
    print(f"\nCurrent log file: {log_file_path}")
    print("\nTo sync your contribution logs to a Git repository:")
    print("1. Create a new repository on GitHub, GitLab, or any Git hosting service")
    print("2. Copy the repository URL (e.g., https://github.com/username/repo.git)")
    print("3. Enter it below")
    
    repo_url = input("\nRepository URL (or press Enter to skip): ").strip()
    
    if not repo_url:
        print("\nRepository setup cancelled.")
        sys.exit(0)
    
    # Validate URL format (basic check)
    if not (repo_url.startswith('http://') or repo_url.startswith('https://') or 
            repo_url.startswith('git@') or repo_url.endswith('.git')):
        print("Warning: URL format may be incorrect. Continuing anyway...")
    
    # Update config
    config['log_repo_url'] = repo_url
    
    # Ask about auto-sync
    print("\nAuto-sync options:")
    print("  - If enabled, logs will be automatically pushed after each contribution")
    print("  - If disabled, you'll need to manually run 'python sync-log.py'")
    auto_sync_input = input("Enable auto-sync? (yes/no, default: no): ").strip().lower()
    config['auto_sync_log'] = auto_sync_input in ['yes', 'y']
    
    # Save config
    if save_config(config):
        print(f"\nConfiguration updated!")
        print(f"Repository URL: {repo_url}")
        print(f"Auto-sync: {'Enabled' if config['auto_sync_log'] else 'Disabled'}")
        
        # Initialize repository
        print("\nInitializing Git repository...")
        if init_log_repository(log_file_path):
            print("Git repository initialized.")
            
            # Try initial sync
            print("\nWould you like to perform an initial sync now?")
            sync_now = input("Sync now? (yes/no, default: yes): ").strip().lower()
            if sync_now not in ['no', 'n']:
                from cleartrack import sync_log_to_repository
                if sync_log_to_repository(config):
                    print("Initial sync completed successfully!")
                else:
                    print("Warning: Initial sync had errors. You can run 'python sync-log.py' later.")
        else:
            print("Warning: Could not initialize Git repository.")
            print("You can initialize it manually later.")
        
        print("\n" + "="*60)
        print("Setup complete!")
        print("="*60)
        print("\nTo sync logs manually, run:")
        print("  python sync-log.py")
        print("\nOr if auto-sync is enabled, logs will sync automatically.")
    else:
        print("Error: Could not save configuration.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
