import random
from typing import List, Optional, Pattern
import re
from playwright.async_api import Browser, BrowserContext, Page, Playwright, Route, Request
import asyncio


USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
]

# Update resource patterns for both search and product pages
ALLOWED_RESOURCES = {
    # Core HTML and data
    'core_html': r'amazon\.com/(s\?|dp/|gp/)',
    
    # Essential CSS bundles
    'core_css': r'(m\.media-amazon|images-na\.ssl-images-amazon)\.com/images/[I|G]/.*?(AmazonUI|NavDesktop|ProductUI|SearchAssets)',
    
    # Critical JS for functionality
    'core_js': r'(m\.media-amazon|images-na\.ssl-images-amazon)\.com/images/[I|G]/.*?(ProductUI|AmazonRush|SearchAssets)',
    
    # Essential API calls
    'api_calls': r'(completion|unagi-na|fls-na)\.amazon\.com/|amazon\.com/(gp/product/ajax|conversion|api)',
    
    # Product-specific resources
    'product': r'amazon\.com/(dp/|gp/product|product-reviews)',
    
    # Minimum required for page structure
    'essential': r'amazon\.com/(images/G/01/AUIClients|ss/|gp/)'
}

# Specific elements we need
REQUIRED_SELECTORS = [
    '#productTitle',
    '#price',
    '#productDetails_techSpec_section_1',
    '#feature-bullets',
    '#acrCustomerReviewText',
    '.s-desktop-width-max'  # Search results container
]

class BrowserManager:
    def __init__(self):
        self.browser = None
        self.context = None
        self.playwright = None
        self.allowed_patterns = {
            category: re.compile(pattern, re.IGNORECASE) 
            for category, pattern in ALLOWED_RESOURCES.items()
        }
        self.route_handlers = []  # Track route handlers
    
    async def __aenter__(self):
        """Async context manager entry"""
        from playwright.async_api import async_playwright
        self.playwright = await async_playwright().start()
        await self.init_browser(self.playwright)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()

    async def init_browser(self, playwright: Playwright):
        """Initialize browser with custom settings"""
        print("Initializing optimized browser...")
        self.browser = await playwright.chromium.launch(
            headless=True,
        )
        
        self.context = await self.browser.new_context(
            user_agent=USER_AGENTS[0],
            viewport={'width': 1920, 'height': 1080},
        )
        
        # Set up route handler
        print("Setting up route handler...")
        await self._setup_route_handler()
        print("Resource whitelist initialized")

    async def _setup_route_handler(self):
        """Set up route handler to block unnecessary resources"""
        async def route_handler(route: Route, request: Request):
            try:
                if request.resource_type == 'document':
                    await route.continue_()
                elif request.resource_type in ['script', 'stylesheet']:
                    if 'search' in request.url or 'product' in request.url:
                        await route.continue_()
                    else:
                        await route.abort()
                elif request.resource_type in ['image', 'media', 'font']:
                    await route.abort()
                else:
                    await route.continue_()
            except Exception as e:
                print(f"Error in route handler: {e}")
                try:
                    await route.continue_()
                except:
                    pass

        # Store handler reference
        self.route_handlers.append(route_handler)
        await self.context.route('**/*', route_handler)

    async def new_page(self) -> Page:
        """Create and return a new page"""
        return await self.context.new_page()

    async def close(self):
        """Close all browser resources"""
        try:
            # Unroute all handlers
            if self.context and self.route_handlers:
                for handler in self.route_handlers:
                    try:
                        await self.context.unroute('**/*', handler)
                    except Exception as e:
                        print(f"Error unrouting handler: {e}")

            # Close context and browser
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
        except Exception as e:
            print(f"Error during browser cleanup: {e}") 