# Setup Instructions - MediCare Analytics Platform

## What You Need to Do Manually

### Step 1: Sign Up for Snowflake (Free 30-Day Trial)

1. Go to: https://signup.snowflake.com/
2. Fill out the form:
   - **Edition**: Select "Standard" (free for 30 days)
   - **Cloud Provider**: AWS, Azure, or GCP (choose AWS for simplicity)
   - **Region**: Select closest to you (e.g., US East for NA)
3. After signup, you'll receive:
   - Account URL (e.g., `abc12345.us-east-1.snowflakecomputing.com`)
   - Username
   - Password
4. Save these credentials - you'll need them

### Step 2: Create Snowflake Database Schema

1. Log into Snowflake web interface
2. Click on "Worksheets" tab
3. Run the following SQL commands:

```sql
-- Create database
CREATE DATABASE MEDICARE_ANALYTICS;

-- Use the database
USE DATABASE MEDICARE_ANALYTICS;

-- Create schemas for medallion architecture
CREATE SCHEMA BRONZE;  -- Raw data layer
CREATE SCHEMA SILVER;  -- Cleaned data layer
CREATE SCHEMA GOLD;    -- Analytics layer

-- Create warehouse (compute resources)
CREATE WAREHOUSE ANALYTICS_WH WITH
  WAREHOUSE_SIZE = 'XSMALL'
  AUTO_SUSPEND = 300
  AUTO_RESUME = TRUE;

-- Use the warehouse
USE WAREHOUSE ANALYTICS_WH;

-- Verify setup
SHOW SCHEMAS;
```

### Step 3: Sign Up for Matillion (14-Day Trial)

1. Go to: https://www.matillion.com/try-now/
2. Select "Matillion ETL for Snowflake"
3. Fill out trial form
4. After signup, you'll get:
   - Matillion instance URL
   - Login credentials
5. **Connect Matillion to Snowflake:**
   - In Matillion, go to Project > Manage Connections
   - Click "Add Connection"
   - Enter your Snowflake credentials:
     - Account: `abc12345.us-east-1` (from Step 1)
     - Username: your Snowflake username
     - Password: your Snowflake password
     - Database: `MEDICARE_ANALYTICS`
     - Warehouse: `ANALYTICS_WH`
     - Schema: `BRONZE`
   - Test connection

### Step 4: Upload Data to Snowflake

After running the data generation script (`python scripts/01_generate_data.py`), you'll have CSV files in `data/raw/`.

**Option A: Using Snowflake Web UI (Easy)**

1. Log into Snowflake web interface
2. Click "Databases" > "MEDICARE_ANALYTICS" > "BRONZE"
3. Click "Create Table" > "From File"
4. Upload each CSV file:
   - Select file
   - Table name: match the CSV name (e.g., `DIM_PATIENTS` for `dim_patients.csv`)
   - Let Snowflake auto-detect schema
   - Click "Finish"
5. Repeat for all 15 CSV files

**Option B: Using SnowSQL (Command Line)**

1. Install SnowSQL: https://docs.snowflake.com/en/user-guide/snowsql-install-config.html
2. Run upload script (I'll create this for you)

```bash
snowsql -a <your_account> -u <your_username>

-- Then run:
PUT file://data/raw/*.csv @MEDICARE_ANALYTICS.BRONZE.%DIM_PATIENTS;
COPY INTO MEDICARE_ANALYTICS.BRONZE.DIM_PATIENTS;
-- Repeat for each table
```

### Step 5: Create .env File

In your project root (`/Users/user/data_analytics/`), create a file named `.env`:

```bash
# Snowflake Configuration
SNOWFLAKE_ACCOUNT=abc12345.us-east-1
SNOWFLAKE_USER=your_username
SNOWFLAKE_PASSWORD=your_password
SNOWFLAKE_DATABASE=MEDICARE_ANALYTICS
SNOWFLAKE_WAREHOUSE=ANALYTICS_WH
SNOWFLAKE_SCHEMA=GOLD
SNOWFLAKE_ROLE=ACCOUNTADMIN

# Application Settings
APP_ENV=development
```

**Replace the placeholders with your actual Snowflake credentials**

### Step 6: Install Python Dependencies

```bash
cd /Users/user/data_analytics
pip install -r requirements.txt
```

### Step 7: Generate Sample Data

```bash
python scripts/01_generate_data.py
```

This will create 15 CSV files in `data/raw/` folder.

### Step 8: Run Matillion ETL Jobs

I'll provide you with:
- SQL transformation scripts that you can paste into Matillion
- Step-by-step instructions for creating Matillion jobs

OR

- Python scripts that mimic Matillion transformations (if you want to test locally first)

### Step 9: Run Streamlit Dashboard

```bash
streamlit run streamlit_app/app.py
```

The dashboard will open at `http://localhost:8501`

### Step 10: Deploy to Streamlit Cloud (Optional)

1. Push code to GitHub
2. Go to: https://share.streamlit.io
3. Click "New app"
4. Select your repo
5. Add Snowflake credentials in "Secrets" section
6. Deploy

---

## Troubleshooting

### Issue: "Account not found" in Snowflake
- Check that your account identifier is correct (without `https://` or `.snowflakecomputing.com`)
- Format should be: `abc12345.us-east-1`

### Issue: "Warehouse not running"
- Snowflake auto-suspends warehouses after 5 minutes
- They auto-resume on query, but first query may be slow

### Issue: Matillion can't connect to Snowflake
- Verify network connectivity
- Check that Snowflake IP whitelist includes Matillion's IP
- Try using ACCOUNTADMIN role

### Issue: CSV upload fails
- Check file encoding (should be UTF-8)
- Verify column names don't have special characters
- Try smaller batch sizes

---

## Cost Considerations

- **Snowflake Trial**: Free for 30 days, $400 credits
- **Matillion Trial**: Free for 14 days
- **After trial**: 
  - Can switch to DuckDB (free, local) for development
  - Streamlit Cloud has free tier
  - You can export the project to your portfolio without ongoing costs

---

## Next Steps After Setup

Once you complete the manual setup:

1. I'll guide you through creating Matillion ETL jobs
2. OR I'll provide Python scripts for local testing
3. Then we'll build the complete Streamlit dashboard
4. Finally, we'll deploy everything

Let me know when you're ready to proceed!

