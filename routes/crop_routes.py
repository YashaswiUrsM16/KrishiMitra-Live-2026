from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from database import db, CropHistory

import pickle
import os

crop_bp = Blueprint('crop', __name__)

# ─── LOAD ML MODEL ──────────────────────────────────
try:
    with open('models/crop_model.pkl', 'rb') as f:
        crop_model = pickle.load(f)
    with open('models/label_encoder.pkl', 'rb') as f:
        label_encoder = pickle.load(f)
    with open('models/crop_info.pkl', 'rb') as f:
        crop_info = pickle.load(f)
except Exception as e:
    crop_model    = None
    label_encoder = None
    crop_info     = {'accuracy': 0.99}

fertilizer_map = {
    'rice':        'N:120kg/ha, P:60kg/ha, K:60kg/ha — Urea + DAP combination',
    'wheat':       'N:150kg/ha, P:60kg/ha, K:40kg/ha — DAP + MOP as basal dose',
    'maize':       'N:120kg/ha, P:60kg/ha, K:40kg/ha — Apply in 3 split doses',
    'cotton':      'N:120kg/ha, P:60kg/ha, K:60kg/ha — Apply in split doses',
    'sugarcane':   'N:250kg/ha, P:85kg/ha, K:60kg/ha — Apply in 4 split doses',
    'chickpea':    'P:60kg/ha, K:20kg/ha — Rhizobium seed inoculation',
    'kidneybeans': 'P:60kg/ha, K:40kg/ha — Rhizobium seed treatment',
    'pigeonpeas':  'P:50kg/ha, K:30kg/ha — Rhizobium seed treatment',
    'mothbeans':   'N:20kg/ha, P:40kg/ha — Minimal fertilizer needed',
    'mungbean':    'P:40kg/ha, K:20kg/ha — Rhizobium inoculation',
    'blackgram':   'P:40kg/ha, K:20kg/ha — Rhizobium seed treatment',
    'lentil':      'P:40kg/ha, K:20kg/ha — Seed inoculation recommended',
    'pomegranate': 'N:625g, P:250g, K:200g per plant per year',
    'banana':      'N:200g, P:60g, K:300g per plant',
    'mango':       'N:500g, P:200g, K:400g per tree per year',
    'grapes':      'N:90kg/ha, P:60kg/ha, K:90kg/ha',
    'watermelon':  'N:80kg/ha, P:40kg/ha, K:60kg/ha — Drip irrigation',
    'muskmelon':   'N:80kg/ha, P:40kg/ha, K:60kg/ha',
    'apple':       'N:70g, P:35g, K:70g per tree',
    'orange':      'N:400g, P:200g, K:400g per tree per year',
    'papaya':      'N:250g, P:250g, K:500g per plant per year',
    'coconut':     'N:500g, P:320g, K:1200g per palm per year',
    'jute':        'N:60kg/ha, P:30kg/ha, K:30kg/ha',
    'coffee':      'N:30g, P:15g, K:30g per plant',
}

secondary_crop_map = {
    'rice': 'Fish farming or Legumes (adds nitrogen and profit)',
    'wheat': 'Mustard or Gram as intercrop',
    'maize': 'Beans or Squash (Three sisters strategy)',
    'cotton': 'Cowpea or Soybean',
    'sugarcane': 'Potato, Onion or Coriander',
    'chickpea': 'Linseed or Mustard',
    'banana': 'Cocoa, Turmeric or Ginger',
    'mango': 'Papaya or Guava',
    'coconut': 'Black Pepper or Cocoa'
}

@crop_bp.route('/crop', methods=['GET'])
@login_required
def crop():
    return render_template('crop.html', user=current_user)

