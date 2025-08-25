from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    full_name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # admin, coordinator, accounting, attendee
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    assignments = db.relationship('TradeShowAssignment', backref='user', lazy='dynamic')
    expenses = db.relationship('Expense', backref='user', lazy='dynamic')

class Company(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    zoho_org_id = db.Column(db.String(100))  # Zoho Books organization ID
    zoho_access_token = db.Column(db.Text)   # Zoho API access token
    zoho_refresh_token = db.Column(db.Text)  # Zoho API refresh token
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    expenses = db.relationship('Expense', backref='company', lazy='dynamic')

class TradeShow(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    location = db.Column(db.String(200), nullable=False)
    status = db.Column(db.String(20), default='planning')  # planning, active, completed, cancelled
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    assignments = db.relationship('TradeShowAssignment', backref='tradeshow', lazy='dynamic')
    expenses = db.relationship('Expense', backref='tradeshow', lazy='dynamic')
    creator = db.relationship('User', backref='created_tradeshows')

class TradeShowAssignment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    tradeshow_id = db.Column(db.Integer, db.ForeignKey('trade_show.id'), nullable=False)
    role_in_show = db.Column(db.String(50))  # attendee, coordinator, etc.
    flight_details = db.Column(db.Text)
    hotel_details = db.Column(db.Text)
    notes = db.Column(db.Text)
    assigned_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (db.UniqueConstraint('user_id', 'tradeshow_id', name='unique_user_tradeshow'),)

class ExpenseCategory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    expenses = db.relationship('Expense', backref='category', lazy='dynamic')

class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tradeshow_id = db.Column(db.Integer, db.ForeignKey('trade_show.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'))
    category_id = db.Column(db.Integer, db.ForeignKey('expense_category.id'))
    
    # Expense details
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    amount = db.Column(db.Decimal(10, 2), nullable=False)
    currency = db.Column(db.String(3), default='USD')
    expense_date = db.Column(db.Date, nullable=False)
    
    # Receipt information
    receipt_id = db.Column(db.Integer, db.ForeignKey('receipt.id'))
    
    # Approval and processing
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected, processed
    approved_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    approved_at = db.Column(db.DateTime)
    
    # Zoho integration
    zoho_expense_id = db.Column(db.String(100))  # ID in Zoho Books
    pushed_to_zoho = db.Column(db.Boolean, default=False)
    zoho_push_date = db.Column(db.DateTime)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    approver = db.relationship('User', foreign_keys=[approved_by], backref='approved_expenses')

class Receipt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_size = db.Column(db.Integer)
    mime_type = db.Column(db.String(100))
    
    # OCR results
    ocr_text = db.Column(db.Text)
    ocr_confidence = db.Column(db.Float)
    extracted_amount = db.Column(db.Decimal(10, 2))
    extracted_date = db.Column(db.Date)
    extracted_merchant = db.Column(db.String(200))
    
    # Zoho WorkDrive information
    zoho_file_id = db.Column(db.String(100))  # File ID in Zoho WorkDrive
    zoho_file_url = db.Column(db.String(500))  # Download URL from Zoho WorkDrive
    
    uploaded_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    uploader = db.relationship('User', backref='uploaded_receipts')
    expenses = db.relationship('Expense', backref='receipt', lazy='dynamic')

# Seed data for expense categories
def create_default_categories():
    default_categories = [
        ('Transportation', 'Flights, trains, taxis, rideshares, parking'),
        ('Accommodation', 'Hotels, lodging, extended stays'),
        ('Meals & Entertainment', 'Business meals, client entertainment'),
        ('Booth & Exhibition', 'Booth rental, setup, decoration, signage'),
        ('Utilities', 'Electricity, internet, phone at booth'),
        ('Materials & Supplies', 'Brochures, business cards, promotional items'),
        ('Shipping', 'Freight, courier, postal services'),
        ('Professional Services', 'Consultants, contractors, temporary staff'),
        ('Equipment Rental', 'Audio/visual, furniture, technology'),
        ('Marketing & Advertising', 'Sponsorships, advertisements, promotions'),
        ('Miscellaneous', 'Other trade show related expenses')
    ]
    
    for name, description in default_categories:
        if not ExpenseCategory.query.filter_by(name=name).first():
            category = ExpenseCategory(name=name, description=description)
            db.session.add(category)
    
    db.session.commit()