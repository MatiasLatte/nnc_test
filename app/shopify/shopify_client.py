import requests
import json
from config.config import config
from app.excel_sheets.sheets_client import ProductData

row = {
    'part_no': 'USB-C-001',
    'price': 14.99,
    'weight': 200,
    'tag': 'cable,usb',
    'collection': 'Cables'
}


#credentials
shop_url = config.shopify.shop_url
access_token = config.shopify.access_token
api_version = config.shopify.api_version

def post_product(product: ProductData):
    """ Turn it into shopify compatible"""
    shopify_product = {
        "product": {
            "title": product.part,
            "body_html": f"<strong>Part number: {product.part}</strong>",
            "vendor": "YourBrandName",  # Change to your real brand
            "product_type": product.collection,
            "tags": product.tag,
            "variants": [
                {
                    "price": f"{product.price:.2f}",
                    "sku": product.part,
                    "weight": product.weight,
                    "weight_unit": "g"
                }
            ]
        }
    }

    url = f"https://{shop_url}/admin/api/{api_version}/products.json"
    headers = {
        "Content-Type": "application/json",
        "X-Shopify-Access-Token": access_token
    }

    response = requests.post(url, headers=headers, data=json.dumps(shopify_product))

    if response.status_code == 201:
        print(f"Product '{product.part}' created successfully")
        return response.json()
    else:
        print(f"Failed to create '{product.part}': {response.status_code} - {response.text}")
        return None

if __name__ == "__main__":
    product = ProductData.from_row(row)
    post_product(product)
