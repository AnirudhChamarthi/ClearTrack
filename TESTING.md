# Testing ClearTrack

## Quick Test Guide

### Step 1: Install ClearTrack

```bash
python install.py
```

This will:
- Ask you where to store the log file (default: `~/cleartrack_contributions.txt`)
- Set up the Git alias `push-tracked`
- Create wrapper scripts

### Step 2: Verify Installation

Check that the configuration was created:
```bash
# On Windows PowerShell
cat $env:USERPROFILE\.cleartrack_config.json

# On Linux/macOS/WSL
cat ~/.cleartrack_config.json
```

Check that the Git alias was created:
```bash
git config --global --get alias.push-tracked
```

### Step 3: Test in a Git Repository

1. Navigate to any Git repository (or create a test one):
```bash
cd /path/to/your/git/repo
# Or create a test repo:
mkdir test-cleartrack
cd test-cleartrack
git init
git remote add origin https://github.com/yourusername/test-repo.git
```

2. Make a test commit (if needed):
```bash
echo "test" > test.txt
git add test.txt
git commit -m "Test commit"
```

3. Test ClearTrack (without actually pushing):
```bash
# This will show the confirmation dialog but won't push if you cancel
git push-tracked --dry-run

# Or test with a real push (if you have a test repository):
git push-tracked
```

### Step 4: Verify Logging

After confirming "yes" to the prompt, check the log file:
```bash
# On Windows PowerShell
cat $env:USERPROFILE\cleartrack_contributions.txt

# On Linux/macOS/WSL
cat ~/cleartrack_contributions.txt
```

You should see a timestamp entry like:
```
2026-02-18 10:30:45 - Contribution logged
```

## Testing Scenarios

### Test 1: Basic Functionality
- ✅ Run `git push-tracked` in a Git repo
- ✅ Verify the confirmation dialog appears
- ✅ Confirm and verify log entry is created

### Test 2: Cancellation
- ✅ Run `git push-tracked`
- ✅ Answer "no" to the prompt
- ✅ Verify no log entry is created

### Test 3: Failed Push
- ✅ Try pushing to a non-existent remote
- ✅ Verify ClearTrack doesn't log failed pushes

### Test 4: Multiple Repositories
- ✅ Test in different Git repositories
- ✅ Verify all log to the same central file

## Exit Code 128 (Git Fatal Error)

When `git push` returns 128, ClearTrack now shows the full Git error (e.g., authentication failed, repository not found). Run:

```bash
git push-tracked diagnose
# or
python sync-log.py --test
```

to test connectivity without pushing. Fix auth/URL/network issues based on the error output.

## Troubleshooting Tests

If something doesn't work:

1. **Check Python version:**
   ```bash
   python --version  # Should be 3.6+
   ```

2. **Check Git is installed:**
   ```bash
   git --version
   ```

3. **Verify you're in a Git repo:**
   ```bash
   git rev-parse --git-dir
   ```

4. **Check script permissions (Unix):**
   ```bash
   ls -l git-push-wrapper.py
   chmod +x git-push-wrapper.py  # If needed
   ```

5. **Test connectivity (no push, no changes):**
   ```bash
   python sync-log.py --test
   # or
   git push-tracked diagnose
   ```

6. **Test the wrapper directly:**
   ```bash
   python lib/git-push-wrapper.py diagnose
   ```

7. **Test cleartrack.py directly:**
   ```bash
   python cleartrack.py
   # Should show "Error: Not in a Git repository" if not in a repo
   ```
