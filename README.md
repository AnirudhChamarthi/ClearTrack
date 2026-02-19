# ClearTrack

A privacy-focused contribution tracker for Git repositories. ClearTrack logs your contributions to other projects without revealing any project details - just that you've been working on something.

## Features

- ✅ **Privacy-First**: Logs contributions without revealing project details
- ✅ **Cross-Platform**: Works on Windows, Linux (including WSL), and macOS
- ✅ **Language Agnostic**: Works with any Git repository regardless of language or framework
- ✅ **Easy Installation**: Simple setup process
- ✅ **User Confirmation**: Shows repository information before logging (similar to Git's branch display)

## Installation

### Prerequisites

- Python 3.6 or higher
- Git installed and configured

### Quick Install

1. **Create a Git repository** for your contribution logs (e.g., on GitHub, GitLab, etc.)
   - You can make it private for privacy
   - The repository will only contain your contribution log file

2. **Clone or download this repository**

3. **Run the installation script:**

```bash
python install.py
```

The installer will prompt you for:
- **Log file location** (default: `~/cleartrack_logs/contributions.txt`)
- **Personal Repository URL** (required) - your personal GitHub/GitLab repository for logs
- **Personal Git Name** (required) - your name for commits to the log repository
- **Personal Git Email** (required) - your email for commits to the log repository

The installer will:
- Set up configuration in your home directory
- Create a Git alias `push-tracked` for easy use
- Create platform-specific wrapper scripts
- Clone your receiving repo (or init if using a custom path) in the log file directory
- Configure **local** Git credentials (separate from work repos) for privacy
- Perform an initial sync to your remote repository

**Privacy Note:** ClearTrack uses **local Git config** for the log repository, separate from your work repository credentials. This means:
- When you `git push-tracked` from a work repo, the work push uses work credentials
- The contribution log sync uses your personal credentials
- Neither repo or codebase knows about the other, ensuring both workplace and personal security

## Uninstall

To remove ClearTrack from your system (Git alias, wrapper scripts, and optionally config):

```bash
python uninstall.py
```

The script will:
- Remove the global Git alias `push-tracked`
- Remove ClearTrack wrapper files from `~/.cleartrack/` (folder removed only if empty)
- Remove any legacy wrappers from older installs
- Ask whether to remove the config file `~/.cleartrack_config.json`
- Display a **record of all uninstalled items**
- Show your contribution log file path (kept; delete manually if you no longer need it)
- Print the ClearTrack source folder path (install.py, cleartrack.py, etc.) so you can delete it if desired

## Usage

### Method 1: Git Alias (Recommended)

After installation, use the `push-tracked` alias:

```bash
git push-tracked
```

This will:
1. Execute `git push` with your arguments
2. If the push succeeds, show you the current repository and push target
3. Ask for confirmation
4. Log the contribution to your central log file
5. Automatically sync the log to your configured repository

### Keywords: `offcheck` and `oncheck`

- **`git push-tracked offcheck`** — Turns off the yes/no confirmation. The push runs, then the contribution is logged and synced without prompting. Use for easier flow when you always want to log.
- **`git push-tracked oncheck`** — Turns on the yes/no step (same as default). Shows push account, sync account, and asks "Proceed with logging? (yes/no)". Use when you want more visibility or to skip logging sometimes.

If you use neither keyword, the default is the same as **oncheck** (confirmation shown). You can combine with other push arguments, e.g. `git push-tracked offcheck origin main`.

- **`git push-tracked repocheck`** — Checks that the contribution log receiving repo is reachable. Does **not** run `git push`. It appends a line "repo checked" with the current date and time to your log file and pushes that to your receiving repo. Use this to verify the receiving repo is getting updates. Output: `repo checked`, then the timestamp, then a confirmation that it was pushed.

- **`git push-tracked --quiet`** — Reduces output for privacy. Skips printing repository paths, push target URLs, and account details. Shows only the confirmation prompt (when applicable) and success message. Combine with other arguments, e.g. `git push-tracked --quiet origin main`.

### Method 2: Shell Alias/Function

#### Bash/Zsh (Linux/macOS/WSL)

Add to your `~/.bashrc` or `~/.zshrc`:

```bash
# Option 1: Use the wrapper script created during installation
alias git-push='~/.cleartrack/cleartrack_push.sh'

# Option 2: Override git push (use with caution)
alias push='python /path/to/git-push-wrapper.py'
```

#### PowerShell (Windows)

Add to your PowerShell profile:

```powershell
function git-push {
    python C:\path\to\git-push-wrapper.py $args
}
```

#### Fish Shell

Add to `~/.config/fish/config.fish`:

```fish
function git-push
    python /path/to/git-push-wrapper.py $argv
end
```

### Method 3: Direct Python Script

You can also run the wrapper directly:

```bash
python git-push-wrapper.py [git push arguments]
```

## Configuration

**Wrapper scripts folder:** `~/.cleartrack/` — The install creates this folder and puts the batch/bash wrappers inside. It's easy to find and uninstall removes it completely.

**Config file:** `~/.cleartrack_config.json`:

```json
{
  "log_file_path": "/home/user/cleartrack_logs/contributions.txt",
  "log_repo_url": "https://github.com/username/cleartrack-logs.git",
  "installed_at": "2026-02-18T10:30:00"
}
```

To change settings, edit this file or re-run `install.py`.

## Repository Syncing

ClearTrack **automatically syncs** your contribution logs to your configured Git repository after each contribution. The repository URL is required during installation.

### How Syncing Works

- **Automatic**: After each successful `git push-tracked` and confirmation, the log is automatically committed and pushed to your remote repository
- **Manual**: Run `python sync-log.py` to manually sync any pending changes

The sync process:
- Clones your receiving repo (or inits) in the log file directory if needed
- Commits any new log entries
- Force-pushes to your configured remote (log repo is single source of truth)

### First-Time Setup

During installation, you'll need:
- A **personal** Git repository URL (e.g., `https://github.com/yourusername/repo.git`)
- Your personal Git name and email (used only for log commits)
- Authentication configured for your personal account:
  - **SSH keys**: Set up SSH key for your personal GitHub account
  - **HTTPS**: Use personal access token (not your work token)
  
**Important:** The log repository uses **local Git config** (separate from global/work config). This preserves privacy:
- Work repos use their own credentials
- Log sync uses personal credentials configured during install
- No credential conflicts between work and personal accounts

## Log Format

Contributions are logged to a simple text file with timestamps:

```
2026-02-18 10:30:45 - Contribution logged
2026-02-18 14:22:10 - Contribution logged
2026-02-19 09:15:33 - Contribution logged
```

No project details, repository names, or commit information is stored - just timestamps indicating that you made a contribution.

## How It Works

1. When you run `git push-tracked` (or your configured alias), ClearTrack executes `git push`
2. If the push succeeds, ClearTrack displays:
   - Current repository path
   - Push target URL
3. You confirm whether to log the contribution
4. If confirmed, a timestamp entry is added to your central log file
5. The log is automatically committed and pushed to your configured **personal** remote repository

**Privacy Preservation:**
- The work repository push uses work credentials (configured in that repo)
- The log sync uses **local Git config** with your personal credentials
- These are completely separate - your work repos never know about personal tracking
- The log repository commits show your personal name/email, not work credentials

## Platform Support

- ✅ **Windows**: Full support via Python and batch scripts
- ✅ **Linux**: Full support via bash scripts
- ✅ **macOS**: Full support via bash/zsh scripts
- ✅ **WSL**: Full support (works as Linux)

## Troubleshooting

### "ClearTrack not configured" error

Run `python install.py` to set up configuration.

### Git alias not working

Check that the alias was created:
```bash
git config --global --get alias.push-tracked
```

If it's not set, run the installer again or set it manually:
```bash
git config --global alias.push-tracked '!python /path/to/git-push-wrapper.py'
```

### Permission denied on Unix systems

Make sure wrapper scripts are executable:
```bash
chmod +x ~/.cleartrack_push.sh
chmod +x git-push-wrapper.py
```

### Python not found

Ensure Python 3 is installed and in your PATH:
```bash
python --version
# or
python3 --version
```

### Authentication errors when syncing

If you get authentication errors when syncing to your personal repository:

1. **For SSH URLs** (`git@github.com:...`):
   - Ensure your personal SSH key is configured
   - Test with: `ssh -T git@github.com`
   - The log repository uses local config, so it respects your SSH config

2. **For HTTPS URLs** (`https://github.com/...`):
   - Use a personal access token (not your work token)
   - Git will prompt for credentials on first push
   - Consider using Git Credential Manager or storing credentials securely

3. **Verify local Git config**:
   ```bash
   cd ~  # or wherever your log file is
   git config --local user.name
   git config --local user.email
   ```
   These should show your personal credentials (not work credentials).

## Privacy & Security

- ClearTrack only logs timestamps - no project details
- Configuration and log files are stored locally
- No data is sent to external servers
- Source code is open for inspection

## License

This project is provided as-is for personal use.

## Contributing

Feel free to submit issues or pull requests if you'd like to improve ClearTrack!
