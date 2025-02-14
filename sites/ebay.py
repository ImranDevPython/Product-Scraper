from typing import List, Dict, Any
from playwright.async_api import Page
from .base_scraper import BaseScraper
import re
import asyncio

class EbayScraper(BaseScraper):
    def __init__(self, page: Page):
        super().__init__(page)
        self.base_url = "https://www.ebay.com"

    @property
    def site_name(self) -> str:
        return "eBay"

    async def search_products(self, query: str, num_products: int = 3) -> List[Dict[str, Any]]:
        search_url = f"{self.base_url}/sch/i.html?_nkw={query}"
        
        try:
            await self.page.goto(search_url, wait_until='domcontentloaded', timeout=10000)
            
            # Use a more specific selector and limit initial query
            selector = "ul.srp-results li.s-item:nth-child(-n+" + str(num_products + 5) + ")"
            await self.page.wait_for_selector(selector, timeout=3000)
            
            # Get all product containers at once
            product_containers = await self.page.query_selector_all(selector)
            
            # Create tasks for all products concurrently
            tasks = [self._extract_product_data(container) for container in product_containers[:num_products + 5]]
            
            # Extract all products concurrently
            products = await asyncio.gather(*tasks)
            
            # Filter out None values and limit to requested number
            valid_products = [p for p in products if p][:num_products]
            
            return valid_products
            
        except Exception as e:
            print(f"Error accessing eBay: {e}")
            return []

    async def _extract_product_data(self, container) -> Dict[str, Any]:
        try:
            # Extract all elements concurrently
            title_task = container.query_selector("div.s-item__title span")
            price_task = container.query_selector("span.s-item__price")
            url_task = container.query_selector("a.s-item__link")
            seller_info_task = self._extract_seller_info(container)
            
            # Wait for all tasks to complete
            title_elem, price_elem, url_elem, seller_info = await asyncio.gather(
                title_task, price_task, url_task, seller_info_task
            )
            
            if not all([title_elem, price_elem, url_elem]):
                return None
            
            # Extract text content concurrently
            name_task = title_elem.text_content()
            price_task = price_elem.text_content()
            url_task = url_elem.get_attribute("href")
            
            name, price, url = await asyncio.gather(name_task, price_task, url_task)
            
            product = {
                "Name": name.strip(),
                "Price": price.strip(),
                "url": url
            }
            
            # Update with seller info
            product.update(seller_info)
            
            return product
            
        except Exception as e:
            return None

    async def _extract_seller_info(self, container):
        """Helper method to extract seller information"""
        try:
            seller_info = {}
            seller_info_element = await container.query_selector("span.s-item__seller-info-text")
            if seller_info_element:
                text = await seller_info_element.text_content()
                seller_info["Seller_username"] = text.split()[0] if text else "Unknown"
                
                feedback_rating = re.search(r"\(([\d,]+)\)", text)
                feedback_percentage = re.search(r"([\d.]+)%", text)
                
                seller_info["Positive_feedback_rating"] = feedback_rating.group(1) if feedback_rating else "No rating"
                seller_info["Positive_feedback_percentage"] = feedback_percentage.group(1) + "%" if feedback_percentage else "No percentage"
            
            return seller_info
        except Exception:
            return {
                "Seller_username": "Unknown",
                "Positive_feedback_rating": "No rating",
                "Positive_feedback_percentage": "No percentage"
            }

    async def get_product_details(self, url: str) -> Dict[str, Any]:
        await self.page.goto(url, wait_until='domcontentloaded')
        details = {"special_features": []}  # Initialize the special features list

        # Extract specifications
        spec_sections = await self.page.query_selector_all("div[data-testid='ux-layout-section-evo__item'] dl[data-testid='ux-labels-values']")
        specifications = {}
        for section in spec_sections:
            labels = await section.query_selector_all("dt span.ux-textspans")
            values = await section.query_selector_all("dd span.ux-textspans")

            for label, value in zip(labels, values):
                spec_key = await label.text_content()
                spec_value = await value.text_content()
                spec_key = spec_key.strip()
                spec_value = spec_value.strip()
                specifications[spec_key] = spec_value

                # Check if the label is 'features' and process it as special features
                if spec_key.lower() == 'features':
                    details['special_features'].extend([f.strip() for f in spec_value.split(',')])

        details['specifications'] = specifications

        return details
