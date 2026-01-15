import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import Config

class EmailService:
    def __init__(self):
        self.host = Config.EMAIL_HOST
        self.port = Config.EMAIL_PORT
        self.user = Config.EMAIL_USER
        self.password = Config.EMAIL_PASSWORD
    
    def send_price_alert(self, to_email, product_title, current_price, target_price, product_url):
        """Send price drop alert email"""
        subject = f"🎉 Price Alert: {product_title}"
        
        html_body = f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px; background-color: #f4f4f4;">
                    <div style="background-color: #4CAF50; color: white; padding: 20px; text-align: center; border-radius: 5px;">
                        <h1 style="margin: 0;">Price Drop Alert! 🎉</h1>
                    </div>
                    
                    <div style="background-color: white; padding: 30px; margin-top: 20px; border-radius: 5px;">
                        <h2 style="color: #4CAF50;">Great News!</h2>
                        <p>The price of your tracked product has dropped below your target price:</p>
                        
                        <div style="background-color: #f9f9f9; padding: 15px; border-left: 4px solid #4CAF50; margin: 20px 0;">
                            <p style="margin: 5px 0;"><strong>Product:</strong> {product_title}</p>
                            <p style="margin: 5px 0;"><strong>Current Price:</strong> <span style="color: #4CAF50; font-size: 20px; font-weight: bold;">₹{current_price}</span></p>
                            <p style="margin: 5px 0;"><strong>Your Target:</strong> ₹{target_price}</p>
                            <p style="margin: 5px 0;"><strong>Savings:</strong> <span style="color: #e74c3c; font-weight: bold;">₹{target_price - current_price}</span></p>
                        </div>
                        
                        <div style="text-align: center; margin: 30px 0;">
                            <a href="{product_url}" 
                               style="background-color: #4CAF50; 
                                      color: white; 
                                      padding: 15px 30px; 
                                      text-decoration: none; 
                                      border-radius: 5px; 
                                      display: inline-block;
                                      font-weight: bold;">
                                View Product Now
                            </a>
                        </div>
                        
                        <p style="color: #777; font-size: 12px; margin-top: 30px;">
                            This is an automated alert from your Price Tracker. 
                            You're receiving this because you set a price alert for this product.
                        </p>
                    </div>
                </div>
            </body>
        </html>
        """
        
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.user
            msg['To'] = to_email
            
            html_part = MIMEText(html_body, 'html')
            msg.attach(html_part)
            
            with smtplib.SMTP(self.host, self.port) as server:
                server.starttls()
                server.login(self.user, self.password)
                server.send_message(msg)
            
            return True
        except Exception as e:
            print(f"Failed to send email: {str(e)}")
            return False