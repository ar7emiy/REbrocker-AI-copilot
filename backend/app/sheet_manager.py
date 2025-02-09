import os
from google.oauth2 import service_account
from googleapiclient.discovery import build
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
LOG_SHEET_ID = "10ggg3VWqssL2W4vhiP2wLyF2G8YkvFjJv42SMVCNm-Q"  # Tracking sheet ID


def get_google_service():
    creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if not creds_path:
        raise ValueError("GOOGLE_APPLICATION_CREDENTIALS not set in .env")
    creds = service_account.Credentials.from_service_account_file(creds_path, scopes=SCOPES)
    return build("sheets", "v4", credentials=creds), build("drive", "v3", credentials=creds)


def create_new_sheet(title, emails):
    sheets_service, drive_service = get_google_service()
    sheet = sheets_service.spreadsheets().create(body={"properties": {"title": title}}).execute()
    sheet_id = sheet.get("spreadsheetId")
    sheet_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}"
    
    # Share with ralaytrading@gmail.com and other specified emails
    all_emails = ["ralaytrading@gmail.com"] + emails
    for email in all_emails:
        permission = {"type": "user", "role": "writer", "emailAddress": email}
        drive_service.permissions().create(fileId=sheet_id, body=permission, fields="id").execute()
    
    log_creation(sheet_url, sheet_id, all_emails)
    return {"sheet_id": sheet_id, "sheet_url": sheet_url}


def log_creation(sheet_url, sheet_id, emails):
    sheets_service, _ = get_google_service()
    log_data = [[sheet_url, sheet_id, ", ".join(emails)]]
    sheets_service.spreadsheets().values().append(
        spreadsheetId=LOG_SHEET_ID,
        range="A1",
        valueInputOption="RAW",
        insertDataOption="INSERT_ROWS",
        body={"values": log_data}
    ).execute()


if __name__ == "__main__":
    sheet_title = input("Enter sheet title: ")
    emails = input("Enter additional emails (comma-separated, leave blank if none): ").split(',')
    emails = [email.strip() for email in emails if email.strip()]
    result = create_new_sheet(sheet_title, emails)
    print(f"✅ Sheet Created: {result['sheet_url']}")