@crop_bp.route('/api/ml_crop', methods=['POST'])
@login_required
def api_ml_crop():
    try:
        data        = request.get_json()
        nitrogen    = float(data.get('N', 0))
        phosphorus  = float(data.get('P', 0))
        potassium   = float(data.get('K', 0))
        temperature = float(data.get('temperature', 25))
        humidity    = float(data.get('humidity', 60))
        ph          = float(data.get('ph', 6.5))
        rainfall    = float(data.get('rainfall', 100))

        if crop_model is None:
            return jsonify({'error': 'ML Model not loaded!'}), 500

        # Main Prediction logic - Optimized for high-speed single row inference
        probabilities = crop_model.predict_proba([[nitrogen, phosphorus, potassium, temperature, humidity, ph, rainfall]])[0]
        top3_idx      = probabilities.argsort()[-3:][::-1]
        
        target_crop_name = label_encoder.inverse_transform([top3_idx[0]])[0]
        soil_suitability_score = round((probabilities[top3_idx[0]] * 100) * 0.95, 1) # Custom scaling for Soil Suitability Index

        top3_crops = []
        for i in top3_idx:
            crop_n = label_encoder.classes_[i]
            top3_crops.append({
                'crop': crop_n.capitalize(),
                'confidence': round(float(probabilities[i]) * 100, 1),
                'fertilizer': fertilizer_map.get(crop_n.lower(), 'Standard Application'),
                'yieldEst': f"{round(10 + (float(probabilities[i])*10), 1)} tons/ha",
                'secondary_crop': secondary_crop_map.get(crop_n.lower(), 'Legumes / Cover crops for secondary profit')
            })

        # Calculate Feature Importance heuristically based on the user's NPK vs Ideal (Simplified explainability)
        feature_importance = {
            'Nitrogen (N)': round((nitrogen / (nitrogen + phosphorus + potassium + 1)) * 100, 1),
            'Phosphorus (P)': round((phosphorus / (nitrogen + phosphorus + potassium + 1)) * 100, 1),
            'Potassium (K)': round((potassium / (nitrogen + phosphorus + potassium + 1)) * 100, 1),
            'Condition': "Optimal" if 5.5 <= ph <= 7.5 else "Needs adjustment"
        }

        # Store History
        record = CropHistory(
            user_id   = current_user.id,
            crop_name = target_crop_name,
            soil_type = f"N:{nitrogen} P:{phosphorus} K:{potassium}",
            season    = f"pH:{ph} Temp:{temperature}°C",
            confidence_score = float(probabilities[top3_idx[0]] * 100),
            soil_suitability = soil_suitability_score
        )
        db.session.add(record)
        db.session.commit()

        return jsonify({
            'status': 'ok',
            'top_crop': top3_crops[0],
            'top3': top3_crops,
            'soil_suitability_score': soil_suitability_score,
            'feature_importance': feature_importance,
            'radar_data': [nitrogen, phosphorus, potassium, ph*10, humidity/2, temperature] # scaled for radar UI
        })

    except Exception as e:
        print(f"ML ERROR: {e}")
        return jsonify({'error': str(e)}), 500
@crop_bp.route('/api/ocr-soil', methods=['POST'])
@login_required
def api_ocr_soil():
    if 'image' not in request.files:
        return jsonify({'status': 'error', 'message': 'No image provided'})
    
    file = request.files['image']
    if file.filename == '':
        return jsonify({'status': 'error', 'message': 'No selected file'})

    import base64
    import json
    import re
    from ai_utils import call_vision_ai

    try:
        image_data = base64.b64encode(file.read()).decode('utf-8')
        
        prompt = """
        Analyze this Soil Health Card image.
        Extract the following values: Nitrogen (N), Phosphorus (P), Potassium (K), and pH Level.
        Return ONLY a JSON object with keys: "N", "P", "K", "ph".
        Use the available nitrogen, phosphorus, and potassium values (usually in kg/ha or mg/kg).
        If a value is not found, use a realistic average based on the card context.
        JSON format only.
        """
        
        res_text = call_vision_ai(image_data, prompt)
        
        # Extract JSON
        json_match = re.search(r'\{.*\}', res_text, re.DOTALL)
        if json_match:
            data = json.loads(json_match.group(0))
            return jsonify({'status': 'success', 'data': data})
        
        return jsonify({'status': 'error', 'message': 'Could not parse soil data from card'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})
