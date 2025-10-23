"""
Database Connection and Query Utilities

Author: Victor Ibhafidon
Description: Abstraction layer for database connectivity supporting both DuckDB (local development)
             and Snowflake (production cloud deployment). Handles query execution, connection pooling,
             and automatic CSV-to-database initialization for local testing.
Pipeline Role: Data access layer connecting Streamlit dashboards to the GOLD layer analytics tables.
              Enables seamless switching between local and cloud data warehouses.
"""

import os
import pandas as pd
from pathlib import Path
import duckdb
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database configuration
DATABASE_TYPE = os.getenv('DATABASE_TYPE', 'duckdb')
DATABASE_PATH = os.getenv('DATABASE_PATH', './data/medicare_analytics.duckdb')

class DatabaseConnection:
    """Database connection handler supporting multiple backends"""
    
    def __init__(self):
        self.db_type = DATABASE_TYPE
        self.conn = None
        
    def connect(self):
        """Establish database connection"""
        if self.db_type == 'duckdb':
            self.conn = duckdb.connect(DATABASE_PATH)
            return self.conn
        elif self.db_type == 'snowflake':
            try:
                import snowflake.connector
                self.conn = snowflake.connector.connect(
                    account=os.getenv('SNOWFLAKE_ACCOUNT'),
                    user=os.getenv('SNOWFLAKE_USER'),
                    password=os.getenv('SNOWFLAKE_PASSWORD'),
                    database=os.getenv('SNOWFLAKE_DATABASE'),
                    warehouse=os.getenv('SNOWFLAKE_WAREHOUSE'),
                    schema=os.getenv('SNOWFLAKE_SCHEMA', 'GOLD'),
                    role=os.getenv('SNOWFLAKE_ROLE', 'ACCOUNTADMIN')
                )
                return self.conn
            except ImportError:
                raise ImportError("snowflake-connector-python not installed. Run: pip install snowflake-connector-python")
        else:
            raise ValueError(f"Unsupported database type: {self.db_type}")
    
    def execute_query(self, query, params=None):
        """Execute a SQL query and return results as DataFrame"""
        if self.conn is None:
            self.connect()
        
        try:
            if self.db_type == 'duckdb':
                if params:
                    result = self.conn.execute(query, params).fetchdf()
                else:
                    result = self.conn.execute(query).fetchdf()
                return result
            elif self.db_type == 'snowflake':
                cursor = self.conn.cursor()
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                result = cursor.fetch_pandas_all()
                cursor.close()
                return result
        except Exception as e:
            print(f"Query execution error: {e}")
            raise
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            self.conn = None

# Global connection instance
_db_connection = None

def get_db_connection():
    """Get or create global database connection"""
    global _db_connection
    if _db_connection is None:
        _db_connection = DatabaseConnection()
    return _db_connection

def query_to_df(query, params=None):
    """
    Execute query and return pandas DataFrame
    
    Args:
        query (str): SQL query
        params (tuple): Query parameters for parameterized queries
    
    Returns:
        pd.DataFrame: Query results
    """
    db = get_db_connection()
    return db.execute_query(query, params)

def initialize_database_from_csv():
    """
    Initialize DuckDB database from CSV files
    This is used for local development without Snowflake
    """
    if DATABASE_TYPE != 'duckdb':
        print("Database initialization only works with DuckDB")
        return
    
    print("Initializing DuckDB database from CSV files...")
    
    db = get_db_connection()
    conn = db.connect()
    
    # Path to raw data
    raw_data_dir = Path(__file__).parent.parent.parent / "data" / "raw"
    
    if not raw_data_dir.exists():
        raise FileNotFoundError(f"Raw data directory not found: {raw_data_dir}")
    
    # Load CSV files into DuckDB
    csv_files = list(raw_data_dir.glob("*.csv"))
    
    if not csv_files:
        raise FileNotFoundError(f"No CSV files found in {raw_data_dir}")
    
    for csv_file in csv_files:
        table_name = csv_file.stem  # e.g., 'dim_patients' from 'dim_patients.csv'
        print(f"Loading {table_name}...")
        
        # Create table from CSV
        conn.execute(f"""
            CREATE OR REPLACE TABLE {table_name} AS
            SELECT * FROM read_csv_auto('{csv_file}', header=True)
        """)
    
    print(f"Successfully loaded {len(csv_files)} tables into DuckDB")
    
    # Verify
    tables = conn.execute("SHOW TABLES").fetchdf()
    print(f"\nAvailable tables: {tables['name'].tolist()}")
    
    return conn

def test_connection():
    """Test database connection and return basic info"""
    try:
        db = get_db_connection()
        
        # Simple test query
        result = db.execute_query("SELECT 1 as test")
        
        if result is not None and len(result) > 0:
            print(f"Database connection successful! (Type: {DATABASE_TYPE})")
            return True
        else:
            print("Database connection failed: No result returned")
            return False
    except Exception as e:
        print(f"Database connection failed: {e}")
        return False

if __name__ == '__main__':
    # Test the connection
    print("Testing database connection...")
    test_connection()
    
    # Initialize from CSV if using DuckDB
    if DATABASE_TYPE == 'duckdb':
        try:
            initialize_database_from_csv()
        except Exception as e:
            print(f"Database initialization failed: {e}")

