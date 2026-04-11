# CropSense AI — Enterprise & Hackathon Upgrade Plan

This document outlines the step-by-step strategy to upgrade the current MVP into a production-grade, AI-driven farming decision intelligence platform.

Because of the massive scope of this upgrade, we will need to transition from a monolithic `app.py` into a modular, blueprint-based architecture.

## Phase 1: Foundation & Authentication (Module 1)
**Goal:** Build a robust, scalable backend architecture with premium onboarding.
* **Refactoring:** Convert `app.py` into a Flask Application Factory pattern with modular Blueprints (e.g., `routes/auth.py`, `routes/dashboard.py`).
* **Database:** Expand the schema to include User Profiles, Preferences, Roles, and Login History.
* **Backend:** Implement JWTs for API routes, role-based access control, OTP boilerplate logic, and rate-limiting.
* **Frontend:** Design a Glassmorphism login/register UI, multi-step onboarding wizard (for district/language/crop profile), and personalized dashboard layout.

## Phase 2: Decision Intelligence Engine (Module 2)
**Goal:** Turn standard ML classification into a comprehensive agronomy advisory system.
* **Backend:** Integrate confidence scoring, top-3 crop comparisons, feature importance extraction (via Random Forest feature importances), and logic for generating a soil suitability index.
* **Frontend:** Implement interactive sliders for NPK values, visual confidence meters, and interactive radar charts for soil suitability. Add a "Demo Mode" with preloaded profiles.

## Phase 3: Diagnostic Intelligence Platform (Module 3)
**Goal:** Deliver advanced pest detection with timeline-based treatment plans.
* **Backend:** Upgrade the Gemini Vision prompt to return structured JSON with risk assessment, severity percentages, historical comparison framing, and timeline generation.
* **Frontend:** Build a medical-style diagnostic dashboard with drag-and-drop uploads, severity progress bars, and risk color indicators mapping to the new structured response.

## Phase 4: Autonomous Chatbot Advisor (Module 4)
**Goal:** Implement conversational memory and profile-aware responses.
* **Backend:** Build a conversational memory system (storing chat history in SQLite) and inject the user's profile (location, crops) into the base Gemini context prompt.
* **Frontend:** Overhaul the chat UI to a WhatsApp-like interface with dynamic suggestion chips, typing indicators, and distinct emergency styling.

## Phase 5: Climate Intelligence Dashboard (Module 5)
**Goal:** Make weather actionable with visual analytics.
* **Backend:** Expand OpenWeatherMap integration to fetch 7-day forecasting and calculate crop impact advisory based on temperature anomalies.
* **Frontend:** Integrate Chart.js/Plotly to visualize rainfall timelines and temperature trends, paired with premium risk alert banners.

## Phase 6: Financial Intelligence Dashboard (Module 6)
**Goal:** Provide AI-driven financial insights for the farm.
* **Backend:** Implement data aggregation for monthly trend detection and profit-loss calculation. Generate basic forecasting heuristics based on historical expense entry dates.
* **Frontend:** Embed interactive pie charts for spend categories and a line graph for monthly trends. Include export-to-PDF/CSV functionality.
