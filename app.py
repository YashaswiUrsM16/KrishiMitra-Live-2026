from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_bcrypt import Bcrypt
from config import Config
from database import db, User, CropHistory, ExpenseRecord, PestDetection, ChatHistory
import os
import json
import base64
import pickle
import pandas as pd

# Implemented Blueprints
from routes.auth_routes import auth_bp
from routes.dashboard_routes import dashboard_bp
from routes.crop_routes import crop_bp
from routes.pest_routes import pest_bp
from routes.chat_routes import chat_bp
from routes.weather_routes import weather_bp
from routes.expense_routes import expense_bp
from routes.voice_routes import voice_bp
from routes.outreach_routes import outreach_bp
from routes.irrigation_routes import irrigation_bp
from routes.radar_routes import radar_bp
from routes.calendar_routes import calendar_bp
from routes.community_routes import community_bp
from routes.simulator_routes import simulator_bp
from routes.alerts_routes import alerts_bp
from routes.sms_routes import sms_bp
from routes.organic_routes import organic_bp

from database import initialize_roles

app = Flask(__name__, static_url_path='/static')
app.config.from_object(Config)
app.debug = True

db.init_app(app)
bcrypt = Bcrypt(app)

login_manager = LoginManager(app)
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Pehle login karo!'

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

with app.app_context():
    db.create_all()
    initialize_roles()
    
app.register_blueprint(auth_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(crop_bp)
app.register_blueprint(pest_bp)
app.register_blueprint(chat_bp)
app.register_blueprint(weather_bp)
app.register_blueprint(expense_bp)
app.register_blueprint(voice_bp)
app.register_blueprint(outreach_bp)
app.register_blueprint(irrigation_bp)
app.register_blueprint(radar_bp)
app.register_blueprint(calendar_bp)
app.register_blueprint(community_bp)
app.register_blueprint(simulator_bp)
app.register_blueprint(alerts_bp)
app.register_blueprint(sms_bp)
app.register_blueprint(organic_bp)


# ─── LOAD ML MODEL ──────────────────────────────────
try:
    with open('models/crop_model.pkl', 'rb') as f:
        crop_model = pickle.load(f)
    with open('models/label_encoder.pkl', 'rb') as f:
        label_encoder = pickle.load(f)
    with open('models/crop_info.pkl', 'rb') as f:
        crop_info = pickle.load(f)
    print(f"ML Model loaded! Accuracy: {crop_info['accuracy']*100:.2f}%")
except Exception as e:
    print(f"ML Model not loaded: {e}")
    crop_model    = None
    label_encoder = None
    crop_info     = None

# ─── HOME ───────────────────────────────────────────
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.dashboard'))
    return render_template('index.html')

# ─── MARKET ─────────────────────────────────────────
@app.route('/market')
@login_required
def market():
    return render_template('market.html', user=current_user)

# ─── SCHEMES ────────────────────────────────────────
@app.route('/schemes')
@login_required
def schemes():
    return render_template('schemes.html', user=current_user)

# ─── TIPS ───────────────────────────────────────────
@app.route('/tips')
@login_required
def tips():
    return render_template('tips.html', user=current_user)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=7860, debug=True)
