# Get Started Now - Production Deployment

**Current Status:** Code on GitHub, ready to deploy  
**Next Steps:** Run dashboards locally, then deploy to Snowflake + Matillion

---

## Step 1: See the Dashboards Running (15 minutes)

### A. Generate Data

```bash
cd /Users/user/data_analytics
python scripts/01_generate_data.py
```

**Expected output:** 15 CSV files in `data/raw/` folder  
**Time:** 2-3 minutes

### B. Launch Dashboard

```bash
streamlit run streamlit_app/app.py
```

**What happens:**
- Browser opens to http://localhost:8501
- Click "Initialize Database from CSV" button
- Wait 30 seconds for data to load
- Dashboard is ready!

### C. Explore Dashboards

**Use the sidebar to navigate:**

1. **Executive Dashboard** - Hospital KPIs, admission trends, revenue
2. **Ward Operations** - Real-time bed status, discharge forecast
3. **Patient Care Plan** ⭐ - Search patient MRN00000001, see full care history
4. **Medication Analytics** - Adherence tracking, error rates
5. **Quality Outcomes** - Readmission analysis, LOS trends

**Try this:** Search for patient "MRN00000001" in Patient Care Plan to see all features

---

## Step 2: Connect to Snowflake (2-3 hours)

### A. Sign Up for Snowflake (15 minutes)

1. Go to: **https://signup.snowflake.com**
2. Fill out form:
   - Edition: **Standard**
   - Cloud: **AWS**
   - Region: **US East (Ohio)** or closest to you
3. Verify email
4. Save credentials:
   - Account URL (e.g., `abc12345.us-east-1.snowflakecomputing.com`)
   - Username
   - Password

**You get:** $400 credits, 30 days free

### B. Create Database Structure (10 minutes)

1. Log into Snowflake web UI
2. Click **Worksheets** tab
3. Copy and paste from `sql/schema/gold_schema.sql`
4. Run these commands:

```sql
-- 1. Create database
CREATE DATABASE MEDICARE_ANALYTICS;
USE DATABASE MEDICARE_ANALYTICS;

-- 2. Create schemas
CREATE SCHEMA BRONZE;   -- Raw data
CREATE SCHEMA SILVER;   -- Cleaned data
CREATE SCHEMA GOLD;     -- Analytics (star schema)

-- 3. Create warehouse
CREATE WAREHOUSE ANALYTICS_WH WITH
  WAREHOUSE_SIZE = 'XSMALL'
  AUTO_SUSPEND = 300
  AUTO_RESUME = TRUE;

USE WAREHOUSE ANALYTICS_WH;

-- 4. Verify
SHOW SCHEMAS;
SHOW WAREHOUSES;
```

**Expected result:** 3 schemas created (BRONZE, SILVER, GOLD)

### C. Upload CSV Data to Snowflake (30 minutes)

**Option 1: Web UI (Easiest)**

For each CSV file in `data/raw/`:
1. In Snowflake UI, go to: **Data** → **Databases** → **MEDICARE_ANALYTICS** → **BRONZE**
2. Click **"Create Table from File"**
3. Upload file (e.g., `dim_patients.csv`)
4. Table name: `DIM_PATIENTS` (uppercase)
5. Let Snowflake auto-detect schema
6. Click **Finish**

Repeat for all 15 files:
- dim_patients.csv → DIM_PATIENTS
- dim_staff.csv → DIM_STAFF  
- dim_wards.csv → DIM_WARDS
- dim_medications.csv → DIM_MEDICATIONS
- dim_procedures.csv → DIM_PROCEDURES
- dim_diagnoses.csv → DIM_DIAGNOSES
- dim_beds.csv → DIM_BEDS
- dim_date.csv → DIM_DATE
- fact_admissions.csv → FACT_ADMISSIONS
- fact_medication_administration.csv → FACT_MEDICATION_ADMINISTRATION
- fact_vital_signs.csv → FACT_VITAL_SIGNS
- fact_daily_activities.csv → FACT_DAILY_ACTIVITIES
- fact_procedures.csv → FACT_PROCEDURES
- fact_lab_results.csv → FACT_LAB_RESULTS
- fact_care_plan_goals.csv → FACT_CARE_PLAN_GOALS

