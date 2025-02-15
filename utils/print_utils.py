from colorama import Fore, Back, Style
from typing import Dict, List, Any
from sites.base_scraper import BaseScraper

def print_header():
    print(f"\n{Back.BLUE}{Fore.WHITE} === Starting optimized scraper === {Style.RESET_ALL}\n")

def print_available_sites(sites: Dict, num_products: int):
    print(f"{Fore.GREEN}Available Sites:{Style.RESET_ALL}")
    for key, (site_name, _) in sites.items():
        print(f"{Fore.YELLOW}{key}. {site_name}{Style.RESET_ALL}")
    print(f"\n{Fore.BLUE}Current number of products to scrape: {num_products}{Style.RESET_ALL}")

def print_search_results(results: List[Dict[str, Any]]):
    print(f"\n{Fore.GREEN}Products Found:{Style.RESET_ALL}\n")
    for i, product in enumerate(results, 1):
        print(f"{Back.BLUE}{Fore.WHITE} Product {i}: {Style.RESET_ALL}")
        for key, value in product.items():
            if key != 'url':  # Don't print the long URL
                print(f"{Fore.YELLOW}{key}: {Style.RESET_ALL}{value}")
        print(f"{Fore.BLUE}{'-' * 80}{Style.RESET_ALL}\n")

def print_product_details(product: Dict[str, Any], details: Dict[str, Any]):
    print(f"\n{Back.BLUE}{Fore.WHITE} Product Information: {Style.RESET_ALL}")
    print(f"{Fore.BLUE}{'-' * 80}{Style.RESET_ALL}")
    
    # Display basic information
    if product.get('site') == 'eBay':
        basic_info = {
            'Name': product['Name'],
            'Price': product['Price'],
            'Seller Username': product['Seller_username'],
            'Seller Record': product.get('Seller_record', 'Not available'),
            'Positive Feedback Rating': product['Positive_feedback_rating'],
            'Positive Feedback Percentage': product['Positive_feedback_percentage']
        }
    else:
        basic_info = {
            'Name': product['Name'],
            'Rating': product.get('Rating', 'Not available'),
            'Rating_count': product.get('Rating_count', 'Not available'),
            'Price': product['Price']
        }
    
    for key, value in basic_info.items():
        if value != 'Not available':
            print(f"{Fore.YELLOW}{key}: {Style.RESET_ALL}{value}")
    print()

    # Display specifications
    if details.get('specifications'):
        print(f"\n{Back.BLUE}{Fore.WHITE} Specifications: {Style.RESET_ALL}")
        for key, value in details['specifications'].items():
            print(f"{Fore.GREEN}{key}: {Style.RESET_ALL}{value}")
        print()

    # Display special features
    if details.get('special_features'):
        print(f"\n{Back.BLUE}{Fore.WHITE} Special Features: {Style.RESET_ALL}")
        if product.get('site') == 'eBay':
            # eBay: Compact, single-line format
            for feature in details['special_features']:
                print(f"{Fore.GREEN}• {Style.RESET_ALL}{feature}")
        else:
            # Amazon: Detailed format with spacing
            print()  # Extra line for Amazon formatting
            for feature in details['special_features']:
                if ']' in feature:
                    title, description = feature.split(']', 1)
                    title = title.strip('[') + ']'
                    description = description.strip()
                    print(f"{Fore.YELLOW}{title}{Style.RESET_ALL}")
                    print(f"{Fore.WHITE}{description}{Style.RESET_ALL}\n")
                else:
                    print(f"{Fore.GREEN}• {Style.RESET_ALL}{feature}\n")
        print()

def print_error(message: str):
    print(f"{Fore.RED}{message}{Style.RESET_ALL}")

def print_success(message: str):
    print(f"{Fore.GREEN}{message}{Style.RESET_ALL}")

def print_info(message: str):
    print(f"{Fore.CYAN}{message}{Style.RESET_ALL}")

def print_separator():
    print("\n" + "="*80 + "\n") 