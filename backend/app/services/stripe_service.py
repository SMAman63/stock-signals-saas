import stripe
from typing import Optional

from app.config import get_settings

settings = get_settings()

# Initialize Stripe
stripe.api_key = settings.stripe_secret_key


class StripeService:
    """Service for Stripe payment operations."""
    
    @staticmethod
    async def create_checkout_session(
        customer_email: str,
        user_id: int,
        success_url: str,
        cancel_url: str
    ) -> str:
        """Create a Stripe Checkout session and return the URL."""
        try:
            session = stripe.checkout.Session.create(
                payment_method_types=["card"],
                line_items=[{
                    "price": settings.stripe_price_id,
                    "quantity": 1,
                }],
                mode="payment",  # One-time payment for ₹499
                success_url=success_url,
                cancel_url=cancel_url,
                customer_email=customer_email,
                metadata={
                    "user_id": str(user_id)
                }
            )
            return session.url
        except stripe.error.StripeError as e:
            raise Exception(f"Stripe error: {str(e)}")
    
    @staticmethod
    def construct_webhook_event(payload: bytes, sig_header: str) -> stripe.Event:
        """Construct and verify a Stripe webhook event."""
        try:
            event = stripe.Webhook.construct_event(
                payload,
                sig_header,
                settings.stripe_webhook_secret
            )
            return event
        except ValueError:
            raise Exception("Invalid payload")
        except stripe.error.SignatureVerificationError:
            raise Exception("Invalid signature")
    
    @staticmethod
    def get_session_metadata(session_id: str) -> Optional[dict]:
        """Retrieve metadata from a checkout session."""
        try:
            session = stripe.checkout.Session.retrieve(session_id)
            return session.metadata
        except stripe.error.StripeError:
            return None
