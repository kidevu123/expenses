from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
from datetime import datetime
from models import db, User, Company, TradeShow, Expense, ExpenseCategory
from utils import admin_required

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    # Get system statistics
    total_users = User.query.count()
    active_users = User.query.filter_by(is_active=True).count()
    total_tradeshows = TradeShow.query.count()
    total_expenses = Expense.query.count()
    total_expense_amount = db.session.query(db.func.sum(Expense.amount)).scalar() or 0
    
    # Get recent activities
    recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
    recent_tradeshows = TradeShow.query.order_by(TradeShow.created_at.desc()).limit(5).all()
    recent_expenses = Expense.query.order_by(Expense.created_at.desc()).limit(10).all()
    
    return render_template('admin/dashboard.html',
                         total_users=total_users,
                         active_users=active_users,
                         total_tradeshows=total_tradeshows,
                         total_expenses=total_expenses,
                         total_expense_amount=total_expense_amount,
                         recent_users=recent_users,
                         recent_tradeshows=recent_tradeshows,
                         recent_expenses=recent_expenses)

@admin_bp.route('/users')
@login_required
@admin_required
def users():
    page = request.args.get('page', 1, type=int)
    role_filter = request.args.get('role', 'all')
    status_filter = request.args.get('status', 'all')
    search_query = request.args.get('search', '')
    
    query = User.query
    
    # Apply filters
    if role_filter != 'all':
        query = query.filter_by(role=role_filter)
    if status_filter == 'active':
        query = query.filter_by(is_active=True)
    elif status_filter == 'inactive':
        query = query.filter_by(is_active=False)
    if search_query:
        query = query.filter(
            db.or_(
                User.username.contains(search_query),
                User.email.contains(search_query),
                User.full_name.contains(search_query)
            )
        )
    
    users = query.order_by(User.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False)
    
    return render_template('admin/users.html',
                         users=users,
                         role_filter=role_filter,
                         status_filter=status_filter,
                         search_query=search_query)

