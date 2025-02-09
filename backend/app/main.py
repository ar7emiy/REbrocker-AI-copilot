from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from homeharvest import scrape_property
import pandas as pd
import os
import socket  # To manually check DNS resolution
import requests  # To check outgoing network requests
from dotenv import load_dotenv
from google.oauth2 import service_account
from googleapiclient.discovery import build

# Remove `os.environ.clear()` to avoid clearing necessary environment variables

# Debug: Print essential environment variables
load_dotenv()  # Load .env variables safely
print("🔹 GOOGLE_APPLICATION_CREDENTIALS:", os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"))
print("🔹 PATH:", os.environ.get("PATH"))
print("🔹 HTTPS_PROXY:", os.environ.get("HTTPS_PROXY"))
print("🔹 HTTP_PROXY:", os.environ.get("HTTP_PROXY"))

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
        
        # Manually test DNS resolution before calling scrape_property
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

        # Select only needed columns
        result = result[KEPT_COLUMNS]

        # Combine bathroom counts
        result['total_baths'] = result['full_baths'] + (result['half_baths'] * 0.5)
        result = result.drop(['full_baths', 'half_baths'], axis=1)

        return {"status": "success", "data": result.to_dict('records')[0]}

    except Exception as e:
        print(f"❌ Error details: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
