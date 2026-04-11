from flask import Blueprint, render_template
from flask_login import login_required, current_user
from database import db, ExpenseRecord, CropHistory, PestDetection
import os
import requests

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/dashboard')
@login_required
def dashboard():
    expenses = ExpenseRecord.query.filter_by(user_id=current_user.id).all()
    crops = CropHistory.query.filter_by(user_id=current_user.id).order_by(
        CropHistory.created_at.desc()).limit(5).all()

    total_expense = sum((float(e.amount) if e.amount else 0.0) for e in expenses if getattr(e, 'type', 'expense') == 'expense')
    total_income = sum((float(e.amount) if e.amount else 0.0) for e in expenses if getattr(e, 'type', 'expense') == 'income')
    net_profit = total_income - total_expense

    total_scans = CropHistory.query.filter_by(user_id=current_user.id).count()
    pest_scan_count = PestDetection.query.filter_by(user_id=current_user.id).count()

    # Community Leadership Logic: Fetch farmers managed by this leader
    managed_farmers = []
    if current_user.role_id in [2, 3]: # Admin or Expert
        from database import User
        managed_farmers = User.query.filter_by(parent_user_id=current_user.id).all()

    # Live weather snippet
    weather_snippet = None
    try:
        city = "Mysuru"
        if hasattr(current_user, 'profile') and current_user.profile and current_user.profile.location_district:
            city = current_user.profile.location_district
        from config import Config
        api_key = Config.WEATHER_API_KEY
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
        r = requests.get(url, timeout=3)
        if r.status_code == 200:
            data = r.json()
            weather_snippet = {
                'city': city,
                'temp': round(data['main']['temp']),
                'desc': data['weather'][0]['description'].title(),
                'icon': data['weather'][0]['icon'],
                'humidity': data['main']['humidity'],
            }
    except:
        pass

    return render_template('dashboard.html',
                           user=current_user,
                           expenses=expenses,
                           crops=crops,
                           total_expense=total_expense,
                           total_income=total_income,
                           net_profit=net_profit,
                           total_scans=total_scans,
                           pest_scan_count=pest_scan_count,
                           weather_snippet=weather_snippet,
                           managed_farmers=managed_farmers)
from flask import jsonify

@dashboard_bp.route('/api/morning-briefing')
@login_required
def morning_briefing():
    from ai_utils import call_ai
    
    # Gather data context
    expenses = ExpenseRecord.query.filter_by(user_id=current_user.id).all()
    total_expense = sum((float(e.amount) if e.amount else 0.0) for e in expenses if getattr(e, 'type', 'expense') == 'expense')
    total_income = sum((float(e.amount) if e.amount else 0.0) for e in expenses if getattr(e, 'type', 'expense') == 'income')
    
    last_crop = CropHistory.query.filter_by(user_id=current_user.id).order_by(CropHistory.created_at.desc()).first()
    crop_name = last_crop.crop_name if last_crop else "crops"
    
    location = current_user.location or "Karnataka"
    
    prompt = f"""
    Namaste! You are KrishiMitra, a friendly AI farming companion.
    Generate a 1-minute 'Morning Briefing' podcast script for a farmer named {current_user.name}.
    Context:
    - Location: {location}
    - Recent Farm Status: Managing {crop_name}.
    - Finance: Total income ₹{total_income}, total investment ₹{total_expense}.
    - Season: Early monsoon.
    
    Tone: Encouraging, respectful, professional.
    Structure: Greeting, Weather/Market outlook, Finance summary, 1 Actionable Tip.
    Language: Simple English. Keep it under 150 words.
    No stage directions or tags like [Music]. Just the spoken text.
    """
    
    try:
        briefing = call_ai([{"role": "user", "content": prompt}], model="llama-3.1-8b-instant")
        return jsonify({"status": "success", "briefing": briefing})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@dashboard_bp.route('/api/send-demo-sms', methods=['POST'])
@login_required
def send_demo_sms():
    from config import Config
    from twilio.rest import Client
    
    account_sid = Config.TWILIO_ACCOUNT_SID
    auth_token  = Config.TWILIO_AUTH_TOKEN
    twilio_num  = Config.TWILIO_PHONE_NUMBER
    user_phone  = current_user.phone
    
    if not account_sid or not auth_token or not twilio_num:
        return jsonify({"status": "error", "message": "Twilio keys missing in .env"})
        
    if not user_phone:
        return jsonify({"status": "error", "message": "User has no phone number"})

    try:
        # Prepend +91 if missing
        sanitized_phone = user_phone if user_phone.startswith('+') else f"+91{user_phone}"
        
        client = Client(account_sid, auth_token)
        msg_body = f"Hello {current_user.name}! Your KrishiMitraAI SMS system is LIVE. We will alert you about pests and local mandi prices here."
        
        client.messages.create(body=f"✅ KrishiMitraAI:\n{msg_body}", from_=twilio_num, to=sanitized_phone)
        return jsonify({"status": "success", "message": f"Demo SMS sent to {sanitized_phone}"})
    except Exception as e:
        return jsonify({"status": "error", "message": f"Twilio Error: {str(e)}"})
