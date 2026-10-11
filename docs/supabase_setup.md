# Supabase Database Setup & End-to-End Integration Guide

This guide walks through creating, configuring, migrating, and connecting your **Supabase PostgreSQL database** with the **FastAPI backend (Render)** and **Next.js frontend (Vercel)**.

---

## 1. Create a Free Supabase Project

1. Log in to [Supabase](https://supabase.com) and navigate to your dashboard.
2. Click **New Project**.
3. Choose an organization, enter a project name (e.g., `forest-cover-analytics`), and set a strong database password.
4. Select a region close to your Render deployment (e.g., `US East (N. Virginia) - us-east-1` or `US West (Oregon) - us-west-1`).
5. Click **Create new project** and wait 1–2 minutes for initialization.

---

## 2. Execute Database Schemas & Migrations

1. In your Supabase project dashboard, open the **SQL Editor** from the left sidebar.
2. Click **New Query**.
3. Open the migration file from this repo: [`database/supabase_migration.sql`](file:///c:/Users/pranshu/Desktop/forest-cover-wildfire/database/supabase_migration.sql).
4. Copy the entire contents, paste into the Supabase SQL Editor, and click **Run**.
5. Confirm output:
   - Schemas created: `raw`, `curated`, `analytics`, `models`, `app`.
   - Tables created: `raw.source_manifests`, `curated.forest_cover`, `analytics.descriptive_statistics`, `analytics.cluster_profiles`, `models.model_registry`, `app.prediction_requests`, `app.wildfire_screening_risk`.
   - Views created: `analytics.v_cover_type_summary`, `analytics.v_wildfire_screening_risk`.
   - Row Level Security (RLS) policies applied.

---

## 3. Retrieve Credentials from Supabase

From your Supabase Project Dashboard:

### A. Project API Keys
- Go to **Project Settings** $\rightarrow$ **API**.
- Copy:
  - **Project URL**: `https://<project-ref>.supabase.co` $\rightarrow$ This is your `SUPABASE_URL`.
  - **Project API Keys (anon / public)** or **service_role (secret)**: $\rightarrow$ This is your `SUPABASE_KEY`.

### B. Connection String (PostgreSQL Pooler)
- Go to **Project Settings** $\rightarrow$ **Database** $\rightarrow$ **Connection Pooling**.
- Select **Session** or **Transaction** mode (port `6543` or `5432`).
- Select **URI**.
- Format:
  ```text
  postgresql+psycopg://postgres.<project-ref>:[YOUR-PASSWORD]@aws-0-[region].pooler.supabase.com:6543/postgres
  ```
  *(Note: Replace `[YOUR-PASSWORD]` with the password set in Step 1).*

---

## 4. Ingest Initial Data into Supabase

In your local project terminal (with `.venv` active):

1. Set the variables in your local `.env` or terminal:
   ```bash
   SUPABASE_URL=https://<project-ref>.supabase.co
   SUPABASE_KEY=<your-key>
   SUPABASE_DB_URL=postgresql+psycopg://postgres.<project-ref>:<password>@aws-0-<region>.pooler.supabase.com:6543/postgres
   ```

2. Run the ingestion loader script:
   ```bash
   python scripts/12_load_supabase.py
   ```
3. Verification:
   - Check Supabase Dashboard $\rightarrow$ **Table Editor** $\rightarrow$ select schema `curated` $\rightarrow$ table `forest_cover`.
   - You should see the ingested rows, column statistics, and manifest record in `raw.source_manifests`.

---

## 5. Connect Backend (Render) to Supabase

In your **Render Web Service** dashboard:
1. Navigate to **Environment**.
2. Add these environment variables:
   - `SUPABASE_URL`: `https://<project-ref>.supabase.co`
   - `SUPABASE_KEY`: `<your-supabase-key>`
   - `SUPABASE_DB_URL`: `postgresql+psycopg://postgres.<project-ref>:<password>@aws-0-<region>.pooler.supabase.com:6543/postgres`
   - `CORS_ORIGINS`: `https://<your-app>.vercel.app,*`
3. Click **Save Changes**. Render will automatically redeploy.

---

## 6. End-to-End Verification Check

Test the live connected endpoints from your browser or curl:
- `GET https://your-backend.onrender.com/health`:
  ```json
  {
    "status": "OK",
    "database": {
      "supabase_configured": true,
      "database_url_configured": true,
      "engine_status": "OK",
      "status": "OK"
    }
  }
  ```
- `GET https://your-backend.onrender.com/api/supabase/status`:
  ```json
  {
    "supabase_configured": true,
    "database_url_configured": true,
    "mode": "CONNECTED",
    "supported_schemas": ["raw", "curated", "analytics", "models", "app"]
  }
  ```
