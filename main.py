import asyncio
from playwright.async_api import async_playwright
from utils.browser import BrowserManager
from sites.amazon import AmazonScraper
from sites.ebay import EbayScraper
from sites.concurrent_search import search_all_sites
import time
from typing import List, Dict, Any, Type
from sites.base_scraper import BaseScraper
from colorama import init, Fore, Back, Style

# Initialize colorama
init(autoreset=True)

AVAILABLE_SITES = {
    "1": ("Amazon", AmazonScraper),
    "2": ("eBay", EbayScraper),
    "3": ("All Sites", None)  
}

async def initialize_browser():
    browser_manager = BrowserManager()
    playwright = await async_playwright().start()
    await browser_manager.init_browser(playwright)
    page = await browser_manager.new_page()
    return browser_manager, playwright, page

async def main(browser_manager, page):
    print(f"\n{Back.BLUE}{Fore.WHITE} === Starting optimized scraper === {Style.RESET_ALL}\n")
    start_time = time.time()

    # Get product search query
    query = input(f"{Fore.CYAN}Enter a product name to search: {Style.RESET_ALL}")
    
    # Show available sites
    print(f"\n{Fore.GREEN}Available Sites:{Style.RESET_ALL}")
    for key, (site_name, _) in AVAILABLE_SITES.items():
        print(f"{Fore.YELLOW}{key}. {site_name}{Style.RESET_ALL}")
    
    # Get site choice
    while True:
        choice = input(f"\n{Fore.CYAN}Choose a site (enter number) or 'all' for concurrent search: {Style.RESET_ALL}")
        if choice in AVAILABLE_SITES or choice.lower() == 'all':
            break
        print(f"{Fore.RED}Invalid choice. Please try again.{Style.RESET_ALL}")

    if choice.lower() == 'all' or choice == '3':
        print(f"\n{Fore.GREEN}Initializing browsers for concurrent search{Style.RESET_ALL}")
        results = await search_all_sites(browser_manager, query)
    else:
        site_name, scraper_class = AVAILABLE_SITES[choice]
        print(f"\n{Fore.GREEN}Initializing browser for {site_name}{Style.RESET_ALL}")
        scraper = scraper_class(page)
        results = await scraper.search_products(query)
        for product in results:
            product['site'] = site_name
        print(f"\n{Fore.GREEN}Search completed in {Fore.YELLOW}{time.time() - start_time:.2f}{Fore.GREEN} seconds{Style.RESET_ALL}")
    
    if not results:
        print(f"{Fore.RED}No products found!{Style.RESET_ALL}")
        return
    
    # Display results as they come
    print(f"\n{Fore.GREEN}Products Found:{Style.RESET_ALL}\n")
    for i, product in enumerate(results, 1):
        print(f"{Back.BLUE}{Fore.WHITE} Product {i}: {Style.RESET_ALL}")
        for key, value in product.items():
            if key != 'url':  # Don't print the long URL
                print(f"{Fore.YELLOW}{key}: {Style.RESET_ALL}{value}")
        print(f"{Fore.BLUE}{'-' * 80}{Style.RESET_ALL}\n")
    
    # Get user choice
    while True:
        try:
            choice = int(input(f"{Fore.CYAN}Enter the product number (1-{len(results)}) to see more details: {Style.RESET_ALL}"))
            if 1 <= choice <= len(results):
                break
            print(f"{Fore.RED}Invalid product number. Please enter a number between 1 and {len(results)}.{Style.RESET_ALL}")
        except ValueError:
            print(f"{Fore.RED}Please enter a valid number.{Style.RESET_ALL}")

    product = results[choice - 1]
    site = product.get('site')
    if site == 'Amazon':
        scraper = AmazonScraper(page)
    elif site == 'eBay':
        scraper = EbayScraper(page)
    else:
        print(f"{Fore.RED}No specific scraper available for displaying detailed product information.{Style.RESET_ALL}")
        return

    await display_product_details(scraper, results, choice - 1, start_time)

async def display_product_details(scraper: BaseScraper, products: List[Dict[str, Any]], choice: int, start_time: float):
    try:
        product = products[choice]
        
        details_start = time.time()
        details = await scraper.get_product_details(product['url'])
        print(f"\n{Fore.GREEN}Details fetched in {Fore.YELLOW}{time.time() - details_start:.2f}{Fore.GREEN} seconds{Style.RESET_ALL}\n")
        
        print(f"{Back.BLUE}{Fore.WHITE} Product Information: {Style.RESET_ALL}")
        print(f"{Fore.BLUE}{'-' * 80}{Style.RESET_ALL}")
        
        # Display all available product information
        if product.get('site') == 'eBay':
            # eBay-specific information display
            basic_info = {
                'Name': product['Name'],
                'Price': product['Price'],
                'Seller Username': product['Seller_username'],
                'Seller Record': product.get('Seller_record', 'Not available'),
                'Positive Feedback Rating': product['Positive_feedback_rating'],
                'Positive Feedback Percentage': product['Positive_feedback_percentage']
            }
        else:
            # Default/Amazon information display
            basic_info = {
                'Name': product['Name'],
                'Rating': product.get('Rating', 'Not available'),
                'Rating_count': product.get('Rating_count', 'Not available'),
                'Price': product['Price']
            }
        
        # Display basic information
        for key, value in basic_info.items():
            if value != 'Not available':
                print(f"{Fore.YELLOW}{key}: {Style.RESET_ALL}{value}")
        print()

        # Display specifications if available
        if details.get('specifications'):
            print(f"{Back.BLUE}{Fore.WHITE} Specifications: {Style.RESET_ALL}")
            for key, value in details['specifications'].items():
                print(f"{Fore.GREEN}{key}: {Style.RESET_ALL}{value}")
            print()

        # Display special features if available
        if details.get('special_features'):
            print(f"{Back.BLUE}{Fore.WHITE} Special Features: {Style.RESET_ALL}")
            for feature in details['special_features']:
                print(f"{Fore.GREEN}• {Style.RESET_ALL}{feature}")
            print()

    except Exception as e:
        print(f"{Fore.RED}Error displaying product details: {e}{Style.RESET_ALL}")
    finally:
        print(f"\n{Fore.GREEN}Total execution time: {Fore.YELLOW}{time.time() - start_time:.2f}{Fore.GREEN} seconds{Style.RESET_ALL}")

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    browser_manager, playwright, page = loop.run_until_complete(initialize_browser())
    try:
        loop.run_until_complete(main(browser_manager, page))
    finally:
        loop.run_until_complete(playwright.stop())  # Ensure playwright is properly closed
        loop.close()  # Close the event loop