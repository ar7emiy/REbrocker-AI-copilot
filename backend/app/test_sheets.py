import os
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from dotenv import load_dotenv
load_dotenv()  # This loads the .env file


SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive.file']

def get_google_sheets_service():
    creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
    if not creds_path:
        raise ValueError("GOOGLE_APPLICATION_CREDENTIALS not set in .env")

    creds = service_account.Credentials.from_service_account_file(
        creds_path,
        scopes=SCOPES
    )
    return build('sheets', 'v4', credentials=creds)

def share_google_sheet(spreadsheet_id, email):
    try:
        # Build Google Drive service to add permissions (share the sheet)
        creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        creds = service_account.Credentials.from_service_account_file(creds_path, scopes=['https://www.googleapis.com/auth/drive.file'])
        service = build('drive', 'v3', credentials=creds)
        
        permissions = {
            'type': 'user',
            'role': 'writer',
            'emailAddress': email
        }
        
        # Add permissions (share the sheet)
        service.permissions().create(
            fileId=spreadsheet_id,
            body=permissions,
            fields='id'
        ).execute()
        print(f"✅ Sheet shared with {email}")
        
    except HttpError as error:
        print(f"An error occurred: {error}")

def test_google_sheets():
    service = get_google_sheets_service()

    # Create a new spreadsheet
    spreadsheet = {
        'properties': {'title': 'Test Property Listings'}
    }
    sheet = service.spreadsheets().create(body=spreadsheet).execute()
    sheet_id = sheet.get('spreadsheetId')

    # Construct Google Sheets URL
    sheet_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}"
    print(f"✅ Google Sheet Created: {sheet_url}")

    # Write sample data
    sample_data = [
        ["Full Street Line", "City", "State", "Price"],
        ["123 Main St", "Chicago", "IL", "$500,000"]
    ]
    
    service.spreadsheets().values().update(
        spreadsheetId=sheet_id,
        range='A1',
        valueInputOption='RAW',
        body={'values': sample_data}
    ).execute()

    print("✅ Sample data written successfully.")

    # Share the sheet with your email (replace with your actual email)
    share_google_sheet(sheet_id, 'ralaytrading@gmail.com')

if __name__ == "__main__":
    test_google_sheets()
