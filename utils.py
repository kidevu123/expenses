from functools import wraps
from flask import redirect, url_for, flash, current_app
from flask_login import current_user
import os
import re
import requests
import json
from datetime import datetime, date
from decimal import Decimal
import uuid
import pandas as pd
from io import BytesIO
import base64

# File upload settings
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf'}

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Role-based access decorators
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('Access denied. Admin privileges required.', 'error')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

def coordinator_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role not in ['admin', 'coordinator']:
            flash('Access denied. Coordinator privileges required.', 'error')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

def accounting_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role not in ['admin', 'accounting']:
            flash('Access denied. Accounting privileges required.', 'error')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

def attendee_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

# OCR Processing Functions
def process_receipt_ocr(file_path):
    """
    Process receipt using OCR to extract information
    This is a placeholder implementation. In production, you would use:
    - Google Cloud Vision API
    - AWS Textract
    - Azure Computer Vision
    - Tesseract OCR
    """
    try:
        # Placeholder OCR processing
        # In a real implementation, you would:
        # 1. Use an OCR service to extract text
        # 2. Use regex patterns to find amounts, dates, merchants
        # 3. Apply machine learning models for better accuracy
        
        # Simulate OCR results
        ocr_results = {
            'text': 'Sample receipt text extracted from OCR',
            'confidence': 0.85,
            'amount': None,
            'date': None,
            'merchant': None
        }
        
        # Simple regex patterns for demonstration
        # In production, use more sophisticated methods
        sample_text = "Restaurant ABC\nDate: 2024-01-15\nTotal: $45.50\nThank you!"
        
        # Extract amount
        amount_pattern = r'\$?(\d+\.?\d*)'
        amount_match = re.search(amount_pattern, sample_text)
        if amount_match:
            ocr_results['amount'] = Decimal(amount_match.group(1))
        
        # Extract date
        date_pattern = r'(\d{4}-\d{2}-\d{2})'
        date_match = re.search(date_pattern, sample_text)
        if date_match:
            ocr_results['date'] = datetime.strptime(date_match.group(1), '%Y-%m-%d').date()
        
        # Extract merchant (first line typically)
        lines = sample_text.split('\n')
        if lines:
            ocr_results['merchant'] = lines[0].strip()
        
        return ocr_results
        
    except Exception as e:
        current_app.logger.error(f"OCR processing error: {str(e)}")
        return {
            'text': '',
            'confidence': 0,
            'amount': None,
            'date': None,
            'merchant': None
        }

# Zoho Integration Functions
def get_zoho_access_token(company):
    """
    Refresh Zoho access token using refresh token
    """
    if not company.zoho_refresh_token:
        return None
    
    try:
        refresh_url = "https://accounts.zoho.com/oauth/v2/token"
        
        data = {
            'refresh_token': company.zoho_refresh_token,
            'client_id': os.environ.get('ZOHO_CLIENT_ID'),
            'client_secret': os.environ.get('ZOHO_CLIENT_SECRET'),
            'grant_type': 'refresh_token'
        }
        
        response = requests.post(refresh_url, data=data)
        
        if response.status_code == 200:
            token_data = response.json()
            company.zoho_access_token = token_data['access_token']
            # Save to database
            from models import db
            db.session.commit()
            return token_data['access_token']
        else:
            current_app.logger.error(f"Failed to refresh Zoho token: {response.text}")
            return None
            
    except Exception as e:
        current_app.logger.error(f"Zoho token refresh error: {str(e)}")
        return None

