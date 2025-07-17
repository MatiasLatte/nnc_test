import gspread
from pathlib import Path
from typing import List, Dict
from google.oauth2.service_account import Credentials
from config.config import config
import time


class GoogleSheetsClient:
    """Interaction with Google Sheets"""

    def __init__(self):
        self.client = None
        self.workbook = None
        self.sheet = None
        self.connect()

    def connect(self):
        """Connects with Google sheets using the service account credentials"""
        try:
            # Credential route from config module
            credentials_path = Path(__file__).resolve().parents[2] / config.google_sheets.credentials_path
            scope = ["https://www.googleapis.com/auth/spreadsheets"]

            # service account authentication
            creds = Credentials.from_service_account_file(str(credentials_path), scopes=scope)
            self.client = gspread.authorize(creds)

            # Open the spreadsheet by their ID
            self.workbook = self.client.open_by_key(config.google_sheets.sheet_id)

            # get "VOIP" worksheet
            try:
                self.sheet = self.workbook.worksheet("VOIP")
            except gspread.WorksheetNotFound:
                # Catch nonexisting worksheet
                print("Worksheet 'VOIP' not found")

            print(f"Successfully connected to Google Sheets: {self.workbook.title}")

        except Exception as e:
            print(f"Error logging into Google sheets: {e}")
            raise

    def get_all_products(self) -> List[Dict]:
        """
        Gets all products from the sheet
        Returns a list of dictionaries with the data
        """
        try:
            # Get all info
            records = self.sheet.get_all_records()

            if not records:
                print("No products found on the sheet")
                return []

            # Clean the data
            products = []
            for i, record in enumerate(records, start=2):  # Start=2 cause row 1 = headers
                try:
                    # Skip empty lines
                    if not record or not any(str(value).strip() for value in record.values()):
                        continue

                    # Normalize names, columns, and values
                    normalized_record = {}
                    for key, value in record.items():
                        # clean the key
                        clean_key = str(key).lower().strip().replace(' ', '_').replace('-', '_')

                        # clean the value
                        clean_value = str(value).strip() if value else ""

                        normalized_record[clean_key] = clean_value

                    # Validate essential spaces
                    if not self._validate_product_record(normalized_record, i):
                        continue

                    # add metadata (row, sheet_name)
                    normalized_record['_row_number'] = i
                    normalized_record['_sheet_name'] = self.sheet.title

                    products.append(normalized_record)

                except Exception as e:
                    print(f"Error processing queue {i}: {e}")
                    continue

            print(f" Read {len(products)} valid products from the sheet")
            return products

        except Exception as e:
            print(f"Error reading products: {e}")
            return []

    def _validate_product_record(self, record: Dict, row_number: int) -> bool:
        """Validates that each product has de minimal amount of requirements needed"""
        required_fields = ['part_no']

        for field in required_fields:
            if not record.get(field):
                print(f"Row {row_number}: is missing required field: '{field}'")
                return False

        return True

    def watch_for_changes(self, callback_function, interval: int = None):
        """
        Monitors changes in the sheet using polling
        """
        if interval is None:
            interval = config.sync_interval

        print(f"Monitoring for changes (interval: {interval})")

        last_data_hash = None #in order to determine changes in data we use a Cryptographic hash Function

        while True:
            try:
                # Get current data
                current_data = self.get_all_products() # -> dict of all products in the sheet

                # Get simple hash to detect changes
                current_hash = hash(str(sorted(current_data, key=lambda x: x.get('part_no', ''))))

                # If there are changes do callback
                if last_data_hash is None:
                    print("First load of data")
                    callback_function(current_data)
                elif current_hash != last_data_hash:
                    print("Changes in the sheet")
                    callback_function(current_data)
                else:
                    print("No changes in the sheet")

                last_data_hash = current_hash

                # Wait until next check
                time.sleep(interval)

            except Exception as e:
                print(f"Error in monitoring for changes: {e}")
                time.sleep(interval * 2)  # Wait more time if there's error and try again

# Helper function to create the Google sheets client
def create_sheets_client() -> GoogleSheetsClient:
    """Function to create the Google sheets client"""
    return GoogleSheetsClient()