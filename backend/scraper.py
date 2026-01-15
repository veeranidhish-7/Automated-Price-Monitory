import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urlparse

class PriceScraper:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Connection': 'keep-alive',
        }
    
    def get_site_source(self, url):
        """Detect which e-commerce site the URL belongs to"""
        domain = urlparse(url).netloc.lower()
        
        if 'amazon.in' in domain or 'amazon.com' in domain or 'amzn.in' in domain:
            return 'amazon'
        elif 'flipkart.com' in domain:
            return 'flipkart'
        else:
            return 'unknown'
    
    def scrape(self, url):
        """Main scraping method that routes to specific scrapers"""
        site = self.get_site_source(url)
        
        try:
            if site == 'amazon':
                return self.scrape_amazon(url)
            elif site == 'flipkart':
                return self.scrape_flipkart(url)
            else:
                return {
                    'success': False,
                    'error': 'Unsupported website. Only Amazon and Flipkart are supported.'
                }
        except Exception as e:
            return {
                'success': False,
                'error': f'Scraping failed: {str(e)}'
            }
    
    def scrape_amazon(self, url):
        """Scrape Amazon product page"""
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract title
            title_elem = soup.find('span', {'id': 'productTitle'})
            title = title_elem.text.strip() if title_elem else 'Amazon Product'
            
            # Extract price - try multiple selectors
            price = None
            
            # Method 1: Whole price
            price_whole = soup.find('span', {'class': 'a-price-whole'})
            price_fraction = soup.find('span', {'class': 'a-price-fraction'})
            
            if price_whole:
                price_str = price_whole.text.replace(',', '').replace('.', '')
                if price_fraction:
                    price_str += '.' + price_fraction.text
                try:
                    price = float(price_str)
                except:
                    pass
            
            # Method 2: Try other common Amazon price classes
            if not price:
                price_elem = soup.find('span', {'class': 'a-price'})
                if price_elem:
                    price_text = price_elem.find('span', {'class': 'a-offscreen'})
                    if price_text:
                        price_str = re.sub(r'[^\d.]', '', price_text.text)
                        if price_str:
                            try:
                                price = float(price_str)
                            except:
                                pass
            
            if price:
                return {
                    'success': True,
                    'title': title[:200],  # Limit title length
                    'price': price,
                    'site': 'amazon'
                }
            else:
                return {
                    'success': False,
                    'error': 'Could not extract price from Amazon page. The page structure may have changed.'
                }
                
        except requests.RequestException as e:
            return {
                'success': False,
                'error': f'Failed to fetch Amazon page: {str(e)}'
            }
    
    def scrape_flipkart(self, url):
        """Scrape Flipkart product page"""
        # Enhanced headers to avoid bot detection
        flipkart_headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0',
        }
        
        try:
            # Add a small delay to avoid rate limiting
            import time
            time.sleep(1)
            
            response = requests.get(url, headers=flipkart_headers, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract title - try multiple selectors
            title = 'Flipkart Product'
            title_selectors = [
                {'class': 'VU-ZEz'},
                {'class': 'B_NuCI'},
                {'class': 'yhB1nd'},
                {'class': 'G6XhRU'}
            ]
            
            for selector in title_selectors:
                title_elem = soup.find('span', selector)
                if title_elem:
                    title = title_elem.text.strip()
                    break
            
            # Extract price - try multiple selectors
            price = None
            
            # Common Flipkart price classes (updated)
            price_selectors = [
                ('div', {'class': 'Nx9bqj CxhGGd'}),
                ('div', {'class': '_30jeq3 _16Jk6d'}),
                ('div', {'class': '_30jeq3'}),
                ('div', {'class': '_25b18c'}),
                ('div', {'class': 'Nx9bqj'}),
            ]
            
            for tag, selector in price_selectors:
                price_elem = soup.find(tag, selector)
                if price_elem:
                    price_text = re.sub(r'[^\d.]', '', price_elem.text)
                    if price_text:
                        try:
                            price = float(price_text)
                            break
                        except:
                            pass
            
            if price:
                return {
                    'success': True,
                    'title': title[:200],
                    'price': price,
                    'site': 'flipkart'
                }
            else:
                return {
                    'success': False,
                    'error': 'Could not extract price from Flipkart page. Try using the full product URL instead of the short link.'
                }
                
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                return {
                    'success': False,
                    'error': 'Flipkart is temporarily blocking requests. Please wait a few minutes and try again. Tip: Use the full product URL (not the short dl.flipkart.com link).'
                }
            return {
                'success': False,
                'error': f'Failed to fetch Flipkart page: {str(e)}'
            }
        except requests.RequestException as e:
            return {
                'success': False,
                'error': f'Failed to fetch Flipkart page: {str(e)}'
            }

# Test function
if __name__ == '__main__':
    scraper = PriceScraper()
    
    # Test with sample URLs
    test_url = input("Enter Amazon or Flipkart product URL: ")
    result = scraper.scrape(test_url)
    print(result)