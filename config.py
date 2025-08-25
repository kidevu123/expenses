import os
from datetime import timedelta

class Config:
    """Base configuration class"""
    
    # Flask Configuration
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # File Upload Configuration
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER') or 'uploads'
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_CONTENT_LENGTH', 16 * 1024 * 1024))  # 16MB
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf'}
    
    # Session Configuration
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    SESSION_COOKIE_SECURE = os.environ.get('SESSION_COOKIE_SECURE', 'False').lower() == 'true'
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Pagination
    ITEMS_PER_PAGE = int(os.environ.get('ITEMS_PER_PAGE', 20))
    
    # Zoho API Configuration
    ZOHO_CLIENT_ID = os.environ.get('ZOHO_CLIENT_ID')
    ZOHO_CLIENT_SECRET = os.environ.get('ZOHO_CLIENT_SECRET')
    ZOHO_REDIRECT_URI = os.environ.get('ZOHO_REDIRECT_URI')
    ZOHO_WORKDRIVE_FOLDER_ID = os.environ.get('ZOHO_WORKDRIVE_FOLDER_ID')
    
    # OCR Configuration
    GOOGLE_CLOUD_PROJECT_ID = os.environ.get('GOOGLE_CLOUD_PROJECT_ID')
    GOOGLE_APPLICATION_CREDENTIALS = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
    
    # AWS Configuration (for Textract OCR)
    AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
    AWS_REGION = os.environ.get('AWS_REGION', 'us-east-1')
    
    # Email Configuration
    SENDGRID_API_KEY = os.environ.get('SENDGRID_API_KEY')
    FROM_EMAIL = os.environ.get('FROM_EMAIL', 'noreply@tradeshow-expenses.com')
    
    # Application Settings
    DEFAULT_TIMEZONE = os.environ.get('DEFAULT_TIMEZONE', 'UTC')
    
    @staticmethod
    def init_app(app):
        """Initialize application with configuration"""
        pass

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///tradeshow_expenses.db'
    
    # Less strict security for development
    SESSION_COOKIE_SECURE = False
    
    @staticmethod
    def init_app(app):
        Config.init_app(app)
        
        # Log to console in development
        import logging
        from logging import StreamHandler
        
        if not app.debug and not app.testing:
            stream_handler = StreamHandler()
            stream_handler.setLevel(logging.INFO)
            app.logger.addHandler(stream_handler)

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    
    # Use PostgreSQL in production (recommended for PythonAnywhere)
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'postgresql://username:password@localhost/tradeshow_expenses'
    
    # Strict security settings
    SESSION_COOKIE_SECURE = True
    
    @staticmethod
    def init_app(app):
        Config.init_app(app)
        
        # Log to file in production
        import logging
        from logging.handlers import RotatingFileHandler
        import os
        
        if not os.path.exists('logs'):
            os.mkdir('logs')
        
        file_handler = RotatingFileHandler(
            'logs/tradeshow_expenses.log',
            maxBytes=10240000,  # 10MB
            backupCount=10
        )
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        
        app.logger.setLevel(logging.INFO)
        app.logger.info('Trade Show Expense Tracker startup')

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    
    # Disable security features for testing
    SESSION_COOKIE_SECURE = False

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

# Company-specific configurations
COMPANIES = {
    'boomin_brands': {
        'name': 'Boomin Brands',
        'zoho_org_id': '',  # Configure in admin panel
        'default_categories': ['Marketing & Advertising', 'Booth & Exhibition']
    },
    'haute_brands': {
        'name': 'Haute Brands',
        'zoho_org_id': '',  # Configure in admin panel
        'default_categories': ['Materials & Supplies', 'Professional Services']
    },
    'summitt_labs': {
        'name': 'Summitt Labs',
        'zoho_org_id': '',  # Configure in admin panel
        'default_categories': ['Equipment Rental', 'Utilities']
    },
    'nirvana_kulture': {
        'name': 'Nirvana Kulture',
        'zoho_org_id': '',  # Configure in admin panel
        'default_categories': ['Transportation', 'Accommodation']
    }
}

# OCR Configuration
OCR_SETTINGS = {
    'confidence_threshold': 0.7,  # Minimum confidence for OCR results
    'supported_formats': ['png', 'jpg', 'jpeg', 'pdf', 'gif'],
    'max_file_size': 16 * 1024 * 1024,  # 16MB
    'preprocessing': {
        'resize_max_width': 2000,
        'enhance_contrast': True,
        'denoise': True
    }
}

# Email Templates
EMAIL_TEMPLATES = {
    'expense_submitted': {
        'subject': 'New Expense Submission: {expense_title}',
        'template': 'emails/expense_submitted.html'
    },
    'expense_approved': {
        'subject': 'Expense Approved: {expense_title}',
        'template': 'emails/expense_approved.html'
    },
    'expense_rejected': {
        'subject': 'Expense Rejected: {expense_title}',
        'template': 'emails/expense_rejected.html'
    },
    'user_created': {
        'subject': 'Welcome to Trade Show Expense Tracker',
        'template': 'emails/user_created.html'
    }
}