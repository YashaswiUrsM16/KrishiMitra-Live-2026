from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
import json
import re
from ai_utils import call_ai

organic_bp = Blueprint('organic', __name__)



@organic_bp.route('/organic-lab')
@login_required
def organic_lab():
    return render_template('organic_lab.html', current_user=current_user)

@organic_bp.route('/api/organic-analysis', methods=['POST'])
@login_required
def api_organic_analysis():
    data = request.get_json()
    crop = data.get('crop', 'Rice')
    location = data.get('location', 'India')

    prompt = f"""
    Acting as an expert in Traditional Indian Agriculture and Organic Farming for {crop} in {location}.
    Provide a detailed "Profit Enhancement Plan" that avoids chemical inputs.
    
    CRITICAL: Provide strong "Numerical Justification" for every cost and profit figure. Explain WHY the chemical costs are high and HOW the organic costs are calculated.
    
    Return ONLY raw JSON with this structure:
    {{
        "crop": "{crop}",
        "traditional_methods": [
            {{
                "name": "Method Name (e.g. Bijamrutha)",
                "description": "Short explanation.",
                "benefit": "How it saves money.",
                "cost_impact": "Low/Zero/Negative"
            }}
        ],
        "profit_comparison": {{
            "chemical_input_cost": "Estimated cost in ₹/acre",
            "organic_input_cost": "Estimated cost in ₹/acre",
            "organic_premium_price": "Expected % price increase",
            "net_profit_gain": "Estimated % increase in net profit",
            "calculation_logic": "Deep justification for the numbers above, explaining the delta between chemical and organic economics.",
            "input_breakdown": ["Urea: ₹20,000", "Pesticides: ₹15,000"]
        }},
        "hidden_gem": "A rare traditional farming hack specifically for {crop}.",
        "sustainability_score": 95
    }}
    Do not include markdown blocks or extra text.
    """

    try:
        reply_text = call_ai(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2
        )
        
        # Robust JSON extraction
        json_match = re.search(r'\{.*\}', reply_text, re.DOTALL)
        if json_match:
            reply_text = json_match.group(0)
            
        json_data = json.loads(reply_text.strip())
        return jsonify({"status": "success", "data": json_data})
    except Exception as e:
        print("ORGANIC LAB ERROR:", e)
        return jsonify({"status": "error", "message": str(e)})
