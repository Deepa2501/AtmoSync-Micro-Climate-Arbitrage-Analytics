from cryptography.hazmat.primitives import serialization
import snowflake.connector

with open("snowflake_key.p8", "rb") as f:
    key = serialization.load_pem_private_key(f.read(), password=None)

private_key = key.private_bytes(
    encoding=serialization.Encoding.DER,
    format=serialization.PrivateFormat.PKCS8,
    encryption_algorithm=serialization.NoEncryption(),
)

conn = snowflake.connector.connect(
    account="ZPLZZLB-NK45236",
    user="PIPELINE_USER",
    private_key=private_key,
    warehouse="SPOILAGE_WH",
    database="SPOILAGE_DB",
)
cur = conn.cursor()
cur.execute("SELECT CURRENT_USER(), CURRENT_ROLE(), CURRENT_WAREHOUSE()")
print(cur.fetchone())
conn.close()
