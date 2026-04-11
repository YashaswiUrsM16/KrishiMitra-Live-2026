from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
import json
import os

simulator_bp = Blueprint('simulator', __name__)

@simulator_bp.route('/simulator')
@login_required
def simulator():
    return render_template('simulator.html', user=current_user)

@simulator_bp.route('/api/simulate', methods=['POST'])
@login_required
def api_simulate():
    data = request.get_json()
    crop1 = data.get('crop1')
    crop2 = data.get('crop2', 'Traditional Method')
    soil = data.get('soil')
    location = data.get('location')
    irrigation = data.get('irrigation')
    fertilizer = data.get('fertilizer')

    prompt = f"""Analyze agricultural scenarios for a farm in {location} with {soil} soil.
Scenario 1: {crop1} with {irrigation} and {fertilizer}.
Scenario 2: {crop2} with {irrigation} and {fertilizer}.

Return ONLY raw JSON strictly following this schema:
{{
  "scenarios": [
    {{
      "crop": "Scenario 1 Name",
      "expected_yield": "Yield in quintals/acre",
      "profit_estimation": "₹ Amount",
      "profit_num": 45000,
      "water_usage": "Usage info",
      "pest_risk_level": "Risk level",
      "weather_impact": "Impact info",
      "score": 85
    }},
    {{
      "crop": "Scenario 2 Name",
      "expected_yield": "...",
      "profit_estimation": "...",
      "profit_num": 30000,
      "water_usage": "...",
      "pest_risk_level": "...",
      "weather_impact": "...",
      "score": 70
    }}
  ],
  "recommendation": "Expert explanation in 3 sentences."
}}
DO NOT include markdown or any other text."""

    try:
        from ai_utils import call_ai

        reply_text = call_ai(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.1-8b-instant",
            max_tokens=800,
            temperature=0.1
        )
        
        # More robust JSON extraction
        import re
        json_match = re.search(r'\{.*\}', reply_text, re.DOTALL)
        if json_match:
            reply_text = json_match.group(0)
            
        json_data = json.loads(reply_text.strip())
        
        return jsonify({"status": "success", "data": json_data})
    except Exception as e:
        print("SIMULATION ERROR:", e)
        return jsonify({"status": "error", "message": f"Engine failed to parse scenarios. Retrying helps. ({str(e)})"})
