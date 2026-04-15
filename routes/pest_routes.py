from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from database import db, PestDetection, ActivityLog
import os
import base64
import json

pest_bp = Blueprint('pest', __name__)

@pest_bp.route('/pest', methods=['GET'])
@login_required
def pest():
    return render_template('pest.html', user=current_user)

@pest_bp.route('/api/detect_pest', methods=['POST'])
@login_required
def api_detect_pest():
    if 'image' not in request.files:
        return jsonify({'error': 'No image uploaded'}), 400

    file = request.files['image']
    crop_type = request.form.get('crop_type', 'unknown crop')

    try:
        from ai_utils import call_vision_ai
        
        img_bytes = file.read()
        file.seek(0)
        img_b64   = base64.b64encode(img_bytes).decode()

        prompt = f"""You are an advanced Agricultural Diagnostic AI Engine.
Analyze this plant image (Crop: {crop_type}).

Perform a deep health diagnostic.
IMPORTANT: Respond ONLY with a raw JSON object. Do not include any conversational text, explanations, or markdown formatting outside the JSON.

JSON structure:
{{
  "disease_name": "String (Scientific and Common name)",
  "confidence": Float (0-100),
  "severity": "String (low, medium, high, critical)",
  "severity_percent": Float (0-100),
  "affected_area": "String (e.g. '15% of visible leaf')",
  "risk_category": "String (green, yellow, orange, red)",
  "traditional_wisdom": "A detailed paragraph on traditional/organic Indian/Kannada traditional methods (e.g. Neem oil, cow urine, ash) to solve this.",
  "treatment_timeline": [
    {{"day": "Day 1", "action": "Immediate spray/action"}}
  ],
  "pesticide_recommendations": [
    {{"type": "Organic/Bio", "item": "String"}},
    {{"type": "Chemical", "item": "String"}}
  ],
  "prevention": "String list of 2 actions"
}}"""

        # Get mime type from file
        mime_type = file.content_type or 'image/jpeg'
        
        ai_response = call_vision_ai(img_b64, prompt, mime_type=mime_type)
        
        if "AI_FAILURE" in ai_response:
            raise Exception(ai_response)

        # Robust JSON cleaning - aggressive extraction
        clean_json = ai_response.strip()
        print(f"RAW AI RESPONSE: {clean_json[:500]}...") # Log first 500 chars for debugging
        
        # Try finding the first { and last }
        start_idx = clean_json.find('{')
        end_idx = clean_json.rfind('}')
        
        if start_idx != -1 and end_idx != -1:
            clean_json = clean_json[start_idx:end_idx+1]
        
        # Secondary cleaning: remove markdown code blocks if still present
        if "```json" in clean_json:
            clean_json = clean_json.split("```json")[1].split("```")[0].strip()
        elif "```" in clean_json:
            clean_json = clean_json.split("```")[1].split("```")[0].strip()
            
        try:
            result = json.loads(clean_json)
        except json.JSONDecodeError as je:
            print(f"JSON Parse Error: {je} | Cleaned: {clean_json[:200]}")
            # Try one more time by removing ANY text before the first {
            if '{' in ai_response:
                try:
                    better_clean = ai_response[ai_response.find('{'):ai_response.rfind('}')+1]
                    result = json.loads(better_clean)
                except:
                    raise Exception(f"AI returned invalid format: {str(je)}. Response started with: {ai_response[:50]}")
            else:
                raise Exception(f"AI returned non-JSON response. Check image clarity.")

        # Store to DB
        risk_score_val = 0.0
        try:
            risk_score_val = float(result.get('severity_percent', 0))
        except (ValueError, TypeError):
            risk_score_val = 0.0

        pest_record = PestDetection(
            user_id    = current_user.id,
            image_path = file.filename,
            result     = json.dumps(result),
            severity   = result.get('severity', 'low'),
            risk_score = risk_score_val,
            location   = current_user.location or (current_user.profile.location_district if current_user.profile else 'Karnataka')
        )
        db.session.add(pest_record)
        
        log = ActivityLog(user_id=current_user.id, action=f"Detected Pest: {result.get('disease_name', 'Unknown')}", ip_address=request.remote_addr)
        db.session.add(log)
        db.session.commit()

        # AUTOMATIC EMERGENCY SMS NOTIFICATION
        if str(result.get('severity', '')).lower() in ['high', 'critical']:
            try:
                from config import Config
                from twilio.rest import Client
                account_sid = Config.TWILIO_ACCOUNT_SID
                auth_token  = Config.TWILIO_AUTH_TOKEN
                twilio_num  = Config.TWILIO_PHONE_NUMBER
                user_phone  = current_user.phone
                
                if account_sid and auth_token and user_phone:
                    client = Client(account_sid, auth_token)
                    if not user_phone.startswith('+'): user_phone = '+91' + user_phone
                    
                    msg_body = f"URGENT: {result.get('disease_name')} detected on your {crop_type}. Severity: {result.get('severity')}. Recommended action: {result.get('treatment_timeline', [{}])[0].get('action', 'Check App for details')}"
                    client.messages.create(body=f"🌾 KrishiMitraAI:\n{msg_body}", from_=twilio_num, to=user_phone)
                    print(f"Emergency Alert Sent to {user_phone}")
            except Exception as sms_err:
                print(f"Automatic SMS Alert Failed: {sms_err}")

        return jsonify(result)

    except Exception as e:
        print(f"PEST ERROR: {e}")
        error_msg = str(e)
        if "AI_FAILURE" in error_msg:
            error_msg = error_msg.split("AI_FAILURE:")[1].strip()
            
        return jsonify({
            "disease_name": "Diagnostic Failed / Connection Issue",
            "confidence": 0,
            "severity": "critical",
            "severity_percent": 100,
            "affected_area": "Unknown",
            "risk_category": "red",
            "treatment_timeline": [{"day": "N/A", "action": "Please ensure you have a stable internet connection and the photo is clear."}],
            "pesticide_recommendations": [{"type": "Error Logic", "item": error_msg}],
            "prevention": "Check API key usage limits."
        })

@pest_bp.route('/api/pest-heatmap')
@login_required
def api_pest_heatmap():
    """Returns recent pest detections for the community radar view."""
    detections = PestDetection.query.order_by(PestDetection.created_at.desc()).limit(100).all()
    
    results = []
    for d in detections:
        try:
            if not d.result:
                continue
            res_data = json.loads(d.result)
            results.append({
                'disease': res_data.get('disease_name', 'Unknown'),
                'severity': d.severity or 'low',
                'location': d.location or 'Unknown',
                'date': d.created_at.strftime('%Y-%m-%d %H:%M') if d.created_at else 'Unknown'
            })
        except Exception as parse_err:
            print(f"Heatmap Parse Error: {parse_err}")
            continue
    return jsonify(results)
