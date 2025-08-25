#!/usr/bin/env python3
"""
Deployment script for Trade Show Expense Tracker
Helps set up the application on PythonAnywhere or other hosting platforms
"""

import os
import sys
import subprocess
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        return False
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} is compatible")
    return True

def install_dependencies():
    """Install required Python packages"""
    print("\n📦 Installing dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError:
        print("❌ Failed to install dependencies")
        return False

def setup_directories():
    """Create necessary directories"""
    print("\n📁 Setting up directories...")
    directories = ['uploads', 'temp', 'logs', 'static/uploads']
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"✅ Created directory: {directory}")

def setup_database():
    """Initialize database with default data"""
    print("\n🗄️ Setting up database...")
    try:
        from app import app, db, create_default_data
        with app.app_context():
            db.create_all()
            create_default_data()
        print("✅ Database initialized successfully")
        return True
    except Exception as e:
        print(f"❌ Database setup failed: {e}")
        return False

def check_config():
    """Check if configuration is properly set"""
    print("\n⚙️ Checking configuration...")
    
    try:
        from config import Config
        
        # Check for essential settings
        warnings = []
        
        if Config.SECRET_KEY == 'dev-secret-key-change-in-production':
            warnings.append("⚠️ Please change the SECRET_KEY in production")
        
        if not Config.ZOHO_CLIENT_ID:
            warnings.append("⚠️ ZOHO_CLIENT_ID not configured")
            
        if not Config.ZOHO_CLIENT_SECRET:
            warnings.append("⚠️ ZOHO_CLIENT_SECRET not configured")
        
        if warnings:
            print("Configuration warnings:")
            for warning in warnings:
                print(f"  {warning}")
        else:
            print("✅ Configuration looks good")
            
        return True
    except Exception as e:
        print(f"❌ Configuration check failed: {e}")
        return False

def create_wsgi_file():
    """Create WSGI file for PythonAnywhere"""
    print("\n🌐 Creating WSGI configuration...")
    
    wsgi_content = '''# WSGI file for PythonAnywhere deployment
import sys
import os

# Add your project directory to the Python path
project_home = '/home/yourusername/mysite'  # Change 'yourusername' to your username
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Set environment to production
os.environ['FLASK_ENV'] = 'production'

from app import app as application

if __name__ == "__main__":
    application.run()
'''
    
    with open('wsgi.py', 'w') as f:
        f.write(wsgi_content)
    
    print("✅ WSGI file created (remember to update the project path)")

def print_next_steps():
    """Print next steps after deployment"""
    print("\n🎉 Deployment setup complete!")
    print("\n📋 Next steps:")
    print("1. Update wsgi.py with your correct PythonAnywhere path")
    print("2. Configure environment variables in config.py")
    print("3. Set up Zoho API credentials")
    print("4. Change the default admin password (admin/admin123)")
    print("5. Test the application by visiting your PythonAnywhere URL")
    print("\n🔗 Default login: admin / admin123")
    print("📖 For detailed instructions, see README.md")

def main():
    """Main deployment function"""
    print("🚀 Trade Show Expense Tracker Deployment Script")
    print("=" * 50)
    
    if not check_python_version():
        sys.exit(1)
    
    if not install_dependencies():
        print("\n💡 Try running: pip install --user -r requirements.txt")
        sys.exit(1)
    
    setup_directories()
    
    if not setup_database():
        print("\n💡 You may need to set up the database manually")
    
    check_config()
    create_wsgi_file()
    print_next_steps()

if __name__ == "__main__":
    main()