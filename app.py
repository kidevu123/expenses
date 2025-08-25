from flask import Flask, render_template, redirect, url_for, flash, session, request
from flask_login import LoginManager, login_required, current_user
from werkzeug.security import generate_password_hash
from datetime import datetime
import os

# Initialize Flask app
app = Flask(__name__)

# Load configuration
config_name = os.environ.get('FLASK_ENV', 'development')
from config import config
app.config.from_object(config[config_name])
config[config_name].init_app(app)

# Import version management
from version import get_version_info

# Make version information available to all templates
@app.context_processor
def inject_version():
    return {'app_version': get_version_info()}

# Initialize database and login manager
from models import db, User, Company, TradeShow, Expense, Receipt, TradeShowAssignment, ExpenseCategory, create_default_categories

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access this page.'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Import blueprints
from auth import auth_bp
from coordinator import coordinator_bp
from attendee import attendee_bp
from accounting import accounting_bp
from admin import admin_bp

# Register blueprints
app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(coordinator_bp, url_prefix='/coordinator')
app.register_blueprint(attendee_bp, url_prefix='/attendee')
app.register_blueprint(accounting_bp, url_prefix='/accounting')
app.register_blueprint(admin_bp, url_prefix='/admin')

@app.route('/')
def index():
    if current_user.is_authenticated:
        # Redirect based on user role
        if current_user.role == 'admin':
            return redirect(url_for('admin.dashboard'))
        elif current_user.role == 'coordinator':
            return redirect(url_for('coordinator.dashboard'))
        elif current_user.role == 'accounting':
            return redirect(url_for('accounting.dashboard'))
        else:  # attendee
            return redirect(url_for('attendee.dashboard'))
    return redirect(url_for('auth.login'))

def create_default_data():
    """Create default companies and admin user"""
    # Create companies
    companies = [
        'Boomin Brands',
        'Haute Brands', 
        'Summitt Labs',
        'Nirvana Kulture'
    ]
    
    for company_name in companies:
        if not Company.query.filter_by(name=company_name).first():
            company = Company(name=company_name)
            db.session.add(company)
    
    # Create default admin user
    if not User.query.filter_by(username='admin').first():
        admin_user = User(
            username='admin',
            email='admin@company.com',
            password_hash=generate_password_hash('admin123'),
            full_name='System Administrator',
            role='admin',
            is_active=True
        )
        db.session.add(admin_user)
    
    # Create default expense categories
    create_default_categories()
    
    db.session.commit()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        create_default_data()
    
    # Create upload directory if it doesn't exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    app.run(debug=True)