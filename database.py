import os
from typing import Optional, List, Dict, Any, Union
import mysql.connector
from mysql.connector import Error
from mysql.connector.abstracts import MySQLConnectionAbstract
from mysql.connector.pooling import PooledMySQLConnection
from dotenv import load_dotenv

load_dotenv()

# Type definition for database connection
DbConnection = Union[PooledMySQLConnection, MySQLConnectionAbstract, None]

def get_db_connection() -> DbConnection:
    """Create and return a database connection with proper encoding."""
    try:
        connection = mysql.connector.connect(
            host=os.getenv("DB_HOST"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME"),
            port=os.getenv("DB_PORT", "3306"),
            use_unicode=True,
            charset="utf8mb4",
            collation="utf8mb4_unicode_ci"
        )
        return connection
    except Error as e:
        print(f"Database connection error: {e}")
        return None

def init_db() -> None:
    """Initialize the land_cases table including years_litigation field."""
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS land_cases (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    region VARCHAR(100) NOT NULL,
                    division VARCHAR(100) NOT NULL,
                    metro_area VARCHAR(100),
                    land_location VARCHAR(255) NOT NULL,
                    land_size VARCHAR(100) NOT NULL,
                    lawyer_name VARCHAR(255) NOT NULL,
                    court_name VARCHAR(255) NOT NULL,
                    dispute_reason TEXT NOT NULL,
                    years_litigation INT NOT NULL,
                    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
            """)
            conn.commit()
            cursor.close()
            conn.close()
        except Error as e:
            print(f"Error initializing database: {e}")

def get_all_cases() -> List[Dict[str, Any]]:
    """Fetch all cases and return as a list of dictionaries with string keys."""
    conn = get_db_connection()
    cases: List[Dict[str, Any]] = []
    if conn:
        try:
            # Use dictionary=True to get rows as actual dict objects
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT id, region, division, metro_area, land_location, land_size,
                       lawyer_name, court_name, dispute_reason, years_litigation, submitted_at
                FROM land_cases ORDER BY submitted_at DESC
            """)
            rows = cursor.fetchall() or []

            # Safe conversion, type‑checked, no errors
            for row in rows:
                # Ensure row is a dict before accessing items
                if isinstance(row, dict):
                    clean_row: Dict[str, Any] = {}
                    for key, value in row.items():
                        clean_row[str(key)] = value
                    cases.append(clean_row)

            cursor.close()
            conn.close()
        except Error as e:
            print(f"Error fetching cases: {e}")
    return cases