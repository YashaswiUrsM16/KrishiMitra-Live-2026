from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required
import random

radar_bp = Blueprint('radar', __name__)

@radar_bp.route('/radar')
@login_required
def radar_dashboard():
    return render_template('radar.html')

@radar_bp.route('/api/radar_data')
@login_required
def get_radar_data():
    districts = [
        {"name": "Mysuru", "lat": 12.3051, "lng": 76.6413, "disease": "Leaf Blight", "cases": random.randint(10, 50)},
        {"name": "Mandya", "lat": 12.5218, "lng": 76.8951, "disease": "Rice Blast", "cases": random.randint(30, 80)},
        {"name": "Hassan", "lat": 13.0068, "lng": 76.1004, "disease": "Powdery Mildew", "cases": random.randint(5, 25)},
        {"name": "Tumakuru", "lat": 13.3391, "lng": 77.1013, "disease": "Stem Borer", "cases": random.randint(15, 60)}
    ]
    return jsonify({"status": "success", "data": districts})
