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


# Keywords: offcheck = skip yes/no for easier flow; oncheck = show yes/no for visibility
CHECK_OFF = "offcheck"
CHECK_ON = "oncheck"


def main():
    """Execute git push and then log contribution if successful."""
    # Parse ClearTrack keywords (strip them so they are not passed to git push)
    raw_args = sys.argv[1:]
    git_only_args = [a for a in raw_args if a not in (CHECK_OFF, CHECK_ON)]
    use_offcheck = CHECK_OFF in raw_args
    use_oncheck = CHECK_ON in raw_args

    # offcheck = skip confirmation; oncheck or default = show confirmation
    skip_confirm = use_offcheck and not use_oncheck

    git_args = ["git", "push"] + git_only_args

    try:
        # Run git push
        result = subprocess.run(git_args, check=False)
        push_exit_code = result.returncode

        # Only log if push was successful
        if push_exit_code == 0:
            # Check if ClearTrack is configured
            config = load_config()
            if config and "log_file_path" in config:
                current_repo_path = get_current_repo_path()
                push_target_url = get_git_remote_url()

                if current_repo_path and push_target_url:
                    if skip_confirm:
                        # offcheck: log without yes/no prompt
                        log_contribution(config)
                        print("\n" + "=" * 60)
                        print("✅ Contribution logged (offcheck).")
                        print("=" * 60)
                    else:
                        # oncheck or default: show account info and yes/no
                        if confirm_with_user(
                            current_repo_path, push_target_url, config
                        ):
                            log_contribution(config)
                            print("\n" + "=" * 60)
                            print("✅ Contribution logged successfully!")
                            print("=" * 60)

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
