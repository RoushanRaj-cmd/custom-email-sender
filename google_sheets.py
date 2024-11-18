import os
import pandas as pd
from google.oauth2 import service_account
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']

def get_google_sheet(sheet_id, range_name):
    creds = service_account.Credentials.from_service_account_file(
        os.environ.get('GOOGLE_SHEET_CREDENTIALS'), scopes=SCOPES)

    service = build('sheets', 'v4', credentials=creds)

    sheet = service.spreadsheets()

    result = sheet.values().get(spreadsheetId=sheet_id, range=range_name).execute()
    values = result.get('values', [])

    if not values:
        return None

    df = pd.DataFrame(values[1:], columns=values[0])  # First row as header
    return df