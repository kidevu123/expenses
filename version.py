"""
Version management for Trade Show Expense Tracker
Handles automatic version incrementing and display
"""

import os
import json
import subprocess
from datetime import datetime
from pathlib import Path

# Version configuration
VERSION_FILE = 'version.json'
DEFAULT_VERSION = {
    'major': 1,
    'minor': 0,
    'patch': 0,
    'build': 0,
    'release_date': None,
    'git_commit': None,
    'git_branch': None
}

class VersionManager:
    def __init__(self):
        self.version_file = Path(VERSION_FILE)
        self.version_data = self._load_version()
    
    def _load_version(self):
        """Load version data from file or create default"""
        if self.version_file.exists():
            try:
                with open(self.version_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                pass
        return DEFAULT_VERSION.copy()
    
    def _save_version(self):
        """Save version data to file"""
        with open(self.version_file, 'w') as f:
            json.dump(self.version_data, f, indent=2)
    
    def get_version_string(self):
        """Get formatted version string"""
        v = self.version_data
        return f"{v['major']}.{v['minor']}.{v['patch']}.{v['build']}"
    
    def get_full_version_info(self):
        """Get complete version information"""
        v = self.version_data
        
        # Get git information if available
        git_commit = self._get_git_commit()
        git_branch = self._get_git_branch()
        
        return {
            'version': self.get_version_string(),
            'major': v['major'],
            'minor': v['minor'],
            'patch': v['patch'],
            'build': v['build'],
            'release_date': v.get('release_date'),
            'git_commit': git_commit or v.get('git_commit'),
            'git_branch': git_branch or v.get('git_branch'),
            'display_name': f"v{self.get_version_string()}"
        }
    
    def _get_git_commit(self):
        """Get current git commit hash"""
        try:
            result = subprocess.run(
                ['git', 'rev-parse', '--short', 'HEAD'],
                capture_output=True,
                text=True,
                cwd=os.path.dirname(os.path.abspath(__file__))
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except (subprocess.SubprocessError, FileNotFoundError):
            pass
        return None
    
    def _get_git_branch(self):
        """Get current git branch"""
        try:
            result = subprocess.run(
                ['git', 'branch', '--show-current'],
                capture_output=True,
                text=True,
                cwd=os.path.dirname(os.path.abspath(__file__))
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except (subprocess.SubprocessError, FileNotFoundError):
            pass
        return None
    
    def increment_version(self, version_type='patch'):
        """Increment version number"""
        if version_type == 'major':
            self.version_data['major'] += 1
            self.version_data['minor'] = 0
            self.version_data['patch'] = 0
        elif version_type == 'minor':
            self.version_data['minor'] += 1
            self.version_data['patch'] = 0
        elif version_type == 'patch':
            self.version_data['patch'] += 1
        
        # Always increment build number
        self.version_data['build'] += 1
        
        # Update metadata
        self.version_data['release_date'] = datetime.now().isoformat()
        self.version_data['git_commit'] = self._get_git_commit()
        self.version_data['git_branch'] = self._get_git_branch()
        
        self._save_version()
        return self.get_version_string()
    
    def create_git_tag(self):
        """Create git tag for current version"""
        version = self.get_version_string()
        tag_name = f"v{version}"
        
        try:
            # Create annotated tag
            subprocess.run([
                'git', 'tag', '-a', tag_name, '-m', f"Release version {version}"
            ], check=True, cwd=os.path.dirname(os.path.abspath(__file__)))
            
            return tag_name
        except (subprocess.SubprocessError, FileNotFoundError):
            return None

# Global version manager instance
version_manager = VersionManager()

def get_version():
    """Get current version string"""
    return version_manager.get_version_string()

def get_version_info():
    """Get complete version information"""
    return version_manager.get_full_version_info()

def increment_version(version_type='patch'):
    """Increment version and return new version string"""
    return version_manager.increment_version(version_type)

def create_release_tag():
    """Create git tag for current version"""
    return version_manager.create_git_tag()