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
import json
from typing import Any, Dict, Optional
import numpy as np

# Load environment variables
load_dotenv()

# Google Sheets Setup
SHEET_ID = "1NnDWfGSaRck9IfVUNMAXItP1feJChq1zEp43sD1YnyM"
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

# Google Sheet Columns for Address Components
SHEET_COLUMNS_TO_CHECK = {
    "street": "D",
    "unit": "E",
    "city": "F",
    "state": "G",
    "zip_code": "H"
}

def convert_numpy_types(obj: Any) -> Any:
    """Convert numpy types to Python native types."""
    #print(f"🔄 Converting numpy type: {type(obj)}")
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
    """Convert complex data types to JSON string representation."""
    #print(f"🔄 Simplifying value type: {type(value)}")
    
    # Handle numpy arrays and pandas Series
    if hasattr(value, '__iter__') and not isinstance(value, (str, dict)):
        return json.dumps([simplify_complex_values(v) for v in value])
    
    # Handle individual values
    if pd.api.types.is_scalar(value):
        if pd.isna(value) or value is None:
            return ''
        elif isinstance(value, (dict, list)):
            return json.dumps(value)
        else:
            return str(value)
    
    return str(value)

def convert_dataframe_for_json(df: pd.DataFrame) -> Dict:
    """Convert DataFrame to JSON-serializable dictionary."""
    print("🔄 Converting DataFrame to JSON")
    #print(f"DataFrame columns: {df.columns.tolist()}")
    result_dict = df.to_dict('records')[0]
    return convert_numpy_types(result_dict)

