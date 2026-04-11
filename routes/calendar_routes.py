from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required
from datetime import datetime, timedelta

calendar_bp = Blueprint('calendar', __name__)

@calendar_bp.route('/calendar')
@login_required
def calendar_dashboard():
    return render_template('calendar.html')

@calendar_bp.route('/api/generate_calendar', methods=['POST'])
@login_required
def generate_calendar():
    crop = request.json.get('crop', 'Paddy')
    sowing_date = request.json.get('sowing_date')
    if not sowing_date:
        sowing_date = datetime.now().strftime("%Y-%m-%d")
        
    start_date = datetime.strptime(sowing_date, "%Y-%m-%d")
    
    tasks = [
        {"dayOffset": 0, "title": "Field Preparation & Sowing", "type": "Tillage", "status": "pending"},
        {"dayOffset": 15, "title": "First Weed Control", "type": "Maintenance", "status": "pending"},
        {"dayOffset": 30, "title": "Urea Top Dressing (1st Dose)", "type": "Fertilizer", "status": "pending"},
        {"dayOffset": 45, "title": "Pest Inspection (Stem Borer)", "type": "Investigation", "status": "pending"},
        {"dayOffset": 60, "title": "Urea Top Dressing (2nd Dose)", "type": "Fertilizer", "status": "pending"},
        {"dayOffset": 90, "title": "Pre-Harvest Irrigation Stop", "type": "Irrigation", "status": "pending"},
        {"dayOffset": 110, "title": "Estimated Harvest Window", "type": "Harvest", "status": "pending"}
    ]
    
    calendar_events = []
    for t in tasks:
        event_date = start_date + timedelta(days=t['dayOffset'])
        calendar_events.append({
            "date": event_date.strftime("%b %d, %Y"),
            "title": t['title'],
            "type": t['type'],
            "status": t['status']
        })

    return jsonify({"status": "success", "data": calendar_events, "crop": crop})
@calendar_bp.route('/api/voice-diary', methods=['POST'])
@login_required
def api_voice_diary():
    data = request.json
    text = data.get('text', '')
    
    from ai_utils import call_ai
    import json
    import re
    from database import db, FarmEvent
    from flask_login import current_user

    prompt = f"""
    Extract a farming task from this transcription: "{text}"
    Current Date: {datetime.now().strftime("%Y-%m-%d")}
    
    Return ONLY JSON:
    {{
        "title": "Short descriptive title (max 5 words)",
        "event_type": "one of: maintenance, fertilization, irrigation, harvest, observation",
        "description": "Short explanation",
        "date_extracted": "YYYY-MM-DD"
    }}
    """
    
    try:
        reply = call_ai([{"role": "user", "content": prompt}], model="llama-3.1-8b-instant")
        json_match = re.search(r'\{.*\}', reply, re.DOTALL)
        if json_match:
            task = json.loads(json_match.group(0))
            
            new_event = FarmEvent(
                user_id    = current_user.id,
                title      = task['title'],
                description = task['description'],
                event_type = task['event_type'],
                event_date = task['date_extracted']
            )
            db.session.add(new_event)
            db.session.commit()
            
            return jsonify({
                "status": "success", 
                "data": {
                    "title": task['title'],
                    "date": datetime.strptime(task['date_extracted'], "%Y-%m-%d").strftime("%b %d, %Y")
                }
            })
    except Exception as e:
        print(f"VOICE DIARY ERROR: {e}")
        
    return jsonify({"status": "error", "message": "Could not parse voice log"}), 400
