from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Request, Header
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.config import get_settings
from app.database import get_db
from app.models.user import User
from app.services.auth import get_current_user
from app.services.redis_service import RedisService, get_redis
from app.services.stripe_service import StripeService
from app.services.razorpay_service import RazorpayService

settings = get_settings()
router = APIRouter(prefix="/billing", tags=["Billing"])


# ============ Response Models ============

class StripeCheckoutResponse(BaseModel):
    """Response for Stripe checkout session."""
    gateway: str = "stripe"
    checkout_url: str


class RazorpayOrderResponse(BaseModel):
    """Response for Razorpay order creation."""
    gateway: str = "razorpay"
    order_id: str
    amount: int
    currency: str
    key_id: str


class SubscriptionStatus(BaseModel):
    """Response for subscription status."""
    is_paid: bool
    email: str
    payment_gateway: str


class PaymentVerifyRequest(BaseModel):
    """Request to verify Razorpay payment."""
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str


class GatewayInfo(BaseModel):
    """Info about available payment gateways."""
    active_gateway: str
    available_gateways: list[str]


# ============ Gateway Info ============

@router.get("/gateway-info", response_model=GatewayInfo)
async def get_gateway_info():
    """Get information about available payment gateways."""
    available = []
    if settings.stripe_secret_key:
        available.append("stripe")
    if settings.razorpay_key_id:
        available.append("razorpay")
    
    return GatewayInfo(
        active_gateway=settings.payment_gateway,
        available_gateways=available if available else [settings.payment_gateway]
    )


# ============ Stripe Endpoints ============

@router.post("/stripe/create-checkout", response_model=StripeCheckoutResponse)
async def create_stripe_checkout(
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Create a Stripe Checkout session for the ₹499 plan."""
    if current_user.is_paid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already has an active subscription"
        )
    
    success_url = f"{settings.frontend_url}/dashboard?payment=success&gateway=stripe"
    cancel_url = f"{settings.frontend_url}/dashboard?payment=cancelled"
    
    try:
        checkout_url = await StripeService.create_checkout_session(
            customer_email=current_user.email,
            user_id=current_user.id,
            success_url=success_url,
            cancel_url=cancel_url
        )
        return StripeCheckoutResponse(checkout_url=checkout_url)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/stripe/webhook")
async def stripe_webhook(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    redis: Annotated[RedisService, Depends(get_redis)],
    stripe_signature: str = Header(alias="Stripe-Signature"),
):
    """Handle Stripe webhook events with idempotency."""
    payload = await request.body()
    
    try:
        event = StripeService.construct_webhook_event(payload, stripe_signature)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    # Check for idempotency
    event_key = f"stripe_event:{event.id}"
    if await redis.exists(event_key):
        return {"status": "already_processed"}
    
    # Process checkout.session.completed event
    if event.type == "checkout.session.completed":
        session = event.data.object
        user_id = session.metadata.get("user_id")
        
        if user_id:
            result = await db.execute(select(User).where(User.id == int(user_id)))
            user = result.scalar_one_or_none()
            
            if user:
                user.is_paid = True
                user.stripe_customer_id = session.customer
                await db.commit()
    
    await redis.set(event_key, "processed", ttl=86400)
    return {"status": "success"}


# ============ Razorpay Endpoints ============

@router.post("/razorpay/create-order", response_model=RazorpayOrderResponse)
async def create_razorpay_order(
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Create a Razorpay order for the ₹499 plan."""
    if current_user.is_paid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already has an active subscription"
        )
    
    try:
        order_data = RazorpayService.create_order(user_id=current_user.id)
        return RazorpayOrderResponse(**order_data)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/razorpay/verify-payment")
async def verify_razorpay_payment(
    payment_data: PaymentVerifyRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    redis: Annotated[RedisService, Depends(get_redis)],
):
    """Verify Razorpay payment and grant access."""
    # Check for idempotency
    payment_key = f"razorpay_payment:{payment_data.razorpay_payment_id}"
    if await redis.exists(payment_key):
        return {"status": "already_processed", "is_paid": True}
    
    # Verify signature
    is_valid = RazorpayService.verify_payment_signature(
        order_id=payment_data.razorpay_order_id,
        payment_id=payment_data.razorpay_payment_id,
        signature=payment_data.razorpay_signature
    )
    
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid payment signature"
        )
    
    # Update user to paid status
    current_user.is_paid = True
    await db.commit()
    
    # Mark as processed
    await redis.set(payment_key, "processed", ttl=86400)
    
    return {"status": "success", "is_paid": True}


@router.post("/razorpay/webhook")
async def razorpay_webhook(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    redis: Annotated[RedisService, Depends(get_redis)],
    x_razorpay_signature: str = Header(alias="X-Razorpay-Signature"),
):
    """Handle Razorpay webhook events."""
    payload = await request.body()
    
    # Verify webhook signature
    if not RazorpayService.verify_webhook_signature(payload, x_razorpay_signature):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid webhook signature"
        )
    
    import json
    event = json.loads(payload)
    
    # Check for idempotency
    event_id = event.get("event")
    payment_id = event.get("payload", {}).get("payment", {}).get("entity", {}).get("id")
    
    if payment_id:
        event_key = f"razorpay_webhook:{payment_id}"
        if await redis.exists(event_key):
            return {"status": "already_processed"}
        
        # Process payment.captured event
        if event_id == "payment.captured":
            payment_entity = event["payload"]["payment"]["entity"]
            notes = payment_entity.get("notes", {})
            user_id = notes.get("user_id")
            
            if user_id:
                result = await db.execute(select(User).where(User.id == int(user_id)))
                user = result.scalar_one_or_none()
                
                if user:
                    user.is_paid = True
                    await db.commit()
        
        await redis.set(event_key, "processed", ttl=86400)
    
    return {"status": "success"}


# ============ Unified Endpoints ============

@router.post("/create-checkout")
async def create_checkout(
    current_user: Annotated[User, Depends(get_current_user)],
    gateway: Optional[str] = None,
):
    """Create a checkout session using the configured gateway.
    
    Optionally specify gateway='stripe' or gateway='razorpay' to override.
    """
    selected_gateway = gateway or settings.payment_gateway
    
    if current_user.is_paid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already has an active subscription"
        )
    
    if selected_gateway == "razorpay":
        try:
            order_data = RazorpayService.create_order(user_id=current_user.id)
            return {"gateway": "razorpay", **order_data}
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e)
            )
    else:  # Default to Stripe
        success_url = f"{settings.frontend_url}/dashboard?payment=success&gateway=stripe"
        cancel_url = f"{settings.frontend_url}/dashboard?payment=cancelled"
        
        try:
            checkout_url = await StripeService.create_checkout_session(
                customer_email=current_user.email,
                user_id=current_user.id,
                success_url=success_url,
                cancel_url=cancel_url
            )
            return {"gateway": "stripe", "checkout_url": checkout_url}
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e)
            )


@router.get("/status", response_model=SubscriptionStatus)
async def get_subscription_status(
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Get current user's subscription status."""
    return SubscriptionStatus(
        is_paid=current_user.is_paid,
        email=current_user.email,
        payment_gateway=settings.payment_gateway
    )
