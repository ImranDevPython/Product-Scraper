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

    async def search_products(self, query: str, num_products: int = 3) -> List[Dict[str, Any]]:
        search_url = f"{self.base_url}/s?k={quote(query)}"
        
        try:
            await self.page.goto(search_url, wait_until='domcontentloaded', timeout=15000)
            await self.page.wait_for_selector(".s-desktop-width-max, .s-error-card", timeout=5000)
            
            # Extract all products in one JavaScript execution
            products = await self.page.evaluate(f"""
                () => {{
                    const products = [];
                    const cards = document.querySelectorAll('div[data-asin]:not([data-asin=""]):nth-child(-n+{num_products + 10})');
                    
                    for (const card of cards) {{
                        try {{
                            if (card.querySelector('[data-component-type="sp-sponsored-result"]')) {{
                                continue;
                            }}
                            
                            const nameElem = card.querySelector('h2.a-size-medium.a-text-normal, h2.a-size-medium.a-text-normal > span') || 
                                           card.querySelector('h2.a-size-base-plus, h2.a-size-base-plus > span');
                            const ratingElem = card.querySelector('span.a-icon-alt');
                            const ratingCountElem = card.querySelector('span.a-size-base');
                            const priceElem = card.querySelector('span.a-price > span.a-offscreen');
                            const urlElem = card.querySelector('a[href*="/dp/"]');
                            
                            if (nameElem && urlElem) {{
                                products.push({{
                                    Name: (nameElem.getAttribute('aria-label') || nameElem.textContent).trim(),
                                    Rating: ratingElem ? ratingElem.textContent.trim() : 'N/A',
                                    Rating_count: ratingCountElem ? ratingCountElem.textContent.trim() : 'N/A',
                                    Price: priceElem ? priceElem.textContent.trim() : 'N/A',
                                    url: urlElem.href
                                }});
                            }}
                            
                            if (products.length >= {num_products}) {{
                                break;
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
            print(f"Error accessing Amazon: {e}")
            return []

    async def get_product_details(self, url: str) -> Dict[str, Any]:
        try:
            await self.page.goto(url, wait_until='domcontentloaded')
            
            details = await self.page.evaluate("""
                () => {
                    const specs = {};
                    const features = new Set();
                    
                    // Get specifications from the product details section
                    const specSelectors = [
                        '#productDetails_techSpec_section_1 tr',
                        '#productDetails_detailBullets_sections1 tr',
                        '#detailBullets_feature_div span.a-list-item'
                    ];
                    
                    specSelectors.forEach(selector => {
                        document.querySelectorAll(selector).forEach(row => {
                            try {
                                if (selector.includes('tr')) {
                                    const label = row.querySelector('th');
                                    const value = row.querySelector('td');
                                    if (label && value) {
                                        const labelText = label.textContent.trim().replace(/\\n/g, '').replace(/:/g, '');
                                        const valueText = value.textContent.trim().replace(/\\n/g, '');
                                        if (!labelText.includes('ASIN') && 
                                            !labelText.includes('Customer Reviews') && 
                                            !labelText.includes('Best Sellers Rank')) {
                                            specs[labelText] = valueText;
                                        }
                                    }
                                } else {
                                    const text = row.textContent.trim();
                                    if (text.includes(':')) {
                                        const [label, value] = text.split(':').map(s => s.trim());
                                        if (label && value && 
                                            !label.includes('ASIN') && 
                                            !label.includes('Customer Reviews') && 
                                            !label.includes('Best Sellers Rank')) {
                                            specs[label] = value;
                                        }
                                    }
                                }
                            } catch (e) {}
                        });
                    });
                    
                    // Get features from bullet points
                    document.querySelectorAll('#feature-bullets ul li span.a-list-item').forEach(item => {
                        const text = item.textContent.trim();
                        if (text && 
                            !text.startsWith('›') && 
                            text.length > 10 && 
                            !text.includes('Flash Player') &&
                            !text.includes('star') &&
                            !text.includes('Computers & Accessories') &&
                            !text.includes('Traditional Laptops')) {
                            features.add(text.replace(/\\s+/g, ' ')
                                           .replace(/\[\s+/g, '[')
                                           .replace(/\s+\]/g, ']'));
                        }
                    });
                    
                    return {
                        specifications: specs,
                        special_features: Array.from(features)
                    };
                }
            """)
            
            # Clean and sort features
            cleaned_features = []
            for feature in details['special_features']:
                if not any(x in feature.lower() for x in ['var', 'function', 'window', 'javascript']):
                    cleaned_features.append(feature)
            
            details['special_features'] = sorted(
                cleaned_features,
                key=lambda x: (not x.startswith('['), x)
            )
            
            return details
            
        except Exception as e:
            print(f"Error extracting product details: {e}")
            return {"specifications": {}, "special_features": []}

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