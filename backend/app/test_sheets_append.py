import os
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from dotenv import load_dotenv

load_dotenv()  # This loads the .env file

SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive.file']
SHEET_ID = "10ggg3VWqssL2W4vhiP2wLyF2G8YkvFjJv42SMVCNm-Q"  # Replace with your actual Google Sheet ID

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
        creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        creds = service_account.Credentials.from_service_account_file(creds_path, scopes=['https://www.googleapis.com/auth/drive.file'])
        service = build('drive', 'v3', credentials=creds)
        
        permissions = {
            'type': 'user',
            'role': 'writer',
            'emailAddress': email
        }
        
        service.permissions().create(
            fileId=spreadsheet_id,
            body=permissions,
            fields='id'
        ).execute()
        print(f"✅ Sheet shared with {email}")
        
    except HttpError as error:
        print(f"An error occurred: {error}")

def append_data_to_sheet():
    service = get_google_sheets_service()

    sample_data = [
        ["123 wherever harriss lives", "Denver", "NY", "$1,000,000,000"],
    ]

    try:
        service.spreadsheets().values().append(
            spreadsheetId=SHEET_ID,
            range="A1",
            valueInputOption="RAW",
            insertDataOption="INSERT_ROWS",
            body={"values": sample_data}
        ).execute()
        print("✅ Data appended successfully.")
    
    except HttpError as error:
        print(f"An error occurred: {error}")

if __name__ == "__main__":
    append_data_to_sheet()
