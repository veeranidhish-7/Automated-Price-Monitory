from apscheduler.schedulers.background import BackgroundScheduler
from models import Database, Product, User
from scraper import PriceScraper
from email_service import EmailService
from config import Config
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PriceChecker:
    def __init__(self):
        self.db = Database()
        self.scraper = PriceScraper()
        self.email_service = EmailService()
        self.scheduler = BackgroundScheduler()
    
    def check_all_prices(self):
        """Check prices for all active products"""
        logger.info("Starting price check for all products...")
        
        try:
            products = Product.get_all_active(self.db)
            
            for product in products:
                self.check_single_product(product)
            
            logger.info(f"Completed price check for {len(products)} products")
        except Exception as e:
            logger.error(f"Error in price check: {str(e)}")
    
    def check_single_product(self, product):
        """Check price for a single product and send alert if needed"""
        try:
            logger.info(f"Checking price for product ID: {product['id']}")
            
            # Scrape current price
            result = self.scraper.scrape(product['url'])
            
            if not result['success']:
                logger.warning(f"Failed to scrape product {product['id']}: {result.get('error')}")
                return
            
            current_price = result['price']
            
            # Update price in database
            Product.update_price(self.db, product['id'], current_price)
            logger.info(f"Updated price for product {product['id']}: ₹{current_price}")
            
            # Check if price dropped below target
            if current_price <= product['target_price'] and not product['alert_sent']:
                logger.info(f"Price alert triggered for product {product['id']}")
                
                # Get user email
                user = User.find_by_email(self.db, self.get_user_email(product['user_id']))
                
                if user:
                    # Send email alert
                    success = self.email_service.send_price_alert(
                        to_email=user['email'],
                        product_title=product['product_title'],
                        current_price=current_price,
                        target_price=product['target_price'],
                        product_url=product['url']
                    )
                    
                    if success:
                        # Mark alert as sent
                        Product.mark_alert_sent(self.db, product['id'])
                        logger.info(f"Alert sent successfully for product {product['id']}")
                    else:
                        logger.error(f"Failed to send email for product {product['id']}")
        
        except Exception as e:
            logger.error(f"Error checking product {product['id']}: {str(e)}")
    
    def get_user_email(self, user_id):
        """Get user email by user_id"""
        cur = self.db.get_cursor()
        cur.execute('SELECT email FROM users WHERE id = ?', (user_id,))
        result = cur.fetchone()
        return dict(result)['email'] if result else None
    
    def start(self):
        """Start the background scheduler"""
        # Schedule price checks every hour
        self.scheduler.add_job(
            self.check_all_prices,
            'interval',
            seconds=Config.PRICE_CHECK_INTERVAL,
            id='price_check_job'
        )
        
        self.scheduler.start()
        logger.info(f"Scheduler started - checking prices every {Config.PRICE_CHECK_INTERVAL} seconds")
    
    def stop(self):
        """Stop the scheduler"""
        self.scheduler.shutdown()
        logger.info("Scheduler stopped")