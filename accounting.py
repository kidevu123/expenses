from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, send_file
from flask_login import login_required, current_user
from datetime import datetime, date
from decimal import Decimal
import json
from models import db, TradeShow, Expense, Company, User, ExpenseCategory
from utils import accounting_required, push_expense_to_zoho, generate_expense_report

accounting_bp = Blueprint('accounting', __name__)

@accounting_bp.route('/dashboard')
@login_required
@accounting_required
def dashboard():
    # Get pending expenses count
    pending_expenses = Expense.query.filter_by(status='pending').count()
    
    # Get approved but not pushed to Zoho
    approved_not_pushed = Expense.query.filter_by(status='approved', pushed_to_zoho=False).count()
    
    # Get total processed expenses this month
    current_month = date.today().replace(day=1)
    monthly_processed = Expense.query.filter(
        Expense.status == 'processed',
        Expense.zoho_push_date >= current_month
    ).count()
    
    # Get recent activities
    recent_expenses = Expense.query.order_by(Expense.created_at.desc()).limit(10).all()
    
    return render_template('accounting/dashboard.html',
                         pending_expenses=pending_expenses,
                         approved_not_pushed=approved_not_pushed,
                         monthly_processed=monthly_processed,
                         recent_expenses=recent_expenses)

@accounting_bp.route('/expenses')
@login_required
@accounting_required
def expenses():
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', 'all')
    tradeshow_filter = request.args.get('tradeshow', 'all')
    company_filter = request.args.get('company', 'all')
    
    query = Expense.query
    
    # Apply filters
    if status_filter != 'all':
        query = query.filter_by(status=status_filter)
    if tradeshow_filter != 'all':
        query = query.filter_by(tradeshow_id=tradeshow_filter)
    if company_filter != 'all':
        query = query.filter_by(company_id=company_filter)
    
    expenses = query.order_by(Expense.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False)
    
    # Get filter options
    tradeshows = TradeShow.query.all()
    companies = Company.query.filter_by(is_active=True).all()
    
    return render_template('accounting/expenses.html',
                         expenses=expenses,
                         tradeshows=tradeshows,
                         companies=companies,
                         status_filter=status_filter,
                         tradeshow_filter=tradeshow_filter,
                         company_filter=company_filter)

@accounting_bp.route('/expenses/<int:id>')
@login_required
@accounting_required
def expense_detail(id):
    expense = Expense.query.get_or_404(id)
    companies = Company.query.filter_by(is_active=True).all()
    return render_template('accounting/expense_detail.html', expense=expense, companies=companies)

@accounting_bp.route('/expenses/<int:id>/approve', methods=['POST'])
@login_required
@accounting_required
def approve_expense(id):
    expense = Expense.query.get_or_404(id)
    
    if expense.status != 'pending':
        flash('Expense is not in pending status.', 'warning')
        return redirect(url_for('accounting.expense_detail', id=id))
    
    company_id = request.form.get('company_id')
    if not company_id:
        flash('Please select a company for this expense.', 'error')
        return redirect(url_for('accounting.expense_detail', id=id))
    
    expense.status = 'approved'
    expense.company_id = company_id
    expense.approved_by = current_user.id
    expense.approved_at = datetime.utcnow()
    
    db.session.commit()
    
    flash('Expense approved successfully!', 'success')
    return redirect(url_for('accounting.expense_detail', id=id))

@accounting_bp.route('/expenses/<int:id>/reject', methods=['POST'])
@login_required
@accounting_required
def reject_expense(id):
    expense = Expense.query.get_or_404(id)
    
    if expense.status != 'pending':
        flash('Expense is not in pending status.', 'warning')
        return redirect(url_for('accounting.expense_detail', id=id))
    
    expense.status = 'rejected'
    expense.approved_by = current_user.id
    expense.approved_at = datetime.utcnow()
    
    db.session.commit()
    
    flash('Expense rejected.', 'info')
    return redirect(url_for('accounting.expenses'))

@accounting_bp.route('/expenses/<int:id>/push-to-zoho', methods=['POST'])
@login_required
@accounting_required
def push_to_zoho(id):
    expense = Expense.query.get_or_404(id)
    
    if expense.status != 'approved':
        flash('Only approved expenses can be pushed to Zoho.', 'warning')
        return redirect(url_for('accounting.expense_detail', id=id))
    
    if expense.pushed_to_zoho:
        flash('Expense has already been pushed to Zoho.', 'warning')
        return redirect(url_for('accounting.expense_detail', id=id))
    
    if not expense.company:
        flash('Please assign a company to this expense first.', 'error')
        return redirect(url_for('accounting.expense_detail', id=id))
    
    try:
        # Push to Zoho Books
        zoho_response = push_expense_to_zoho(expense)
        
        if zoho_response.get('success'):
            expense.zoho_expense_id = zoho_response.get('expense_id')
            expense.pushed_to_zoho = True
            expense.zoho_push_date = datetime.utcnow()
            expense.status = 'processed'
            
            db.session.commit()
            
            flash('Expense pushed to Zoho successfully!', 'success')
        else:
            flash(f'Error pushing to Zoho: {zoho_response.get("error", "Unknown error")}', 'error')
            
    except Exception as e:
        flash(f'Error pushing to Zoho: {str(e)}', 'error')
    
    return redirect(url_for('accounting.expense_detail', id=id))

