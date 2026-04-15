from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
import os

bio_bp = Blueprint('bio', __name__)

@bio_bp.route('/bio_dashboard')
@login_required
def bio_dashboard():
    return render_template('bio_dashboard.html', user=current_user)

@bio_bp.route('/api/farm/sync_intelligence', methods=['POST'])
@login_required
def sync_intelligence():
    """Syncs farm data with simulated ISRO Bhuvan and IMD feeds."""
    data = request.json
    size = float(data.get('size', 1.0))
    
    # Logic: Base revenue per acre * size * multipliers
    base_rev = 8500 * size
    
    intelligence_pack = {
        "status": "synchronized",
        "topology": {"type": "irregular_plateau", "risk": "low"},
        "weather_fusion": {"imd_forecast": "Intermittent showers", "intensity": "moderate"},
        "scenarios": {
            "best": round(base_rev * 1.8),
            "average": round(base_rev),
            "worst": round(base_rev * 0.3)
        }
    }
    return jsonify(intelligence_pack)

@bio_bp.route('/api/market/trending')
@login_required
def market_trending():
    """Returns trending commodity data for PRO insights."""
    # Data synced with market.html values
    trending = [
        {"name": "Rice (A)", "price": 3200, "trend": "up", "pct": 4.2},
        {"name": "Wheat", "price": 2150, "trend": "up", "pct": 1.5},
        {"name": "Maize", "price": 1850, "trend": "down", "pct": -2.1},
        {"name": "Cotton", "price": 6800, "trend": "neutral", "pct": 0}
    ]
    return jsonify(trending)