def upload_to_zoho_workdrive(file_path, original_filename):
    """
    Upload receipt to Zoho WorkDrive
    """
    try:
        # This is a placeholder implementation
        # In production, you would:
        # 1. Get Zoho WorkDrive access token
        # 2. Upload file to specific folder
        # 3. Return file ID and download URL
        
        # Simulate successful upload
        file_id = str(uuid.uuid4())
        download_url = f"https://workdrive.zoho.com/file/{file_id}/download"
        
        return {
            'success': True,
            'file_id': file_id,
            'download_url': download_url
        }
        
    except Exception as e:
        current_app.logger.error(f"Zoho WorkDrive upload error: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }

def push_expense_to_zoho(expense):
    """
    Push expense to Zoho Books
    """
    try:
        if not expense.company:
            return {'success': False, 'error': 'No company assigned'}
        
        access_token = get_zoho_access_token(expense.company)
        if not access_token:
            return {'success': False, 'error': 'Failed to get Zoho access token'}
        
        # Prepare expense data for Zoho Books
        expense_data = {
            'account_name': 'Expense Account',  # Configure based on category
            'amount': float(expense.amount),
            'currency_code': expense.currency,
            'date': expense.expense_date.strftime('%Y-%m-%d'),
            'description': expense.description,
            'employee_id': expense.user.email,  # Use email as employee identifier
            'expense_type': 'non_billable',
            'merchant_name': expense.title,
            'project_name': expense.tradeshow.name,
            'receipt_name': expense.receipt.original_filename if expense.receipt else None
        }
        
        headers = {
            'Authorization': f'Zoho-oauthtoken {access_token}',
            'Content-Type': 'application/json'
        }
        
        # Zoho Books API endpoint
        api_url = f"https://books.zoho.com/api/v3/expenses?organization_id={expense.company.zoho_org_id}"
        
        response = requests.post(api_url, json=expense_data, headers=headers)
        
        if response.status_code in [200, 201]:
            result = response.json()
            expense_id = result.get('expense', {}).get('expense_id')
            return {
                'success': True,
                'expense_id': expense_id,
                'response': result
            }
        else:
            return {
                'success': False,
                'error': f"Zoho API error: {response.status_code} - {response.text}"
            }
            
    except Exception as e:
        current_app.logger.error(f"Zoho Books push error: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }

# Reporting Functions
def generate_expense_report(report_type='html', tradeshow_id=None, company_id=None, start_date=None, end_date=None):
    """
    Generate expense reports in various formats
    """
    from models import Expense, TradeShow, Company, User, ExpenseCategory
    
    # Build query
    query = Expense.query
    
    if tradeshow_id:
        query = query.filter_by(tradeshow_id=tradeshow_id)
    if company_id:
        query = query.filter_by(company_id=company_id)
    if start_date:
        query = query.filter(Expense.expense_date >= start_date)
    if end_date:
        query = query.filter(Expense.expense_date <= end_date)
    
    expenses = query.all()
    
    # Prepare report data
    report_data = {
        'title': 'Expense Report',
        'generated_at': datetime.now(),
        'filters': {
            'tradeshow': TradeShow.query.get(tradeshow_id).name if tradeshow_id else None,
            'company': Company.query.get(company_id).name if company_id else None,
            'start_date': start_date,
            'end_date': end_date
        },
        'expenses': expenses,
        'total_amount': sum(expense.amount for expense in expenses),
        'expense_count': len(expenses)
    }
    
    if report_type == 'excel':
        return generate_excel_report(report_data)
    else:
        return report_data

def generate_excel_report(report_data):
    """
    Generate Excel report
    """
    try:
        # Create DataFrame
        expense_list = []
        for expense in report_data['expenses']:
            expense_list.append({
                'Date': expense.expense_date,
                'Trade Show': expense.tradeshow.name,
                'User': expense.user.full_name,
                'Company': expense.company.name if expense.company else '',
                'Category': expense.category.name if expense.category else '',
                'Title': expense.title,
                'Description': expense.description,
                'Amount': float(expense.amount),
                'Currency': expense.currency,
                'Status': expense.status,
                'Approved By': expense.approver.full_name if expense.approver else '',
                'Approved At': expense.approved_at,
                'Zoho ID': expense.zoho_expense_id or '',
                'Pushed to Zoho': 'Yes' if expense.pushed_to_zoho else 'No'
            })
        
        df = pd.DataFrame(expense_list)
        
        # Create Excel file in memory
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Expenses', index=False)
            
            # Add summary sheet
            summary_data = {
                'Metric': ['Total Expenses', 'Total Amount', 'Report Generated'],
                'Value': [
                    report_data['expense_count'],
                    f"${report_data['total_amount']:,.2f}",
                    report_data['generated_at'].strftime('%Y-%m-%d %H:%M:%S')
                ]
            }
            summary_df = pd.DataFrame(summary_data)
            summary_df.to_excel(writer, sheet_name='Summary', index=False)
        
        output.seek(0)
        
        # Save to temp file
        filename = f"expense_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        temp_path = os.path.join('temp', filename)
        os.makedirs('temp', exist_ok=True)
        
        with open(temp_path, 'wb') as f:
            f.write(output.getvalue())
        
        return {
            'file_path': temp_path,
            'filename': filename,
            'success': True
        }
        
    except Exception as e:
        current_app.logger.error(f"Excel report generation error: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }

# Data validation functions
def validate_expense_data(data):
    """
    Validate expense data before submission
    """
    errors = []
    
    if not data.get('title'):
        errors.append('Title is required')
    
    if not data.get('amount'):
        errors.append('Amount is required')
    else:
        try:
            amount = Decimal(str(data['amount']))
            if amount <= 0:
                errors.append('Amount must be greater than 0')
        except:
            errors.append('Invalid amount format')
    
    if not data.get('expense_date'):
        errors.append('Expense date is required')
    else:
        try:
            expense_date = datetime.strptime(data['expense_date'], '%Y-%m-%d').date()
            if expense_date > date.today():
                errors.append('Expense date cannot be in the future')
        except:
            errors.append('Invalid date format')
    
    if not data.get('category_id'):
        errors.append('Category is required')
    
    return errors

# Email notification functions (placeholder)
def send_notification_email(to_email, subject, message):
    """
    Send notification email
    In production, integrate with email service like SendGrid, AWS SES, etc.
    """
    try:
        # Placeholder for email sending
        current_app.logger.info(f"Email notification sent to {to_email}: {subject}")
        return True
    except Exception as e:
        current_app.logger.error(f"Email sending error: {str(e)}")
        return False

def notify_expense_submission(expense):
    """
    Notify relevant parties about expense submission
    """
    # Notify accounting team
    accounting_users = User.query.filter_by(role='accounting', is_active=True).all()
    for user in accounting_users:
        send_notification_email(
            user.email,
            f"New Expense Submitted: {expense.title}",
            f"A new expense has been submitted by {expense.user.full_name} for {expense.tradeshow.name}"
        )

def notify_expense_approval(expense):
    """
    Notify user about expense approval/rejection
    """
    status = expense.status.title()
    send_notification_email(
        expense.user.email,
        f"Expense {status}: {expense.title}",
        f"Your expense '{expense.title}' has been {status.lower()}."
    )