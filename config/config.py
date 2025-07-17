import os
from dotenv import load_dotenv
from dataclasses import dataclass

# Load env variables
load_dotenv()


@dataclass
class DatabaseConfig:
    """DATABASE configuration"""
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
        """Returns in string the connection of PostgreSQL"""
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}?sslmode={self.ssl_mode}"


@dataclass
class GoogleSheetsConfig:
    """Google Sheets config"""
    credentials_path: str
    sheet_id: str

    @classmethod
    def from_env(cls) -> 'GoogleSheetsConfig':
        credentials_path = os.getenv('GOOGLE_CREDENTIALS_PATH', 'excel_credentials.json')
        sheet_id = os.getenv('SHEETS_ID')

        if not sheet_id:
            raise ValueError("SHEETS_ID is needed")

        return cls(
            credentials_path=credentials_path,
            sheet_id=sheet_id
        )


@dataclass
class ShopifyConfig:
    """Shopify config"""
    shop_url: str
    access_token: str
    api_version: str = "2024-01"

    @classmethod
    def from_env(cls) -> 'ShopifyConfig':
        shop_url = os.getenv('SHOPIFY_SHOP_URL')
        access_token = os.getenv('SHOPIFY_ACCESS_TOKEN')

        if not shop_url or not access_token:
            raise ValueError("SHOPIFY_SHOP_URL and SHOPIFY_ACCESS_TOKEN are requiered")

        return cls(
            shop_url=shop_url,
            access_token=access_token,
            api_version=os.getenv('SHOPIFY_API_VERSION', '2024-01')
        )


@dataclass
class AppConfig:
    """General config"""
    environment: str
    debug: bool
    log_level: str
    sync_interval: int
    database: DatabaseConfig
    google_sheets: GoogleSheetsConfig
    shopify: ShopifyConfig

    @classmethod
    def from_env(cls) -> 'AppConfig':
        environment = os.getenv('ENVIRONMENT', 'development')

        return cls(
            environment=environment,
            debug=os.getenv('DEBUG', 'False').lower() == 'true',
            log_level=os.getenv('LOG_LEVEL', 'INFO'),
            sync_interval=int(os.getenv('SYNC_INTERVAL', '30')),
            database=DatabaseConfig.from_env(),
            google_sheets=GoogleSheetsConfig.from_env(),
            shopify=ShopifyConfig.from_env()
        )


def validate_config():
    """Checks all env are configured"""
    required_vars = [
        'DB_HOST', 'DB_PORT', 'DB_NAME', 'DB_USER', 'DB_PASSWORD', 'SHEETS_ID', 'SHOPIFY_SHOP_URL', 'SHOPIFY_ACCESS_TOKEN'
    ]
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)

    if missing_vars:
        raise ValueError(f"Missing env variable: {missing_vars}")

    print("Valid config")


# Calling for global configuration
config = AppConfig.from_env()

if __name__ == "__main__":
    validate_config()