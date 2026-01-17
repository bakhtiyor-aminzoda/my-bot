import gspread
from oauth2client.service_account import ServiceAccountCredentials
from bot.config import GOOGLE_KEY_FILE, SPREADSHEET_ID
import datetime
import os
import json

def get_service():
    """
    Authenticates with Google Sheets and returns the client.
    Returns None if credentials file is missing or invalid.
    """
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    
    try:
        if os.path.exists(GOOGLE_KEY_FILE):
             creds = ServiceAccountCredentials.from_json_keyfile_name(GOOGLE_KEY_FILE, scope)
        else:
             # Fallback for Render: Load from Env Var
             json_creds = os.getenv("GOOGLE_CREDENTIALS_JSON")
             if json_creds:
                 creds_dict = json.loads(json_creds)
                 creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
             else:
                 print("⚠️ No credentials found (File or Env Var).")
                 return None

        client = gspread.authorize(creds)
        return client
    except Exception as e:
        print(f"⚠️ Google Sheets Auth Error: {e}")
        return None

def add_lead(data: dict):
    """
    Adds a new lead row to the spreadsheet.
    Expected data dict: name, business_type, task_description, contact_info, service_context
    """
    client = get_service()
    if not client:
        return

    try:
        sheet = client.open_by_key(SPREADSHEET_ID).sheet1
        
        # Prepare row
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        row = [
            timestamp,
            data.get("service_context", "N/A"),
            data.get("name", ""),
            data.get("business_type", ""),
            data.get("task_description", ""),
            data.get("contact_info", ""),
            data.get("budget", "")
        ]
        
        sheet.append_row(row)
        print("✅ Lead saved to Google Sheet.")
        
    except Exception as e:
        print(f"❌ Failed to save to Sheet: {repr(e)}")
        # import traceback
        # traceback.print_exc()
