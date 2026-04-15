import os
import time
import requests
import sys
from groq import Groq

from config import Config
from database import db, AgriculturalKnowledge
try:
    from knowledge_base import AgriVectorStore
except ImportError:
    AgriVectorStore = None

def safe_print(msg):
    """Print that won't crash on Windows CP1252 consoles with Unicode."""
    try:
        print(msg)
    except (UnicodeEncodeError, UnicodeDecodeError):
        print(msg.encode('ascii', 'replace').decode('ascii'))

def get_groq_client():
    return Groq(api_key=Config.GROQ_API_KEY)

def get_relevant_context(query):
    """Retrieves relevant agricultural facts using Hugging Face embeddings."""
    if AgriVectorStore is None:
        return ""
        
    try:
        from app import app # Needed for DB context
        with app.app_context():
            store = AgriVectorStore()
            fact_ids = store.search(query)
            if not fact_ids:
                return ""
                
            facts = AgriculturalKnowledge.query.filter(AgriculturalKnowledge.id.in_(fact_ids)).all()
            context = "\n".join([f"- {f.content}" for f in facts])
            return f"\nRELEVANT AGRICULTURAL FACTS:\n{context}\n"
    except Exception as e:
        print(f"Retrieval error: {e}")
        return ""

def call_ai(messages, model="llama-3.1-8b-instant", max_tokens=1800, temperature=0.5):
    """
    Calls AI. Goes straight to Groq (Gemini quota is exhausted).
    """
    import sys
    
    def _safe_print(msg):
        try:
            print(str(msg).encode('ascii', 'replace').decode('ascii'))
        except Exception:
            pass

    # --- Sanitize messages: remove any None or non-string content ---
    clean_messages = []
    for msg in messages:
        role = msg.get('role', 'user')
        content = msg.get('content', '')
        if content is None:
            content = ''
        content = str(content).strip()
        if role in ('system', 'user', 'assistant') and content:
            clean_messages.append({"role": role, "content": content})
    
    if not clean_messages:
        clean_messages = [{"role": "user", "content": "Hello"}]

    # --- PROFESSIONAL RAG: Inject Knowledge Base Context ---
    last_user_query = ""
    for m in reversed(clean_messages):
        if m['role'] == 'user':
            last_user_query = m['content']
            break
            
    if last_user_query:
        context = get_relevant_context(last_user_query)
        if context:
            # Inject into system prompt or as a new message
            system_injected = False
            for m in clean_messages:
                if m['role'] == 'system':
                    m['content'] += f"\nUse these verified facts if relevant: {context}"
                    system_injected = True
                    break
            if not system_injected:
                clean_messages.insert(0, {"role": "system", "content": f"You are an expert agricultural assistant. Use these verified facts if relevant: {context}"})

    _safe_print(f"DEBUG: call_ai called, {len(clean_messages)} messages, model={model}")

    # --- Try Groq first (Gemini free-tier quota is exhausted) ---
    # Prioritize Llama 3.1 8B for speed and availability (70B often hits rate limits)
    # --- Define Groq models and ensure requested model is tried FIRST ---
    groq_models = ["llama-3.3-70b-versatile", "llama-3.1-8b-instant", "llama-3.2-3b-preview", "mixtral-8x7b-32768"]
    if model:
        if model in groq_models:
            groq_models.remove(model)
        groq_models.insert(0, model)

    # --- Trim messages to fit within free-tier token limits ---
    # Keep system prompt + more history for better relevance
    def trim_messages(msgs, max_chars=12000):
        total = sum(len(m.get('content', '')) for m in msgs)
        if total <= max_chars:
            return msgs
            
        # Keep system prompt
        system = [m for m in msgs if m['role'] == 'system']
        others = [m for m in msgs if m['role'] != 'system']
        
        # Keep last 10 messages (5 exchanges) for better context
        others = others[-10:]
        trimmed = system + others
        
        # If still too big, shorten system prompt but keep its core
        current_total = sum(len(m.get('content','')) for m in trimmed)
        if current_total > max_chars and system:
            allowed = max_chars - sum(len(m.get('content','')) for m in others)
            system[0]['content'] = system[0]['content'][:max(1000, allowed)]
        return trimmed

    trimmed_messages = trim_messages(clean_messages)
    _safe_print(f"DEBUG: Sending {len(trimmed_messages)} messages ({sum(len(m.get('content','')) for m in trimmed_messages)} chars)")

    if Config.GROQ_API_KEY and len(Config.GROQ_API_KEY) > 10:
        try:
            client = Groq(api_key=Config.GROQ_API_KEY)
            for groq_model in groq_models:
                try:
                    _safe_print(f"DEBUG: Trying Groq {groq_model}")
                    resp = client.chat.completions.create(
                        messages=trimmed_messages,
                        model=groq_model,
                        max_tokens=max_tokens,
                        temperature=temperature
                    )
                    result = resp.choices[0].message.content
                    if result:
                        _safe_print(f"DEBUG: Groq {groq_model} SUCCESS")
                        return result.strip()
                except Exception as e:
                    err_str = str(e)[:150]
                    _safe_print(f"DEBUG: Groq {groq_model} failed: {err_str}")
                    continue
        except Exception as ge:
            _safe_print(f"DEBUG: Groq init failed: {ge}")

    # --- Fallback: Try Gemini if quota might be available ---
    if Config.GEMINI_API_KEY and len(Config.GEMINI_API_KEY) > 10:
        try:
            gemini_contents = []
            system_text = ""
            for msg in clean_messages:
                if msg['role'] == 'system':
                    system_text += msg['content'] + "\n"
                else:
                    role = "user" if msg['role'] == 'user' else "model"
                    gemini_contents.append({"role": role, "parts": [{"text": msg['content']}]})
            
            payload = {
                "contents": gemini_contents,
                "generationConfig": {"maxOutputTokens": max_tokens, "temperature": temperature}
            }
            if system_text:
                payload["system_instruction"] = {"parts": [{"text": system_text.strip()}]}
            
            url = f"https://generativelanguage.googleapis.com/v1/models/gemini-2.0-flash:generateContent?key={Config.GEMINI_API_KEY}"
            resp = requests.post(url, json=payload, headers={"Content-Type": "application/json"}, timeout=30)
            if resp.status_code == 200:
                data = resp.json()
                if data.get('candidates'):
                    text = data['candidates'][0].get('content', {}).get('parts', [{}])[0].get('text', '')
                    if text:
                        return text.strip()
        except Exception as e:
            _safe_print(f"DEBUG: Gemini fallback failed: {e}")

    return "I'm having trouble connecting right now. Please try again in a moment."

                
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
