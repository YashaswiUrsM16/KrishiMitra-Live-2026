from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
import time
import os
from database import db, CropHistory, ChatHistory, User
from twilio.twiml.voice_response import VoiceResponse, Gather

voice_bp = Blueprint('voice', __name__)

@voice_bp.route('/ivr')
@login_required
def ivr_dashboard():
    return render_template('voice.html')

@voice_bp.route('/api/ai_test')
def ai_test():
    """Quick diagnostic - tests AI pipeline directly."""
    try:
        from ai_utils import call_ai
        result = call_ai(
            messages=[{"role": "user", "content": "Say hello in one sentence"}],
            model="llama-3.1-8b-instant",
            max_tokens=100,
            temperature=0.5
        )
        return jsonify({"status": "ok", "reply": result})
    except Exception as e:
        import traceback
        return jsonify({"status": "error", "error": str(e), "trace": traceback.format_exc()})

@voice_bp.route('/api/voice_call', methods=['POST'])
@login_required
def api_voice_call():
    data = request.get_json()
    message = data.get('message', '')
    
    try:
        from ai_utils import call_ai
        import traceback

        location = "India"
        crops = "farming"
        if hasattr(current_user, 'profile') and current_user.profile:
            location = current_user.profile.location_district or location
            crops = current_user.profile.primary_crops or crops
            
        latest_prediction = CropHistory.query.filter_by(user_id=current_user.id).order_by(CropHistory.created_at.desc()).first()
        prediction_context = ""
        if latest_prediction:
            prediction_context = f"The ML engine predicted {latest_prediction.crop_name} as the best crop for this user with an accuracy of {round(latest_prediction.confidence_score, 1)}%. The soil is {latest_prediction.soil_type}. If they ask, make sure to state this accurate prediction and recommend secondary crops to boost profit."

        import requests as req_lib
        weather_context = "Weather data unavailable."
        from config import Config
        try:
            api_key = Config.WEATHER_API_KEY
            url = f"http://api.openweathermap.org/data/2.5/weather?q={location}&appid={api_key}&units=metric"
            r = req_lib.get(url, timeout=2)
            if r.status_code == 200:
                d = r.json()
                weather_context = f"{d['main']['temp']}C, {d['weather'][0]['description']}"
        except: pass

        dialect_instruction = "respond in standard pure Kannada (if using Kannada)."
        loc_lower = location.lower() if location else ""
        if any(c in loc_lower for c in ["mangalore", "mangaluru", "dakshina kannada", "udupi"]):
            dialect_instruction = "if using Kannada, use the Mangalore (Kundagannada) dialect with coastal slang."
        elif any(c in loc_lower for c in ["hubli", "hubballi", "dharwad", "belagavi", "bijapur"]):
            dialect_instruction = "if using Kannada, use the North Karnataka (Jawari) dialect."
        elif any(c in loc_lower for c in ["mysore", "mysuru", "mandya"]):
            dialect_instruction = "if using Kannada, use the Old Mysuru/Mandya dialect style."

        system_prompt = f"""You are KrishiMitraAI, a Senior Agricultural Expert on a live AUDIO PHONE CALL.
Farmer: {current_user.name} | Region: {location} | Crops: {crops}
LIVE WEATHER: {weather_context}
{prediction_context}

STRICT PHONE CALL RULES:
1. Act like a helpful, conversational human expert.
2. Respond in the SAME language the farmer uses (Kannada or English).
3. {dialect_instruction}
4. DO NOT use markdown, asterisks, or bullet points. Speak in clear natural sentences.
5. Provide elaborated, science-backed farming advice based on {location} and {crops}.
6. Keep answers reasonably concise (under 6 sentences) but thorough.
7. Use the weather ({weather_context}) proactively to give advice."""

        messages = [{"role": "system", "content": system_prompt}]
        
        # Cross-platform persistent memory: load ONLY last 3 entries to stay under token limits
        recent_chats = ChatHistory.query.filter_by(user_id=current_user.id).order_by(ChatHistory.timestamp.desc()).limit(3).all()
        recent_chats.reverse()
        for chat in recent_chats:
            if chat.message:  # Skip any remaining null entries
                messages.append({"role": "assistant" if chat.role == "ai" else "user", "content": chat.message})
            
        messages.append({"role": "user", "content": message})

        reply_text = call_ai(
            messages=messages,
            model="llama-3.1-8b-instant",  # Faster for voice
            max_tokens=1500,
            temperature=0.5
        )

        # Update persistent history for omnichannel continuity - ONLY if response is valid
        if reply_text and "trouble connecting" not in reply_text and "AI_LINK_FAILURE" not in reply_text:
            new_user_msg = ChatHistory(user_id=current_user.id, role='user', message=message)
            new_ai_msg = ChatHistory(user_id=current_user.id, role='ai', message=reply_text)
            db.session.add(new_user_msg)
            db.session.add(new_ai_msg)
            db.session.commit()

        return jsonify({
            "status": "success",
            "reply": reply_text
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"status": "error", "reply": f"Sorry, connection error: {str(e)}"})


