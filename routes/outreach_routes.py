from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required
import random

outreach_bp = Blueprint('outreach', __name__)

@outreach_bp.route('/outreach')
@login_required
def outreach_dashboard():
    return render_template('outreach.html')

@outreach_bp.route('/api/simulate_outreach', methods=['POST'])
@login_required
def simulate_outreach():
    alerts = [
        {
            "id": random.randint(1000, 9999),
            "type": "URGENT",
            "trigger": "Weather API: 40mm Heavy Rain Predicted in 12 hours",
            "action": "IVR + SMS Sent",
            "message": "Do not spray pesticides for 48 hours to prevent wash-off.",
            "district": "Mandya",
            "color": "danger"
        },
        {
            "id": random.randint(1000, 9999),
            "type": "WARNING",
            "trigger": "Market API: Tomato Price Dropped 15%",
            "action": "SMS Alert Sent",
            "message": "Market volatility detected. Consider delaying harvest or using cold storage.",
            "district": "Kolar",
            "color": "warning"
        },
        {
            "id": random.randint(1000, 9999),
            "type": "ACTION",
            "trigger": "Crop Stage: Day 45 Output",
            "action": "App Notification",
            "message": "Time for second round of Urea application.",
            "district": "Mysuru",
            "color": "info"
        }
    ]
    return jsonify({
        "status": "success",
        "data": random.choice(alerts)
    })
