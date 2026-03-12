from google.oauth2 import service_account
from googleapiclient.discovery import build
import pandas as pd

SERVICE_ACCOUNT_FILE = 'valuation-430503-780d52190443.json'
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

# ID of the Google Sheet you want to access
SPREADSHEET_ID = '1FqpSV4aYl1jWwbVddXjrbarGVLiSwIJ0HjEdY1zjZPM'
RANGE_NAME = 'STOCK MARKET!G1:I12'

def connect_to_google_sheets():
    # Authenticate using the service account JSON file
    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES
    )

    # Build the Google Sheets API service
    service = build('sheets', 'v4', credentials=credentials)

    return service

def download_sheet_data():
    # Connect to Google Sheets API
    sheets_service = connect_to_google_sheets()

    # Call the Sheets API to get the values from the specified range
    sheet = sheets_service.spreadsheets()
    result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=RANGE_NAME).execute()
    values = result.get('values', [])
    data = pd.DataFrame(values, columns=None) 
    return data
            
def update_cell_data(ticker):
    # Connect to Google Sheets API
    sheets_service = connect_to_google_sheets()

    # Define the range and the value to update
    update_range = 'STOCK MARKET!I1'
    value_input_option = 'RAW'
    values = [
        [ticker[:-3]]
    ]
    body = {
        'values': values
    }

    # Call the Sheets API to update the specified cell
    sheets_service.spreadsheets().values().update(
        spreadsheetId=SPREADSHEET_ID,
        range=update_range,
        valueInputOption=value_input_option,
        body=body
    ).execute()