# ─── REAL PHONE CALL INTEGRATION (TWILIO IVR) ───────────────────────

@voice_bp.route('/voice/incoming', methods=['POST'])
def voice_incoming():
    """Entry point for Twilio Voice Webhook."""
    resp = VoiceResponse()
    
    # Identify user by phone number
    from_number = request.form.get('From', '')
    user_context = "Farmer"
    # Search for user in DB (assuming phone is stored with prefix)
    clean_num = from_number.replace('+91', '')[-10:] # get last 10 digits
    user = User.query.filter(User.phone.contains(clean_num)).first()
    
    greeting = "Welcome to KrishiMitraAI. How can I help your farm today?"
    lang = "en-IN"
    
    speech_hints = "kannada, agriculture, bele, raitha, krishi, test, ok, hello"
    
    if user:
        user_context = user.name
        # Set language
        if hasattr(user, 'profile') and user.profile and user.profile.language == 'kn':
            greeting = f"ನಮಸ್ಕಾರ {user.name}, ಕೃಷಿಮಿತ್ರಾ ಎಐ ಗೆ ಸ್ವಾಗತ. ನಾನು ನಿಮಗೆ ಹೇಗೆ ಸಹಾಯ ಮಾಡಲಿ?"
            lang = "kn-IN"
        else:
            greeting = f"Hello {user.name}, welcome to KrishiMitraAI. How can I assist you today?"
            
        # Set hints based on region
        if hasattr(user, 'profile') and user.profile and user.profile.location_district:
            loc_lower = user.profile.location_district.lower()
            if any(c in loc_lower for c in ["mangalore", "mangaluru", "dakshina kannada", "udupi"]):
                speech_hints = "yenta, maaraya, kanchodu, edde, porlu, daane, aanda, ijji, krishi, bele"
            elif any(c in loc_lower for c in ["uttara kannada", "karwar", "sirsi", "kumta"]):
                speech_hints = "gottada, aatu, kelsa, henga, haudu, maraya, krishi, bele"
            elif any(c in loc_lower for c in ["hubli", "hubballi", "dharwad", "belagavi"]):
                speech_hints = "togo, barri, aithri, henge, khare, beku, krishi, raitha, bele"

    gather = Gather(input='speech', action='/voice/respond', language=lang, speechTimeout='auto', hints=speech_hints)
    gather.say(greeting, language=lang)
    resp.append(gather)
    
    # If no input
    resp.redirect('/voice/incoming')
    return str(resp)

