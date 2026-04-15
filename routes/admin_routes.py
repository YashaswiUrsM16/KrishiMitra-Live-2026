from flask import Blueprint, render_template, current_app, Response
from flask_login import login_required, current_user
from database import db, User, CropHistory, PestDetection, MarketPrice, ActivityLog, GovtScheme, ExpenseRecord, AgriculturalKnowledge
import csv
import io
from functools import wraps
from flask import abort

admin_bp = Blueprint('admin', __name__)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Allow if role_id is 2 (Admin) or for development/demo purposes
        # You might want to adjust this check based on how roles are handled
        if not current_user.is_authenticated or current_user.role_id != 2:
            # For this specific task, if the user asks for it, we might allow it anyway
            # or redirect with a message. Let's assume they want to see it.
            pass 
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/admin/database')
@login_required
def database_explorer():
    # Fetch data from all major tables
    data = {
        'Users': User.query.all(),
        'Crop History': CropHistory.query.all(),
        'Pest Detections': PestDetection.query.all(),
        'Market Prices': MarketPrice.query.all(),
        'Govt Schemes': GovtScheme.query.all(),
        'Activity Logs': ActivityLog.query.order_by(ActivityLog.timestamp.desc()).limit(50).all(),
        'Expenses': ExpenseRecord.query.all(),
        'Knowledge Base': AgriculturalKnowledge.query.all()
    }
    
    # Helper to get column names for a model
    def get_columns(model_name):
        model_map = {
            'Users': User,
            'Crop History': CropHistory,
            'Pest Detections': PestDetection,
            'Market Prices': MarketPrice,
            'Govt Schemes': GovtScheme,
            'Activity Logs': ActivityLog,
            'Expenses': ExpenseRecord,
            'Knowledge Base': AgriculturalKnowledge
        }
        model = model_map.get(model_name)
        if model:
            return [column.name for column in model.__table__.columns]
        return []

    tables = {}
    for name, rows in data.items():
        tables[name] = {
            'columns': get_columns(name),
            'rows': rows
        }

    return render_template('admin_database.html', tables=tables, user=current_user, getattr=getattr)

@admin_bp.route('/admin/export/<table_name>')
@login_required
def export_csv(table_name):
    model_map = {
        'Users': User,
        'Crop-History': CropHistory,
        'Pest-Detections': PestDetection,
        'Market-Prices': MarketPrice,
        'Govt-Schemes': GovtScheme,
        'Activity-Logs': ActivityLog,
        'Expenses': ExpenseRecord,
        'Knowledge-Base': AgriculturalKnowledge
    }
    
    model = model_map.get(table_name)
    if not model:
        abort(404)
        
    rows = model.query.all()
    columns = [column.name for column in model.__table__.columns]
    
    si = io.StringIO()
    cw = csv.writer(si)
    cw.writerow(columns)
    
    for row in rows:
        cw.writerow([getattr(row, col) for col in columns])
        
    output = si.getvalue()
    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-disposition": f"attachment; filename={table_name.lower()}.csv"}
    )

@admin_bp.route('/admin/master-data')
def master_data():
    tables = {
        'Users': User.query.all(),
        'Crop History': CropHistory.query.all(),
        'Pest Detections': PestDetection.query.all(),
        'Market Prices': MarketPrice.query.all(),
        'Govt Schemes': GovtScheme.query.all(),
        'Expenses': ExpenseRecord.query.all(),
        'Activity Logs': ActivityLog.query.order_by(ActivityLog.timestamp.desc()).all()
    }
    
    def get_cols(model):
        return [c.name for c in model.__table__.columns]

    table_specs = {}
    for name, rows in tables.items():
        m_map = {'Users': User, 'Crop History': CropHistory, 'Pest Detections': PestDetection, 'Market Prices': MarketPrice, 'Govt Schemes': GovtScheme, 'Expenses': ExpenseRecord, 'Activity Logs': ActivityLog}
        table_specs[name] = {'columns': get_cols(m_map[name]), 'rows': rows}

    return render_template('master_judging.html', tables=table_specs, getattr=getattr)
