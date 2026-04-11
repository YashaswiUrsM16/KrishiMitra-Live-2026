import os
import time
import requests
from groq import Groq

from config import Config

def get_groq_client():
    return Groq(api_key=Config.GROQ_API_KEY)

def call_ai(messages, model="gemini-3-flash-preview", max_tokens=1800, temperature=0.5):
    """
    Calls AI models with a sequence-based fallback mechanism.
    Prioritizes Gemini if API key is present, fallback to Groq.
    Using REST API for Gemini to avoid SDK issues on Python 3.14.
    """
    
    # List of models confirmed available for this API key - prioritizing speed and stability
    gemini_models = ["gemini-2.0-flash", "gemini-flash-latest", "gemini-3-flash-preview", "gemini-2.5-flash"]
    
    # If a specific Llama model was requested, skip Gemini to save time (Crucial for Voice AI)
    is_llama_requested = model and "llama" in model.lower()

    if not is_llama_requested and Config.GEMINI_API_KEY and len(Config.GEMINI_API_KEY) > 10:
        # Use the requested model first if it's a gemini model
        ordered_models = []
        if model and "gemini" in model.lower():
            ordered_models.append(model)
        for gm in gemini_models:
            if gm not in ordered_models: ordered_models.append(gm)

        for gem_model in ordered_models:
            try:
                # Convert messages to Gemini format and extract system prompt
                gemini_contents = []
                system_instruction_text = ""
                
                for msg in messages:
                    if msg['role'] == 'system':
                        system_instruction_text += msg['content'] + "\n"
                    else:
                        role = "user" if msg['role'] == 'user' else "model"
                        content = msg.get('content', '')
                        if content:
                            gemini_contents.append({
                                "role": role,
                                "parts": [{"text": content}]
                            })
                
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{gem_model}:generateContent?key={Config.GEMINI_API_KEY}"
                
                payload = {
                    "contents": gemini_contents,
                    "generationConfig": {
                        "maxOutputTokens": max_tokens,
                        "temperature": temperature
                    }
                }
                
                if system_instruction_text:
                    payload["system_instruction"] = {
                        "parts": [{"text": system_instruction_text.strip()}]
                    }
                
                headers = {"Content-Type": "application/json"}
                
                response = requests.post(url, json=payload, headers=headers, timeout=60)
                
                if response.status_code == 200:
                    data = response.json()
                    if 'candidates' in data and len(data['candidates']) > 0:
                        candidate = data['candidates'][0]
                        if 'content' in candidate and 'parts' in candidate['content']:
                            return candidate['content']['parts'][0]['text'].strip()
                
                print(f"Gemini {gem_model} error: {response.status_code}")
                if response.status_code == 429 or response.status_code == 503:
                    continue # Try next Gemini model
            except Exception as e:
                print(f"Gemini {gem_model} Call failed: {e}")
                continue

    # Fallback to Groq - Use faster model for better UX
    client = get_groq_client()
    
    # Prioritize the explicitly requested model, then fall back to speed/scale
    models_to_try = [model] if model else []
    for fallback_idx in ["llama-3.1-8b-instant", "llama-3.3-70b-versatile", "llama-3.1-70b-versatile"]:
        if fallback_idx not in models_to_try:
            models_to_try.append(fallback_idx)
    
    last_error = None
    for m in models_to_try:
        try:
            response = client.chat.completions.create(
                messages=messages,
                model=m,
                max_tokens=max_tokens,
                temperature=temperature
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            last_error = str(e)
            print(f"Groq AI Call failed for model {m}: {e}")
            if "limit" in last_error.lower() or "rate" in last_error.lower():
                continue
            else:
                break
                
def call_vision_ai(image_b64, prompt, model="gemini-2.0-flash", mime_type="image/jpeg"):
    """
    Calls Gemini Vision to analyze an image with fallback mechanism.
    """
    if not Config.GEMINI_API_KEY or len(Config.GEMINI_API_KEY) < 10:
        return "Error: Gemini API key missing or invalid."
    
    # Try these models in order - these are confirmed available for this key
    models_to_try = [model, "gemini-3-flash-preview", "gemini-2.0-flash", "gemini-2.5-flash", "gemini-flash-latest"]
    unique_models = []
    for m in models_to_try:
        if m not in unique_models: unique_models.append(m)

    last_err = ""
    for m in unique_models:
        model_id = m if m.startswith("models/") else f"models/{m}"
        url = f"https://generativelanguage.googleapis.com/v1beta/{model_id}:generateContent?key={Config.GEMINI_API_KEY}"
        
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt},
                        {
                            "inline_data": {
                                "mime_type": mime_type,
                                "data": image_b64
                            }
                        }
                    ]
                }
            ],
            "generationConfig": {
                "maxOutputTokens": 2048,
                "temperature": 0.1
            }
        }
        
        try:
            response = requests.post(url, json=payload, headers={"Content-Type": "application/json"}, timeout=30)
            if response.status_code == 200:
                data = response.json()
                if 'candidates' in data and len(data['candidates']) > 0:
                    candidate = data['candidates'][0]
                    if 'content' in candidate and 'parts' in candidate['content']:
                        return candidate['content']['parts'][0]['text']
                    elif 'finishReason' in candidate:
                        last_err = f"Vision Blocked ({m}): Reason {candidate['finishReason']}"
                        continue
                last_err = f"Vision Warning ({m}): No content in response. Keys: {list(data.keys())}"
                continue
            
            last_err = f"Vision Error ({m}): {response.status_code} - {response.text}"
            print(last_err)
        except Exception as e:
            last_err = f"Vision Exception ({m}): {str(e)}"
            print(last_err)
            
    return f"AI_FAILURE: {last_err}"

