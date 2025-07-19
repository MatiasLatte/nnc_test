import time
import re
from typing import Dict
import random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException

VENDOR_URL = "https://www.voipsupply.com"

def setup_driver():
    """Setup Chrome"""
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')

    try:
        driver = webdriver.Chrome(options=options)
        return driver
    except Exception as e:
        print(f"Error setting up Chrome driver: {e}")
        print("Make sure ChromeDriver is installed")
        return None


def search_sku_price(sku: str) -> Dict:
    """
    Search for SKU in vendor website using Selenium and return price
    Returns: {"sku": str, "price": float, "found": bool, "title": str}
    """
    driver = None
    try:
        print(f"Searching for: {sku}")

        driver = setup_driver()
        if not driver:
            return {
                "sku": sku,
                "price": 0.0,
                "found": False,
                "title": "Driver error"
            }

        base_url = VENDOR_URL
        driver.get(base_url)

        time.sleep(random.uniform(2, 3))


        try:
            search_selectors = [
                'input[name="q"]',
                'input[type="search"]',
                '#search',
                '.search-input',
                'input[placeholder*="search" i]'
            ]

            search_box = None
            for selector in search_selectors:
                try:
                    search_box = WebDriverWait(driver, 5).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    break
                except TimeoutException:
                    continue

            if not search_box:
                print(f"Could not find search box for {sku}")
                return {
                    "sku": sku,
                    "price": 0.0,
                    "found": False,
                    "title": "Search box not found"
                }


            search_box.clear()
            search_box.send_keys(sku)
            search_box.send_keys(Keys.ENTER)

            # Wait for search results
            time.sleep(random.uniform(2, 4))

            # Look for price and title on the page
            price = find_price_on_page(driver)
            title = find_title_on_page(driver, sku)

            if price > 0:
                print(f" Found {sku}: ${price:.2f}")
                return {
                    "sku": sku,
                    "price": price,
                    "found": True,
                    "title": title
                }
            else:
                print(f" Price not found for: {sku}")
                return {
                    "sku": sku,
                    "price": 0.0,
                    "found": False,
                    "title": title if title != f"Product {sku}" else "Not found"
                }

        except TimeoutException:
            print(f" Timeout searching for {sku}")
            return {
                "sku": sku,
                "price": 0.0,
                "found": False,
                "title": "Timeout"
            }

    except Exception as e:
        print(f"Error searching {sku}: {e}")
        return {
            "sku": sku,
            "price": 0.0,
            "found": False,
            "title": "Error"
        }
    finally:
        if driver:
            driver.quit()


def find_price_on_page(driver) -> float:
    """Find price on the page using Selenium"""

    price_selectors = [
        'span.price',
        '.price',
        '.regular-price',
        '.special-price',
        '.product-price',
        '[class*="price"]',
        '[data-price]'
    ]

    for selector in price_selectors:
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            for element in elements:
                price_text = element.text.strip()
                price = clean_price(price_text)
                if price > 0:
                    return price

                price_data = element.get_attribute('data-price')
                if price_data:
                    price = clean_price(price_data)
                    if price > 0:
                        return price
        except NoSuchElementException:
            continue

    # If no specific price element, look for $ in page text
    try:
        page_text = driver.find_element(By.TAG_NAME, "body").text
        dollar_matches = re.findall(r'\$\s*(\d+(?:,\d{3})*(?:\.\d{2})?)', page_text)

        for match in dollar_matches:
            price = clean_price(match)
            if price > 0:
                return price
    except:
        pass

    return 0.0


def find_title_on_page(driver, sku: str) -> str:
    """Find product title on page using Selenium"""

    # Primary title selector
    title_selectors = [
        'span.base[data-ui-id="page-title-wrapper"]',
        'h1',
        '.product-name',
        '.product-title',
        '.page-title',
        '[data-ui-id="page-title-wrapper"]'
    ]

    for selector in title_selectors:
        try:
            element = driver.find_element(By.CSS_SELECTOR, selector)
            title = element.text.strip()
            if title and len(title) > 0:
                return title[:100]  # Limit length
        except NoSuchElementException:
            continue

    # Try page title as fallback
    try:
        title = driver.title
        if title and len(title) > 0:
            return title[:100]
    except:
        pass

    return f"Product {sku}"


def clean_price(price_text: str) -> float:
    """Convert price text to float"""
    try:
        if not price_text:
            return 0.0

        # Remove everything except digits, commas, and periods
        cleaned = re.sub(r'[^\d.,]', '', str(price_text))

        if not cleaned:
            return 0.0


        if ',' in cleaned:
            cleaned = cleaned.replace(',', '')

        return float(cleaned)

    except (ValueError, TypeError):
        return 0.0


def batch_search_products(skus: list) -> list:
    """Search for multiple SKUs and return results"""
    results = []
    total = len(skus)

    print(f"Starting batch search for {total} products...")

    for i, sku in enumerate(skus, 1):
        print(f"\n[{i}/{total}] Processing: {sku}")

        try:
            result = search_sku_price(sku)
            results.append(result)
        except Exception as e:
            print(f"Error processing {sku}: {e}")
            results.append({
                "sku": sku,
                "price": 0.0,
                "found": False,
                "title": "Error"
            })

        # Progress update every 10 items
        if i % 10 == 0:
            found_count = sum(1 for r in results if r['found'])
            print(f"Progress: {i}/{total} ({found_count} found)")

    found_count = sum(1 for r in results if r['found'])
    print(f"\nBatch search complete: {found_count}/{total} products found")

    return results
