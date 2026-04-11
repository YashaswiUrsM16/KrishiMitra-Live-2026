# 🚀 CropSense AI — Enterprise Edition Run Guide

Congratulations! Your agricultural assistant has been successfully upgraded to an Enterprise/Hackathon-grade application utilizing modular blueprints, advanced AI diagnostic flows, Chart.js integrations, and Glassmorphism dashboards.

Follow these exact steps to run the newly upgraded system:

## ⚠️ 1. Reset the Database
Because we completely overhauled the Database Schema in `database.py` to support User Profiles, Roles, AI Confidence metrics, and Timeline structures, **your old database file must be reset** to allow Flask to rebuild the new schema dynamically.

1. Navigate to the `instance/` folder inside your project.
2. Delete the file named `farming.db` (or whatever your old SQLite file was named).
   - *(Note: Do not worry, `app.py` has a `db.create_all()` command safely set up to instantly recreate the brand-new, robust database structure the second you run it).*

## 🔑 2. API Keys Configured
I have successfully hard-coded your provided **Google Gemini API Key** and **OpenWeatherMap API Key** directly into the application's fallback handlers (`chat_routes.py`, `pest_routes.py`, `weather_routes.py`). 

You do **NOT** need to set up environment variables manually anymore. The application will connect directly to Gemini and OpenWeatherMap out-of-the-box!



## 🏃 3. Start the Server
Everything is configured perfectly out-of-the-box. We used CDN scripts for our interactive charts (Chart.js), so no massive npm installations are needed.

1. Open your terminal in the `AI_POWERED_FARMING_ASSISTANCE` directory.
2. Run the application:
```bash
python app.py
```
3. Open your browser and go to: **http://127.0.0.1:7860** (or whatever port Flask selects).

## 🌟 4. Hackathon Demo Path
To truly impress your judges, try walking through the App in this exact order:

1. **The Registration Wizard:** Go to Login -> Click "New to CropSense?". Show off the beautiful Multi-step Glassmorphism profile generator. Create an account.
2. **The New Dashboard:** Marvel at the Bento Grid UI layout upon login, showcasing quick alerts and history tracking.
3. **Crop Intelligence (`/crop`):** Click "Preload Sample Soil Profile" and hit Generate to show off the instant Radar Chart and Top-3 comparisons.
4. **Diagnostic AI (`/pest`):** Drag and drop a sample plant leaf image. Show off the "Action Timeline" and the JSON-structured response handling that outputs "Risk Assessment Banners".
5. **Climate Intelligence (`/weather`):** Show the 24-hr Bar and Line charts reacting beautifully to the OpenWeatherMap algorithms, highlighting the smart Irrigation advices.
6. **AI Advisor (`/chatbot`):** Type: "What crops do you think I farm and where am I from?". Watch the AI instantly know the user's District mapping thanks to the background Profile-Injection context!

Enjoy your masterpiece and good luck at the hackathon! 🏆
