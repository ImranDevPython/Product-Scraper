import asyncio
from playwright.async_api import async_playwright
from utils.browser import BrowserManager
from sites.amazon import AmazonScraper
from sites.ebay import EbayScraper
from sites.concurrent_search import search_all_sites
from typing import List, Dict, Any
from sites.base_scraper import BaseScraper
from colorama import init
from utils.print_utils import (
    print_header, print_available_sites, print_search_results,
    print_product_details, print_error, print_success, print_info,
    print_separator
)

# Initialize colorama
init(autoreset=True)

AVAILABLE_SITES = {
    "1": ("Amazon", AmazonScraper),
    "2": ("eBay", EbayScraper),
    "3": ("All Sites", None),
    "4": ("Change Number of Products", None)
}

async def initialize_browser():
    browser_manager = BrowserManager()
    playwright = await async_playwright().start()
    await browser_manager.init_browser(playwright)
    page = await browser_manager.new_page()
    return browser_manager, playwright, page

async def display_product_details(scraper: BaseScraper, products: List[Dict[str, Any]], choice: int):
    try:
        product = products[choice]
        details = await scraper.get_product_details(product['url'])
        print_product_details(product, details)
    except Exception as e:
        print_error(f"Error displaying product details: {e}")

async def main(browser_manager, page):
    while True:
        try:
            print_header()
            num_products = 3  # Default value
            
            while True:
                print_available_sites(AVAILABLE_SITES, num_products)
                choice = input("\nChoose an option: ")
                
                if choice == "4":
                    while True:
                        try:
                            num_input = input("Enter number of products to scrape (1-21): ")
                            new_num = int(num_input)
                            if 1 <= new_num <= 21:
                                num_products = new_num
                                print_success(f"Number of products updated to: {num_products}\n")
                                break
                            print_error("Please enter a number between 1 and 21.")
                        except ValueError:
                            print_error("Please enter a valid number.")
                elif choice in ["1", "2", "3"] or choice.lower() == 'all':
                    break
                else:
                    print_error("Invalid choice. Please try again.\n")

            query = input("Enter a product name to search: ")

            if choice.lower() == 'all' or choice == '3':
                print_success("Initializing browsers for concurrent search")
                results = await search_all_sites(browser_manager, query, num_products)
            else:
                site_name, scraper_class = AVAILABLE_SITES[choice]
                print_success(f"Initializing browser for {site_name}")
                scraper = scraper_class(page)
                results = await scraper.search_products(query, num_products)
                for product in results:
                    product['site'] = site_name

            if not results:
                print_error("No products found!")
                continue
            
            print_search_results(results)
            
            while True:
                try:
                    choice = int(input(f"Enter the product number (1-{len(results)}) to see more details: "))
                    if 1 <= choice <= len(results):
                        break
                    print_error(f"Invalid product number. Please enter a number between 1 and {len(results)}.")
                except ValueError:
                    print_error("Please enter a valid number.")

            product = results[choice - 1]
            site = product.get('site')
            if site == 'Amazon':
                scraper = AmazonScraper(page)
            elif site == 'eBay':
                scraper = EbayScraper(page)
            else:
                print_error("No specific scraper available for displaying detailed product information.")
                continue

            await display_product_details(scraper, results, choice - 1)

            while True:
                continue_choice = input("\nWould you like to perform another search? (y/N): ").lower()
                if continue_choice in ['y', 'n', '']:
                    break
                print_error("Please enter 'y' for yes or 'n' for no.")

            if continue_choice != 'y':
                print_success("\nThank you for using the scraper!")
                break

            print_separator()

        except Exception as e:
            print_error(f"An error occurred: {e}")
            break

if __name__ == "__main__":
    browser_manager = None
    playwright = None
    
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        browser_manager, playwright, page = loop.run_until_complete(initialize_browser())
        loop.run_until_complete(main(browser_manager, page))
        
    except Exception as e:
        print_error(f"Fatal error: {e}")
    finally:
        try:
            if browser_manager and playwright:
                loop.run_until_complete(browser_manager.close())
                loop.run_until_complete(playwright.stop())
            if loop:
                loop.run_until_complete(loop.shutdown_asyncgens())
                loop.close()
        except Exception as e:
            print_error(f"Error during cleanup: {e}")