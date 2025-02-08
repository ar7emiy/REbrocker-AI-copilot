from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from homeharvest import scrape_property
import pandas as pd
from google.oauth2 import service_account
from googleapiclient.discovery import build
import os
#from pathlib import Path
from dotenv import load_dotenv

os.environ['HTTPS_PROXY'] = ''
os.environ['HTTP_PROXY'] = ''

os.environ.clear()  # Clear any existing env vars
print("Environment before load:", os.environ.get('GOOGLE_APPLICATION_CREDENTIALS'))
load_dotenv()
print("Environment after load:", os.environ.get('GOOGLE_APPLICATION_CREDENTIALS'))

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
# [THIS IS WHERE WE SELECTED SPECIFIC COLUMNS - EASY TO MODIFY]
KEPT_COLUMNS = [
    'full_street_line',
    'city',
    'state',
    'zip_code',
    'list_price',
    'beds',
    'full_baths',
    'half_baths',
    'sqft',
    'status'
]

# Google Sheets setup
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

def get_google_sheets_service():
    creds_path = os.path.abspath(os.getenv('GOOGLE_APPLICATION_CREDENTIALS'))
    print(f"Attempting to load credentials from: {creds_path}")
    print(f"File exists: {os.path.exists(creds_path)}")
    
    creds = service_account.Credentials.from_service_account_file(
        creds_path,
        scopes=SCOPES
    )
    return build('sheets', 'v4', credentials=creds)

# Initialize sheet ID globally (we'll create it on first run)
SHEET_ID = None

@app.get("/")
async def read_root():
    return {"status": "running"}

@app.post("/process-address")
async def process_address(address: str):
    try:
        # Add debug print
        print(f"Processing address: {address}")
        
        result = scrape_property(location=address)
        
        # Add debug print
        print(f"Result received: {result is not None}")
        
        if not isinstance(result, pd.DataFrame):
            result = pd.DataFrame([result])
            
        result = result[KEPT_COLUMNS]
        result['total_baths'] = result['full_baths'] + (result['half_baths'] * 0.5)
        result = result.drop(['full_baths', 'half_baths'], axis=1)
        
        await update_sheet(result)
        return {"status": "success", "data": result.to_dict('records')[0]}
    
    except Exception as e:
        print(f"Error details: {str(e)}")  # Debug print
        raise HTTPException(
            status_code=500, 
            detail=f"Error processing address: {str(e)}"
        )

async def update_sheet(data: pd.DataFrame):
    global SHEET_ID
    
    service = get_google_sheets_service()
    
    # If sheet doesn't exist, create it
    if not SHEET_ID:
        spreadsheet = {
            'properties': {
                'title': 'Property Listings'
            }
        }
        spreadsheet = service.spreadsheets().create(body=spreadsheet).execute()
        SHEET_ID = spreadsheet.get('spreadsheetId')
        
        # Add headers
        headers = [data.columns.tolist()]
        service.spreadsheets().values().update(
            spreadsheetId=SHEET_ID,
            range='A1',
            valueInputOption='RAW',
            body={'values': headers}
        ).execute()
    
    # Append new data
    values = data.values.tolist()
    service.spreadsheets().values().append(
        spreadsheetId=SHEET_ID,
        range='A2',
        valueInputOption='RAW',
        body={'values': values}
    ).execute()

@app.get("/sheet")
async def get_sheet():
    if not SHEET_ID:
        raise HTTPException(status_code=404, detail="Sheet not created yet")
    return {"sheet_id": SHEET_ID}