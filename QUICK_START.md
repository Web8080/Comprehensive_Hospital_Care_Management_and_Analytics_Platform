# Quick Start Guide

## What's Been Built

A complete hospital analytics platform with:
- 15 CSV files with 5 years of synthetic patient data
- Star schema database (8 dimensions, 9 facts)
- 5 interactive Streamlit dashboards
- Complete ETL pipeline architecture
- Comprehensive documentation

## Get Started in 3 Steps

### Step 1: Install Dependencies (2 minutes)

```bash
cd /Users/user/data_analytics
pip install -r requirements.txt
```

### Step 2: Generate Data (3 minutes)

```bash
python scripts/01_generate_data.py
```

Expected output:
- 500 patients
- 150 staff
- 2000+ admissions
- 50,000+ medication records
- 30,000+ vital signs
- Files saved to `data/raw/`

### Step 3: Run Dashboard (1 minute)

```bash
streamlit run streamlit_app/app.py
```

Dashboard opens at: http://localhost:8501

On first run, click "Initialize Database from CSV" to load data into DuckDB.

## Explore the Dashboard

### 1. Executive Dashboard
- View hospital KPIs
- See 12-month admission trends
- Check revenue by department

### 2. Ward Operations
- Real-time bed status
- 48-hour discharge forecast

### 3. Patient Care Plan (THE STAR FEATURE)
- Search for a patient (try: MRN00000001)
- View medication MAR
- See vital signs charts
- Log daily activities with COMMENTS
- Browse 5-year history

### 4. Medication Analytics
- Adherence rates by ward
- Error tracking
- Cost analysis

### 5. Quality & Outcomes
- Readmission analysis
- Length of stay trends
- Quality metrics

## What You Need to Provide Manually (Optional)

### For Snowflake + Matillion (Cloud Deployment):

1. **Sign up for Snowflake** (30-day trial)
   - Go to: https://signup.snowflake.com
   - Save your account URL, username, password

2. **Sign up for Matillion** (14-day trial)
   - Go to: https://www.matillion.com/try-now
   - Connect to your Snowflake account

3. **Upload data to Snowflake**
   - Follow instructions in `SETUP_INSTRUCTIONS.md`
   - Or use the Snowflake web UI to upload CSV files

4. **Create .env file** with your credentials:
```bash
SNOWFLAKE_ACCOUNT=your_account.us-east-1
SNOWFLAKE_USER=your_username
SNOWFLAKE_PASSWORD=your_password
SNOWFLAKE_DATABASE=MEDICARE_ANALYTICS
SNOWFLAKE_WAREHOUSE=ANALYTICS_WH
SNOWFLAKE_SCHEMA=GOLD
```

5. **Deploy to Streamlit Cloud**
   - Push code to GitHub
   - Go to https://share.streamlit.io
   - Deploy your app (free)

## Project Files Created

```
data_analytics/
├── README.md                                 # Complete documentation
├── PROJECT_STUDY_GUIDE.md                    # Interview prep guide
├── SETUP_INSTRUCTIONS.md                     # Snowflake + Matillion setup
├── QUICK_START.md                            # This file
├── requirements.txt                          # Python dependencies
├── config.py                                 # Configuration
│
├── scripts/
│   └── 01_generate_data.py                   # Data generator (READY TO RUN)
│
├── sql/
│   └── schema/
│       └── gold_schema.sql                   # Star schema DDL
│
├── streamlit_app/
│   ├── app.py                                # Main dashboard
│   ├── pages/
│   │   ├── 1_Executive_Dashboard.py          # KPIs & trends
│   │   ├── 2_Ward_Operations.py              # Bed status
│   │   ├── 3_Patient_Care_Plan.py            # STAR FEATURE (with comments)
│   │   ├── 4_Medication_Analytics.py         # Medication tracking
│   │   └── 5_Quality_Outcomes.py             # Quality metrics
│   └── utils/
│       ├── database.py                       # DB connection
│       └── queries.py                        # SQL queries
│
└── data/                                     # Created after running script
    └── raw/                                  # 15 CSV files
```

## Troubleshooting

### "ModuleNotFoundError: No module named 'faker'"
```bash
pip install -r requirements.txt
```

### "No such file or directory: data/raw/"
```bash
python scripts/01_generate_data.py
```

### Dashboard won't load
```bash
# Make sure you're in the project root
cd /Users/user/data_analytics

# Then run
streamlit run streamlit_app/app.py
```

### Database errors
- Click "Initialize Database from CSV" button on home page
- Or delete `data/medicare_analytics.duckdb` and restart

## Next Steps

1. **Test locally** (what you can do now)
   - Run all 3 steps above
   - Explore all 5 dashboards
   - Test patient search and daily activity logging
   - Take screenshots for your portfolio

2. **Optional: Deploy to cloud** (if you want Matillion experience)
   - Sign up for Snowflake trial
   - Sign up for Matillion trial
   - Upload data and create ETL jobs
   - Deploy to Streamlit Cloud

3. **Customize for your portfolio**
   - Update README with your name/contact
   - Add your own "consulting story"
   - Customize hospital name and branding
   - Take demo video/screenshots

4. **Interview prep**
   - Read `PROJECT_STUDY_GUIDE.md`
   - Practice explaining architecture
   - Prepare to demo the dashboard
   - Be ready to discuss trade-offs and decisions

## Support

If you encounter issues:
1. Check the troubleshooting section above
2. Review `SETUP_INSTRUCTIONS.md` for detailed guidance
3. Check that all files were created successfully
4. Verify Python version is 3.9+

## Ready for Snap Analytics Interview!

This project demonstrates:
- End-to-end data pipeline development
- Cloud data warehouse architecture (Snowflake-ready)
- ETL/ELT implementation (Matillion-compatible)
- Dimensional modeling (star schema)
- Business intelligence delivery (Streamlit dashboards)
- Real-world healthcare analytics use case

Good luck with your application!

