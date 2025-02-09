from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from homeharvest import scrape_property
import pandas as pd
import os
import socket
import requests
from dotenv import load_dotenv
from google.oauth2 import service_account
from googleapiclient.discovery import build
import numpy as np
import json
from typing import Any, Dict

# Load environment variables
load_dotenv()

# Google Sheets Setup
SHEET_ID = "1NnDWfGSaRck9IfVUNMAXItP1feJChq1zEp43sD1YnyM"
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

def convert_numpy_types(obj: Any) -> Any:
    """Convert numpy types to Python native types."""
    if isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.bool_):
        return bool(obj)
    elif isinstance(obj, dict):
        return {key: convert_numpy_types(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_types(item) for item in obj]
    elif isinstance(obj, np.ndarray):
        return convert_numpy_types(obj.tolist())
    return obj

def simplify_complex_values(value: Any) -> str:
    """Convert complex data types to string representation."""
    if pd.isna(value) or value is None:
        return ''
    elif isinstance(value, (dict, list)):
        return json.dumps(convert_numpy_types(value))
    elif isinstance(value, (int, float, bool, str)):
        return str(value)
    else:
        return str(value)

def convert_dataframe_for_json(df: pd.DataFrame) -> Dict:
    """Convert DataFrame to JSON-serializable dictionary."""
    # First convert to dict
    result_dict = df.to_dict('records')[0]
    # Then convert all numpy types
    return convert_numpy_types(result_dict)

def get_google_sheets_service():
    """Authenticate and return a Google Sheets API service instance."""
    creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if not creds_path:
        raise ValueError("GOOGLE_APPLICATION_CREDENTIALS not set in .env")
    
    creds = service_account.Credentials.from_service_account_file(creds_path, scopes=SCOPES)
    return build("sheets", "v4", credentials=creds)

app = FastAPI()

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("FRONTEND_URL", "http://localhost:3000")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define columns we want to keep
KEPT_COLUMNS = [
    'mls', 'mls_id', 'full_street_line', 'street', 'unit', 'city', 'state', 'zip_code',
    'beds', 'full_baths', 'half_baths', 'sqft', 'year_built', 'days_on_mls', 'list_price',
    'list_price_min', 'list_price_max', 'list_date', 'sold_price', 'last_sold_date',
    'assessed_value', 'estimated_value', 'tax', 'tax_history', 'new_construction',
    'lot_sqft', 'price_per_sqft', 'latitude', 'longitude', 'neighborhoods', 'county',
    'fips_code', 'stories', 'hoa_fee', 'parking_garage', 'agent_id', 'agent_name',
    'agent_email', 'agent_phones', 'agent_mls_set', 'agent_nrds_id', 'broker_id',
    'broker_name', 'builder_id', 'builder_name', 'office_id', 'office_mls_set', 'office_name',
    'office_email', 'office_phones', 'nearby_schools'
]

@app.get("/")
def read_root():
    return {"status": "running"}

@app.get("/debug-dns")
def debug_dns():
    """Manually test DNS resolution & network connectivity."""
    target_host = "parser-external.geo.moveaws.com"
    try:
        resolved_ip = socket.gethostbyname(target_host)
        google_test = requests.get("https://www.google.com", timeout=5).status_code
        return {
            "status": "success",
            "resolved_ip": resolved_ip,
            "google_test_status": google_test
        }
    except socket.gaierror as e:
        return {"status": "error", "dns_error": str(e)}
    except requests.RequestException as e:
        return {"status": "error", "network_error": str(e)}

@app.post("/process-address")
def process_address(address: str):
    try:
        print(f"📍 Processing address: {address}")

        # DNS resolution check
        try:
            test_host = "parser-external.geo.moveaws.com"
            print(f"🔍 Resolving {test_host}...")
            resolved_ip = socket.gethostbyname(test_host)
            print(f"✅ Resolved {test_host} to {resolved_ip}")
        except socket.gaierror as e:
            raise HTTPException(status_code=500, detail=f"DNS resolution failed: {str(e)}")

        # Fetch property data
        result = scrape_property(location=address)

        # Convert to DataFrame if not already
        if not isinstance(result, pd.DataFrame):
            result = pd.DataFrame([result])

        # Select only needed columns and handle missing columns
        available_columns = [col for col in KEPT_COLUMNS if col in result.columns]
        result = result[available_columns]

        # Combine bathroom counts if columns exist
        if 'full_baths' in result.columns and 'half_baths' in result.columns:
            full_baths = result['full_baths'].fillna(0).astype(float)
            half_baths = result['half_baths'].fillna(0).astype(float)
            result['total_baths'] = full_baths + (half_baths * 0.5)
            result = result.drop(['full_baths', 'half_baths'], axis=1)

        # Replace NaN values with None
        result = result.replace({np.nan: None})

        # Convert to JSON-serializable format
        result_dict = convert_dataframe_for_json(result)

        # Prepare data for Google Sheets by simplifying complex values
        sheet_data = result.copy()
        for column in sheet_data.columns:
            sheet_data[column] = sheet_data[column].apply(simplify_complex_values)

        # Append to Google Sheet
        append_to_google_sheet(sheet_data)

        return {"status": "success", "data": result_dict}

    except Exception as e:
        print(f"❌ Error details: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

def check_existing_entry(service, address):
    """Check if an address already exists in the Google Sheet."""
    try:
        sheet = service.spreadsheets()
        response = sheet.values().get(spreadsheetId=SHEET_ID, range="C:C").execute()
        existing_addresses = response.get("values", [])
        return address in [row[0] for row in existing_addresses if row]
    except Exception as e:
        print(f"⚠️ Error checking existing entries: {str(e)}")
        return False

def append_to_google_sheet(dataframe: pd.DataFrame):
    """Append data to the Google Sheet if the address doesn't exist."""
    sheets_service = get_google_sheets_service()
    sheet = sheets_service.spreadsheets()

    # Extract address to check for duplicates
    address = dataframe.iloc[0]['full_street_line']
    
    if check_existing_entry(sheets_service, address):
        print(f"ℹ️ Address '{address}' already exists in the sheet. Skipping entry.")
        return {"status": "skipped", "message": f"Address '{address}' already exists."}

    # Convert to list of lists for Google Sheets
    values = dataframe.values.tolist()

    # Append data
    try:
        sheet.values().append(
            spreadsheetId=SHEET_ID,
            range="A1",
            valueInputOption="RAW",
            insertDataOption="INSERT_ROWS",
            body={"values": values}
        ).execute()
        print(f"✅ Data for '{address}' successfully appended to the sheet.")
        return {"status": "success", "message": f"Data for '{address}' appended successfully."}
    except Exception as e:
        print(f"❌ Error appending to sheet: {str(e)}")
        raise e