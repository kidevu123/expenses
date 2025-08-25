from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from datetime import datetime, date
from decimal import Decimal
import os
import uuid
from models import db, TradeShow, TradeShowAssignment, Expense, ExpenseCategory, Receipt, Company
from utils import attendee_required, allowed_file, process_receipt_ocr, upload_to_zoho_workdrive

attendee_bp = Blueprint('attendee', __name__)

@attendee_bp.route('/dashboard')
@login_required
@attendee_required
def dashboard():
    # Get trade shows this user is assigned to
    assignments = TradeShowAssignment.query.filter_by(user_id=current_user.id).all()
    
    # Get user's expenses
    user_expenses = Expense.query.filter_by(user_id=current_user.id).order_by(Expense.created_at.desc()).limit(10).all()
    
    # Calculate statistics
    total_expenses = db.session.query(db.func.sum(Expense.amount)).filter_by(user_id=current_user.id).scalar() or 0
    pending_expenses = Expense.query.filter_by(user_id=current_user.id, status='pending').count()
    
    return render_template('attendee/dashboard.html', 
                         assignments=assignments,
                         user_expenses=user_expenses,
                         total_expenses=total_expenses,
                         pending_expenses=pending_expenses)

@attendee_bp.route('/tradeshows')
@login_required
@attendee_required
def my_tradeshows():
    assignments = TradeShowAssignment.query.filter_by(user_id=current_user.id).all()
    return render_template('attendee/my_tradeshows.html', assignments=assignments)

@attendee_bp.route('/tradeshows/<int:id>/expenses')
@login_required
@attendee_required
def tradeshow_expenses(id):
    # Verify user is assigned to this trade show
    assignment = TradeShowAssignment.query.filter_by(tradeshow_id=id, user_id=current_user.id).first_or_404()
    
    expenses = Expense.query.filter_by(tradeshow_id=id, user_id=current_user.id).order_by(Expense.created_at.desc()).all()
    
    return render_template('attendee/tradeshow_expenses.html', 
                         assignment=assignment,
                         expenses=expenses)

@attendee_bp.route('/tradeshows/<int:id>/submit-expense', methods=['GET', 'POST'])
@login_required
@attendee_required
def submit_expense(id):
    # Verify user is assigned to this trade show
    assignment = TradeShowAssignment.query.filter_by(tradeshow_id=id, user_id=current_user.id).first_or_404()
    
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description', '')
        amount = request.form.get('amount')
        expense_date = request.form.get('expense_date')
        category_id = request.form.get('category_id')
        
        # Handle receipt upload
        receipt_file = request.files.get('receipt')
        receipt_id = None
        
        if receipt_file and receipt_file.filename != '' and allowed_file(receipt_file.filename):
            try:
                # Generate unique filename
                filename = str(uuid.uuid4()) + '.' + receipt_file.filename.rsplit('.', 1)[1].lower()
                file_path = os.path.join('uploads', filename)
                receipt_file.save(file_path)
                
                # Process OCR
                ocr_results = process_receipt_ocr(file_path)
                
                # Upload to Zoho WorkDrive
                zoho_file_info = upload_to_zoho_workdrive(file_path, receipt_file.filename)
                
                # Create receipt record
                receipt = Receipt(
                    filename=filename,
                    original_filename=receipt_file.filename,
                    file_path=file_path,
                    file_size=os.path.getsize(file_path),
                    mime_type=receipt_file.mimetype,
                    ocr_text=ocr_results.get('text', ''),
                    ocr_confidence=ocr_results.get('confidence', 0),
                    extracted_amount=ocr_results.get('amount'),
                    extracted_date=ocr_results.get('date'),
                    extracted_merchant=ocr_results.get('merchant'),
                    zoho_file_id=zoho_file_info.get('file_id'),
                    zoho_file_url=zoho_file_info.get('download_url'),
                    uploaded_by=current_user.id
                )
                
                db.session.add(receipt)
                db.session.flush()  # Get the receipt ID
                receipt_id = receipt.id
                
                # Use OCR data to pre-fill if not provided
                if not amount and receipt.extracted_amount:
                    amount = str(receipt.extracted_amount)
                if not expense_date and receipt.extracted_date:
                    expense_date = receipt.extracted_date.strftime('%Y-%m-%d')
                if not title and receipt.extracted_merchant:
                    title = f"Expense from {receipt.extracted_merchant}"
                
            except Exception as e:
                flash(f'Error processing receipt: {str(e)}', 'error')
                return render_template('attendee/submit_expense.html', 
                                     assignment=assignment,
                                     categories=ExpenseCategory.query.filter_by(is_active=True).all())
        
        # Validate required fields
        if not all([title, amount, expense_date, category_id]):
            flash('Please fill in all required fields.', 'error')
            return render_template('attendee/submit_expense.html', 
                                 assignment=assignment,
                                 categories=ExpenseCategory.query.filter_by(is_active=True).all())
        
        try:
            expense = Expense(
                tradeshow_id=id,
                user_id=current_user.id,
                title=title,
                description=description,
                amount=Decimal(amount),
                expense_date=datetime.strptime(expense_date, '%Y-%m-%d').date(),
                category_id=category_id,
                receipt_id=receipt_id,
                status='pending'
            )
            
            db.session.add(expense)
            db.session.commit()
            
            flash(f'Expense "{title}" submitted successfully!', 'success')
            return redirect(url_for('attendee.tradeshow_expenses', id=id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error submitting expense: {str(e)}', 'error')
    
    categories = ExpenseCategory.query.filter_by(is_active=True).all()
    return render_template('attendee/submit_expense.html', 
                         assignment=assignment,
                         categories=categories)

@attendee_bp.route('/expenses')
@login_required
@attendee_required
def all_expenses():
    page = request.args.get('page', 1, type=int)
    expenses = Expense.query.filter_by(user_id=current_user.id).order_by(Expense.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False)
    return render_template('attendee/all_expenses.html', expenses=expenses)

@attendee_bp.route('/expenses/<int:id>')
@login_required
@attendee_required
def expense_detail(id):
    expense = Expense.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    return render_template('attendee/expense_detail.html', expense=expense)

@attendee_bp.route('/receipt-scan', methods=['POST'])
@login_required
@attendee_required
def scan_receipt():
    """AJAX endpoint for receipt scanning"""
    if 'receipt' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['receipt']
    if file.filename == '' or not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file type'}), 400
    
    try:
        # Save file temporarily
        filename = str(uuid.uuid4()) + '.' + file.filename.rsplit('.', 1)[1].lower()
        temp_path = os.path.join('temp', filename)
        os.makedirs('temp', exist_ok=True)
        file.save(temp_path)
        
        # Process OCR
        ocr_results = process_receipt_ocr(temp_path)
        
        # Clean up temp file
        os.remove(temp_path)
        
        return jsonify({
            'success': True,
            'amount': str(ocr_results.get('amount', '')),
            'date': ocr_results.get('date').strftime('%Y-%m-%d') if ocr_results.get('date') else '',
            'merchant': ocr_results.get('merchant', ''),
            'confidence': ocr_results.get('confidence', 0)
        })
        
    except Exception as e:
        return jsonify({'error': f'Error processing receipt: {str(e)}'}), 500