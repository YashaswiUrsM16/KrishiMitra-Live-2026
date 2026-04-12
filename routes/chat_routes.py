from flask import Blueprint, render_template, request, jsonify, session
from flask_login import login_required, current_user
import os
from database import db, CropHistory, ChatHistory

chat_bp = Blueprint('chat', __name__)

@chat_bp.route('/chatbot')
@login_required
def chatbot():
    recent_chats = ChatHistory.query.filter_by(user_id=current_user.id).order_by(ChatHistory.timestamp.desc()).limit(20).all()
    recent_chats.reverse()
    return render_template('chatbot.html', user=current_user, chat_history=recent_chats)

@chat_bp.route('/api/chat', methods=['POST'])
@login_required
def api_chat():
    data = request.get_json()
    message = data.get('message', '')

    try:
        from ai_utils import call_ai

        # Gather profile context
        location = "India"
        crops = "farming"
        if hasattr(current_user, 'profile') and current_user.profile:
            location = current_user.profile.location_district or location
            crops = current_user.profile.primary_crops or crops
            
        latest_prediction = CropHistory.query.filter_by(user_id=current_user.id).order_by(CropHistory.created_at.desc()).first()
        prediction_context = ""
        if latest_prediction:
            prediction_context = f"The ML engine recently predicted {latest_prediction.crop_name} as the best crop for this user with an accuracy/confidence of {round(latest_prediction.confidence_score, 1)}%. The soil is {latest_prediction.soil_type}. Highly recommend mentioning this prediction accuracy and suggesting secondary crops/intercrops to boost profit."

        import requests
        weather_context = "Weather data unavailable."
        from config import Config
        try:
            api_key = Config.WEATHER_API_KEY
            url = f"http://api.openweathermap.org/data/2.5/weather?q={location}&appid={api_key}&units=metric"
            r = requests.get(url, timeout=2)
            if r.status_code == 200:
                d = r.json()
                weather_context = f"{d['main']['temp']}°C, {d['weather'][0]['description']}"
        except: pass

        dialect_instruction = "respond in standard pure Kannada (if using Kannada)."
        loc_lower = location.lower() if location else ""
        if any(c in loc_lower for c in ["mangalore", "mangaluru", "dakshina kannada", "udupi"]):
            dialect_instruction = "if responding in Kannada, use the Mangalore/Coastal Kannada dialect (Kundagannada) with local seafaring and farming slang."
        elif any(c in loc_lower for c in ["hubli", "hubballi", "dharwad", "belagavi", "bijapur", "bagalkot"]):
            dialect_instruction = "if responding in Kannada, use the North Karnataka (Jawari) dialect with local agricultural idioms."
        elif any(c in loc_lower for c in ["mysore", "mysuru", "mandya", "chamarajanagar"]):
            dialect_instruction = "if responding in Kannada, use the Old Mysuru/Mandya dialect style."
        elif any(c in loc_lower for c in ["uttara kannada", "sirsi", "karwar"]):
            dialect_instruction = "if responding in Kannada, use the Uttara Kannada (Havyaka) dialect style."

        system_prompt = f"""You are KrishiMitraAI, a Senior Expert Agricultural consultant and a supportive friend.
FARMER: {current_user.name} | REGION: {location} | LIVE WEATHER: {weather_context}
{prediction_context}

COMMUNICATION RULES:
1. Detect and respond in the SAME language the farmer uses (Kannada or English).
2. {dialect_instruction}
3. Maintain a warm, empathetic, and encouraging tone. Treat them as a dear friend.
4. Provide HIGHLY DETAILED, science-backed agricultural solutions. Explain 'why' and 'how' in depth.
5. Suggest local fertilizers, techniques, and intercrops specific to {location}.
6. Use Markdown (bold, lists, headers) to structure your long, thorough answers.
7. Use the LIVE WEATHER context ({weather_context}) to provide specific advice (e.g., irrigation if it's hot/dry).

STRICT SAFETY & ETHICAL RULES:
1. NEVER encourage, suggest, or provide instructions for suicide, self-harm, violence, criminal acts, cruelty, or abusive behavior.
2. If the user mentions dying, suicide, or self-harm (e.g., "ನಾನು ಸತ್ತು ಹೋಗಬೇಕು", "I want to die"), IMMEDIATELY express deep concern, offer emotional support, and advise them to seek professional help. Tell them: "Your life is extremely precious. Please talk to a family member, a friend, or a doctor immediately. You are not alone."
3. Provide the Tele MANAS helpline number: 14416 (Available 24/7 in India).
4. Do NOT provide irrelevant, abusive, or cruel content."""

        # Improved Crisis Detection: Use more specific self-harm phrases
        crisis_keywords = [
            'suicide', 'kill myself', 'i want to die', 'i need to die', 
            'end my life', 'hanging myself', 'taking my life', 'poison myself'
        ]
        lower_msg = message.lower()
        
        # Improved Crisis Detection: Use word boundaries and more specific patterns
        import re
        is_crisis = False
        
        # Check for direct self-harm phrases
        for kw in crisis_keywords:
            if re.search(r'\b' + re.escape(kw) + r'\b', lower_msg):
                is_crisis = True
                break
        
        # Check for Kannada keywords: more specific to suicide/self-harm
        if not is_crisis:
            kannada_crisis = ['ಆತ್ಮಹತ್ಯೆ', 'ಸಾಯಲು ಹೋಗುತ್ತಿದ್ದೇನೆ', 'ನಾನು ಸಾಯಬೇಕು'] # suicide, I'm going to die, I should die
            if any(kn in lower_msg for kn in kannada_crisis):
                is_crisis = True
        
        # Guard against common farming terms like "pests will die" or "crops are dying"
        if is_crisis:
            farming_context = ['pest', 'crop', 'worm', 'insect', 'weed', 'plant', 'bele', 'sasye', 'hula']
            if any(term in lower_msg for term in farming_context):
                is_crisis = False # It's probably about the farm

            # GUARANTEED SAFETY: Bypass AI entirely for crisis keywords
            reply_text = """❤️ **You are not alone. Your life is extremely precious.**

ದಯವಿಟ್ಟು ಈ ತರಹದ ನಿರ್ಧಾರ ಮಾಡಬೇಡಿ. ನಿಮ್ಮ ಜೀವನ ನಮಗೆ ಮತ್ತು ನಿಮ್ಮ ಕುಟುಂಬಕ್ಕೆ ಬಹಳ ಮುಖ್ಯ. ನಾವು ನಿಮ್ಮನ್ನು ಪ್ರೀತಿಸುತ್ತೇವೆ ಮತ್ತು ನೀವು ಸುರಕ್ಷಿತವಾಗಿರಬೇಕೆಂದು ಹಾರೈಸುತ್ತೇವೆ.

**Please do not take this step.** Reach out to someone you trust—a friend, family member, or a doctor—immediately. 

📞 **Call Tele MANAS Helpline: 14416**
(Available 24/7, Free and Confidential help in Kannada and English)

Your presence matters more than any problem you are facing. Please reach out now."""
            
            # Save to history so it persists
            new_user_msg = ChatHistory(user_id=current_user.id, role='user', message=message)
            new_ai_msg = ChatHistory(user_id=current_user.id, role='ai', message=reply_text)
            db.session.add(new_user_msg)
            db.session.add(new_ai_msg)
            db.session.commit()

            return jsonify({
                'reply': reply_text, 
                'status': 'ok',
                'is_crisis': True
            })

        # Regular AI Flow
        messages = [{"role": "system", "content": system_prompt}]
        recent_chats = ChatHistory.query.filter_by(user_id=current_user.id).order_by(ChatHistory.timestamp.desc()).limit(10).all()
        recent_chats.reverse()
        for chat in recent_chats:
            messages.append({"role": "assistant" if chat.role == "ai" else "user", "content": chat.message})
        messages.append({"role": "user", "content": message})

        reply_text = call_ai(
            messages=messages,
            model="gemini-2.0-flash",
            max_tokens=3000,
            temperature=0.5
        )

        # Update Persistent History - ONLY save valid AI responses
        if reply_text and "trouble connecting" not in reply_text and "AI_LINK_FAILURE" not in reply_text and "error occurred" not in reply_text:
            new_user_msg = ChatHistory(user_id=current_user.id, role='user', message=message)
            new_ai_msg = ChatHistory(user_id=current_user.id, role='ai', message=reply_text)
            db.session.add(new_user_msg)
            db.session.add(new_ai_msg)
            db.session.commit()

        return jsonify({
            'reply': reply_text, 
            'status': 'ok',
            'is_crisis': False
        })

    except Exception as e:
        print(f"CHAT ERROR: {e}")
        return jsonify({'reply': f'An error occurred: {str(e)}. Please check API connections.', 'status': 'error'})

@chat_bp.route('/api/chat/clear', methods=['POST'])
@login_required
def clear_chat():
    # Delete from DB
    ChatHistory.query.filter_by(user_id=current_user.id).delete()
    db.session.commit()
    return jsonify({'status': 'cleared'})
