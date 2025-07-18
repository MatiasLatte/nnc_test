import sys
from app.excel_sheets.sheets_client import create_sheets_client
from app.shopify.shopify_client import sync_sheets_to_shopify
from app.database.database import setup_database

CHECK_INTERVAL = 30

def sync_callback(sheet_products):
    """
    This function gets called whenever changes are detected in Google Sheets
    """
    print(f"CHANGES DETECTED! Found {len(sheet_products)} products in sheet")
    print("Starting automatic sync...")

    try:
        results = sync_sheets_to_shopify(sheet_products)

        # Show results
        print(f"\nAuto-sync complete!")
        print(f" Created: {results['created']}")
        print(f" Updated: {results['updated']}")
        print(f" Failed: {results['failed']}")
        print(f"️ Skipped: {results['skipped']}")

        if results['created'] > 0 or results['updated'] > 0:
            print(f" Successfully synced {results['created'] + results['updated']} products!")

        print(f"\n Continuing to monitor for changes...")

    except Exception as e:
        print(f" Auto-sync failed: {e}")
        print(f" Continuing to monitor for changes...")


def run_one_time_sync():
    """Run sync once and exit"""
    print("Product Sync - One-time sync")
    print("=" * 50)

    # Try to setup database
    print("Setting up database...")
    db_working = setup_database()

    if not db_working:
        print("Database is not available - continuing with Shopify sync only")

    try:
        # Get products from Google Sheets
        print("Getting products from Google Sheets...")
        sheets_client = create_sheets_client()
        sheet_products = sheets_client.get_all_products()

        if not sheet_products:
            print("No products found in Google Sheets!")
            return False

        print(f"Found {len(sheet_products)} products")

        # Sync to Shopify
        print("Syncing to Shopify...")
        results = sync_sheets_to_shopify(sheet_products)

        # Final results
        print(f"\n One-time sync complete!")
        print(f" Created: {results['created']}")
        print(f" Updated: {results['updated']}")
        print(f" Failed: {results['failed']}")
        print(f"️ Skipped: {results['skipped']}")

        return True

    except Exception as e:
        print(f" Error: {e}")
        return False


def run_continuous_monitoring():
    """Run continuous monitoring - watches for changes and syncs automatically"""
    print("Product Sync - Continuous Monitoring")
    print("=" * 60)

    # Try to setup database
    print("Setting up database...")
    db_working = setup_database()

    if not db_working:
        print("Database not available - continuing with Shopify sync only")

    try:
        print(" Setting up Google Sheets monitoring...")
        sheets_client = create_sheets_client()

        # Test initial connection
        initial_products = sheets_client.get_all_products()
        print(f" Connected! Found {len(initial_products)} products initially")

        print(f"\n Starting continuous monitoring...")
        print(f"   • Checking for changes every 30 seconds")
        print(f"   • Any changes in Google Sheets will automatically sync to Shopify")
        print(f"   • Press Ctrl+C to stop monitoring")
        print(f"=" * 60)

        # Start watching for changes
        # This will run forever until stoped
        sheets_client.watch_for_changes(
            callback_function=sync_callback,
            interval=CHECK_INTERVAL  # Check every 30 seconds
        )

    except KeyboardInterrupt:
        print(f"\n\nMonitoring stopped by user")

    except Exception as e:
        print(f"Monitoring error: {e}")


def main():
    """Main function with options"""
    print("Product Sync System")
    print("=" * 50)

    # Check command line arguments
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()

        if command == "sync":
            # One-time sync
            success = run_one_time_sync()
            sys.exit(0 if success else 1)

        elif command == "watch" or command == "monitor":
            # Continuous monitoring
            run_continuous_monitoring()
            sys.exit(0)

        else:
            print(f" Unknown command: {command}")
            print("Use 'python main.py help' to see available commands")
            sys.exit(1)
    else:
        # No command specified - ask user what they want
        print("What would you like to do?")
        print("1. Run one-time sync")
        print("2. Start continuous monitoring (recommended)")

        try:
            choice = input("\nChoice (1/2): ").strip()

            if choice == "1":
                success = run_one_time_sync()
                sys.exit(0 if success else 1)
            elif choice == "2":
                run_continuous_monitoring()
                sys.exit(0)
            else:
                print("Invalid choice")
                sys.exit(1)

        except KeyboardInterrupt:
            print("\n\n Goodbye!")
            sys.exit(0)


if __name__ == "__main__":
    main()