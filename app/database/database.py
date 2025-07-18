import psycopg2
from config.config import config


def clean_price(price_value):
    """Clean and convert price"""
    if not price_value:
        return 0.0

    try:
        # Convert to string
        price_str = str(price_value).strip()

        # Remove currency symbols
        price_str = price_str.replace(',', '')
        price_str = price_str.replace(' ', '')
        price_str = price_str.replace('$', '')      # Regular dollar sign
        price_str = price_str.replace('$', '')      # Unicode dollar sign

        # handle empty string
        if not price_str:
            return 0.0

        # Convert to float
        return float(price_str)

    except (ValueError, TypeError) as e:
        print(f"Could not convert price '{price_value}'")
        return 0.0

def get_db_connection():
    """Get database connection"""
    try:
        conn = psycopg2.connect(
            host=config.database.host,
            port=config.database.port,
            database=config.database.database,
            user=config.database.user,
            password=config.database.password,
            sslmode=config.database.ssl_mode
        )
        return conn
    except Exception as e:
        print(f"Error connecting to database: {e}")
        raise


def setup_database():
    """Create tables if they don't exist"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Create products table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id SERIAL PRIMARY KEY,
            part_no VARCHAR(100) UNIQUE NOT NULL,
            price DECIMAL(10,2),
            weight INTEGER,
            tag TEXT,
            collection VARCHAR(100),
            shopify_id BIGINT,
            last_synced TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        conn.commit()
        cursor.close()
        conn.close()

        print("Database tables ready")
        return True

    except Exception as e:
        print(f"Error setting up database: {e}")
        return False


def save_product_to_db(product_data, shopify_id=None):
    """Save or update product in database"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        part_no = product_data.get('part_no', '')
        price = clean_price(product_data.get('price', 0))
        weight = int(float(product_data.get('weight', 0)))
        tag = product_data.get('tag', '')
        collection = product_data.get('collection', '')

        # Try to update first
        cursor.execute("""
                       UPDATE products
                       SET price       = %s,
                           weight      = %s,
                           tag         = %s,
                           collection  = %s,
                           shopify_id  = %s,
                           last_synced = CURRENT_TIMESTAMP
                       WHERE part_no = %s
                       """, (price, weight, tag, collection, shopify_id, part_no))

        if cursor.rowcount == 0:
            # Insert new
            cursor.execute("""
                           INSERT INTO products (part_no, price, weight, tag, collection, shopify_id)
                           VALUES (%s, %s, %s, %s, %s, %s)
                           """, (part_no, price, weight, tag, collection, shopify_id))

        conn.commit()
        cursor.close()
        conn.close()
        return True

    except Exception as e:
        print(f"Error saving product to database: {e}")
        return False

