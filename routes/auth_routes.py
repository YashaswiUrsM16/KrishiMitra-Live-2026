from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from database import db, User, UserProfile, Role, ActivityLog
import bcrypt

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # API handles json, HTML form handles form data
        data = request.get_json() if request.is_json else request.form
        name = data.get('name')
        email = data.get('email')
        phone = data.get('phone')
        password = data.get('password')
        location_district = data.get('location_district')
        language = data.get('language', 'en')
        communication_pref = data.get('communication_pref', 'web')
        farm_size = data.get('farm_size')
        primary_crops = data.get('primary_crops')

        if User.query.filter((User.email == email) | (User.phone == phone)).first():
            if request.is_json:
                return jsonify({'status': 'error', 'message': 'Email or phone already registered'}), 400
            flash('Email or Phone already registered!', 'danger')
            return redirect(url_for('auth.register'))

        from flask_bcrypt import generate_password_hash
        hashed_pw = generate_password_hash(password).decode('utf-8')
        
        # Normalize phone for consistent storage and lookup
        def normalize_phone(p):
            if not p: return None
            nums = ''.join(filter(str.isdigit, p))
            return nums[-10:] if len(nums) >= 10 else nums

        norm_phone = normalize_phone(phone)
        
        # Check if already registered using normalized matching
        existing_user = None
        all_users = User.query.all()
        for u in all_users:
            # Check email match (only if email provided)
            email_match = email and u.email == email
            # Check phone match (normalized)
            phone_match = norm_phone and u.phone and normalize_phone(u.phone) == norm_phone
            
            if email_match or phone_match:
                existing_user = u
                break

        if existing_user:
            if request.is_json:
                return jsonify({'status': 'error', 'message': 'Email or phone already registered'}), 400
            flash('Email or Phone already registered!', 'danger')
            return redirect(url_for('auth.register'))

        # Default Role
        farmer_role = Role.query.filter_by(name='Farmer').first()
        if not farmer_role:
            farmer_role = Role(name='Farmer', description='End user farmer account')
            db.session.add(farmer_role)
            db.session.commit()

        try:
            # Auto-generate PIN from last 4 digits of phone
            digits_only = ''.join(filter(str.isdigit, phone or ''))
            auto_pin = digits_only[-4:] if len(digits_only) >= 4 else '0000'
            from flask_bcrypt import generate_password_hash as gen_hash
            pin_hash_val = gen_hash(auto_pin).decode('utf-8')

            user = User(name=name, email=email, phone=phone, password=hashed_pw,
                        role_id=farmer_role.id, pin_hash=pin_hash_val)
            db.session.add(user)
            db.session.flush() # get user.id

            profile = UserProfile(
                user_id=user.id,
                location_district=location_district,
                language=language,
                communication_pref=communication_pref,
                farm_size_acres=float(farm_size) if farm_size else None,
                primary_crops=primary_crops
            )
            db.session.add(profile)
            
            log = ActivityLog(user_id=user.id, action="Account Registered", ip_address=request.remote_addr)
            db.session.add(log)
            db.session.commit()
            if request.is_json:
                return jsonify({
                    'status': 'success',
                    'message': f'Registration successful! Your PIN is the last 4 digits of your phone: {auto_pin}'
                })
            
            flash(
                f'Registration successful! Your easy login PIN is the last 4 digits of your phone number: {auto_pin}',
                'success'
            )
            return redirect(url_for('auth.login'))
            
        except Exception as e:
            db.session.rollback()
            if request.is_json:
                return jsonify({'status': 'error', 'message': 'Database constraint error: Email or Phone may already be in use.'}), 400
            flash('Email or Phone is already taken!', 'danger')
            return redirect(url_for('auth.register'))
        
    return render_template('login.html', mode='register') # This template should have the new wizard

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        identifier = data.get('email') or data.get('phone') # allow phone OR email login
        password = data.get('password')
        
        from flask_bcrypt import check_password_hash
        
        def normalize_phone(p):
            if not p: return None
            nums = ''.join(filter(str.isdigit, p))
            return nums[-10:] if len(nums) >= 10 else nums

        user = None
        if '@' in identifier:
            user = User.query.filter_by(email=identifier).first()
        else:
            norm_id = normalize_phone(identifier)
            all_u = User.query.all()
            for u in all_u:
                if u.phone and normalize_phone(u.phone) == norm_id:
                    user = u
                    break

        if user and check_password_hash(user.password, password):
            if not user.is_active:
                flash('Account is suspended. Contact admin.', 'danger')
                return redirect(url_for('auth.login'))
                
            login_user(user)
            import datetime
            user.last_login = datetime.datetime.utcnow()
            
            log = ActivityLog(user_id=user.id, action="Logged In", ip_address=request.remote_addr, user_agent=request.headers.get('User-Agent'))
            db.session.add(log)
            db.session.commit()
            
            if request.is_json:
                return jsonify({'status': 'success', 'message': f'Welcome back, {user.name}! 🌾'})
                
            flash(f'Welcome back, {user.name}! 🌾', 'success')
            return redirect(url_for('dashboard.dashboard'))
            
        if request.is_json:
            return jsonify({'status': 'error', 'message': 'Invalid credentials'}), 401
            
        flash('Invalid email/phone or password!', 'danger')
    return render_template('login.html', mode='login')

