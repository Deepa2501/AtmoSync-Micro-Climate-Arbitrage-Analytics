
"""
Snowflake connection utilities for AtmoSync.
"""

import snowflake.connector

from config.settings import get_snowflake_config


def get_snowflake_connection():
    """
    Establish and return a Snowflake connection.
    """

    config = get_snowflake_config()

    if not config["password"]:
        raise ValueError(
            "SNOWFLAKE_PASSWORD is missing from the .env file."
        )

    connection = snowflake.connector.connect(
        account=config["account"],
        user=config["user"],
        password=config["password"],
        warehouse=config["warehouse"],
        database=config["database"],
        schema=config["schema"],
        role=config["role"] or None,
    )

    return connection


def test_snowflake_connection():
    """
    Test Snowflake connection and display account details.
    """

    connection = None

    try:
        connection = get_snowflake_connection()

        cursor = connection.cursor()

        try:
            cursor.execute("""
                SELECT
                    CURRENT_ACCOUNT(),
                    CURRENT_DATABASE(),
                    CURRENT_SCHEMA(),
                    CURRENT_WAREHOUSE()
            """)

            result = cursor.fetchone()

            print("Snowflake connection successful!")
            print(f"Account: {result[0]}")
            print(f"Database: {result[1]}")
            print(f"Schema: {result[2]}")
            print(f"Warehouse: {result[3]}")

        finally:
            cursor.close()

    except Exception as error:
        print("Snowflake connection failed!")
        print(f"Error: {error}")
        raise

    finally:
        if connection is not None:
            connection.close()


if __name__ == "__main__":
    test_snowflake_connection()