def get_google_sheets_service():
    """Authenticate and return a Google Sheets API service instance."""
    print("🔑 Getting Google Sheets service")
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
async def process_address(address: str):
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
        print("🏠 Fetching property data...")
        result = scrape_property(location=address)
        print(f"📊 Raw result type: {type(result)}")

        # Convert to DataFrame if not already
        if not isinstance(result, pd.DataFrame):
            print("🔄 Converting result to DataFrame")
            result = pd.DataFrame([result])
        
        #print(f"📋 Available columns: {result.columns.tolist()}")

        # Select only needed columns and handle missing columns
        print("🔍 Filtering out noisy columns...")
        available_columns = [col for col in KEPT_COLUMNS if col in result.columns]
        #print(f"📋 Filtered columns: {available_columns}")
        result = result[available_columns]

        # Combine bathroom counts if columns exist
        print("🚽 Processing bathroom data...")
        if all(col in result.columns for col in ['full_baths', 'half_baths']):
            print("Found both bathroom columns")
            print(f"Full baths data: {result['full_baths'].tolist()}")
            print(f"Half baths data: {result['half_baths'].tolist()}")
            
            # Convert to numeric and handle NaN values properly
            full_baths = pd.to_numeric(result['full_baths'], errors='coerce').fillna(0)
            half_baths = pd.to_numeric(result['half_baths'], errors='coerce').fillna(0)
            result['total_baths'] = full_baths + (half_baths * 0.5)
            result = result.drop(['full_baths', 'half_baths'], axis=1)
            print(f"Total baths calculated: {result['total_baths'].tolist()}")

        # Replace NaN values with None
        print("🧹 Cleaning up NaN values...")
        result = result.replace({np.nan: None})

        # Extract address components for duplicate check
        print("🏠 Extracting address components...")
        address_components_to_check = {}
        for key in SHEET_COLUMNS_TO_CHECK.keys():
            if key in result.columns:
                value = result.iloc[0][key]
                print(f"Component {key}: {value}")
                address_components_to_check[key] = value

        print(f"📍 Address components to check: {address_components_to_check}")

        sheets_service = get_google_sheets_service()

        # Check for existing entry based on address components
        print("🔍 Checking for existing entries...")
        if check_existing_entry(sheets_service, address_components_to_check):
            address_str = result.iloc[0].get('full_street_line', 'N/A')
            print(f"⚠️ Duplicate found for address: {address_str}")
            return {"status": "skipped", "message": f"Address '{address_str}' already exists with similar details. Skipping entry."}

        # Convert to JSON-serializable format
        print("🔄 Converting to JSON format...")
        result_dict = convert_dataframe_for_json(result)

        # Prepare data for Google Sheets by simplifying complex values
        print("📝 Preparing data for Google Sheets...")
        sheet_data = result.copy()
        for column in sheet_data.columns:
            sheet_data[column] = sheet_data[column].apply(simplify_complex_values)

        # Append to Google Sheet
        print("📤 Appending to Google Sheet...")
        append_to_google_sheet(sheet_data)

        print("✅ Process completed successfully")
        return {"status": "success", "data": result_dict}

    except Exception as e:
        print(f"❌ Error details: {str(e)}")
        print(f"Error type: {type(e)}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

def check_existing_entry(service, address_components: Dict[str, Optional[str]]) -> bool:
    """
    Check if an entry with similar address components already exists in the Google Sheet.
    """
    print(f"🔍 Checking existing entry with components: {address_components}")
    sheet = service.spreadsheets()
    sheet_values = sheet.values()

    # Prepare ranges to fetch from Google Sheets based on configured columns
    ranges_to_fetch = [f"{SHEET_COLUMNS_TO_CHECK[key]}:{SHEET_COLUMNS_TO_CHECK[key]}" 
                      for key in address_components]
    print(f"📊 Ranges to fetch: {ranges_to_fetch}")

    if not ranges_to_fetch:
        print("⚠️ No address components provided for duplicate check. Skipping check.")
        return False

    try:
        response = sheet_values.batchGet(spreadsheetId=SHEET_ID, ranges=ranges_to_fetch).execute()
        value_ranges = response.get('valueRanges', [])
        sheet_data = {}

        for i, value_range in enumerate(value_ranges):
            component_name = list(address_components.keys())[i]
            sheet_values_list = value_range.get('values', [])
            sheet_data[component_name] = [row[0] if row else None for row in sheet_values_list]
            print(f"📋 Fetched {len(sheet_values_list)} values for {component_name}")

        num_rows = max(len(v) for v in sheet_data.values()) if sheet_data else 0
        print(f"📊 Checking {num_rows} rows")

        for row_index in range(num_rows):
            is_match_for_row = True
            for component_name, component_value in address_components.items():
                sheet_component_values = sheet_data[component_name]
                sheet_value = sheet_component_values[row_index] if row_index < len(sheet_component_values) else None
                
                #print(f"🔍 Comparing row {row_index}: {component_name}")
                # print(f"   Sheet value: {sheet_value}")
                # print(f"   Input value: {component_value}")

                if component_value is not None and sheet_value is not None:
                    if str(sheet_value).strip().lower() != str(component_value).strip().lower():
                        is_match_for_row = False
                        break

            if is_match_for_row:
                print("✅ Match found!")
                return True

        print("❌ No matches found")
        return False
    except Exception as e:
        print(f"❌ Error checking for existing entries: {str(e)}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")
        return False

def append_to_google_sheet(data: pd.DataFrame) -> None:
    """Append processed data to Google Sheets."""
    print("📤 Starting Google Sheet append...")
    sheets_service = get_google_sheets_service()
    sheet = sheets_service.spreadsheets()
    
    try:
        # Prepare values in list format
        values_to_append = data.values.tolist()
        range_to_append = "A1"
        print(f"📊 Preparing to append {len(values_to_append)} rows")
        
        sheet.values().append(
            spreadsheetId=SHEET_ID,
            range=range_to_append,
            valueInputOption="RAW",
            insertDataOption="INSERT_ROWS",
            body={"values": values_to_append}
        ).execute()

        print("✅ Data successfully appended to Google Sheets.")

    except Exception as e:
        print(f"❌ Error appending data to Google Sheets: {str(e)}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))