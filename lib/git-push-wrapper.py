#!/usr/bin/env python3
"""
Git Push Wrapper for ClearTrack
Wraps git push and logs contributions after successful pushes.
"""

import sys
import subprocess
from pathlib import Path
from datetime import datetime

# Import cleartrack functions
sys.path.insert(0, str(Path(__file__).parent))
from cleartrack import (
    get_current_repo_path,
    get_git_remote_url,
    load_config,
    log_contribution,
    log_repocheck,
    confirm_with_user,
)


# Keywords: offcheck = skip yes/no; oncheck = show yes/no; repocheck = test receiving repo
# --quiet = minimal output (no paths, URLs, or account info)
CHECK_OFF = "offcheck"
CHECK_ON = "oncheck"
REPO_CHECK = "repocheck"
CHECK_QUIET = "--quiet"


def main():
    """Execute git push and then log contribution if successful."""
    raw_args = sys.argv[1:]

    # repocheck: only add "repo checked" + timestamp and push to receiving repo (no git push)
    if REPO_CHECK in raw_args:
        try:
            config = load_config()
            if not config or "log_file_path" not in config:
                print("Error: ClearTrack not configured. Run 'python install.py' first.", file=sys.stderr)
                sys.exit(1)
            if "log_repo_url" not in config or not config["log_repo_url"]:
                print("Error: No receiving repo configured.", file=sys.stderr)
                sys.exit(1)
            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print("repo checked")
            print(ts)
            if log_repocheck(config):
                print("Pushed to receiving repo.")
            else:
                print("Warning: push to receiving repo had errors.", file=sys.stderr)
                sys.exit(1)
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
        sys.exit(0)

    # Parse other keywords (strip so they are not passed to git push)
    git_only_args = [a for a in raw_args if a not in (CHECK_OFF, CHECK_ON, CHECK_QUIET)]
    use_offcheck = CHECK_OFF in raw_args
    use_oncheck = CHECK_ON in raw_args
    use_quiet = CHECK_QUIET in raw_args
    skip_confirm = use_offcheck and not use_oncheck
    # Work repo push: pass user args verbatim, never add --force (force is only for log repo sync)
    git_args = ["git", "push"] + git_only_args

    try:
        result = subprocess.run(git_args, check=False)
        push_exit_code = result.returncode

        if push_exit_code == 0:
            # Check if ClearTrack is configured
            config = load_config()
            if config and "log_file_path" in config:
                current_repo_path = get_current_repo_path()
                push_target_url = get_git_remote_url()

                if current_repo_path and push_target_url:
                    if skip_confirm:
                        # offcheck: log without yes/no prompt
                        log_contribution(config, quiet=use_quiet)
                        if not use_quiet:
                            print("\n" + "=" * 60)
                        print("✅ Contribution logged (offcheck).")
                        if not use_quiet:
                            print("=" * 60)
                    else:
                        # oncheck or default: show account info and yes/no
                        if confirm_with_user(
                            current_repo_path, push_target_url, config, quiet=use_quiet
                        ):
                            log_contribution(config, quiet=use_quiet)
                            if not use_quiet:
                                print("\n" + "=" * 60)
                            print("✅ Contribution logged successfully!")
                            if not use_quiet:
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
