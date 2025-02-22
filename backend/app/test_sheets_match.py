import os
from dotenv import load_dotenv
from google.oauth2 import service_account
from googleapiclient.discovery import build
from typing import Any, Dict, Optional

# Load environment variables (assuming .env file is in the same directory or accessible)
load_dotenv()

# Google Sheets Setup - IMPORTANT: Replace with your actual Sheet ID if different for testing
SHEET_ID = "1NnDWfGSaRck9IfVUNMAXItP1feJChq1zEp43sD1YnyM"  # Or your test sheet ID
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

# Google Sheet Columns for Address Components (Correct as per your setup)
SHEET_COLUMNS_TO_CHECK = {
    "street": "D",
    "unit": "E",
    "city": "F",
    "state": "G",
    "zip_code": "H"
}

def get_google_sheets_service():
    """Authenticate and return a Google Sheets API service instance."""
    creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if not creds_path:
        raise ValueError("GOOGLE_APPLICATION_CREDENTIALS not set in .env")

    creds = service_account.Credentials.from_service_account_file(creds_path, scopes=SCOPES)
    return build("sheets", "v4", credentials=creds)

def check_existing_entry(service, address_components: Dict[str, Optional[str]]) -> bool:
    """
    Check if an entry with similar address components already exists in the Google Sheet.
    Compares based on available address components in both input and sheet data.
    Uses AND logic - all provided components must match for a duplicate.
    """
    sheet = service.spreadsheets()
    sheet_values = sheet.values()

    # Prepare ranges to fetch from Google Sheets based on configured columns
    ranges_to_fetch = [f"{SHEET_COLUMNS_TO_CHECK[key]}:{SHEET_COLUMNS_TO_CHECK[key]}" for key in address_components]

    if not ranges_to_fetch:
        print("⚠️ No address components provided for duplicate check. Skipping check.") # Log if no components to check
        return False # If no components to check, default to not existing to be safe, or change to True to skip all inserts.

    try:
        response = sheet_values.batchGet(spreadsheetId=SHEET_ID, ranges=ranges_to_fetch).execute()
        value_ranges = response.get('valueRanges', [])
        sheet_data = {} # Store sheet data by component name

        for i, value_range in enumerate(value_ranges):
            component_name = list(address_components.keys())[i] # Get component name in order
            sheet_values_list = value_range.get('values', [])
            sheet_data[component_name] = [row[0] if row else None for row in sheet_values_list] # Flatten to list of values, handle empty rows

        # Check for match across all provided address components (AND logic)
        num_rows = max(len(v) for v in sheet_data.values()) if sheet_data else 0
        for row_index in range(num_rows):
            is_match_for_row = True
            for component_name, component_value in address_components.items():
                sheet_component_values = sheet_data[component_name]
                sheet_value = sheet_component_values[row_index] if row_index < len(sheet_component_values) else None

                if component_value is not None and sheet_value is not None:
                    if str(sheet_value).strip().lower() != str(component_value).strip().lower(): # Compare string values, case-insensitive, and strip whitespace
                        is_match_for_row = False
                        break # No match for this component, check next row
                elif component_value is not None or sheet_value is not None: # If one is None and the other is not, then no match. Both must be None to be considered a match in terms of missing data.
                    is_match_for_row = False
                    break # No match if one is present and the other is missing

            if is_match_for_row:
                print(f"ℹ️ Duplicate entry found in sheet for address components: {address_components}")
                return True # Found a row where all provided components match

        return False # No matching entry found

    except Exception as e:
        print(f"⚠️ Error checking existing entries: {str(e)}")
        return False

if __name__ == "__main__":
    # Get Google Sheets service
    sheets_service = get_google_sheets_service()

    # --- Test Cases ---

    # Test Case 1: Exact match - should return True (assuming this address exists in your sheet)
    address_components_1 = {
        "street": "2427 N Greenview Ave",
        "unit": "Apt 1",
        "city": "Chicago",
        "state": "IL",
        "zip_code": "60614"
    }
    is_duplicate_1 = check_existing_entry(sheets_service, address_components_1)
    print(f"\nTest Case 1 - Exact Match:\nComponents: {address_components_1}\nDuplicate found: {is_duplicate_1}")

    # Test Case 2: No match - street address slightly different - should return False
    address_components_2 = {
        "street": "2428 N Greenview Ave", # Street number changed
        "unit": "Apt 1",
        "city": "Chicago",
        "state": "IL",
        "zip_code": "60614"
    }
    is_duplicate_2 = check_existing_entry(sheets_service, address_components_2)
    print(f"\nTest Case 2 - No Street Match:\nComponents: {address_components_2}\nDuplicate found: {is_duplicate_2}")

    # Test Case 3: No match - different unit - should return False
    address_components_3 = {
        "street": "2427 N Greenview Ave",
        "unit": "Apt 2", # Unit changed
        "city": "Chicago",
        "state": "IL",
        "zip_code": "60614"
    }
    is_duplicate_3 = check_existing_entry(sheets_service, address_components_3)
    print(f"\nTest Case 3 - No Unit Match:\nComponents: {address_components_3}\nDuplicate found: {is_duplicate_3}")

    # Test Case 4: Match - only street and zip provided (assuming sheet has entry with these and other matching components might exist but are not provided in input) - should return True if there's a row with this street and zip.
    address_components_4 = {
        "street": "2427 N Greenview Ave",
        "zip_code": "60614"
    }
    is_duplicate_4 = check_existing_entry(sheets_service, address_components_4)
    print(f"\nTest Case 4 - Partial Match (Street and Zip):\nComponents: {address_components_4}\nDuplicate found: {is_duplicate_4}")

    # Test Case 5: No Match - different zip code - should return False
    address_components_5 = {
        "street": "2427 N Greenview Ave",
        "unit": "Apt 1",
        "city": "Chicago",
        "state": "IL",
        "zip_code": "60615" # Zip code changed
    }
    is_duplicate_5 = check_existing_entry(sheets_service, address_components_5)
    print(f"\nTest Case 5 - No Zip Match:\nComponents: {address_components_5}\nDuplicate found: {is_duplicate_5}")

    # Test Case 6: Case-insensitive match - should return True if the sheet has the address in a different case.
    address_components_6 = {
        "street": "2427 n greenview ave", # lowercase street
        "unit": "apt 1", # lowercase unit
        "city": "chicago", # lowercase city
        "state": "il", # lowercase state
        "zip_code": "60614"
    }
    is_duplicate_6 = check_existing_entry(sheets_service, address_components_6)
    print(f"\nTest Case 6 - Case-Insensitive Match:\nComponents: {address_components_6}\nDuplicate found: {is_duplicate_6}")

    # Test Case 7: Whitespace variations - should return True if sheet has address with extra spaces
    address_components_7 = {
        "street": "  2427 N Greenview Ave  ", # Extra spaces
        "unit": "Apt 1 ", # Trailing space
        "city": " Chicago ", # Leading and trailing spaces
        "state": "IL",
        "zip_code": "60614"
    }
    is_duplicate_7 = check_existing_entry(sheets_service, address_components_7)
    print(f"\nTest Case 7 - Whitespace Variations:\nComponents: {address_components_7}\nDuplicate found: {is_duplicate_7}")