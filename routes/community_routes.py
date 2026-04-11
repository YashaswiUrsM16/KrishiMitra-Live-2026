from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required
import random

community_bp = Blueprint('community', __name__)

@community_bp.route('/community')
@login_required
def community_dashboard():
    return render_template('community.html')

@community_bp.route('/api/community_feed')
@login_required
def get_community_feed():
    posts = [
        {
            "id": 1,
            "farmer": "Nanjunda Gowda",
            "district": "Mandya",
            "audio_url": "farmer_voice_1.mp3",
            "timestamp": "2 hrs ago",
            "transcript_local": "Nanage bevu kabbu bele alli yenu madabeku anta gottagtilla, yaro sahaya madtira?",
            "transcript_translated": "I don't know what to do about the neem/sugarcane crop issues, can someone help?",
            "ai_insight": "Common issue detected: Sugarcane pest management in Mandya region.",
            "tags": ["Sugarcane", "Urgent", "Pest"]
        },
        {
            "id": 2,
            "farmer": "Siddappa",
            "district": "Hassan",
            "audio_url": "farmer_voice_2.mp3",
            "timestamp": "5 hrs ago",
            "transcript_local": "Male jaasti agide, alugedde koilu madodu kasta agtide.",
            "transcript_translated": "Rain is heavy, making it difficult to harvest potatoes.",
            "ai_insight": "Weather impact on potato harvest timelines.",
            "tags": ["Potato", "Weather", "Harvest"]
        }
    ]
    return jsonify({"status": "success", "data": posts})
