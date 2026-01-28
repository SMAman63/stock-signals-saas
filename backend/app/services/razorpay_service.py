import razorpay
import hmac
import hashlib
from typing import Optional

from app.config import get_settings

settings = get_settings()

# Initialize Razorpay client
razorpay_client = None
if settings.razorpay_key_id and settings.razorpay_key_secret:
    razorpay_client = razorpay.Client(
        auth=(settings.razorpay_key_id, settings.razorpay_key_secret)
    )


class RazorpayService:
    """Service for Razorpay payment operations."""
    
    @staticmethod
    def create_order(user_id: int, amount: int = None) -> dict:
        """Create a Razorpay order and return order details."""
        if not razorpay_client:
            raise Exception("Razorpay not configured")
        
        amount = amount or settings.razorpay_plan_amount
        
        order_data = {
            "amount": amount,  # Amount in paise
            "currency": "INR",
            "receipt": f"order_user_{user_id}",
            "notes": {
                "user_id": str(user_id)
            }
        }
        
        try:
            order = razorpay_client.order.create(data=order_data)
            return {
                "order_id": order["id"],
                "amount": order["amount"],
                "currency": order["currency"],
                "key_id": settings.razorpay_key_id
            }
        except Exception as e:
            raise Exception(f"Razorpay error: {str(e)}")
    
    @staticmethod
    def verify_payment_signature(
        order_id: str,
        payment_id: str,
        signature: str
    ) -> bool:
        """Verify Razorpay payment signature."""
        if not razorpay_client:
            return False
        
        try:
            razorpay_client.utility.verify_payment_signature({
                "razorpay_order_id": order_id,
                "razorpay_payment_id": payment_id,
                "razorpay_signature": signature
            })
            return True
        except razorpay.errors.SignatureVerificationError:
            return False
    
    @staticmethod
    def verify_webhook_signature(payload: bytes, signature: str) -> bool:
        """Verify Razorpay webhook signature."""
        if not settings.razorpay_webhook_secret:
            return False
        
        expected_signature = hmac.new(
            settings.razorpay_webhook_secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(expected_signature, signature)
    
    @staticmethod
    def get_payment_details(payment_id: str) -> Optional[dict]:
        """Fetch payment details from Razorpay."""
        if not razorpay_client:
            return None
        
        try:
            payment = razorpay_client.payment.fetch(payment_id)
            return payment
        except Exception:
            return None
