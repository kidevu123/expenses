#!/usr/bin/env python3
"""
Release management script for Trade Show Expense Tracker
Handles version incrementing, git tagging, and deployment
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path
from version import version_manager, get_version_info

def run_command(command, cwd=None):
    """Run shell command and return result"""
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            cwd=cwd or os.getcwd(),
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip(), result.stderr.strip()
    except subprocess.CalledProcessError as e:
        print(f"❌ Command failed: {command}")
        print(f"Error: {e.stderr}")
        return None, e.stderr

def check_git_status():
    """Check if git repository is clean"""
    print("🔍 Checking git status...")
    
    stdout, stderr = run_command("git status --porcelain")
    if stdout is None:
        print("❌ Git not initialized or error checking status")
        return False
    
    if stdout.strip():
        print("⚠️ Warning: You have uncommitted changes:")
        print(stdout)
        response = input("Continue anyway? (y/N): ")
        if response.lower() != 'y':
            return False
    
    print("✅ Git repository is clean")
    return True

def setup_git_repository():
    """Initialize git repository and set up remote"""
    print("🚀 Setting up git repository...")
    
    # Check if git is already initialized
    if not Path('.git').exists():
        print("Initializing git repository...")
        stdout, stderr = run_command("git init")
        if stdout is None:
            print("❌ Failed to initialize git repository")
            return False
    
    # Add remote origin
    print("Adding GitHub remote...")
    stdout, stderr = run_command("git remote get-url origin")
    if stdout is None:
        stdout, stderr = run_command("git remote add origin https://github.com/kidevu123/expenses.git")
        if stdout is None:
            print("❌ Failed to add remote origin")
            return False
        print("✅ Added remote origin")
    else:
        print("✅ Remote origin already configured")
    
    return True

def commit_and_push(version_type, message=None):
    """Commit changes and push to GitHub"""
    print(f"📝 Committing changes for {version_type} release...")
    
    # Add all files
    stdout, stderr = run_command("git add .")
    if stdout is None:
        return False
    
    # Get current version info
    version_info = get_version_info()
    commit_message = message or f"Release version {version_info['version']}"
    
    # Commit changes
    stdout, stderr = run_command(f'git commit -m "{commit_message}"')
    if stdout is None and "nothing to commit" not in stderr:
        return False
    
    # Create git tag
    tag_name = version_manager.create_git_tag()
    if tag_name:
        print(f"✅ Created git tag: {tag_name}")
    
    # Push to GitHub
    print("🚀 Pushing to GitHub...")
    stdout, stderr = run_command("git push origin main")
    if stdout is None:
        print("❌ Failed to push to main branch")
        return False
    
    # Push tags
    stdout, stderr = run_command("git push origin --tags")
    if stdout is None:
        print("❌ Failed to push tags")
        return False
    
    print("✅ Successfully pushed to GitHub with tags")
    return True

def create_release(version_type='patch', message=None):
    """Create a new release"""
    print(f"🎉 Creating {version_type} release...")
    
    # Check git status
    if not check_git_status():
        return False
    
    # Setup git repository
    if not setup_git_repository():
        return False
    
    # Increment version
    old_version = get_version_info()['version']
    new_version = version_manager.increment_version(version_type)
    
    print(f"📈 Version incremented: {old_version} → {new_version}")
    
    # Commit and push changes
    if not commit_and_push(version_type, message):
        return False
    
    print(f"🎉 Release {new_version} created successfully!")
    print(f"🔗 GitHub Repository: https://github.com/kidevu123/expenses")
    print(f"📋 Version: {new_version}")
    print(f"🏷️ Tag: v{new_version}")
    
    return True

def show_version():
    """Show current version information"""
    version_info = get_version_info()
    
    print("📊 Current Version Information:")
    print(f"Version: {version_info['version']}")
    print(f"Build: {version_info['build']}")
    if version_info['release_date']:
        print(f"Released: {version_info['release_date']}")
    if version_info['git_branch']:
        print(f"Branch: {version_info['git_branch']}")
    if version_info['git_commit']:
        print(f"Commit: {version_info['git_commit']}")

def deploy_to_pythonanywhere():
    """Instructions for deploying to PythonAnywhere"""
    print("\n🌐 PythonAnywhere Deployment Instructions:")
    print("=" * 50)
    print("1. Upload files to your PythonAnywhere account:")
    print("   - Go to Files tab in PythonAnywhere")
    print("   - Navigate to ~/mysite/")
    print("   - Upload all project files")
    print()
    print("2. Install dependencies:")
    print("   pip3.10 install --user -r requirements.txt")
    print()
    print("3. Set up database:")
    print("   python3.10 app.py")
    print()
    print("4. Configure WSGI file:")
    print("   - Update wsgi.py with your username")
    print("   - Set FLASK_ENV=production")
    print()
    print("5. Test application:")
    print("   https://yourusername.pythonanywhere.com")
    print()
    print("🔗 For detailed instructions, see README.md")

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Release management for Trade Show Expense Tracker')
    parser.add_argument('action', choices=['show', 'patch', 'minor', 'major', 'deploy-info'], 
                       help='Action to perform')
    parser.add_argument('-m', '--message', help='Custom commit message')
    
    args = parser.parse_args()
    
    print("🎯 Trade Show Expense Tracker - Release Manager")
    print("=" * 50)
    
    if args.action == 'show':
        show_version()
    elif args.action in ['patch', 'minor', 'major']:
        if create_release(args.action, args.message):
            deploy_to_pythonanywhere()
        else:
            sys.exit(1)
    elif args.action == 'deploy-info':
        deploy_to_pythonanywhere()

if __name__ == "__main__":
    main()