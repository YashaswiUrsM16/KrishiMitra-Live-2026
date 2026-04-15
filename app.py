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

from routes.bio_routes import bio_bp
from routes.admin_routes import admin_bp
from database import initialize_roles, MarketPrice, GovtScheme

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

    # Seed Market and Schemes if empty
    if not MarketPrice.query.first():
        prices = [
            MarketPrice(name='Wheat', icon='🌾', price=2150, unit='quintal', change=50, category='grain', state='Punjab'),
            MarketPrice(name='Rice / Paddy', icon='🍚', price=3200, unit='quintal', change=-30, category='grain', state='Maharashtra'),
            MarketPrice(name='Maize / Corn', icon='🌽', price=1850, unit='quintal', change=20, category='grain', state='Uttar Pradesh'),
            MarketPrice(name='Tomato', icon='🍅', price=25, unit='kg', change=-5, category='vegetable', state='Maharashtra'),
            MarketPrice(name='Onion', icon='🧅', price=22, unit='kg', change=8, category='vegetable', state='Maharashtra'),
            MarketPrice(name='Potato', icon='🥔', price=18, unit='kg', change=3, category='vegetable', state='Uttar Pradesh'),
            MarketPrice(name='Banana', icon='🍌', price=30, unit='dozen', change=-5, category='fruit', state='Karnataka'),
            MarketPrice(name='Mango', icon='🥭', price=80, unit='kg', change=15, category='fruit', state='Maharashtra'),
        ]
        db.session.add_all(prices)
        db.session.commit()

    if not GovtScheme.query.first():
        schemes = [
            GovtScheme(name='PM Kisan Samman Nidhi', icon='🌾', category='income', amount='₹6,000 / year', description='Small & marginal farmers get ₹2,000 in 3 installments directly.', eligibility='Any farmer owning up to 2 hectares', documents='Aadhaar, Bank Passbook', tags='Central, Direct Benefit', link='https://pmkisan.gov.in'),
            GovtScheme(name='PM Fasal Bima Yojana', icon='🛡️', category='insurance', amount='Up to 90% coverage', description='Insurance for crop losses due to natural calamities.', eligibility='All farmers', documents='Aadhaar, Land Record', tags='Insurance, Central', link='https://pmfby.gov.in'),
            GovtScheme(name='Kisan Credit Card (KCC)', icon='💳', category='loan', amount='Up to ₹3 lakh @ 4%', description='Low-interest agri loan.', eligibility='All farmers', documents='Aadhaar, Land Records', tags='Low Interest, Bank', link='https://www.nabard.org'),
        ]
        db.session.add_all(schemes)
        db.session.commit()

    from database import AgriculturalKnowledge
    if not AgriculturalKnowledge.query.first():
        tips = [
            AgriculturalKnowledge(category='general', content='Get your soil tested every 2-3 years — Soil Health Card is FREE!', icon='🌍', soil_type='All', crop_name='General'),
            AgriculturalKnowledge(category='general', content='Practice crop rotation — never grow the same crop repeatedly.', icon='🔄', soil_type='All', crop_name='General'),
            AgriculturalKnowledge(category='kharif', content='Treat seeds with Rhizobium before sowing — builds resistance.', icon='🌱', soil_type='Loamy', crop_name='Legumes'),
            AgriculturalKnowledge(category='rabi', content='First wheat irrigation at CRI stage — 20-25 days after sowing.', icon='🌿', soil_type='Clayey', crop_name='Wheat'),
            AgriculturalKnowledge(category='water', content='Install drip irrigation — saves 50-70% water and increases yield.', icon='💧', soil_type='Sandy', crop_name='Vegetables'),
        ]
        db.session.add_all(tips)
        db.session.commit()
    
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
app.register_blueprint(bio_bp)
app.register_blueprint(admin_bp)


# ─── LOAD ML MODEL ──────────────────────────────────
try:
    with open('models/crop_model.pkl', 'rb') as f:
        crop_model = pickle.load(f)
    with open('models/label_encoder.pkl', 'rb') as f:
        label_encoder = pickle.load(f)
    with open('models/crop_info.pkl', 'rb') as f:
        crop_info = pickle.load(f)
    print(f"SUCCESS: ML Model loaded! Accuracy: {crop_info['accuracy']*100:.2f}%")
except Exception as e:
    print(f"WARNING: ML Model not loaded: {e}")
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
    prices = MarketPrice.query.all()
    return render_template('market.html', user=current_user, prices=prices)

# ─── SCHEMES ────────────────────────────────────────
@app.route('/schemes')
@login_required
def schemes():
    schemes = GovtScheme.query.all()
    return render_template('schemes.html', user=current_user, schemes=schemes)

# ─── TIPS ───────────────────────────────────────────
@app.route('/tips')
@login_required
def tips():
    from database import AgriculturalKnowledge
    all_tips = AgriculturalKnowledge.query.all()
    # Group by category for the template
    grouped_tips = {}
    for t in all_tips:
        if t.category not in grouped_tips:
            grouped_tips[t.category] = []
        grouped_tips[t.category].append({'tip': t.content, 'icon': t.icon})
    return render_template('tips.html', user=current_user, grouped_tips=grouped_tips)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=7860, debug=True)
