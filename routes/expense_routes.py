from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from database import db, ExpenseRecord
from datetime import datetime
from collections import defaultdict
import calendar

expense_bp = Blueprint('expense', __name__)

@expense_bp.route('/expense', methods=['GET', 'POST'])
@login_required
def expense():
    if request.method == 'POST':
        title    = request.form.get('title')
        amount   = float(request.form.get('amount'))
        category = request.form.get('category')
        type_val = request.form.get('type', 'expense')
        
        # Simple Anomaly Detection Heuristic
        is_anomaly = True if amount > 50000 and type_val == 'expense' else False

        record = ExpenseRecord(
            user_id=current_user.id,
            title=title, 
            amount=amount,
            type=type_val,
            category=category,
            is_anomaly=is_anomaly
        )
        db.session.add(record)
        db.session.commit()
        flash(f"{type_val.capitalize()} recorded successfully.", 'success')
        return redirect(url_for('expense.expense'))

    # GET request - Load Intelligence
    expenses = ExpenseRecord.query.filter_by(user_id=current_user.id).order_by(ExpenseRecord.date.desc()).all()
    
    total_expense = sum(e.amount for e in expenses if e.type == 'expense')
    total_income  = sum(e.amount for e in expenses if e.type == 'income')
    net_profit    = total_income - total_expense
    
    monthly_data = defaultdict(float)
    category_data = defaultdict(float)
    anomalies = []

    for e in expenses:
        month = e.date.strftime("%b %Y")
        if e.type == 'expense':
            category_data[e.category] += e.amount
            monthly_data[month] -= e.amount
        else:
            monthly_data[month] += e.amount
            
        if e.is_anomaly:
            anomalies.append(e)

    # Sort months chronologically if possible
    sorted_months = list(monthly_data.keys())
    
    # Chart Data
    chart_labels_cat = list(category_data.keys())
    chart_values_cat = list(category_data.values())
    
    chart_labels_month = sorted_months[:6][::-1] # Last 6 months
    chart_values_month = [monthly_data[m] for m in chart_labels_month]

    return render_template('expense.html', 
                           user=current_user,
                           expenses=expenses,
                           total_expense=total_expense,
                           total_income=total_income,
                           net_profit=net_profit,
                           anomalies=anomalies,
                           chart_labels_cat=chart_labels_cat,
                           chart_values_cat=chart_values_cat,
                           chart_labels_month=chart_labels_month,
                           chart_values_month=chart_values_month)

@expense_bp.route('/expense/delete/<int:id>', methods=['POST'])
@login_required
def delete_expense(id):
    record = ExpenseRecord.query.get_or_404(id)
    if record.user_id == current_user.id:
        db.session.delete(record)
        db.session.commit()
        flash('Record securely deleted.', 'info')
    return redirect(url_for('expense.expense'))
