"""
Debug script to test your sync components
"""

from app.excel_sheets.sheets_client import create_sheets_client
from app.shopify.shopify_client import get_all_shopify_products
from collections import Counter


def test_everything():
    print("🔍 DEBUGGING YOUR SYNC")
    print("=" * 50)

    # Test Google Sheets
    print("\n1. 📊 Testing Google Sheets...")
    sheets_client = create_sheets_client()
    sheet_products = sheets_client.get_all_products()

    print(f"   Total products from sheets: {len(sheet_products)}")

    # Check for duplicates in sheets
    part_numbers = [p.get('part_no', '') for p in sheet_products]
    duplicates = [part for part, count in Counter(part_numbers).items() if count > 1]

    if duplicates:
        print(f"   ⚠️ DUPLICATES FOUND in sheets: {duplicates}")
    else:
        print("   ✅ No duplicates in sheets")

    # Test Shopify
    print("\n2. 🛍️ Testing Shopify...")
    shopify_products = get_all_shopify_products()
    print(f"   Total products from Shopify: {len(shopify_products)}")

    if len(shopify_products) == 0:
        print("   ⚠️ WARNING: Getting 0 products from Shopify!")
        print("   This means duplicate checking won't work!")

    # Show first few products from each
    print(f"\n3. 📋 Sample Data:")
    print("   First 3 products from sheets:")
    for i, product in enumerate(sheet_products[:3]):
        print(f"      {i + 1}. {product.get('part_no', 'NO_PART_NO')} - ${product.get('price', '0')}")

    if shopify_products:
        print("   First 3 products from Shopify:")
        for i, product in enumerate(shopify_products[:3]):
            title = product.get('title', 'No title')
            sku = product['variants'][0].get('sku', 'No SKU') if product.get('variants') else 'No variants'
            print(f"      {i + 1}. {title} (SKU: {sku})")


if __name__ == "__main__":
    test_everything()