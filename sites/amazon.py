from typing import List, Dict, Any
from playwright.async_api import Page
import asyncio
from urllib.parse import quote
from .base_scraper import BaseScraper

class AmazonScraper(BaseScraper):
    def __init__(self, page: Page):
        super().__init__(page)
        self.base_url = "https://www.amazon.com"

    @property
    def site_name(self) -> str:
        return "Amazon"

    async def search_products(self, query: str) -> List[Dict[str, Any]]:
        search_url = f"{self.base_url}/s?k={quote(query)}"
        
        # Use 'commit' for fastest initial load
        await self.page.goto(search_url, wait_until='commit')
        
        products = []
        try:
            # Wait for the grid container
            await self.page.wait_for_selector(".s-desktop-width-max", timeout=5000)

            # Get all product cards at once
            cards = await self.page.query_selector_all('div[data-asin]:not([data-asin=""])')
            
            # Process first 3 valid products
            count = 0
            for card in cards:
                if count >= 3:
                    break
                    
                try:
                    product = await self._extract_product_data(card)
                    if product and product['url']:  # Only add valid products
                        products.append(product)
                        count += 1
                except Exception as e:
                    print(f"Error extracting product: {e}")
                    continue
                
        except Exception as e:
            print(f"Error in search: {e}")
            
        return products

    async def _extract_product_data(self, card) -> Dict[str, Any]:
        try:
            # Attempt to extract using the first selector
            name_elem = await card.query_selector("h2.a-size-medium.a-text-normal, h2.a-size-medium.a-text-normal > span")
            if not name_elem:
                # If the first selector fails, try the second selector
                name_elem = await card.query_selector("h2.a-size-base-plus, h2.a-size-base-plus > span")

            rating_elem = await card.query_selector("span.a-icon-alt")
            rating_count_elem = await card.query_selector("span.a-size-base")
            price_elem = await card.query_selector("span.a-price > span.a-offscreen")
            url_elem = await card.query_selector("a[href*='/dp/']")

            # Extract text content and attributes
            name = await name_elem.get_attribute("aria-label") if name_elem else await name_elem.text_content()
            name = name.strip() if name else "N/A"
            rating = await rating_elem.text_content() if rating_elem else "N/A"
            rating_count = await rating_count_elem.text_content() if rating_count_elem else "N/A"
            price = await price_elem.text_content() if price_elem else "N/A"
            url = await url_elem.get_attribute("href") if url_elem else None

            if url:
                url = f"{self.base_url}{url}" if url.startswith('/') else url

            return {
                "Name": name,
                "Rating": rating.strip(),
                "Rating_count": rating_count.strip(),
                "Price": price.strip(),
                "url": url
            }
        except Exception as e:
            print(f"Error extracting product data: {e}")
            return None

    async def get_product_details(self, url: str) -> Dict[str, Any]:
        # Use 'commit' for fastest initial load
        await self.page.goto(url, wait_until='commit')
        
        details = {}
        
        try:
            # Extract only specifications and features in parallel
            specs_task = asyncio.create_task(self._extract_specifications())
            features_task = asyncio.create_task(self._extract_features())
            
            # Wait for both tasks with timeout
            specs, features = await asyncio.gather(
                specs_task,
                features_task,
                return_exceptions=True
            )
            
            if not isinstance(specs, Exception):
                details['specifications'] = specs
            if not isinstance(features, Exception):
                details['special_features'] = features
                
        except Exception as e:
            print(f"Error extracting product details: {e}")
            
        return details
    
    async def _extract_basic_info(self) -> Dict[str, str]:
        info = {}
        
        # Wait for title with short timeout
        try:
            name_elem = await self.page.wait_for_selector('h2.a-size-medium.a-text-normal, h2.a-size-medium.a-text-normal > span', timeout=3000)
            if name_elem:
                info['Name'] = (await name_elem.text_content()).strip()
        except:
            pass
        
        # Get other basic elements if available
        for selector, key in [
            ("span.a-icon-alt", 'Rating'),
            ("#acrCustomerReviewText", 'Rating_count'),
            ("span.a-price > span.a-offscreen", 'Price')
        ]:
            try:
                elem = await self.page.query_selector(selector)
                if elem:
                    info[key] = (await elem.text_content()).strip()
            except:
                pass
            
        return info
    
    async def _extract_specifications(self) -> Dict[str, str]:
        specs = {}
        try:
            print("Extracting specifications...")
            # Wait for specifications section
            await self.page.wait_for_selector('table.a-normal.a-spacing-micro', timeout=5000)
            
            # Get all specification rows
            rows = await self.page.query_selector_all('tr.a-spacing-small')
            print(f"Found {len(rows)} specification rows")
            
            for row in rows:
                try:
                    label_elem = await row.query_selector('td span.a-text-bold')
                    value_elem = await row.query_selector('td span.po-break-word')
                    if label_elem and value_elem:
                        label = (await label_elem.text_content()).strip()
                        value = (await value_elem.text_content()).strip()
                        specs[label] = value
                except Exception as e:
                    print(f"Error extracting spec row: {e}")
                    continue
                    
        except Exception as e:
            print(f"Error extracting specifications: {e}")
            
        return specs
    
    async def _extract_features(self) -> List[str]:
        features = []
        try:
            print("Extracting features...")
            # Wait for features section
            await self.page.wait_for_selector('#feature-bullets', timeout=5000)
            
            # Get all feature items
            feature_items = await self.page.query_selector_all('#feature-bullets ul li span.a-list-item')
            print(f"Found {len(feature_items)} feature items")
            
            for item in feature_items:
                try:
                    text = (await item.text_content()).strip()
                    if text and not text.startswith('›'):  # Skip navigation items
                        features.append(text)
                except Exception as e:
                    print(f"Error extracting feature item: {e}")
                    continue
                    
        except Exception as e:
            print(f"Error extracting features: {e}")
            
        return features 