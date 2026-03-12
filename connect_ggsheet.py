import streamlit as st
from google.oauth2 import service_account
from googleapiclient.discovery import build
import pandas as pd

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

# ID Google Sheet
SPREADSHEET_ID = '1FqpSV4aYl1jWwbVddXjrbarGVLiSwIJ0HjEdY1zjZPM'
RANGE_NAME = 'STOCK MARKET!G1:I12'


def connect_to_google_sheets():
    # dùng secrets của streamlit thay vì file json
    credentials = service_account.Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=SCOPES
    )

    service = build('sheets', 'v4', credentials=credentials)

    return service


def download_sheet_data():

    sheets_service = connect_to_google_sheets()

    sheet = sheets_service.spreadsheets()

    result = sheet.values().get(
        spreadsheetId=SPREADSHEET_ID,
        range=RANGE_NAME
    ).execute()

    values = result.get('values', [])

    data = pd.DataFrame(values, columns=None)

    return data


def update_cell_data(ticker):

    sheets_service = connect_to_google_sheets()

    update_range = 'STOCK MARKET!I1'

    values = [[ticker[:-3]]]

    body = {'values': values}

    sheets_service.spreadsheets().values().update(
        spreadsheetId=SPREADSHEET_ID,
        range=update_range,
        valueInputOption='RAW',
        body=body
    ).execute()
