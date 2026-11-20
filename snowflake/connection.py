import os
import snowflake.connector

from dotenv import load_dotenv

load_dotenv()


def get_snowflake_connection():

    connection = snowflake.connector.connect(
        account=os.getenv("SNOWFLAKE_ACCOUNT"),
        user=os.getenv("SNOWFLAKE_USER"),
        password=os.getenv("SNOWFLAKE_PASSWORD"),
        warehouse=os.getenv("SNOWFLAKE_WAREHOUSE"),
        database=os.getenv("SNOWFLAKE_DATABASE"),
        schema=os.getenv("SNOWFLAKE_SCHEMA"),
        role=os.getenv("SNOWFLAKE_ROLE") or None
    )

    return connection


if __name__ == "__main__":

    conn = get_snowflake_connection()

    print("Snowflake connection successful!")

    conn.close()