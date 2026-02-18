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
