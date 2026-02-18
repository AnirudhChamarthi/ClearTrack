#!/usr/bin/env python3
"""
Git Push Wrapper for ClearTrack
Wraps git push and logs contributions after successful pushes.
"""

import sys
import subprocess
from pathlib import Path

# Import cleartrack functions
sys.path.insert(0, str(Path(__file__).parent))
from cleartrack import (
    get_current_repo_path,
    get_git_remote_url,
    load_config,
    log_contribution,
    confirm_with_user
)


def main():
    """Execute git push and then log contribution if successful."""
    # Execute git push with all arguments passed to this script
    git_args = ['git', 'push'] + sys.argv[1:]
    
    try:
        # Run git push
        result = subprocess.run(git_args, check=False)
        push_exit_code = result.returncode
        
        # Only log if push was successful
        if push_exit_code == 0:
            # Check if ClearTrack is configured
            config = load_config()
            if config and 'log_file_path' in config:
                current_repo_path = get_current_repo_path()
                push_target_url = get_git_remote_url()
                
                if current_repo_path and push_target_url:
                    # Confirm with user before logging
                    if confirm_with_user(current_repo_path, push_target_url):
                        # Log contribution and optionally sync to repository
                        auto_sync = config.get('auto_sync_log', False)
                        log_contribution(config, auto_sync=auto_sync)
        
        # Exit with git push's exit code
        sys.exit(push_exit_code)
        
    except KeyboardInterrupt:
        print("\nPush cancelled by user.", file=sys.stderr)
        sys.exit(130)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
