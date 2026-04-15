from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

# ----------------- MODULE 1: ROLES & AUTH -----------------

class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False) # Farmer, Admin, Expert
    description = db.Column(db.String(200))

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True) # Optional for phone-only users
    phone = db.Column(db.String(15), unique=True, nullable=True)  # Phone login support
    password = db.Column(db.String(200), nullable=False)          # Bcrypt hash
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'), default=1) # 1 = Farmer
    is_active = db.Column(db.Boolean, default=True)               # For account suspension
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # OTP specific
    otp_secret = db.Column(db.String(50), nullable=True)          # Secret for TOTP/SMS validation
    otp_verified = db.Column(db.Boolean, default=False)
    last_login = db.Column(db.DateTime, nullable=True)
    location = db.Column(db.String(100), nullable=True)           # Quick location for display

    # Accessibility: 4-digit PIN for illiterate farmers (phone + PIN login)
    pin_hash = db.Column(db.String(200), nullable=True)           # Bcrypt hash of 4-digit PIN

    # Community Accessibility: Allow a Leader/VLE to manage multiple farmers
    parent_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    managed_farmers = db.relationship('User', backref=db.backref('leader', remote_side=[id]), lazy='dynamic')

    # Relationships
    profile = db.relationship('UserProfile', backref='user', uselist=False, cascade="all, delete-orphan")
    activity_logs = db.relationship('ActivityLog', backref='user', lazy='dynamic')
    expenses = db.relationship('ExpenseRecord', backref='user', lazy='dynamic')
    crops = db.relationship('CropHistory', backref='user', lazy='dynamic')
    chats = db.relationship('ChatHistory', backref='user', lazy='dynamic')

class UserProfile(db.Model):
    __tablename__ = 'user_profiles'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    location_district = db.Column(db.String(100))                 # Extended location tracking
    farm_size_acres = db.Column(db.Float, nullable=True)
    primary_crops = db.Column(db.String(255))                     # Comma separated list
    language = db.Column(db.String(10), default='en')             # Default English
    communication_pref = db.Column(db.String(20), default='web')  # web / sms / voice
    theme_preference = db.Column(db.String(10), default='light')
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class ActivityLog(db.Model):
    __tablename__ = 'activity_logs'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    action = db.Column(db.String(255), nullable=False)            # e.g. "Logged In", "Password Reset", "Crop Predicted"
    ip_address = db.Column(db.String(50))
    user_agent = db.Column(db.String(255))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

# ----------------- MODULE 2: DECISION INT -----------------

class CropHistory(db.Model):
    __tablename__ = 'crop_history'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    crop_name = db.Column(db.String(100))
    soil_type = db.Column(db.String(50))
    season = db.Column(db.String(50))
    recommendation = db.Column(db.Text)
    confidence_score = db.Column(db.Float, nullable=True)         # ML Confidence %
    soil_suitability = db.Column(db.Float, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# ----------------- MODULE 3: DIAGNOSTICS & CHAT -----------------

class ChatHistory(db.Model):
    __tablename__ = 'chat_histories'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    role = db.Column(db.String(20)) # 'user' or 'ai'
    message = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class PestDetection(db.Model):
    __tablename__ = 'pest_detections'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    image_path = db.Column(db.String(200))
    result = db.Column(db.Text)                                   # Store JSON string natively based on new prompt
    severity = db.Column(db.String(20), nullable=True)            # low/medium/high/critical
    risk_score = db.Column(db.Float, nullable=True)
    location   = db.Column(db.String(100), nullable=True)         # Tracking for community heatmap
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# ----------------- MODULE 6: FINANCIAL INT -----------------

class ExpenseRecord(db.Model):
    __tablename__ = 'expense_records'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    title = db.Column(db.String(100))
    amount = db.Column(db.Float)
    type = db.Column(db.String(10), default='expense')            # 'expense' or 'income'
    category = db.Column(db.String(50))
    date = db.Column(db.DateTime, default=datetime.utcnow)
    is_anomaly = db.Column(db.Boolean, default=False)             # For cost anomaly detection


class FarmEvent(db.Model):
    __tablename__ = 'farm_events'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    event_type = db.Column(db.String(50))                         # 'maintenance', 'harvest', 'fertilizer', 'voice_log'
    status = db.Column(db.String(20), default='completed')        # For logs, usually completed
    event_date = db.Column(db.String(50))                         # Human readable date or ISO
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# ----------------- MODULE 10: KNOWLEDGE BASE -----------------

class AgriculturalKnowledge(db.Model):
    __tablename__ = 'agri_knowledge'
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(50))                           # e.g. "Soil Suitability", "Pest Control"
    content = db.Column(db.Text, nullable=False)                  # Detailed fact for AI to read
    icon = db.Column(db.String(10))                               # UI Icon
    soil_type = db.Column(db.String(50))                          # Optional metadata
    crop_name = db.Column(db.String(50))                          # Optional metadata
    source = db.Column(db.String(255))                             # Where the data came from
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# ----------------- MODULE 11: MARKET & WELFARE -----------------

class MarketPrice(db.Model):
    __tablename__ = 'market_prices'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    icon = db.Column(db.String(10))
    price = db.Column(db.Float, nullable=False)
    unit = db.Column(db.String(20), default='quintal')
    change = db.Column(db.Float, default=0.0)
    category = db.Column(db.String(50))                           # grain, vegetable, fruit, pulse, spice
    state = db.Column(db.String(50))
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class GovtScheme(db.Model):
    __tablename__ = 'govt_schemes'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    icon = db.Column(db.String(10))
    category = db.Column(db.String(50))                           # income, insurance, loan, equipment, irrigation
    amount = db.Column(db.String(100))
    description = db.Column(db.Text)
    eligibility = db.Column(db.Text)
    documents = db.Column(db.Text)
    tags = db.Column(db.String(255))                              # Comma-separated
    link = db.Column(db.String(255))
    status = db.Column(db.String(20), default='Active')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Helper to automatically create basic roles and data
def initialize_roles():
    if not Role.query.first():
        db.session.add(Role(name='Farmer', description='End user farmer account'))
        db.session.add(Role(name='Admin', description='System Administrator'))
        db.session.add(Role(name='Expert', description='Agricultural Expert account'))
        db.session.commit()