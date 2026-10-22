import os
import mysql.connector
from mysql.connector import Error


class Config:
    SECRET_KEY = os.environ.get(
        "SECRET_KEY",
        "blood-donor-dev-key-change-before-deployment"
    )

    DB_HOST = os.environ.get("DB_HOST", "localhost")
    DB_USER = os.environ.get("DB_USER", "root")
    DB_PASSWORD = os.environ.get("DB_PASSWORD", "")
    DB_NAME = os.environ.get("DB_NAME", "blood_donor_db")


def get_db_connection():
    """Connect Python Flask to the MySQL database."""

    try:
        connection = mysql.connector.connect(
            host=Config.DB_HOST,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            database=Config.DB_NAME
        )

        if connection.is_connected():
            return connection

    except Error as error:
        print(f"MySQL Connection Error: {error}")

    return None