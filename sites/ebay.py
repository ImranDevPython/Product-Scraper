from typing import List, Dict, Any
from playwright.async_api import Page
from .base_scraper import BaseScraper
import re

class EbayScraper(BaseScraper):
    def __init__(self, page: Page):
        super().__init__(page)
        self.base_url = "https://www.ebay.com"

    @property
    def site_name(self) -> str:
        return "eBay"

    async def search_products(self, query: str) -> List[Dict[str, Any]]:
        search_url = f"{self.base_url}/sch/i.html?_nkw={query}"
        await self.page.goto(search_url, wait_until='domcontentloaded')

        products = []
        product_containers = await self.page.query_selector_all("div#srp-river-results ul.srp-results.srp-list.clearfix > li:not(.srp-river-answer)")
        
        for index, container in enumerate(product_containers):
            if index >= 3:  # Limit to first 3 products
                break

            title_element = await container.query_selector("div.s-item__title span[role='heading'][aria-level='3']")
            price_element = await container.query_selector("span.s-item__price")
            url_element = await container.query_selector("a.s-item__link")
            seller_record_element = await container.query_selector("span.s-item__etrs-text")
            seller_info_element = await container.query_selector("span.s-item__seller-info-text")

            title = await title_element.text_content() if title_element else "No title"
            price = await price_element.text_content() if price_element else "No price"
            url = await url_element.get_attribute("href") if url_element else "No URL"
            seller_record = await seller_record_element.text_content() if seller_record_element else None
            seller_info_text = await seller_info_element.text_content() if seller_info_element else ""

            # Extract seller username, feedback rating, and feedback percentage
            seller_username = seller_info_text.split()[0] if seller_info_text else "Unknown"
            feedback_rating = re.search(r"\(([\d,]+)\)", seller_info_text)
            feedback_percentage = re.search(r"([\d.]+)%", seller_info_text)

            feedback_rating = feedback_rating.group(1) if feedback_rating else "No rating"
            feedback_percentage = feedback_percentage.group(1) + "%" if feedback_percentage else "No percentage"

            products.append({
                "name": title.strip(),
                "price": price.strip(),
                "url": url,
                "seller_record": seller_record,
                "seller_username": seller_username,
                "positive_feedback_rating": feedback_rating,
                "positive_feedback_percentage": feedback_percentage
            })


        return products

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
