from flask import Flask, request, jsonify
from flask_cors import CORS
from models import Database, User, Product
from scraper import PriceScraper
from auth import generate_token, token_required
from scheduler import PriceChecker
from config import Config
import re

app = Flask(__name__)
CORS(app)

# Initialize database
db = Database()

# Initialize scraper
scraper = PriceScraper()

# Initialize and start price checker
price_checker = PriceChecker()
price_checker.start()

# Helper function to validate email
def is_valid_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

# Helper function to validate URL
def is_valid_url(url):
    pattern = r'^https?://'
    return re.match(pattern, url) is not None

# ==================== AUTH ROUTES ====================

@app.route('/api/auth/register', methods=['POST'])
def register():
    """Register a new user"""
    try:
        data = request.get_json()
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        
        # Validation
        if not email or not password:
            return jsonify({'error': 'Email and password are required'}), 400
        
        if not is_valid_email(email):
            return jsonify({'error': 'Invalid email format'}), 400
        
        if len(password) < 6:
            return jsonify({'error': 'Password must be at least 6 characters'}), 400
        
        # Check if user already exists
        existing_user = User.find_by_email(db, email)
        if existing_user:
            return jsonify({'error': 'Email already registered'}), 400
        
        # Create user
        user_id = User.create(db, email, password)
        
        # Generate token
        token = generate_token(user_id, email)
        
        return jsonify({
            'message': 'Registration successful',
            'token': token,
            'user': {
                'id': user_id,
                'email': email
            }
        }), 201
    
    except Exception as e:
        return jsonify({'error': f'Registration failed: {str(e)}'}), 500

@app.route('/api/auth/login', methods=['POST'])
def login():
    """Login user"""
    try:
        data = request.get_json()
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        
        # Validation
        if not email or not password:
            return jsonify({'error': 'Email and password are required'}), 400
        
        # Find user
        user = User.find_by_email(db, email)
        if not user:
            return jsonify({'error': 'Invalid email or password'}), 401
        
        # Verify password
        if not User.verify_password(user['password_hash'], password):
            return jsonify({'error': 'Invalid email or password'}), 401
        
        # Generate token
        token = generate_token(user['id'], user['email'])
        
        return jsonify({
            'message': 'Login successful',
            'token': token,
            'user': {
                'id': user['id'],
                'email': user['email']
            }
        }), 200
    
    except Exception as e:
        return jsonify({'error': f'Login failed: {str(e)}'}), 500

# ==================== PRODUCT ROUTES ====================

@app.route('/api/products', methods=['GET'])
@token_required
def get_products():
    """Get all products for logged-in user"""
    try:
        products = Product.get_user_products(db, request.user_id)
        
        # Convert Decimal to float for JSON serialization
        products_list = []
        for p in products:
            product_dict = dict(p)
            if product_dict.get('current_price'):
                product_dict['current_price'] = float(product_dict['current_price'])
            if product_dict.get('target_price'):
                product_dict['target_price'] = float(product_dict['target_price'])
            products_list.append(product_dict)
        
        return jsonify({
            'products': products_list,
            'count': len(products_list)
        }), 200
    
    except Exception as e:
        return jsonify({'error': f'Failed to fetch products: {str(e)}'}), 500

@app.route('/api/products', methods=['POST'])
@token_required
def add_product():
    """Add a new product to track"""
    try:
        data = request.get_json()
        url = data.get('url', '').strip()
        target_price = data.get('target_price')
        
        # Validation
        if not url or not target_price:
            return jsonify({'error': 'URL and target price are required'}), 400
        
        if not is_valid_url(url):
            return jsonify({'error': 'Invalid URL format'}), 400
        
        try:
            target_price = float(target_price)
            if target_price <= 0:
                raise ValueError
        except (ValueError, TypeError):
            return jsonify({'error': 'Target price must be a positive number'}), 400
        
        # Check product limit
        current_count = Product.count_user_products(db, request.user_id)
        if current_count >= Config.MAX_PRODUCTS_PER_USER:
            return jsonify({
                'error': f'You have reached the maximum limit of {Config.MAX_PRODUCTS_PER_USER} products'
            }), 400
        
        # Scrape product details
        result = scraper.scrape(url)
        
        if not result['success']:
            return jsonify({'error': result.get('error', 'Failed to fetch product details')}), 400
        
        # Create product
        product_id = Product.create(
            db,
            user_id=request.user_id,
            url=url,
            target_price=target_price,
            site_source=result['site'],
            product_title=result['title'],
            current_price=result['price']
        )
        
        # Check if price is already below target and send email immediately
        if result['price'] <= target_price:
            from email_service import EmailService
            email_service = EmailService()
            
            # Get user email
            user = User.find_by_email(db, request.user_email)
            if user:
                email_service.send_price_alert(
                    to_email=user['email'],
                    product_title=result['title'],
                    current_price=result['price'],
                    target_price=target_price,
                    product_url=url
                )
                # Mark alert as sent
                Product.mark_alert_sent(db, product_id)
        
        return jsonify({
            'message': 'Product added successfully',
            'product': {
                'id': product_id,
                'title': result['title'],
                'current_price': result['price'],
                'target_price': target_price,
                'site': result['site']
            }
        }), 201
    
    except Exception as e:
        return jsonify({'error': f'Failed to add product: {str(e)}'}), 500

@app.route('/api/products/<int:product_id>', methods=['DELETE'])
@token_required
def delete_product(product_id):
    """Delete a product"""
    try:
        Product.delete(db, product_id, request.user_id)
        return jsonify({'message': 'Product deleted successfully'}), 200
    
    except Exception as e:
        return jsonify({'error': f'Failed to delete product: {str(e)}'}), 500

# ==================== UTILITY ROUTES ====================

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy'}), 200

@app.route('/api/scrape-test', methods=['POST'])
@token_required
def test_scrape():
    """Test scraping endpoint for debugging"""
    try:
        data = request.get_json()
        url = data.get('url', '').strip()
        
        if not url:
            return jsonify({'error': 'URL is required'}), 400
        
        result = scraper.scrape(url)
        return jsonify(result), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ==================== ERROR HANDLERS ====================

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

# ==================== RUN APP ====================

if __name__ == '__main__':
    app.run(debug=True, port=5000)