@admin_bp.route('/users/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_user():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        full_name = request.form.get('full_name')
        role = request.form.get('role')
        password = request.form.get('password')
        is_active = request.form.get('is_active') == 'on'
        
        # Validate required fields
        if not all([username, email, full_name, role, password]):
            flash('Please fill in all required fields.', 'error')
            return render_template('admin/create_user.html')
        
        # Check if username or email already exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists.', 'error')
            return render_template('admin/create_user.html')
        
        if User.query.filter_by(email=email).first():
            flash('Email already exists.', 'error')
            return render_template('admin/create_user.html')
        
        # Create new user
        user = User(
            username=username,
            email=email,
            full_name=full_name,
            role=role,
            password_hash=generate_password_hash(password),
            is_active=is_active
        )
        
        db.session.add(user)
        db.session.commit()
        
        flash(f'User "{username}" created successfully!', 'success')
        return redirect(url_for('admin.users'))
    
    return render_template('admin/create_user.html')

@admin_bp.route('/users/<int:id>')
@login_required
@admin_required
def user_detail(id):
    user = User.query.get_or_404(id)
    
    # Get user's trade show assignments
    assignments = user.assignments.all()
    
    # Get user's expenses
    expenses = user.expenses.order_by(Expense.created_at.desc()).limit(10).all()
    
    # Calculate user statistics
    total_expenses = db.session.query(db.func.sum(Expense.amount)).filter_by(user_id=id).scalar() or 0
    expense_count = user.expenses.count()
    
    return render_template('admin/user_detail.html',
                         user=user,
                         assignments=assignments,
                         expenses=expenses,
                         total_expenses=total_expenses,
                         expense_count=expense_count)

@admin_bp.route('/users/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_user(id):
    user = User.query.get_or_404(id)
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        full_name = request.form.get('full_name')
        role = request.form.get('role')
        password = request.form.get('password')
        is_active = request.form.get('is_active') == 'on'
        
        # Validate required fields
        if not all([username, email, full_name, role]):
            flash('Please fill in all required fields.', 'error')
            return render_template('admin/edit_user.html', user=user)
        
        # Check if username or email already exists (excluding current user)
        if User.query.filter(User.username == username, User.id != id).first():
            flash('Username already exists.', 'error')
            return render_template('admin/edit_user.html', user=user)
        
        if User.query.filter(User.email == email, User.id != id).first():
            flash('Email already exists.', 'error')
            return render_template('admin/edit_user.html', user=user)
        
        # Update user
        user.username = username
        user.email = email
        user.full_name = full_name
        user.role = role
        user.is_active = is_active
        
        if password:  # Only update password if provided
            user.password_hash = generate_password_hash(password)
        
        db.session.commit()
        
        flash(f'User "{username}" updated successfully!', 'success')
        return redirect(url_for('admin.user_detail', id=id))
    
    return render_template('admin/edit_user.html', user=user)

@admin_bp.route('/users/<int:id>/toggle-status', methods=['POST'])
@login_required
@admin_required
def toggle_user_status(id):
    user = User.query.get_or_404(id)
    
    # Prevent admin from deactivating themselves
    if user.id == current_user.id:
        flash('You cannot deactivate your own account.', 'error')
        return redirect(url_for('admin.user_detail', id=id))
    
    user.is_active = not user.is_active
    db.session.commit()
    
    status = 'activated' if user.is_active else 'deactivated'
    flash(f'User "{user.username}" {status} successfully!', 'success')
    return redirect(url_for('admin.user_detail', id=id))

@admin_bp.route('/companies')
@login_required
@admin_required
def companies():
    companies = Company.query.all()
    return render_template('admin/companies.html', companies=companies)

@admin_bp.route('/companies/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_company():
    if request.method == 'POST':
        name = request.form.get('name')
        
        if not name:
            flash('Company name is required.', 'error')
            return render_template('admin/create_company.html')
        
        if Company.query.filter_by(name=name).first():
            flash('Company name already exists.', 'error')
            return render_template('admin/create_company.html')
        
        company = Company(name=name)
        db.session.add(company)
        db.session.commit()
        
        flash(f'Company "{name}" created successfully!', 'success')
        return redirect(url_for('admin.companies'))
    
    return render_template('admin/create_company.html')

@admin_bp.route('/companies/<int:id>/toggle-status', methods=['POST'])
@login_required
@admin_required
def toggle_company_status(id):
    company = Company.query.get_or_404(id)
    company.is_active = not company.is_active
    db.session.commit()
    
    status = 'activated' if company.is_active else 'deactivated'
    flash(f'Company "{company.name}" {status} successfully!', 'success')
    return redirect(url_for('admin.companies'))

@admin_bp.route('/categories')
@login_required
@admin_required
def categories():
    categories = ExpenseCategory.query.all()
    return render_template('admin/categories.html', categories=categories)

@admin_bp.route('/categories/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_category():
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description', '')
        
        if not name:
            flash('Category name is required.', 'error')
            return render_template('admin/create_category.html')
        
        if ExpenseCategory.query.filter_by(name=name).first():
            flash('Category name already exists.', 'error')
            return render_template('admin/create_category.html')
        
        category = ExpenseCategory(name=name, description=description)
        db.session.add(category)
        db.session.commit()
        
        flash(f'Category "{name}" created successfully!', 'success')
        return redirect(url_for('admin.categories'))
    
    return render_template('admin/create_category.html')

@admin_bp.route('/categories/<int:id>/toggle-status', methods=['POST'])
@login_required
@admin_required
def toggle_category_status(id):
    category = ExpenseCategory.query.get_or_404(id)
    category.is_active = not category.is_active
    db.session.commit()
    
    status = 'activated' if category.is_active else 'deactivated'
    flash(f'Category "{category.name}" {status} successfully!', 'success')
    return redirect(url_for('admin.categories'))

@admin_bp.route('/tradeshows')
@login_required
@admin_required
def tradeshows():
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', 'all')
    
    query = TradeShow.query
    if status_filter != 'all':
        query = query.filter_by(status=status_filter)
    
    tradeshows = query.order_by(TradeShow.start_date.desc()).paginate(
        page=page, per_page=20, error_out=False)
    
    return render_template('admin/tradeshows.html', 
                         tradeshows=tradeshows,
                         status_filter=status_filter)

@admin_bp.route('/system-logs')
@login_required
@admin_required
def system_logs():
    # This would typically show system logs, audit trails, etc.
    # For now, we'll show recent activities
    recent_activities = []
    
    # Recent user creations
    recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
    for user in recent_users:
        recent_activities.append({
            'timestamp': user.created_at,
            'action': 'User Created',
            'details': f'User "{user.username}" was created',
            'type': 'user'
        })
    
    # Recent trade shows
    recent_tradeshows = TradeShow.query.order_by(TradeShow.created_at.desc()).limit(5).all()
    for ts in recent_tradeshows:
        recent_activities.append({
            'timestamp': ts.created_at,
            'action': 'Trade Show Created',
            'details': f'Trade show "{ts.name}" was created',
            'type': 'tradeshow'
        })
    
    # Recent expenses
    recent_expenses = Expense.query.order_by(Expense.created_at.desc()).limit(10).all()
    for expense in recent_expenses:
        recent_activities.append({
            'timestamp': expense.created_at,
            'action': 'Expense Submitted',
            'details': f'Expense "{expense.title}" was submitted',
            'type': 'expense'
        })
    
    # Sort by timestamp
    recent_activities.sort(key=lambda x: x['timestamp'], reverse=True)
    
    return render_template('admin/system_logs.html', activities=recent_activities[:20])