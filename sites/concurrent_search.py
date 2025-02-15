from .amazon import AmazonScraper
from .ebay import EbayScraper
import asyncio

async def search_all_sites(browser_manager, query, num_products):
    amazon_page = None
    ebay_page = None
    
    try:
        # Initialize both scrapers with a new page from the browser manager
        amazon_page = await browser_manager.new_page()
        ebay_page = await browser_manager.new_page()
        
        amazon_scraper = AmazonScraper(amazon_page)
        ebay_scraper = EbayScraper(ebay_page)
        
        # Start both searches concurrently
        amazon_future = amazon_scraper.search_products(query, num_products)
        ebay_future = ebay_scraper.search_products(query, num_products)
        
        # Wait for both to complete with timeout
        amazon_results, ebay_results = await asyncio.gather(
            amazon_future, 
            ebay_future,
            return_exceptions=True
        )
        
        # Handle potential exceptions
        final_amazon_results = []
        final_ebay_results = []
        
        if isinstance(amazon_results, Exception):
            print(f"Error fetching Amazon results: {amazon_results}")
        else:
            final_amazon_results = amazon_results
            
        if isinstance(ebay_results, Exception):
            print(f"Error fetching eBay results: {ebay_results}")
        else:
            final_ebay_results = ebay_results
        
        # Tag results with their respective site
        for product in final_amazon_results:
            product['site'] = 'Amazon'
        for product in final_ebay_results:
            product['site'] = 'eBay'
        
        return final_amazon_results + final_ebay_results
        
    except Exception as e:
        print(f"Error in concurrent search: {e}")
        return []
    finally:
        # Clean up pages
        if amazon_page:
            try:
                await amazon_page.close()
            except:
                pass
        if ebay_page:
            try:
                await ebay_page.close()
            except:
                pass