@voice_bp.route('/voice/respond', methods=['POST'])
def voice_respond():
    """Processes speech transcript from Twilio."""
    resp = VoiceResponse()
    speech_result = request.form.get('SpeechResult', '')
    from_number = request.form.get('From', '')
    
    if not speech_result:
        resp.redirect('/voice/incoming')
        return str(resp)
        
    # Find user to get AI context
    clean_num = from_number.replace('+91', '')[-10:]
    user = User.query.filter(User.phone.contains(clean_num)).first()
    
    # Call AI logic (similar to api_voice_call)
    try:
        from ai_utils import call_ai
        
        location = "India"
        crops = "farming"
        prediction_context = ""
        user_id = 1 # fallback
        
        if user:
            user_id = user.id
            if hasattr(user, 'profile') and user.profile:
                location = user.profile.location_district or location
                crops = user.profile.primary_crops or crops
            
            latest_prediction = CropHistory.query.filter_by(user_id=user.id).order_by(CropHistory.created_at.desc()).first()
            if latest_prediction:
                prediction_context = f"The ML engine predicted {latest_prediction.crop_name} for this user. Accuracy: {round(latest_prediction.confidence_score, 1)}%."

        dialect_instruction = "respond in standard pure Kannada."
        loc_lower = location.lower() if location else ""
        if any(c in loc_lower for c in ["mangalore", "mangaluru", "dakshina kannada", "udupi"]):
            dialect_instruction = "respond ONLY in Mangalore Kannada dialect (Kundagannada/Coastal Kannada style), using coastal slang and intonation."
        elif any(c in loc_lower for c in ["uttara kannada", "karwar", "sirsi", "kumta"]):
            dialect_instruction = "respond ONLY using Uttara Kannada dialect (Havyaka/Kumta Kannada style) with local slang."
        elif any(c in loc_lower for c in ["hubli", "hubballi", "dharwad", "belagavi", "bijapur"]):
            dialect_instruction = "respond ONLY using North Karnataka Kannada (Jawari/Hubballi dialect) slang."
        elif any(c in loc_lower for c in ["mysore", "mysuru", "mandya"]):
            dialect_instruction = "respond ONLY using old Mysuru/Mandya dialect Kannada."

        system_prompt = f"You are KrishiMitraAI on a REAL PHONE CALL with farmer {user.name if user else 'User'}. Region: {location}. Crops: {crops}. {prediction_context}. Speak naturally, NO markdown. If they speak in Kannada or if the region is in Karnataka, {dialect_instruction}"
        
        messages = [{"role": "system", "content": system_prompt}]
        
        # Load history
        if user:
            recent_chats = ChatHistory.query.filter_by(user_id=user.id).order_by(ChatHistory.timestamp.desc()).limit(5).all()
            recent_chats.reverse()
            for chat in recent_chats:
                messages.append({"role": "assistant" if chat.role == "ai" else "user", "content": chat.message})
        
        messages.append({"role": "user", "content": speech_result})
        
        reply_text = call_ai(messages=messages, model="llama-3.1-8b-instant")
        
        # Save history if valid
        if user and reply_text and "I'm having trouble connecting" not in reply_text:
            db.session.add(ChatHistory(user_id=user.id, role='user', message=speech_result))
            db.session.add(ChatHistory(user_id=user.id, role='ai', message=reply_text))
            db.session.commit()
            
        lang = "en-IN"
        speech_hints = "kannada, agriculture, bele, raitha, krishi, test, ok, hello"
        loc_lower = location.lower() if location else ""

        if user and hasattr(user, 'profile') and user.profile and user.profile.language == 'kn':
            lang = "kn-IN"
            
        if any(c in loc_lower for c in ["mangalore", "mangaluru", "dakshina kannada", "udupi"]):
            speech_hints = "yenta, maaraya, kanchodu, edde, porlu, daane, aanda, ijji, krishi, bele"
        elif any(c in loc_lower for c in ["uttara kannada", "karwar", "sirsi", "kumta"]):
            speech_hints = "gottada, aatu, kelsa, henga, haudu, maraya, krishi, bele"
        elif any(c in loc_lower for c in ["hubli", "hubballi", "dharwad", "belagavi"]):
            speech_hints = "togo, barri, aithri, henge, khare, beku, krishi, raitha, bele"

        gather = Gather(input='speech', action='/voice/respond', language=lang, speechTimeout='auto', hints=speech_hints)
        gather.say(reply_text, language=lang)
        resp.append(gather)
        resp.redirect('/voice/incoming')

    except Exception as e:
        resp.say("Sorry, I encountered an error. Please call again later.")
        print("IVR Error:", e)
        
    return str(resp)
