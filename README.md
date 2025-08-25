# Trade Show Expense Tracker

A comprehensive web application for managing trade show expenses with OCR receipt scanning, multi-company support, and Zoho Books integration.

## Features

### 🎯 **Multi-Role System**
- **Admin**: Complete system management, user administration
- **Coordinator**: Trade show setup, attendee management, expense oversight
- **Accounting**: Expense approval, Zoho integration, financial reporting
- **Attendee**: Expense submission with OCR receipt scanning

### 📱 **Smart Receipt Processing**
- OCR-powered receipt scanning
- Automatic expense data extraction
- Support for images and PDF receipts
- Zoho WorkDrive integration for receipt storage

### 🏢 **Multi-Company Support**
- Boomin Brands
- Haute Brands
- Summitt Labs
- Nirvana Kulture
- Individual Zoho Books integration per company

### 📊 **Comprehensive Reporting**
- Trade show expense summaries
- Company-wise expense breakdown
- Excel export functionality
- Real-time analytics dashboards

## Quick Start

### Prerequisites
- Python 3.8+
- PythonAnywhere account (for deployment)
- Zoho Developer Account (for integrations)

### Installation

1. **Clone/Upload to PythonAnywhere**:
   ```bash
   # In PythonAnywhere console
   cd ~/mysite
   # Upload all files to this directory
   ```

2. **Install Dependencies**:
   ```bash
   pip3.10 install --user -r requirements.txt
   ```

3. **Environment Setup**:
   ```bash
   # Copy and configure environment variables
   cp config.py.example config.py
   # Edit config.py with your settings
   ```

4. **Database Setup**:
   ```bash
   python3.10 app.py
   # This will create the database and default admin user
   ```

5. **Access the Application**:
   - Navigate to `https://yourusername.pythonanywhere.com`
   - Login with: `admin` / `admin123`

## Configuration

### Required Environment Variables

```python
# Essential Settings
SECRET_KEY = "your-super-secret-key"
DATABASE_URL = "sqlite:///tradeshow_expenses.db"  # or PostgreSQL for production

# Zoho Integration
ZOHO_CLIENT_ID = "your-zoho-client-id"
ZOHO_CLIENT_SECRET = "your-zoho-client-secret"
ZOHO_WORKDRIVE_FOLDER_ID = "folder-id-for-receipts"

# Optional: OCR Services
GOOGLE_CLOUD_PROJECT_ID = "your-project-id"
AWS_ACCESS_KEY_ID = "your-aws-key"
```

### Zoho Setup

1. **Create Zoho Developer App**:
   - Go to [Zoho Developer Console](https://api-console.zoho.com/)
   - Create new app with Books and WorkDrive scopes
   - Note down Client ID and Secret

2. **Configure Companies**:
   - Login as admin
   - Go to Admin → Companies
   - Configure Zoho settings for each company

## User Management

### Default Users
- **Admin**: `admin` / `admin123`

### Creating Users
1. Login as admin
2. Navigate to Admin → Users → Create User
3. Set appropriate role:
   - **Coordinator**: Can create/manage trade shows
   - **Accounting**: Can approve expenses and manage Zoho
   - **Attendee**: Can submit expenses for assigned shows

## Usage Workflow

### 1. Setup Trade Shows (Coordinator)
```
Coordinator Dashboard → Create Trade Show → Add Attendees → Set Initial Expenses
```

### 2. Submit Expenses (Attendees)
```
My Trade Shows → Select Show → Submit Expense → Upload Receipt → OCR Scan
```

### 3. Process Expenses (Accounting)
```
Accounting Dashboard → Review Expenses → Approve → Assign Company → Push to Zoho
```

### 4. Generate Reports (Accounting)
```
Reports → Select Parameters → Generate Excel/PDF → Download
```

## Version Management

### Automated Version Tracking
The application includes sophisticated version management:

- **Version Display**: Shown in UI navbar (e.g., v1.0.0)
- **Auto-Increment**: Automatic version bumping on updates
- **GitHub Integration**: Seamless repository management
- **Release Tags**: Proper git tagging for each version

### Creating Releases
```bash
# For bug fixes (1.0.0 → 1.0.1)
python release.py patch

# For new features (1.0.1 → 1.1.0)
python release.py minor

# For major changes (1.1.0 → 2.0.0)
python release.py major
```

## PythonAnywhere Deployment

### WSGI Configuration

Create/edit `~/mysite/wsgi.py`:

```python
import sys
import os

# Add your project directory to Python path
project_home = '/home/yourusername/mysite'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Set environment
os.environ['FLASK_ENV'] = 'production'

from app import app as application

if __name__ == "__main__":
    application.run()
```

### Database Setup

For production, consider upgrading to PostgreSQL:

```bash
# In PythonAnywhere console
pip3.10 install --user psycopg2
```

Update `config.py`:
```python
SQLALCHEMY_DATABASE_URI = 'postgresql://username:password@hostname/database'
```

### File Uploads

Configure upload directory with proper permissions:

```bash
mkdir -p ~/mysite/uploads
chmod 755 ~/mysite/uploads
```

## API Integration

### Zoho Books API

The application integrates with Zoho Books for:
- Pushing approved expenses
- Syncing with company accounting systems
- Automated expense categorization

### Zoho WorkDrive API

Receipt storage integration:
- Automatic upload of scanned receipts
- Organized folder structure by trade show
- Secure file access with download links

## Troubleshooting

### Common Issues

1. **Database Errors**:
   ```bash
   # Reset database
   rm tradeshow_expenses.db
   python3.10 app.py
   ```

2. **OCR Not Working**:
   - Check Google Cloud or AWS credentials
   - Verify image format support
   - Ensure file size under 16MB

3. **Zoho Integration Fails**:
   - Verify API credentials
   - Check token expiration
   - Confirm organization IDs

### Log Files

Check application logs:
```bash
tail -f ~/mysite/logs/tradeshow_expenses.log
```

## Security Considerations

### Production Security
- Change default admin password immediately
- Use strong SECRET_KEY
- Enable HTTPS (handled by PythonAnywhere)
- Configure proper CORS if needed
- Regular backup of database

### File Security
- Receipts stored in Zoho WorkDrive
- Local files cleaned periodically
- Access control by user role

## Support & Maintenance

### Regular Tasks
- Monitor expense approval queue
- Update Zoho API tokens when expired
- Backup database regularly
- Clean temporary files

### Updates
- Check for Flask security updates
- Update OCR dependencies
- Monitor Zoho API changes

## GitHub Repository

- **Repository**: https://github.com/kidevu123/expenses
- **Releases**: Available with automated version management
- **Issues**: Track bugs and feature requests
- **Documentation**: Comprehensive guides and API docs

## License

Copyright © 2024 Trade Show Expense Management System
All rights reserved.

---

## Quick Commands Reference

```bash
# Start development server
python3.10 app.py

# Install dependencies
pip3.10 install --user -r requirements.txt

# Reset database (DEV ONLY)
rm tradeshow_expenses.db && python3.10 app.py

# Check logs
tail -f logs/tradeshow_expenses.log

# Backup database
cp tradeshow_expenses.db backup_$(date +%Y%m%d).db
```

For technical support or feature requests, contact your system administrator.