import requests
import json
from config.config import config
import time
from app.database.database import save_product_to_db, clean_price


#credentials
shop_url = config.shopify.shop_url
access_token = config.shopify.access_token
api_version = config.shopify.api_version

#Global variables
HEADERS = {
    "Content-Type": "application/json",
    "X-Shopify-Access-Token": access_token
}
URL = f"https://{shop_url}/admin/api/{api_version}/products.json"


def create_shopify_product(sheet_row):
    """Create a new product in Shopify from sheet data"""
    try:
        part_no = sheet_row.get('part_no', '')
        price = clean_price(sheet_row.get('price', 0))
        weight = int(float(sheet_row.get('weight', 0)))
        tag = sheet_row.get('tag', '')
        collection = sheet_row.get('collection', '')

        # Create product data
        product_data = {
            "product": {
                "title": part_no,
                "body_html": f"<strong>Part Number:</strong> {part_no}",
                "vendor": "VOIP Supply",
                "product_type": collection,
                "tags": tag,
                "variants": [
                    {
                        "price": f"{price:.2f}",
                        "sku": part_no,
                        "weight": weight,
                        "weight_unit": "g"
                    }
                ]
            }
        }

        response = requests.post(URL, headers=HEADERS, data=json.dumps(product_data))

        if response.status_code == 201:
            # Get Shopify product ID and save to database
            product_result = response.json()
            shopify_id = product_result['product']['id']
            save_product_to_db(sheet_row, shopify_id)
            print(f"Product '{part_no}' created successfully")
            return True
        else:
            print(f"Failed to create '{part_no}': {response.status_code} - {response.text}")
            return None

    except Exception as e:
        print(f"Error creating {sheet_row.get('part_no', 'Unknown')}: {e}")
        return False

def update_shopify_product(product_id, sheet_row):
    """Update existing product in Shopify"""
    try:
        part_no = sheet_row.get('part_no', '')
        price = clean_price(sheet_row.get('price', 0))
        weight = int(float(sheet_row.get('weight', 0)))
        tag = sheet_row.get('tag', '')
        collection = sheet_row.get('collection', '')


        # Get current product to find variant ID
        product_url = f"https://{shop_url}/admin/api/{api_version}/products/{product_id}.json"
        response = requests.get(product_url, headers=HEADERS)

        if response.status_code != 200:
            print(f"Can't get product {product_id} for update")
            return False

        current_product = response.json()['product']
        variant_id = current_product['variants'][0]['id']

        # Update product
        update_data = {
            "product": {
                "id": product_id,
                "title": part_no,
                "body_html": f"<strong>Part Number:</strong> {part_no}",
                "product_type": collection,
                "tags": tag,
            }
        }

        response = requests.put(product_url, headers=HEADERS, data=json.dumps(update_data))

        if response.status_code == 200:
            # Update variant price and weight
            variant_data = {
                "variant": {
                    "id": variant_id,
                    "price": f"{price:.2f}",
                    "weight": weight,
                    "sku": part_no
                }
            }

            variant_url = f"https://{shop_url}/admin/api/{api_version}/variants/{variant_id}.json"
            variant_response = requests.put(variant_url, headers=HEADERS, data=json.dumps(variant_data))

            if variant_response.status_code == 200:
                save_product_to_db(sheet_row, product_id)
                print(f"Updated: {part_no}")
                return True
            else:
                print(f"Failed to update variant for {part_no}")
                return False
        else:
            print(f"Failed to update {part_no}: {response.status_code}")
            return False

    except Exception as e:
        print(f" Error updating {sheet_row.get('part_no', 'Unknown')}: {e}")
        return False

def find_product_by_sku(sku, shopify_products):
    """Find a product in Shopify by SKU"""
    for product in shopify_products:
        for variant in product.get('variants', []):
            if variant.get('sku') == sku:
                return product
    return None

def get_all_shopify_products():
    """Get all products from Shopify"""
    print("Getting all products from Shopify")

    all_products = []

    try:
        # Debug the URL and headers
        url = f"https://{config.shopify.shop_url}/admin/api/{config.shopify.api_version}/products.json?limit=250"

        response = requests.get(url, headers=HEADERS)

        print(f"Response Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            products = data.get('products', [])
            all_products.extend(products)


        elif response.status_code == 400:
            print(f"Bad Request (400)")
            print(f"Response Text: {response.text}")

            # Try a different API version
            print("Trying with API version 2023-10...")
            url_v2 = f"https://{config.shopify.shop_url}/admin/api/2023-10/products.json?limit=250"
            response2 = requests.get(url_v2, headers=HEADERS)
            print(f"Version 2023-10 Status: {response2.status_code}")


        elif response.status_code == 401:
            print(f"Unauthorized (401) - Check access token")
            print(f"Response: {response.text}")

        elif response.status_code == 403:
            print(f"Forbidden (403) - Check API permissions")
            print(f"Response: {response.text}")

        else:
            print(f"Error {response.status_code}: {response.text}")

    except Exception as e:
        print(f"Exception: {e}")

    print(f"Found {len(all_products)} products")
    return all_products

def sync_sheets_to_shopify(sheet_products):
    """Main function to sync all products from sheets to Shopify"""
    print(f" Starting sync of {len(sheet_products)} products...")

    # Counters
    created = 0
    updated = 0
    failed = 0
    skipped = 0

    # Get existing Shopify products
    shopify_products = get_all_shopify_products()

    # Process each product from sheets
    for i, sheet_product in enumerate(sheet_products, 1):
        part_no = sheet_product.get('part_no', '')

        if not part_no:
            print(f"[{i}/{len(sheet_products)}] Skipping: No part number")
            skipped += 1
            continue

        print(f"\n[{i}/{len(sheet_products)}] Processing: {part_no}")

        # Check if product exists
        existing_product = find_product_by_sku(part_no, shopify_products)

        if existing_product:
            # Update existing
            if update_shopify_product(existing_product['id'], sheet_product):
                updated += 1
            else:
                failed += 1
        else:
            # Create new
            if create_shopify_product(sheet_product):
                created += 1
            else:
                failed += 1

        # Wait a bit to avoid hitting APIs request limit
        time.sleep(0.5)

    return {
        'created': created,
        'updated': updated,
        'failed': failed,
        'skipped': skipped
    }