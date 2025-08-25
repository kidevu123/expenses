from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime, date
from decimal import Decimal
from models import db, TradeShow, User, TradeShowAssignment, Expense, ExpenseCategory, Company
from utils import coordinator_required

coordinator_bp = Blueprint('coordinator', __name__)

@coordinator_bp.route('/dashboard')
@login_required
@coordinator_required
def dashboard():
    # Get trade shows created by this coordinator
    tradeshows = TradeShow.query.filter_by(created_by=current_user.id).order_by(TradeShow.start_date.desc()).all()
    
    # Get some statistics
    total_shows = len(tradeshows)
    active_shows = len([ts for ts in tradeshows if ts.status == 'active'])
    upcoming_shows = len([ts for ts in tradeshows if ts.status == 'planning' and ts.start_date > date.today()])
    
    return render_template('coordinator/dashboard.html', 
                         tradeshows=tradeshows,
                         total_shows=total_shows,
                         active_shows=active_shows,
                         upcoming_shows=upcoming_shows)

@coordinator_bp.route('/tradeshows')
@login_required
@coordinator_required
def tradeshows():
    page = request.args.get('page', 1, type=int)
    tradeshows = TradeShow.query.filter_by(created_by=current_user.id).order_by(TradeShow.start_date.desc()).paginate(
        page=page, per_page=10, error_out=False)
    return render_template('coordinator/tradeshows.html', tradeshows=tradeshows)

@coordinator_bp.route('/tradeshows/create', methods=['GET', 'POST'])
@login_required
@coordinator_required
def create_tradeshow():
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description', '')
        start_date = datetime.strptime(request.form.get('start_date'), '%Y-%m-%d').date()
        end_date = datetime.strptime(request.form.get('end_date'), '%Y-%m-%d').date()
        location = request.form.get('location')
        
        if not all([name, start_date, end_date, location]):
            flash('Please fill in all required fields.', 'error')
            return render_template('coordinator/create_tradeshow.html')
        
        if start_date > end_date:
            flash('Start date cannot be after end date.', 'error')
            return render_template('coordinator/create_tradeshow.html')
        
        tradeshow = TradeShow(
            name=name,
            description=description,
            start_date=start_date,
            end_date=end_date,
            location=location,
            created_by=current_user.id
        )
        
        db.session.add(tradeshow)
        db.session.commit()
        
        flash(f'Trade show "{name}" created successfully!', 'success')
        return redirect(url_for('coordinator.tradeshow_detail', id=tradeshow.id))
    
    return render_template('coordinator/create_tradeshow.html')

@coordinator_bp.route('/tradeshows/<int:id>')
@login_required
@coordinator_required
def tradeshow_detail(id):
    tradeshow = TradeShow.query.filter_by(id=id, created_by=current_user.id).first_or_404()
    assignments = TradeShowAssignment.query.filter_by(tradeshow_id=id).all()
    expenses = Expense.query.filter_by(tradeshow_id=id).all()
    
    # Calculate total expenses
    total_expenses = sum(expense.amount for expense in expenses)
    
    return render_template('coordinator/tradeshow_detail.html', 
                         tradeshow=tradeshow, 
                         assignments=assignments,
                         expenses=expenses,
                         total_expenses=total_expenses)

@coordinator_bp.route('/tradeshows/<int:id>/attendees', methods=['GET', 'POST'])
@login_required
@coordinator_required
def manage_attendees(id):
    tradeshow = TradeShow.query.filter_by(id=id, created_by=current_user.id).first_or_404()
    
    if request.method == 'POST':
        user_id = request.form.get('user_id')
        role_in_show = request.form.get('role_in_show', 'attendee')
        flight_details = request.form.get('flight_details', '')
        hotel_details = request.form.get('hotel_details', '')
        notes = request.form.get('notes', '')
        
        # Check if user is already assigned to this trade show
        existing_assignment = TradeShowAssignment.query.filter_by(
            user_id=user_id, tradeshow_id=id).first()
        
        if existing_assignment:
            flash('User is already assigned to this trade show.', 'warning')
        else:
            assignment = TradeShowAssignment(
                user_id=user_id,
                tradeshow_id=id,
                role_in_show=role_in_show,
                flight_details=flight_details,
                hotel_details=hotel_details,
                notes=notes
            )
            db.session.add(assignment)
            db.session.commit()
            flash('Attendee added successfully!', 'success')
    
    # Get available users (attendees and other coordinators)
    available_users = User.query.filter(User.role.in_(['attendee', 'coordinator']), User.is_active == True).all()
    current_assignments = TradeShowAssignment.query.filter_by(tradeshow_id=id).all()
    
    return render_template('coordinator/manage_attendees.html', 
                         tradeshow=tradeshow,
                         available_users=available_users,
                         current_assignments=current_assignments)

@coordinator_bp.route('/tradeshows/<int:id>/expenses', methods=['GET', 'POST'])
@login_required
@coordinator_required
def manage_expenses(id):
    tradeshow = TradeShow.query.filter_by(id=id, created_by=current_user.id).first_or_404()
    
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description', '')
        amount = Decimal(request.form.get('amount'))
        expense_date = datetime.strptime(request.form.get('expense_date'), '%Y-%m-%d').date()
        category_id = request.form.get('category_id')
        company_id = request.form.get('company_id')
        
        expense = Expense(
            tradeshow_id=id,
            user_id=current_user.id,
            title=title,
            description=description,
            amount=amount,
            expense_date=expense_date,
            category_id=category_id,
            company_id=company_id,
            status='approved'  # Coordinator expenses are auto-approved
        )
        
        db.session.add(expense)
        db.session.commit()
        
        flash(f'Expense "{title}" added successfully!', 'success')
        return redirect(url_for('coordinator.manage_expenses', id=id))
    
    categories = ExpenseCategory.query.filter_by(is_active=True).all()
    companies = Company.query.filter_by(is_active=True).all()
    expenses = Expense.query.filter_by(tradeshow_id=id).all()
    
    return render_template('coordinator/manage_expenses.html', 
                         tradeshow=tradeshow,
                         categories=categories,
                         companies=companies,
                         expenses=expenses)

@coordinator_bp.route('/attendees/<int:assignment_id>/remove', methods=['POST'])
@login_required
@coordinator_required
def remove_attendee(assignment_id):
    assignment = TradeShowAssignment.query.get_or_404(assignment_id)
    
    # Verify the coordinator owns this trade show
    tradeshow = TradeShow.query.filter_by(id=assignment.tradeshow_id, created_by=current_user.id).first()
    if not tradeshow:
        flash('Access denied.', 'error')
        return redirect(url_for('coordinator.dashboard'))
    
    db.session.delete(assignment)
    db.session.commit()
    
    flash('Attendee removed successfully.', 'success')
    return redirect(url_for('coordinator.manage_attendees', id=assignment.tradeshow_id))