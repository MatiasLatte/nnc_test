import os
from dotenv import load_dotenv
from dataclasses import dataclass
from typing import Optional

# Load env variables
load_dotenv()


@dataclass
class DatabaseConfig:
    """Configuración de base de datos"""
    host: str
    port: int
    database: str
    user: str
    password: str
    ssl_mode: str = "require"

    @classmethod
    def from_env(cls) -> 'DatabaseConfig':
        return cls(
            host=os.getenv('DB_HOST', 'localhost'),
            port=int(os.getenv('DB_PORT', '5432')),
            database=os.getenv('DB_NAME', 'postgres'),
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASSWORD', ''),
            ssl_mode=os.getenv('DB_SSL_MODE', 'require')
        )

    def get_connection_string(self) -> str:
        """Retorna string de conexión para PostgreSQL"""
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}?sslmode={self.ssl_mode}"


@dataclass
class GoogleSheetsConfig:
    """Configuración de Google Sheets"""
    credentials_path: str
    sheet_url: str

    @classmethod
    def from_env(cls) -> 'GoogleSheetsConfig':
        credentials_path = os.getenv('GOOGLE_CREDENTIALS_PATH')
        sheet_url = os.getenv('SHEET_URL')

        if not credentials_path or not sheet_url:
            raise ValueError("GOOGLE_CREDENTIALS_PATH y SHEET_URL son requeridos")

        return cls(
            credentials_path=credentials_path,
            sheet_url=sheet_url
        )