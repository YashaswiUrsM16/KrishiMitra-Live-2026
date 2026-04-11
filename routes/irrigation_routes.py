from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
import random

irrigation_bp = Blueprint('irrigation', __name__)

@irrigation_bp.route('/irrigation')
@login_required
def irrigation_dashboard():
    return render_template('irrigation.html')

@irrigation_bp.route('/api/irrigation_data', methods=['GET'])
@login_required
def get_irrigation_data():
    return jsonify({
        "status": "success",
        "data": {
            "soil_moisture": random.randint(25, 45),
            "evapotranspiration": round(random.uniform(4.0, 7.5), 1),
            "rain_probability": random.randint(10, 80),
            "recommendation": "SKIP IRRIGATION" if random.choice([True, False]) else "IRRIGATE TODAY",
            "water_quantity": f"{random.randint(400, 800)} Liters / Acre",
            "sustainability_score": random.randint(75, 98)
        }
    })
