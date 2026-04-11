from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
import requests
import os
import datetime
import random
from config import Config

weather_bp = Blueprint('weather', __name__)

@weather_bp.route('/weather')
@login_required
def weather():
    api_key = Config.WEATHER_API_KEY

    # Prefer user's profile location, fallback to Mysuru
    city = "Mysuru"
    if hasattr(current_user, 'profile') and current_user.profile and current_user.profile.location_district:
        city = current_user.profile.location_district

    # Fetch Weather Data with robustness
    current_data = None
    forecast_data = None
    api_success = False
    try:
        current_url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
        current_resp = requests.get(current_url, timeout=5)
        if current_resp.status_code == 200:
            current_data = current_resp.json()
            api_success = True

        forecast_url = f"http://api.openweathermap.org/data/2.5/forecast?q={city}&appid={api_key}&units=metric"
        forecast_resp = requests.get(forecast_url, timeout=5)
        if forecast_resp.status_code == 200:
            forecast_data = forecast_resp.json()
    except Exception as e:
        print(f"Weather API Fetch Error: {e}")
        api_success = False

    # Agronomy Intelligence Logic
    alerts = []
    irrigation_advisory = "Standard irrigation cycles recommended."
    five_day_forecast = []

    if not api_success or not current_data:
        # FALLBACK / DEMO MODE: If API fails, generate realistic Mysuru weather
        current_data = {
            'main': {'temp': 28 + random.uniform(-2, 2), 'humidity': 65, 'feels_like': 30, 'pressure': 1012},
            'weather': [{'description': 'Partly Cloudy (Demo Mode)', 'icon': '02d'}],
            'wind': {'speed': 4.2},
            'name': city
        }
        # Mock 5-day forecast
        five_day_forecast = []
        days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        today_idx = datetime.datetime.now().weekday()
        for i in range(1, 6):
            five_day_forecast.append({
                'day': days[(today_idx + i) % 7],
                'temp': 27 + random.uniform(-3, 3),
                'icon': '01d' if random.random() > 0.3 else '04d',
                'desc': 'Clear' if random.random() > 0.3 else 'Cloudy'
            })
    
    if current_data:
        temp = current_data.get('main', {}).get('temp', 25)
        humidity = current_data.get('main', {}).get('humidity', 60)
        
        if temp > 35:
            alerts.append({"type": "heat", "msg": "Severe Heat Stress Indicator. Deploy shade nets."})
            irrigation_advisory = "CRITICAL: Increase irrigation frequency by 30%."
        elif temp < 10:
            alerts.append({"type": "cold", "msg": "Frost Warning. Monitor sensitive crops."})
        if humidity > 85:
            alerts.append({"type": "fungal", "msg": "High Humidity: Risk of Blight/Fungal outbreaks."})
        
        # 5-Day Logic
        seen_days = set()
        if forecast_data and 'list' in forecast_data:
            for item in forecast_data.get('list', []):
                dt = datetime.datetime.fromtimestamp(item['dt'])
                day_str = dt.strftime('%Y-%m-%d')
                if day_str not in seen_days and "12:00:00" in item.get('dt_txt', ''):
                    five_day_forecast.append({
                        'day': dt.strftime('%a'),
                        'temp': item['main']['temp'],
                        'icon': item['weather'][0]['icon'],
                        'desc': item['weather'][0]['main']
                    })
                    seen_days.add(day_str)
                if len(five_day_forecast) == 5: break

    # AI Tip
    weather_ai_tip = "Optimal conditions for standard sowing cycles."
    try:
        from ai_utils import call_ai
        weather_summary = f"Currently {current_data['main']['temp']:.1f}°C, {current_data['weather'][0]['description']}."
        ai_resp = call_ai(
            messages=[{"role": "user", "content": f"Give 1 farming tip for {city} given {weather_summary}. 20 words max."}],
            model="llama-3.1-8b-instant"
        )
        weather_ai_tip = ai_resp
    except:
        pass

    return render_template('weather.html',
                           user=current_user,
                           city=city,
                           current=current_data,
                           alerts=alerts,
                           irrigation_advisory=irrigation_advisory,
                           five_day=five_day_forecast,
                           weather_ai_tip=weather_ai_tip)

@weather_bp.route('/api/current_weather')
@login_required
def api_current_weather():
    city = "Mysuru"
    if hasattr(current_user, 'profile') and current_user.profile:
        city = current_user.profile.location_district or city
    
    api_key = Config.WEATHER_API_KEY
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
    resp = requests.get(url)
    data = resp.json()
    
    if resp.status_code == 200:
        return jsonify({
            'temperature': data['main']['temp'],
            'humidity': data['main']['humidity'],
            'rainfall': data.get('rain', {}).get('1h', 0),
            'city': city
        })
    return jsonify({'error': 'Could not fetch weather'}), 500
