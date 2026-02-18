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

1. Clone or download this repository
2. Run the installation script:

```bash
python install.py
```

The installer will:
- Set up configuration in your home directory
- Create a Git alias `push-tracked` for easy use
- Create platform-specific wrapper scripts

### Manual Setup (Alternative)

If you prefer not to use the installer:

1. Copy `cleartrack.py` to a location in your PATH
2. Create a configuration file at `~/.cleartrack_config.json`:

```json
{
  "log_file_path": "/path/to/your/contributions.txt"
}
```

3. Set up a Git alias or shell wrapper (see Usage section)

## Uninstall

To remove ClearTrack from your system (Git alias, wrapper scripts, and optionally config):

```bash
python uninstall.py
```

The script will:
- Remove the global Git alias `push-tracked`
- Delete the wrapper script (e.g. `cleartrack_push.bat` on Windows, `~/.cleartrack_push.sh` on Unix)
- Ask whether to remove the config file `~/.cleartrack_config.json`

Your contribution log file is **not** deleted. Delete it manually if you no longer need it. The ClearTrack folder (this repo) is left as-is; remove it yourself if desired.

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

### Method 2: Shell Alias/Function

#### Bash/Zsh (Linux/macOS/WSL)

Add to your `~/.bashrc` or `~/.zshrc`:

```bash
# Option 1: Use the wrapper script created during installation
alias git-push='~/.cleartrack_push.sh'

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

Configuration is stored in `~/.cleartrack_config.json`:

```json
{
  "log_file_path": "/home/user/cleartrack_contributions.txt",
  "installed_at": "2026-02-18T10:30:00"
}
```

To change the log file location, edit this file or re-run `install.py`.

## Repository Syncing (Optional)

You can sync your contribution logs to a Git repository (e.g., GitHub, GitLab) for backup, cross-device access, or sharing.

### Quick Setup

1. **Create a repository** on GitHub, GitLab, or any Git hosting service
   - You can make it private for privacy
   - The repository will only contain your contribution log file

2. **Run the setup script:**
   ```bash
   python setup-log-repo.py
   ```

3. **Enter your repository URL** when prompted (e.g., `https://github.com/username/cleartrack-logs.git`)

4. **Choose auto-sync option:**
   - **Enabled**: Logs automatically sync after each contribution
   - **Disabled**: Manually sync with `python sync-log.py`

### Manual Setup

Alternatively, edit `~/.cleartrack_config.json` and add:

```json
{
  "log_file_path": "/home/user/cleartrack_contributions.txt",
  "installed_at": "2026-02-18T10:30:00",
  "log_repo_url": "https://github.com/username/cleartrack-logs.git",
  "auto_sync_log": false
}
```

### Syncing Logs

- **Automatic** (if `auto_sync_log` is `true`): Logs sync automatically after each contribution
- **Manual**: Run `python sync-log.py` to sync at any time

The sync script will:
- Initialize a Git repository in your log file directory (if needed)
- Commit any new log entries
- Push to your configured remote repository

### First-Time Sync

On first sync, you may need to:
- Set up authentication (SSH keys or personal access tokens)
- Configure Git user name/email if not already set:
  ```bash
  git config --global user.name "Your Name"
  git config --global user.email "your.email@example.com"
  ```

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
5. If repository syncing is enabled, the log is automatically committed and pushed to your remote repository

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

## Privacy & Security

- ClearTrack only logs timestamps - no project details
- Configuration and log files are stored locally
- No data is sent to external servers
- Source code is open for inspection

## License

This project is provided as-is for personal use.

## Contributing

Feel free to submit issues or pull requests if you'd like to improve ClearTrack!
