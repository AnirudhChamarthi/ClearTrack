#!/usr/bin/env python3
"""
Simple test script for ClearTrack
Tests basic functionality without requiring actual git pushes.
"""

import sys
from pathlib import Path

# Ensure cleartrack can be imported (it lives in lib/)
sys.path.insert(0, str(Path(__file__).resolve().parent / "lib"))

import json
import subprocess
from datetime import datetime

def test_config():
    """Test configuration loading."""
    print("Test 1: Configuration")
    print("-" * 40)
    
    try:
        from cleartrack import load_config, get_config_path
        config = load_config()
        if config:
            print(f"✅ Configuration found: {get_config_path()}")
            print(f"   Log file: {config.get('log_file_path', 'Not set')}")
            return True
        else:
            print("❌ No configuration found. Run 'python install.py' first.")
            return False
    except Exception as e:
        print(f"❌ Error loading config: {e}")
        return False


def test_git_repo():
    """Test if we're in a Git repository."""
    print("\nTest 2: Git Repository Detection")
    print("-" * 40)
    
    try:
        from cleartrack import get_current_repo_path, get_git_remote_url
        
        repo_path = get_current_repo_path()
        if repo_path:
            print(f"✅ In Git repository: {repo_path}")
            
            remote_url = get_git_remote_url()
            if remote_url:
                print(f"✅ Remote URL: {remote_url}")
            else:
                print("⚠️  No remote URL configured (this is okay)")
            return True
        else:
            print("❌ Not in a Git repository")
            print("   Navigate to a Git repo to test full functionality")
            return False
    except Exception as e:
        print(f"❌ Error detecting Git repo: {e}")
        return False


def test_log_file():
    """Test log file access."""
    print("\nTest 3: Log File Access")
    print("-" * 40)
    
    try:
        from cleartrack import load_config
        
        config = load_config()
        if not config:
            print("⚠️  Skipping - no configuration")
            return False
        
        log_path = Path(config['log_file_path'])
        log_dir = log_path.parent
        
        # Check if directory exists or can be created
        try:
            log_dir.mkdir(parents=True, exist_ok=True)
            print(f"✅ Log directory accessible: {log_dir}")
        except Exception as e:
            print(f"❌ Cannot access log directory: {e}")
            return False
        
        # Check if file exists or can be created
        try:
            # Try to append (create if doesn't exist)
            with open(log_path, 'a') as f:
                pass
            print(f"✅ Log file accessible: {log_path}")
            
            # Show existing entries if any
            if log_path.exists() and log_path.stat().st_size > 0:
                with open(log_path, 'r') as f:
                    lines = f.readlines()
                    print(f"   Found {len(lines)} existing log entries")
            else:
                print("   (Log file is empty - this is normal for first run)")
            
            return True
        except Exception as e:
            print(f"❌ Cannot access log file: {e}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing log file: {e}")
        return False


def test_wrapper_import():
    """Test that wrapper script can import cleartrack."""
    print("\nTest 4: Module Imports")
    print("-" * 40)
    
    try:
        # Test importing cleartrack
        import cleartrack
        print("✅ cleartrack module imports successfully")
        
        # Test that wrapper script exists and can be executed
        wrapper_path = Path(__file__).parent / "lib" / "git-push-wrapper.py"
        if wrapper_path.exists():
            print(f"✅ git-push-wrapper.py exists: {wrapper_path}")
            
            # Test that it can import cleartrack (simulate what wrapper does)
            from cleartrack import get_current_repo_path, load_config
            print("✅ Wrapper can import cleartrack functions")
        else:
            print(f"❌ git-push-wrapper.py not found")
            return False
        
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_connectivity():
    """Test connectivity to the log repository (ls-remote, no changes)."""
    print("\nTest 5: Log Repository Connectivity")
    print("-" * 40)

    try:
        from cleartrack import load_config, diagnose_sync

        config = load_config()
        if not config:
            print("⚠️  Skipping - no configuration")
            return False
        if "log_repo_url" not in config or not config["log_repo_url"]:
            print("⚠️  Skipping - no log_repo_url configured")
            return False

        ok, msgs = diagnose_sync(config, verbose=True)
        for m in msgs:
            print(f"  {m}")
        if ok:
            print("✅ Log repository is reachable")
            return True
        else:
            print("❌ Log repository not reachable (check URL, auth, network)")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_git_alias():
    """Test if Git alias is configured."""
    print("\nTest 6: Git Alias Configuration")
    print("-" * 40)
    
    try:
        result = subprocess.run(
            ['git', 'config', '--global', '--get', 'alias.push-tracked'],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print(f"✅ Git alias 'push-tracked' is configured")
            print(f"   Command: {result.stdout.strip()}")
            return True
        else:
            print("⚠️  Git alias 'push-tracked' not configured")
            print("   Run 'python install.py' to set it up")
            return False
    except Exception as e:
        print(f"❌ Error checking Git alias: {e}")
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("ClearTrack Test Suite")
    print("=" * 60)
    
    results = []
    results.append(("Configuration", test_config()))
    results.append(("Git Repository", test_git_repo()))
    results.append(("Log File", test_log_file()))
    results.append(("Module Imports", test_wrapper_import()))
    results.append(("Log Repo Connectivity", test_connectivity()))
    results.append(("Git Alias", test_git_alias()))
    
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! ClearTrack is ready to use.")
        print("\nNext steps:")
        print("  1. Navigate to a Git repository")
        print("  2. Run: git push-tracked")
        print("  3. Confirm when prompted")
        print("  4. Check your log file for the entry")
    else:
        print("\n⚠️  Some tests failed. Please fix the issues above.")
        print("\nCommon fixes:")
        print("  - Run 'python install.py' to set up configuration")
        print("  - Make sure you're in a Git repository for full testing")
        print("  - Check that Python 3.6+ is installed")


if __name__ == "__main__":
    main()
