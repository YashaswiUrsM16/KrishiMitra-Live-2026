from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
import os

sms_bp = Blueprint('sms', __name__)

@sms_bp.route('/api/sms/send', methods=['POST'])
@login_required
def send_sms():
    """
    Receives an emergency payload from the frontend or worker queue
    and dispatches a priority SMS using the Twilio API.
    """
    data = request.get_json()
    message_body = data.get('message', 'Alert from KrishiMitraAI!')
    phone_number = data.get('phone', None)
    
    # Intelligently fallback to registered number if exact push target is unknown
    if not phone_number:
        if hasattr(current_user, 'phone') and current_user.phone:
            phone_number = current_user.phone
        elif hasattr(current_user, 'profile') and current_user.profile and hasattr(current_user.profile, 'phone'):
             # fallback for legacy profile field if exists
            phone_number = current_user.profile.phone

    if not phone_number:
         return jsonify({"status": "error", "message": "No mobile number linked to dispatcher. Please update your profile."})

    # PROD-READY: Setup TWILIO_ variables in your OS/Heroku environment
    account_sid = os.environ.get('TWILIO_ACCOUNT_SID', 'AC_placeholder_sid')
    auth_token  = os.environ.get('TWILIO_AUTH_TOKEN', 'placeholder_auth_token')
    twilio_number = os.environ.get('TWILIO_PHONE_NUMBER', '+12345678900')

    if account_sid == 'AC_placeholder_sid':
        return jsonify({"status": "simulated", "message": "SIMULATION MODE: Insert your Twilio keys to enable live routing."})

    try:
        from twilio.rest import Client
        client = Client(account_sid, auth_token)

        # Enforce international prefix tracking (+91 for India context)
        if not phone_number.startswith('+'):
            phone_number = '+91' + phone_number

        message = client.messages.create(
            body=f"🌾 KrishiMitraAI Alert:\n{message_body}",
            from_=twilio_number,
            to=phone_number
        )

        return jsonify({"status": "success", "sid": message.sid})
    
    except Exception as e:
        print("TWILIO SMS ERROR:", e)
        return jsonify({"status": "error", "message": "Twilio Configuration Error: Ensure trailing package 'twilio' is installed alongside valid auth tokens."})
