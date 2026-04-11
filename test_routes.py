import sys, warnings
warnings.filterwarnings('ignore')
from app import app
with app.test_request_context():
    from flask import url_for
    tests = ['crop.crop','pest.pest','weather.weather','expense.expense',
             'chat.chatbot','schemes','tips','market','dashboard.dashboard',
             'auth.login','auth.register','auth.logout',
             'voice.ivr_dashboard','outreach.outreach_dashboard',
             'irrigation.irrigation_dashboard','radar.radar_dashboard',
             'calendar.calendar_dashboard','community.community_dashboard']
    for t in tests:
        try:
            u = url_for(t)
            print(f'OK   {t} -> {u}')
        except Exception as e:
            print(f'FAIL {t} -> {e}')
