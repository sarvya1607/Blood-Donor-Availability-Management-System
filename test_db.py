from config import get_db_connection


def test_connection():
    connection = get_db_connection()

    if connection is None:
        print("FAILED: MySQL Database Connection Failed!")
        return

    try:
        print("SUCCESS: MySQL Database Connected!")

        cursor = connection.cursor()
        cursor.execute("SHOW TABLES")

        print("\nAvailable Tables:")

        for table in cursor.fetchall():
            print("-", table[0])

        cursor.close()

    finally:
        connection.close()


if __name__ == "__main__":
    test_connection()