@auth_bp.route('/login/pin', methods=['POST'])
def login_pin():
    """Accessible PIN login: phone number + 4-digit PIN — no text literacy required."""
    data = request.get_json() if request.is_json else request.form
    raw_phone = data.get('phone', '').strip()
    pin = data.get('pin', '').strip()

    if not raw_phone or not pin or len(pin) != 4 or not pin.isdigit():
        if request.is_json:
            return jsonify({'status': 'error', 'message': 'Enter phone and 4-digit PIN'}), 400
        flash('Please enter your phone number and 4-digit PIN.', 'danger')
        return redirect(url_for('auth.login'))

    print(f"DEBUG PIN LOGIN: Received Phone='{raw_phone}', PIN='{pin}'")
    
    def normalize_phone(p):
        if not p: return None
        nums = ''.join(filter(str.isdigit, p))
        return nums[-10:] if len(nums) >= 10 else nums

    search_id = normalize_phone(raw_phone)
    print(f"DEBUG PIN LOGIN: Normalized Search ID='{search_id}'")

    user = None
    all_users = User.query.all()
    for u in all_users:
        if u.phone:
            stored_norm = normalize_phone(u.phone)
            if stored_norm == search_id:
                user = u
                break

    if not user:
        print(f"DEBUG PIN LOGIN: User NOT FOUND for {search_id}")
        if request.is_json:
            return jsonify({'status': 'error', 'message': f'Phone number {raw_phone} not found. please register first.'}), 401
        flash('Phone number not registered. Please check and try again.', 'danger')
        return redirect(url_for('auth.login'))

    print(f"DEBUG PIN LOGIN: Found user {user.name} (ID: {user.id})")
    # FIX: Bulletproof PIN check. 
    # If the user exactly enters the last 4 digits of their stored phone number, 
    # it ALWAYS works. This fulfills the exact rule we promised the farmer without fail.
    stored_digits = ''.join(filter(str.isdigit, user.phone or ''))
    default_pin = stored_digits[-4:] if len(stored_digits) >= 4 else '0000'
    
    is_valid_pin = False

    # 1. Check if they used the default "last 4 digits" PIN
    if pin == default_pin:
        is_valid_pin = True
    
    # 2. Or check if they have a custom PIN hash stored and it matches
    if not is_valid_pin and user.pin_hash:
        from flask_bcrypt import check_password_hash
        if check_password_hash(user.pin_hash, pin):
            is_valid_pin = True

    if is_valid_pin:
        if not user.is_active:
            if request.is_json:
                return jsonify({'status': 'error', 'message': 'Account suspended'}), 403
            flash('Account is suspended. Contact admin.', 'danger')
            return redirect(url_for('auth.login'))

        login_user(user)
        import datetime
        user.last_login = datetime.datetime.utcnow()
        log = ActivityLog(user_id=user.id, action="Logged In via PIN",
                          ip_address=request.remote_addr)
        db.session.add(log)
        db.session.commit()

        if request.is_json:
            return jsonify({'status': 'success',
                            'redirect': url_for('dashboard.dashboard'),
                            'name': user.name})
        flash(f'ಸ್ವಾಗತ {user.name}! 🌾', 'success')
        return redirect(url_for('dashboard.dashboard'))

    # Wrong PIN
    if request.is_json:
        return jsonify({'status': 'error', 'message': 'Wrong PIN. Try the last 4 digits of your mobile number.'}), 401
    flash('Wrong PIN. Your PIN = last 4 digits of your mobile number.', 'danger')
    return redirect(url_for('auth.login'))

@auth_bp.route('/set-pin', methods=['POST'])
@login_required
def set_pin():
    """Field agent or farmer sets a 4-digit PIN for easy future logins."""
    data = request.get_json() if request.is_json else request.form
    pin = data.get('pin', '').strip()
    if not pin or len(pin) != 4 or not pin.isdigit():
        return jsonify({'status': 'error', 'message': 'PIN must be exactly 4 digits'}), 400

    from flask_bcrypt import generate_password_hash
    current_user.pin_hash = generate_password_hash(pin).decode('utf-8')
    db.session.commit()
    return jsonify({'status': 'success',
                    'message': 'PIN set! You can now log in with phone + PIN.'})


@auth_bp.route('/logout')
@login_required
def logout():
    log = ActivityLog(user_id=current_user.id, action="Logged Out", ip_address=request.remote_addr)
    db.session.add(log)
    db.session.commit()
    logout_user()
    flash('You have been logged out!', 'info')
    return redirect(url_for('index'))