**Option 2: SnowSQL (Faster for bulk)**

```bash
# Install SnowSQL
brew install --cask snowflake-snowsql  # macOS

# Connect
snowsql -a <your_account> -u <username>

# Upload all files
PUT file:///Users/user/data_analytics/data/raw/*.csv @~/staged;
```

### D. Verify Data in Snowflake (5 minutes)

Run these queries in Snowflake:

```sql
USE DATABASE MEDICARE_ANALYTICS;
USE SCHEMA BRONZE;

-- Check row counts
SELECT 'DIM_PATIENTS' as table_name, COUNT(*) as row_count FROM DIM_PATIENTS
UNION ALL
SELECT 'FACT_ADMISSIONS', COUNT(*) FROM FACT_ADMISSIONS
UNION ALL
SELECT 'FACT_MEDICATION_ADMINISTRATION', COUNT(*) FROM FACT_MEDICATION_ADMINISTRATION;
```

**Expected:** 500 patients, ~2000 admissions, ~50,000 medication records

---

## Step 3: Set Up Matillion ETL (1-2 hours)

### A. Sign Up for Matillion (15 minutes)

1. Go to: **https://www.matillion.com/try-now/**
2. Select: **"Matillion ETL for Snowflake"**
3. Fill out trial form
4. Choose deployment: **Cloud-hosted** (easiest)
5. Verify email and log in

**You get:** 14 days free trial

### B. Connect Matillion to Snowflake (10 minutes)

1. In Matillion, click **Project** → **Manage Connections**
2. Click **"Add Connection"**
3. Enter Snowflake details:
   - **Connection Name:** `MediCare_Snowflake`
   - **Account:** `abc12345.us-east-1` (from Step 2A)
   - **Username:** your Snowflake username
   - **Password:** your Snowflake password
   - **Database:** `MEDICARE_ANALYTICS`
   - **Warehouse:** `ANALYTICS_WH`
   - **Schema:** `BRONZE`
   - **Role:** `ACCOUNTADMIN`
4. Click **Test Connection**
5. If successful, click **Save**

### C. Create ETL Jobs (45 minutes)

Use the SQL from `sql/matillion_transformations.sql` and create 3 jobs:

**Job 1: Bronze → Silver (Data Cleaning)**

1. Click **Project** → **Create Job** → **Orchestration Job**
2. Name: `Bronze_to_Silver_Cleaning`
3. Add components:
   - **Table Input** (read from BRONZE schema)
   - **Transformation** (paste SQL from lines 1-150 of matillion_transformations.sql)
   - **Table Output** (write to SILVER schema)
4. Save and **Run**

**Job 2: Silver → Gold (Star Schema)**

1. Create new Orchestration Job: `Silver_to_Gold_StarSchema`
2. Add components:
   - **Table Input** (read from SILVER schema)
   - **Transformation** (paste SQL from lines 151-300 of matillion_transformations.sql)
   - **Table Output** (write to GOLD schema)
3. Save and **Run**

**Job 3: Master Orchestration**

1. Create new Orchestration Job: `Master_ETL_Pipeline`
2. Add:
   - **Job 1 component** → Run Bronze_to_Silver_Cleaning
   - **Job 2 component** → Run Silver_to_Gold_StarSchema
3. Link them in sequence
4. Save and **Run**

**Expected result:** GOLD schema populated with analytics-ready star schema

### D. Schedule Daily Runs (10 minutes)

1. Right-click on `Master_ETL_Pipeline`
2. Select **Schedule**
3. Set:
   - **Frequency:** Daily
   - **Time:** 2:00 AM
   - **Timezone:** Your timezone
4. Save

---

## Step 4: Connect Dashboard to Snowflake (15 minutes)

### A. Update Configuration

Create `.env` file in project root:

```bash
cd /Users/user/data_analytics
touch .env
```

Add this content:

```
DATABASE_TYPE=snowflake
SNOWFLAKE_ACCOUNT=abc12345.us-east-1
SNOWFLAKE_USER=your_username
SNOWFLAKE_PASSWORD=your_password
SNOWFLAKE_DATABASE=MEDICARE_ANALYTICS
SNOWFLAKE_WAREHOUSE=ANALYTICS_WH
SNOWFLAKE_SCHEMA=GOLD
SNOWFLAKE_ROLE=ACCOUNTADMIN
```

