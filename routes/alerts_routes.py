from flask import Blueprint, jsonify
from flask_login import login_required, current_user
import os
import requests

alerts_bp = Blueprint('alerts', __name__)

@alerts_bp.route('/api/alerts/live')
@login_required
def get_live_alerts():
    city = current_user.profile.location_district if hasattr(current_user, 'profile') and current_user.profile and current_user.profile.location_district else "Mysuru"
    alerts = []
    
    # 1. Weather Logic
    try:
        api_key = os.environ.get('WEATHER_API_KEY', '793fc1ba19e4a307049079f29107ccfa')
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
        r = requests.get(url, timeout=3)
        if r.status_code == 200:
            data = r.json()
            temp = data['main']['temp']
            weather_desc = data['weather'][0]['main'].lower()
            
            if 'rain' in weather_desc or 'storm' in weather_desc or 'drizzle' in weather_desc:
                alerts.append({
                    "id": "w1",
                    "type": "weather",
                    "priority": "Emergency",
                    "title": "🌧️ Rain Alert",
                    "message": f"Precipitation detected in {city}. Do not irrigate today! Delay any chemical spraying.",
                    "time": "Just now"
                })
            elif temp > 35:
                alerts.append({
                    "id": "w2",
                    "type": "weather",
                    "priority": "Warning",
                    "title": "🔥 High Heat Warning",
                    "message": f"Temperatures reaching {temp}°C. Turn on drip irrigation to prevent crop heat stress.",
                    "time": "Just now"
                })
    except:
        pass

    # 2. Growth & Lifecycle logical alerts
    alerts.append({
        "id": "s1",
        "type": "schedule",
        "priority": "Normal",
        "title": "🌱 Fertilizer Schedule",
        "message": "It is time to apply the top dressing of NPK according to your active Maize calendar.",
        "time": "2 hours ago"
    })
    
    alerts.append({
        "id": "p1",
        "type": "risk",
        "priority": "Warning",
        "title": "🐛 Pest Outbreak Warning",
        "message": "High incidence of Fall Armyworm reported in your district this week. Check lower leaves.",
        "time": "Yesterday"
    })

    # Sort alerts so Emergency is on top
    priority_order = {"Emergency": 0, "Warning": 1, "Normal": 2}
    alerts.sort(key=lambda x: priority_order.get(x['priority'], 3))

    return jsonify({"status": "success", "alerts": alerts})
