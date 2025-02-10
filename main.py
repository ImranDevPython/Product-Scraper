import asyncio
from playwright.async_api import async_playwright
from utils.browser import BrowserManager
from sites.amazon import AmazonScraper
import time
from typing import List, Dict, Any, Type
from sites.base_scraper import BaseScraper

AVAILABLE_SITES = {
    "1": ("Amazon", AmazonScraper),
    # "2": ("eBay", EbayScraper),  # Will add later
    # "3": ("All Sites", None)      # For concurrent search
}

async def initialize_browser():
    browser_manager = BrowserManager()
    playwright = await async_playwright().start()
    await browser_manager.init_browser(playwright)
    page = await browser_manager.new_page()
    return browser_manager, playwright, page

async def main():
    print("\n=== Starting optimized scraper ===\n")
    start_time = time.time()

    # Get product search query
    query = input("Enter a product name to search: ")
    
    # Show available sites
    print("\nAvailable Sites:")
    for key, (site_name, _) in AVAILABLE_SITES.items():
        print(f"{key}. {site_name}")
    
    # Get site choice
    while True:
        choice = input("\nChoose a site (enter number) or 'all' for concurrent search: ")
        if choice in AVAILABLE_SITES or choice.lower() == 'all':
            break
        print("Invalid choice. Please try again.")

    async with BrowserManager() as browser_manager:
        if choice.lower() == 'all':
            # Will implement concurrent search later
            results = await search_all_sites(browser_manager, query)
        else:
            # Single site search
            site_name, scraper_class = AVAILABLE_SITES[choice]
            print("\nInitializing browser for", site_name)
            scraper = scraper_class(await browser_manager.new_page())
            
            # Measure search time
            search_start = time.time()
            results = await scraper.search_products(query)
            print(f"\nSearch completed in {time.time() - search_start:.2f} seconds")
            
        if not results:
            print("No products found!")
            return
        
        # Display results as they come
        print("\nProducts Found:\n")
        for i, product in enumerate(results, 1):
            print(f"Product {i}:")
            for key, value in product.items():
                if key != 'url':  # Don't print the long URL
                    print(f"{key}: {value}")
            print("-" * 80 + "\n")
        
        # Get user choice
        while True:
            try:
                choice = int(input(f"Enter the product number (1-{len(results)}) to see more details: "))
                if 1 <= choice <= len(results):
                    break
                print(f"Please enter a number between 1 and {len(results)}")
            except ValueError:
                print("Please enter a valid number.")
        
        # Display product details
        await display_product_details(scraper, results, choice, start_time)

async def display_product_details(scraper: BaseScraper, products: List[Dict[str, Any]], choice: int, start_time: float):
    try:
        product = products[choice - 1]
        
        details_start = time.time()
        details = await scraper.get_product_details(product['url'])
        print(f"\nDetails fetched in {time.time() - details_start:.2f} seconds\n")
        
        print("Product Information:")
        print("-" * 80)
        print(f"name: {product['name']}")
        print(f"rating: {product['rating']}")
        print(f"rating_count: {product.get('rating_count', 'Not available')}")
        print(f"price: {product['price']}\n")

        if details.get('specifications'):
            print("Specifications:")
            for key, value in details['specifications'].items():
                print(f"{key}: {value}")
            print()

        if details.get('special_features'):
            print("Special Features:")
            for feature in details['special_features']:
                print(f"• {feature}")
            print()

    except Exception as e:
        print(f"Error displaying product details: {e}")
    finally:
        print(f"\nTotal execution time: {time.time() - start_time:.2f} seconds")

if __name__ == "__main__":
    asyncio.run(main()) 