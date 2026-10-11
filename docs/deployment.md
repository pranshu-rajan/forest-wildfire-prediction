# Complete Deployment Guide: Vercel (Frontend), Render (Backend) & Supabase (Database)

## Forest Cover Type Prediction & Wildfire-Risk Analysis Platform

This document describes how to deploy the entire multi-tier system to production using **Vercel** for the Next.js frontend, **Render** for the FastAPI backend, and **Supabase** for managed PostgreSQL storage.

```text
┌─────────────────────────┐
│     Next.js on Vercel   │ (Public Web App & UI)
└────────────┬────────────┘
             │ HTTP REST
             ▼
┌─────────────────────────┐
│    FastAPI on Render    │ (Inference & Analytics API)
└────────────┬────────────┘
             │ PostgreSQL / Supabase Client
             ▼
┌─────────────────────────┐
│    Supabase Database    │ (raw, curated, analytics, models, app)
└─────────────────────────┘
```

---

## Part 1: Supabase Database Setup

1. **Create Project**:
   - Go to [supabase.com](https://supabase.com) and create a free project.
   - Note the database password and select a region (e.g. `us-east-1` or `us-west-1`).

2. **Execute Migrations**:
   - In Supabase Dashboard, open **SQL Editor**.
   - Copy and run the entire script in [`database/supabase_migration.sql`](file:///c:/Users/pranshu/Desktop/forest-cover-wildfire/database/supabase_migration.sql).
   - This creates all 5 functional schemas (`raw`, `curated`, `analytics`, `models`, `app`), views, and Row Level Security policies.

3. **Get Credentials**:
   - From **Project Settings $\rightarrow$ API**: Copy `Project URL` (`SUPABASE_URL`) and `anon public key` (`SUPABASE_KEY`).
   - From **Project Settings $\rightarrow$ Database $\rightarrow$ Connection Pooling**: Copy the URI (port 6543 pooler mode). This is your `SUPABASE_DB_URL`.

4. **Load Data (Optional/Initial)**:
   - Run locally:
     ```bash
     SUPABASE_DB_URL="postgresql+psycopg://postgres.<ref>:<pass>@<host>:6543/postgres" python scripts/12_load_supabase.py
     ```

---

## Part 2: Render Backend Deployment

Render hosts the FastAPI service using the configuration provided in [`render.yaml`](file:///c:/Users/pranshu/Desktop/forest-cover-wildfire/render.yaml) and [`Procfile`](file:///c:/Users/pranshu/Desktop/forest-cover-wildfire/Procfile).

1. **Create Web Service**:
   - Log in to [render.com](https://render.com) $\rightarrow$ click **New +** $\rightarrow$ **Web Service**.
   - Connect your GitHub repository.
2. **Configure Settings**:
   - **Name**: `forest-cover-backend`
   - **Region**: Oregon (or matching your Supabase region)
   - **Branch**: `main`
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
   - **Plan**: `Free`
3. **Environment Variables**:
   Add the following in Render **Environment**:
   - `PYTHON_VERSION`: `3.11.9`
   - `CORS_ORIGINS`: `*` (or your Vercel domain `https://your-app.vercel.app`)
   - `SUPABASE_URL`: `https://<project-ref>.supabase.co`
   - `SUPABASE_KEY`: `<your-supabase-key>`
   - `SUPABASE_DB_URL`: `postgresql+psycopg://postgres.<ref>:<pass>@<host>:6543/postgres`
   - `ENVIRONMENT`: `production`
4. **Deploy**:
   - Click **Create Web Service**.
   - Once deployed, copy your Render service URL: `https://forest-cover-backend.onrender.com`.
   - Verify health at: `https://forest-cover-backend.onrender.com/health` and docs at `/docs`.

---

## Part 3: Vercel Frontend Deployment

Vercel hosts the Next.js React 19 web application located in `frontend/`.

1. **Import Project**:
   - Log in to [vercel.com](https://vercel.com) $\rightarrow$ click **Add New...** $\rightarrow$ **Project**.
   - Select your GitHub repository.
2. **Configure Project Settings**:
   - **Framework Preset**: `Next.js`
   - **Root Directory**: Click *Edit* and select `frontend`.
3. **Environment Variables**:
   - Add:
     - `NEXT_PUBLIC_API_URL`: `https://forest-cover-backend.onrender.com` (your live Render backend URL).
4. **Deploy**:
   - Click **Deploy**.
   - In 60 seconds, Vercel completes the build and provides your live public URL (e.g., `https://forest-cover-analytics.vercel.app`).

---

## Part 4: End-to-End Integration Verification

Once all three tiers are deployed:
1. Open the live Vercel URL in your browser.
2. Check the navigation badge:
   - Green indicator: **● FastAPI Online** indicates that the frontend is communicating with your Render backend.
3. Check the **Governance & Tools** tab:
   - Confirms Supabase database status, schema versioning, and loaded tables.
4. Test the **Prediction Playground**:
   - Select any ecological preset (e.g. *Subalpine Spruce/Fir*) and click **Run Prediction**.
   - The frontend transmits the 54-feature vector to Render, which executes inference on the serialized pipeline and returns predicted species with confidence percentages.
5. Check the Supabase Dashboard:
   - Query `app.prediction_requests` to see logged inference calls.

---

## Part 5: Local Development Run Commands

```bash
# 1. Start FastAPI backend (port 8000)
.venv\Scripts\python -m uvicorn backend.main:app --port 8000 --reload

# 2. Start Next.js frontend (port 3000)
cd frontend
npm run dev
```
