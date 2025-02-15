# E-Commerce Product Scraper

A high-performance, concurrent web scraper for Amazon and eBay built with Python and Playwright.

## Features

- 🚀 Lightning-fast concurrent scraping from multiple e-commerce sites
- 🔄 Simultaneous product searches on Amazon and eBay
- 📊 Detailed product information including specifications and features
- 🛡️ Built-in rate limiting and resource optimization
- 🎨 Clean, colorful CLI interface
- 🔍 Smart filtering of sponsored products
- 📱 Responsive design that works with different product layouts

## Screenshots

### Search Interface
![Search Interface](screenshots/capture1.png)

### Product Details
![Product Details](screenshots/capture2.png)

## Performance

- Concurrent scraping reduces search time by up to 50%
- Smart resource filtering reduces bandwidth usage
- Optimized selectors for faster page processing
- Efficient error handling and recovery

## Installation

1. Clone the repository
   ```bash
   git clone https://github.com/ImranDevPython/Product-Scraper.git
   cd Product-Scraper
   ```

2. Create and activate a virtual environment
   ```bash
   python -m venv venv
   source venv/Scripts/Activate.ps1 # On Windows: venv\Scripts\activate
   ```

3. Install dependencies
   ```bash
   pip install -r requirements.txt
   ```

4. Install Playwright browsers
   ```bash
   playwright install chromium
   ```

## Usage

1. Run the scraper
   ```bash
   python main.py
   ```

2. Choose your options:
   - Select a specific site (Amazon or eBay)
   - Search both sites concurrently
   - Adjust the number of products to scrape

3. Enter your search query and view the results

4. Select a product to view detailed information:
   - Product specifications
   - Special features
   - Seller information (eBay)
   - Ratings and reviews (Amazon)

5. Choose to perform another search or exit

## Features in Detail

### Concurrent Searching
- Simultaneously search multiple e-commerce sites
- Reduce total search time by up to 50%
- Smart error handling and recovery

### Product Information
- Comprehensive product details
- Site-specific information:
  - Amazon: Ratings, reviews, specifications
  - eBay: Seller details, feedback ratings, item condition

### Resource Optimization
- Smart request filtering
- Efficient bandwidth usage
- Optimized page loading
- Minimal memory footprint

### User Interface
- Colorful, easy-to-read output
- Clear navigation options
- Progress indicators
- Error messages in red
- Success messages in green

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Author

Created by [ImranDevPython](https://github.com/ImranDevPython)

## Acknowledgments

- Built with [Playwright](https://playwright.dev/)
- Thanks to the Python community for the amazing packages used in this project
