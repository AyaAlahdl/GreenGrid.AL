from google.cloud import bigquery
import os
from datetime import datetime, timedelta, timezone

# Set service account key file
SERVICE_ACCOUNT_KEY_PATH = "greengrid-ai-multi-agent.json"
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = SERVICE_ACCOUNT_KEY_PATH

# Constants
PROJECT_ID = "greengrid-ai-multi-agent"
DATASET_ID = "energy_data"
TABLE_ID = "energy_readings"
TABLE_REF = f"{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}"

# BigQuery client
client = bigquery.Client(project=PROJECT_ID)

# ✅ Insert data using load_table_from_json (BigQuery free-tier friendly)
def insert_energy_record(
    timestamp,
    consumption_kWh,
    solar_generation_kWh,
    predicted_consumption_kWh=None,
    predicted_solar_kWh=None,
    price_kWh=None,
    expected_cost=None,
    decision=None,
):
    try:
        # Ensure timestamp is ISO 8601 string (required by BigQuery JSON load)
        if isinstance(timestamp, datetime):
            timestamp = timestamp.astimezone(timezone.utc).isoformat()

        rows_to_insert = [{
            "timestamp": timestamp,
            "consumption_kWh": consumption_kWh,
            "solar_generation_kWh": solar_generation_kWh,
            "predicted_consumption_kWh": predicted_consumption_kWh,
            "predicted_solar_kWh": predicted_solar_kWh,
            "price_kWh": price_kWh,
            "expected_cost": expected_cost,
            "decision": decision or "No decision"
        }]

        job = client.load_table_from_json(rows_to_insert, TABLE_REF)
        job.result()  # Wait for the job to complete

        if job.errors:
            print(f"❌ BigQuery load error: {job.errors}")
        else:
            print("✅ Data loaded into BigQuery successfully.")
    except Exception as e:
        print(f"⚠️ Exception during insert: {e}")


# ✅ Retrieve energy data for past `days` as list of dicts (for plotting)
def get_energy_data(days=30, limit=100):
    try:
        start_date = (datetime.utcnow() - timedelta(days=days)).strftime('%Y-%m-%d')

        query = f"""
            SELECT *
            FROM `{TABLE_REF}`
            WHERE timestamp >= TIMESTAMP('{start_date}')
            ORDER BY timestamp DESC
            LIMIT {limit}
        """
        query_job = client.query(query)
        results = query_job.result()

        return [dict(row) for row in results]
    except Exception as e:
        print(f"⚠️ Exception during BigQuery query: {e}")
        return []
