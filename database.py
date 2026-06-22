import os
from dotenv import load_dotenv
import mysql.connector
from mysql.connector import Error
from mysql.connector.abstracts import MySQLConnectionAbstract
from mysql.connector.pooling import PooledMySQLConnection
from typing import Optional, List, Dict, Any, Union, cast

load_dotenv()

ConnectionType = Union[PooledMySQLConnection, MySQLConnectionAbstract]

def get_db_connection() -> Optional[ConnectionType]:
    try:
        db_port_str: Optional[str] = os.getenv("DB_PORT")
        db_port: int = int(db_port_str) if db_port_str is not None else 3306

        connection = mysql.connector.connect(
            host=os.getenv("DB_HOST"),
            port=db_port,
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME"),
            use_unicode=True,
            charset="utf8mb4"
        )
        return connection
    except Error as e:
        print(f"Database connection error: {e}")
        return None

def init_db() -> None:
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS land_cases (
                id INT AUTO_INCREMENT PRIMARY KEY,
                region VARCHAR(100) NOT NULL,
                division VARCHAR(100) NOT NULL,
                metro_area VARCHAR(100) NULL,
                land_location VARCHAR(255) NOT NULL,
                land_size VARCHAR(100) NOT NULL,
                lawyer_name VARCHAR(255) NOT NULL,
                court_name VARCHAR(255) NOT NULL,
                dispute_reason TEXT NOT NULL,
                submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)
        conn.commit()
        cursor.close()
        conn.close()

def get_all_cases() -> List[Dict[str, Any]]:
    conn = get_db_connection()
    if not conn:
        return []
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM land_cases ORDER BY submitted_at DESC")
        rows = cursor.fetchall()
        cases: List[Dict[str, Any]] = cast(List[Dict[str, Any]], rows)
        cursor.close()
        conn.close()
        return cases
    except Error as e:
        print(f"Error fetching cases: {e}")
        return []