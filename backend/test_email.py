from email_service import EmailService
from config import Config

print(f"Email User: {Config.EMAIL_USER}")
print(f"Email Password: {'*' * len(Config.EMAIL_PASSWORD)}")

service = EmailService()

result = service.send_price_alert(
    to_email="g.veeranidhish014@gmail.com",  # PUT YOUR EMAIL HERE
    product_title="Test Product",
    current_price=200,
    target_price=250,
    product_url="https://amazon.in"
)

print(f"Email sent: {result}")