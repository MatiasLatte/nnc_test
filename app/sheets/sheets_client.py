import sqlite3
from dataclasses import dataclass
from pathlib import Path
import gspread
from google.oauth2.service_account import credentials, Credentials

CREDENTIALS_PATH = Path(__file__).resolve().parents[2] / 'excel_credentials.json' #navigating file structure for the correct path
scope = ["https://www.googleapis.com/auth/spreadsheets"]
creds = Credentials.from_service_account_file(f"{CREDENTIALS_PATH}", scopes = scope)
client = gspread.authorize(creds)

sheets_id =  #TODO: add the env variable named the same
workbook = client.open_by_key(sheets_id)

sheet = workbook.worksheet("VOIP")

@dataclass
class ProductData:
    """Data structure for each product"""
    part: str
    price: float
    weight: int
    tag: str
    collection: str

    def to_dict(self) -> dict:
        return {
            'part': self.part,
            'price': self.price,
            'weight': self.weight,
            'tag': self.tag,
            'collection': self.collection,
        }
