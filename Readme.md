# 🌾 KrishiMitraAI — Smart Farming Assistant

> An AI-powered personal farming assistant built for Indian farmers using Python, Flask, Scikit-learn, and Gemini AI.

![Python](https://img.shields.io/badge/Python-3.10-blue)
![Flask](https://img.shields.io/badge/Flask-3.1-green)
![ML Accuracy](https://img.shields.io/badge/ML%20Accuracy-99.55%25-brightgreen)
![AI Model](https://img.shields.io/badge/AI%20Model-Gemini%202.0%20Flash-orange)
![License](https://img.shields.io/badge/License-MIT-yellow)

---

## 📖 About the Project

**KrishiMitraAI** is an intelligent web-based farming assistant that helps Indian farmers make better agricultural decisions using Artificial Intelligence and Machine Learning.

The system provides:
- 🌱 **AI-powered crop recommendations** based on soil NPK values, pH, temperature, humidity and rainfall.
- 🐛 **Plant disease detection** using image analysis (Gemini 2.0 Flash).
- 🤖 **Multilingual AI chatbot** supporting regional Kannada slangs and 10+ Indian languages.
- 📊 **Real-time market prices** for 35+ commodities.
- 🌤️ **Weather forecasting** with farming-specific AI advice.
- 🏛️ **Government scheme information** with direct apply links.
- 💰 **Farm expense tracking** with category-wise analytics.
- 💡 **Voice-First Accessibility** for farmers with varying literacy levels.

---

## 🚀 Features

### 🧪 ML-Powered Crop Recommendation
- Trained on **Kaggle Crop Recommendation Dataset**.
- **Random Forest Classifier** — 99.55% accuracy.

### 🐛 Pest & Disease Detection (Go Organic!)
- Upload plant leaf photo for instant AI analysis.
- **NEW:** "Go Organic" feature provides traditional/traditional Indian wisdom for solutions.

### 🤖 AI Chatbot Advisor
- Powered by **Google Gemini 2.0 Flash**.
- Supports: Kannada (Regional Dialects), Hindi, English, and more.
- Voice input & Auto-speak support for high accessibility.

### 📊 Live Market Prices
- Real-time commodity prices with daily updates across Indian states.

### 💰 Financial Intelligence
- Track farm expenses, identify anomalies, and manage agricultural budgets.

---

## ⚙️ Installation & Setup

### Prerequisites
- Python 3.10+
- Git

### Step 1 — Clone & Setup
```bash
git clone https://github.com/Yashaswiurs/KrishiMitraAI.git
cd KrishiMitraAI
python -m venv venv
source venv/bin/activate  # venv\Scripts\activate on Windows
pip install -r requirements.txt
```

### Step 2 — Configure API Keys
Create a `.env` file in the root directory:
```env
SECRET_KEY=your-secret-key
WEATHER_API_KEY=your-openweathermap-key
GEMINI_API_KEY=your-google-gemini-key
TWILIO_ACCOUNT_SID=your-twilio-sid
TWILIO_AUTH_TOKEN=your-twilio-token
TWILIO_PHONE_NUMBER=your-twilio-number
```

### Step 3 — Run the Application
```bash
python app.py
```
Open browser: **http://127.0.0.1:7860**

---

## 📄 License

This project is licensed under the MIT License.

---

<div align="center">
  <strong>🌾 KrishiMitraAI — Empowering Indian Farmers with Technology 🌾</strong>
  <br/>
  Developed by <strong>Yashaswi Urs</strong>
</div>