**Replace with your actual Snowflake credentials**

### B. Install Snowflake Connector

```bash
pip install snowflake-connector-python
```

### C. Test Connection

```bash
python -c "from streamlit_app.utils.database import test_connection; test_connection()"
```

**Expected:** "Database connection successful! (Type: snowflake)"

### D. Run Dashboard with Snowflake

```bash
streamlit run streamlit_app/app.py
```

**Now your dashboard queries Snowflake (not local DuckDB)!**

---

## Step 5: Deploy Dashboard to Cloud (30 minutes)

### A. Push Latest Changes

```bash
git add .
git commit -m "Add Snowflake configuration"
git push origin main
```

### B. Deploy to Streamlit Cloud

1. Go to: **https://share.streamlit.io**
2. Sign in with GitHub
3. Click **"New app"**
4. Select your repository
5. Main file path: `streamlit_app/app.py`
6. Click **Advanced settings**
7. Add secrets (paste your .env content):

```toml
[snowflake]
account = "abc12345.us-east-1"
user = "your_username"
password = "your_password"
database = "MEDICARE_ANALYTICS"
warehouse = "ANALYTICS_WH"
schema = "GOLD"
role = "ACCOUNTADMIN"
```

8. Click **Deploy**

**Wait 5-10 minutes for deployment**

**Your live URL:** `https://your-app-name.streamlit.app`

---

## What You'll Have Running

After completing all steps:

✅ **Local Development:**
- Dashboards running on localhost
- DuckDB for fast testing

✅ **Production Cloud:**
- Data warehouse: Snowflake (BRONZE → SILVER → GOLD)
- ETL: Matillion (scheduled daily at 2 AM)
- Dashboards: Streamlit Cloud (public URL)
- Architecture: Production-grade data platform

---

## Timeline

| Step | Time | Difficulty |
|------|------|------------|
| Step 1: Local dashboards | 15 min | Easy |
| Step 2: Snowflake setup | 2-3 hours | Medium |
| Step 3: Matillion ETL | 1-2 hours | Medium |
| Step 4: Connect dashboard | 15 min | Easy |
| Step 5: Deploy to cloud | 30 min | Easy |
| **Total** | **4-6 hours** | **Medium** |

---

## Troubleshooting

**Dashboard won't load:**
```bash
# Check if data was generated
ls data/raw/

# Reinstall requirements
pip install -r requirements.txt
```

**Snowflake upload fails:**
- Check file encoding (must be UTF-8)
- Try uploading one file at a time via UI
- Verify warehouse is running

**Matillion can't connect:**
- Double-check Snowflake credentials
- Use ACCOUNTADMIN role
- Verify Snowflake warehouse is running

**Dashboard can't connect to Snowflake:**
- Check .env file exists and has correct values
- Run: `pip install snowflake-connector-python`
- Test with: `python -c "from streamlit_app.utils.database import test_connection; test_connection()"`

---

## Cost Breakdown

**Development (Free):**
- Local: $0 (DuckDB, Streamlit local)

**Production (Trial Period):**
- Snowflake: $0 (30 days, $400 credits)
- Matillion: $0 (14 days trial)
- Streamlit Cloud: $0 (free tier)

**After Trial:**
- Snowflake: ~$50-150/month (consumption-based)
- Matillion: ~$2,000/month (can replace with Python/dbt)
- Streamlit Cloud: Free tier OK, or $20/month for custom domain

---

## Next After This

Once production system is running:

**Week 2-3:** Monitor and optimize
- Track Snowflake credit usage
- Optimize slow queries
- Add monitoring alerts

**Week 4-6:** Machine learning (Phase 3 from ROADMAP.md)
- Readmission prediction model
- Integrate predictions into dashboards

**Week 7-10:** Real-time streaming (Phase 4 from ROADMAP.md)
- Kafka for vital signs
- Real-time alerts

---

## Where You Are Now

✅ Code complete and on GitHub  
⏳ Step 1: Run dashboards locally ← **START HERE**  
⏳ Step 2-5: Production deployment  

**Ready? Start with Step 1 to see your dashboards!**

```bash
python scripts/01_generate_data.py
streamlit run streamlit_app/app.py
```

