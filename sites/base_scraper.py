from abc import ABC, abstractmethod
from typing import List, Dict, Any
from playwright.async_api import Page

class BaseScraper(ABC):
    """Base class for all e-commerce site scrapers"""
    
    def __init__(self, page: Page):
        self.page = page
        self.base_url = ""  # Each site will set its own base URL
        
    @abstractmethod
    async def search_products(self, query: str, num_products: int = 3) -> List[Dict[str, Any]]:
        """Search for products and return specified number of valid results"""
        pass
        
    @abstractmethod
    async def get_product_details(self, url: str) -> Dict[str, Any]:
        """Get detailed information about a specific product"""
        pass

    @property
    @abstractmethod
    def site_name(self) -> str:
        """Return the name of the e-commerce site"""
        pass 