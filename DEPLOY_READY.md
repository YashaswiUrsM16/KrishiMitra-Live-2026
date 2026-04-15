# 🚀 Agribot Deployment Guide (Render / Heroku)

Your project is now **Production Ready**. Follow these steps to deploy your Agribot.

## 1. Create a Web Service
- Link your GitHub repository to [Render.com](https://render.com) or [Heroku.com](https://heroku.com).
- **Runtime**: Python 3
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `gunicorn wsgi:app`

## 2. Important: Environment Variables
You must set these "Secret Keys" in the **Environment** tab of your hosting dashboard. Do **NOT** hardcode these anymore.

| Key | Value |
| :--- | :--- |
| `SECRET_KEY` | (Anything random, e.g., `agri-secret-99`) |
| `GEMINI_API_KEY` | (Your Google AI API Key) |
| `WEATHER_API_KEY` | (Your OpenWeatherMap API Key) |
| `GROQ_API_KEY` | (Optional: If using Groq) |

## 3. Persistent Storage (SQLite)
Since you are using SQLite (`farming.db`), most free hosting (like Render/Heroku) will **reset your data** every time you restart.
- **On Render**: You should add a "Disk" (Mount Path: `/opt/render/project/src/instance`) if you want the data to stay forever.
- **Alternative**: Use a hosted PostgreSQL database (like Render's free Postgres) for permanent storage.

## 4. Final Files Checked
- ✅ `Procfile` (tells the server to use Gunicorn)
- ✅ `wsgi.py` (entry point for the server)
- ✅ `requirements.txt` (updated with all dependencies)
- ✅ `Config` (updated to read from environment variables)

You are ready to push to GitHub and Deploy! 🚀
