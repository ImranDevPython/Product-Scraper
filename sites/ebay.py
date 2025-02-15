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
            await self.page.goto(search_url, wait_until='domcontentloaded', timeout=15000)
            await self.page.wait_for_selector("ul.srp-results", timeout=5000)
            
            # Extract all products in one JavaScript execution
            products = await self.page.evaluate(f"""
                () => {{
                    const products = [];
                    const containers = document.querySelectorAll('ul.srp-results li.s-item:nth-child(-n+{num_products + 5})');
                    
                    for (const container of containers) {{
                        try {{
                            const titleElem = container.querySelector('div.s-item__title span');
                            const priceElem = container.querySelector('span.s-item__price');
                            const urlElem = container.querySelector('a.s-item__link');
                            const sellerInfoElem = container.querySelector('span.s-item__seller-info-text');
                            
                            if (titleElem && priceElem && urlElem) {{
                                const sellerInfo = sellerInfoElem ? sellerInfoElem.textContent : '';
                                const feedbackMatch = sellerInfo.match(/\\(([\d,]+)\\)/);
                                const percentageMatch = sellerInfo.match(/([\d.]+)%/);
                                
                                products.push({{
                                    Name: titleElem.textContent.trim(),
                                    Price: priceElem.textContent.trim(),
                                    url: urlElem.href,
                                    Seller_username: sellerInfo ? sellerInfo.split(' ')[0] : 'Unknown',
                                    Positive_feedback_rating: feedbackMatch ? feedbackMatch[1] : 'No rating',
                                    Positive_feedback_percentage: percentageMatch ? percentageMatch[1] + '%' : 'No percentage'
                                }});
                            }}
                        }} catch (e) {{
                            continue;
                        }}
                    }}
                    
                    return products.slice(0, {num_products});
                }}
            """)
            
            return products
            
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
        
        try:
            # Extract everything in one JavaScript execution
            details = await self.page.evaluate("""
                () => {
                    const specs = {};
                    const features = [];
                    
                    // Get all specification sections
                    const sections = document.querySelectorAll("div[data-testid='ux-layout-section-evo__item'] dl[data-testid='ux-labels-values']");
                    sections.forEach(section => {
                        const labels = section.querySelectorAll("dt span.ux-textspans");
                        const values = section.querySelectorAll("dd span.ux-textspans");
                        
                        labels.forEach((label, index) => {
                            if (values[index]) {
                                const key = label.textContent.trim();
                                const value = values[index].textContent.trim();
                                
                                // Extract features but don't add to specs
                                if (key.toLowerCase() === 'features') {
                                    features.push(...value.split(',').map(f => f.trim()));
                                } else {
                                    specs[key] = value;
                                }
                            }
                        });
                    });
                    
                    return {
                        specifications: specs,
                        special_features: features
                    };
                }
            """)
            
            return details
            
        except Exception as e:
            print(f"Error extracting product details: {e}")
            return {"specifications": {}, "special_features": []}