@accounting_bp.route('/expenses/bulk-push', methods=['POST'])
@login_required
@accounting_required
def bulk_push_to_zoho():
    expense_ids = request.form.getlist('expense_ids')
    
    if not expense_ids:
        flash('No expenses selected.', 'warning')
        return redirect(url_for('accounting.expenses'))
    
    success_count = 0
    error_count = 0
    
    for expense_id in expense_ids:
        try:
            expense = Expense.query.get(expense_id)
            if expense and expense.status == 'approved' and not expense.pushed_to_zoho and expense.company:
                zoho_response = push_expense_to_zoho(expense)
                
                if zoho_response.get('success'):
                    expense.zoho_expense_id = zoho_response.get('expense_id')
                    expense.pushed_to_zoho = True
                    expense.zoho_push_date = datetime.utcnow()
                    expense.status = 'processed'
                    success_count += 1
                else:
                    error_count += 1
        except Exception:
            error_count += 1
    
    db.session.commit()
    
    flash(f'Bulk push completed: {success_count} successful, {error_count} errors.', 'info')
    return redirect(url_for('accounting.expenses'))

@accounting_bp.route('/reports')
@login_required
@accounting_required
def reports():
    tradeshows = TradeShow.query.all()
    companies = Company.query.filter_by(is_active=True).all()
    return render_template('accounting/reports.html', tradeshows=tradeshows, companies=companies)

@accounting_bp.route('/reports/generate', methods=['POST'])
@login_required
@accounting_required
def generate_report():
    report_type = request.form.get('report_type')
    tradeshow_id = request.form.get('tradeshow_id')
    company_id = request.form.get('company_id')
    start_date = request.form.get('start_date')
    end_date = request.form.get('end_date')
    
    try:
        # Generate the report
        report_data = generate_expense_report(
            report_type=report_type,
            tradeshow_id=tradeshow_id,
            company_id=company_id,
            start_date=datetime.strptime(start_date, '%Y-%m-%d').date() if start_date else None,
            end_date=datetime.strptime(end_date, '%Y-%m-%d').date() if end_date else None
        )
        
        if report_type == 'excel':
            return send_file(
                report_data['file_path'],
                as_attachment=True,
                download_name=report_data['filename'],
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
        else:
            return render_template('accounting/report_view.html', report_data=report_data)
            
    except Exception as e:
        flash(f'Error generating report: {str(e)}', 'error')
        return redirect(url_for('accounting.reports'))

@accounting_bp.route('/companies')
@login_required
@accounting_required
def companies():
    companies = Company.query.all()
    return render_template('accounting/companies.html', companies=companies)

@accounting_bp.route('/companies/<int:id>/configure-zoho', methods=['GET', 'POST'])
@login_required
@accounting_required
def configure_zoho(id):
    company = Company.query.get_or_404(id)
    
    if request.method == 'POST':
        zoho_org_id = request.form.get('zoho_org_id')
        zoho_access_token = request.form.get('zoho_access_token')
        zoho_refresh_token = request.form.get('zoho_refresh_token')
        
        company.zoho_org_id = zoho_org_id
        company.zoho_access_token = zoho_access_token
        company.zoho_refresh_token = zoho_refresh_token
        
        db.session.commit()
        
        flash(f'Zoho configuration updated for {company.name}!', 'success')
        return redirect(url_for('accounting.companies'))
    
    return render_template('accounting/configure_zoho.html', company=company)

@accounting_bp.route('/api/expense-stats')
@login_required
@accounting_required
def expense_stats():
    """API endpoint for dashboard charts"""
    # Get monthly expense totals for the current year
    current_year = date.today().year
    monthly_stats = db.session.query(
        db.func.extract('month', Expense.expense_date).label('month'),
        db.func.sum(Expense.amount).label('total')
    ).filter(
        db.func.extract('year', Expense.expense_date) == current_year,
        Expense.status == 'processed'
    ).group_by(db.func.extract('month', Expense.expense_date)).all()
    
    # Get expense breakdown by category
    category_stats = db.session.query(
        ExpenseCategory.name,
        db.func.sum(Expense.amount).label('total')
    ).join(Expense).filter(
        Expense.status == 'processed'
    ).group_by(ExpenseCategory.name).all()
    
    # Get company breakdown
    company_stats = db.session.query(
        Company.name,
        db.func.sum(Expense.amount).label('total')
    ).join(Expense).filter(
        Expense.status == 'processed'
    ).group_by(Company.name).all()
    
    return jsonify({
        'monthly': [{'month': int(stat.month), 'total': float(stat.total)} for stat in monthly_stats],
        'categories': [{'name': stat.name, 'total': float(stat.total)} for stat in category_stats],
        'companies': [{'name': stat.name, 'total': float(stat.total)} for stat in company_stats]
    })