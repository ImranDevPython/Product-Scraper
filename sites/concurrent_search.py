from .amazon import AmazonScraper
from .ebay import EbayScraper
import asyncio

async def search_all_sites(browser_manager, query):
    # Initialize both scrapers with a new page from the browser manager
    amazon_scraper = AmazonScraper(await browser_manager.new_page())
    ebay_scraper = EbayScraper(await browser_manager.new_page())
    
    # Start both searches concurrently
    amazon_future = amazon_scraper.search_products(query)
    ebay_future = ebay_scraper.search_products(query)
    
    # Wait for both to complete
    amazon_results, ebay_results = await asyncio.gather(amazon_future, ebay_future)
    
    # Tag results with their respective site
    for product in amazon_results:
        product['site'] = 'Amazon'
    for product in ebay_results:
        product['site'] = 'eBay'
    
    # Combine results
    return amazon_results + ebay_results
