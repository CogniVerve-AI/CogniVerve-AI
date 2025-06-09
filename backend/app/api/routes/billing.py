from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any
import stripe
from datetime import datetime, timedelta

from app.core.database import get_db
from app.core.config import settings
from app.models.database import User, Subscription, UsageTracking
from app.models.schemas import (
    SubscriptionCreate, SubscriptionResponse, APIResponse, UsageResponse
)
from app.api.dependencies import get_current_user

# Initialize Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY

router = APIRouter()

# Subscription plans configuration
SUBSCRIPTION_PLANS = {
    "free": {
        "name": "Free",
        "price": 0,
        "api_calls_limit": 100,
        "compute_minutes_limit": 60,
        "storage_gb_limit": 1.0,
        "agents_limit": 3,
        "features": [
            "Basic AI agents",
            "100 API calls/month",
            "1 hour compute time",
            "1GB storage",
            "Community support"
        ]
    },
    "basic": {
        "name": "Basic",
        "price": 9.99,
        "stripe_price_id": "price_basic_monthly",
        "api_calls_limit": 10000,
        "compute_minutes_limit": 600,
        "storage_gb_limit": 10.0,
        "agents_limit": 10,
        "features": [
            "Advanced AI agents",
            "10,000 API calls/month",
            "10 hours compute time",
            "10GB storage",
            "Email support",
            "Custom tools"
        ]
    },
    "pro": {
        "name": "Pro",
        "price": 29.99,
        "stripe_price_id": "price_pro_monthly",
        "api_calls_limit": 100000,
        "compute_minutes_limit": 3600,
        "storage_gb_limit": 100.0,
        "agents_limit": 50,
        "features": [
            "Premium AI agents",
            "100,000 API calls/month",
            "60 hours compute time",
            "100GB storage",
            "Priority support",
            "Advanced analytics",
            "API access",
            "White-label options"
        ]
    },
    "enterprise": {
        "name": "Enterprise",
        "price": 99.99,
        "stripe_price_id": "price_enterprise_monthly",
        "api_calls_limit": -1,  # Unlimited
        "compute_minutes_limit": -1,  # Unlimited
        "storage_gb_limit": -1,  # Unlimited
        "agents_limit": -1,  # Unlimited
        "features": [
            "Unlimited everything",
            "Custom AI models",
            "Dedicated support",
            "SLA guarantees",
            "On-premise deployment",
            "Custom integrations",
            "Advanced security"
        ]
    }
}


@router.get("/plans", response_model=APIResponse)
async def get_subscription_plans():
    """Get available subscription plans."""
    return APIResponse(
        success=True,
        message="Subscription plans retrieved",
        data={"plans": SUBSCRIPTION_PLANS}
    )


@router.get("/current", response_model=SubscriptionResponse)
async def get_current_subscription(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's subscription."""
    subscription = db.query(Subscription).filter(
        Subscription.user_id == current_user.id,
        Subscription.status == "active"
    ).first()
    
    if not subscription:
        # Create free subscription if none exists
        subscription = Subscription(
            user_id=current_user.id,
            plan="free",
            status="active",
            billing_cycle="monthly",
            current_period_start=datetime.utcnow(),
            current_period_end=datetime.utcnow() + timedelta(days=30)
        )
        db.add(subscription)
        db.commit()
        db.refresh(subscription)
    
    return SubscriptionResponse.from_orm(subscription)


@router.post("/create-checkout-session", response_model=APIResponse)
async def create_checkout_session(
    subscription_data: SubscriptionCreate,
    current_user: User = Depends(get_current_user)
):
    """Create Stripe checkout session for subscription."""
    plan = subscription_data.plan
    
    if plan not in SUBSCRIPTION_PLANS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid subscription plan"
        )
    
    if plan == "free":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Free plan doesn't require payment"
        )
    
    plan_config = SUBSCRIPTION_PLANS[plan]
    
    try:
        # Create Stripe checkout session
        checkout_session = stripe.checkout.Session.create(
            customer_email=current_user.email,
            payment_method_types=['card'],
            line_items=[{
                'price': plan_config['stripe_price_id'],
                'quantity': 1,
            }],
            mode='subscription',
            success_url=f"{settings.FRONTEND_URL}/dashboard?subscription=success",
            cancel_url=f"{settings.FRONTEND_URL}/pricing?subscription=cancelled",
            metadata={
                'user_id': current_user.id,
                'plan': plan
            }
        )
        
        return APIResponse(
            success=True,
            message="Checkout session created",
            data={
                "checkout_url": checkout_session.url,
                "session_id": checkout_session.id
            }
        )
        
    except stripe.error.StripeError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Stripe error: {str(e)}"
        )


@router.post("/webhook", response_model=APIResponse)
async def stripe_webhook(
    request: dict,
    db: Session = Depends(get_db)
):
    """Handle Stripe webhooks."""
    # In production, verify the webhook signature
    # sig_header = request.headers.get('stripe-signature')
    # event = stripe.Webhook.construct_event(payload, sig_header, settings.STRIPE_WEBHOOK_SECRET)
    
    event = request  # Simplified for demo
    
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        user_id = session['metadata']['user_id']
        plan = session['metadata']['plan']
        
        # Update user subscription
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            # Deactivate existing subscriptions
            db.query(Subscription).filter(
                Subscription.user_id == user_id,
                Subscription.status == "active"
            ).update({"status": "cancelled"})
            
            # Create new subscription
            subscription = Subscription(
                user_id=user_id,
                plan=plan,
                status="active",
                billing_cycle="monthly",
                current_period_start=datetime.utcnow(),
                current_period_end=datetime.utcnow() + timedelta(days=30),
                stripe_subscription_id=session.get('subscription')
            )
            
            db.add(subscription)
            user.subscription_type = plan
            db.commit()
    
    elif event['type'] == 'invoice.payment_failed':
        # Handle failed payment
        subscription_id = event['data']['object']['subscription']
        db.query(Subscription).filter(
            Subscription.stripe_subscription_id == subscription_id
        ).update({"status": "past_due"})
        db.commit()
    
    elif event['type'] == 'customer.subscription.deleted':
        # Handle subscription cancellation
        subscription_id = event['data']['object']['id']
        subscription = db.query(Subscription).filter(
            Subscription.stripe_subscription_id == subscription_id
        ).first()
        
        if subscription:
            subscription.status = "cancelled"
            user = db.query(User).filter(User.id == subscription.user_id).first()
            if user:
                user.subscription_type = "free"
            db.commit()
    
    return APIResponse(success=True, message="Webhook processed")


@router.post("/cancel", response_model=APIResponse)
async def cancel_subscription(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Cancel current subscription."""
    subscription = db.query(Subscription).filter(
        Subscription.user_id == current_user.id,
        Subscription.status == "active"
    ).first()
    
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active subscription found"
        )
    
    if subscription.plan == "free":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot cancel free subscription"
        )
    
    try:
        # Cancel Stripe subscription
        if subscription.stripe_subscription_id:
            stripe.Subscription.delete(subscription.stripe_subscription_id)
        
        # Update local subscription
        subscription.status = "cancelled"
        current_user.subscription_type = "free"
        db.commit()
        
        return APIResponse(
            success=True,
            message="Subscription cancelled successfully"
        )
        
    except stripe.error.StripeError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Stripe error: {str(e)}"
        )


@router.get("/usage", response_model=UsageResponse)
async def get_usage_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current usage statistics."""
    # Get current period usage
    now = datetime.utcnow()
    period_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    period_end = (period_start + timedelta(days=32)).replace(day=1) - timedelta(seconds=1)
    
    usage = db.query(UsageTracking).filter(
        UsageTracking.user_id == current_user.id,
        UsageTracking.period_start >= period_start,
        UsageTracking.period_end <= period_end
    ).first()
    
    if not usage:
        # Create usage record if it doesn't exist
        usage = UsageTracking(
            user_id=current_user.id,
            period_start=period_start,
            period_end=period_end,
            api_calls=0,
            compute_minutes=0,
            storage_gb=0.0,
            bandwidth_gb=0.0
        )
        db.add(usage)
        db.commit()
        db.refresh(usage)
    
    return UsageResponse.from_orm(usage)


@router.get("/limits", response_model=APIResponse)
async def get_subscription_limits(
    current_user: User = Depends(get_current_user)
):
    """Get current subscription limits."""
    plan = current_user.subscription_type or "free"
    plan_config = SUBSCRIPTION_PLANS.get(plan, SUBSCRIPTION_PLANS["free"])
    
    return APIResponse(
        success=True,
        message="Subscription limits retrieved",
        data={
            "plan": plan,
            "limits": {
                "api_calls": plan_config["api_calls_limit"],
                "compute_minutes": plan_config["compute_minutes_limit"],
                "storage_gb": plan_config["storage_gb_limit"],
                "agents": plan_config["agents_limit"]
            },
            "features": plan_config["features"]
        }
    )


def check_usage_limits(user: User, db: Session, resource_type: str, amount: int = 1) -> bool:
    """Check if user has exceeded usage limits."""
    plan = user.subscription_type or "free"
    plan_config = SUBSCRIPTION_PLANS.get(plan, SUBSCRIPTION_PLANS["free"])
    
    # Get current usage
    now = datetime.utcnow()
    period_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    period_end = (period_start + timedelta(days=32)).replace(day=1) - timedelta(seconds=1)
    
    usage = db.query(UsageTracking).filter(
        UsageTracking.user_id == user.id,
        UsageTracking.period_start >= period_start,
        UsageTracking.period_end <= period_end
    ).first()
    
    if not usage:
        return True  # No usage yet, allow
    
    # Check limits
    limit_key = f"{resource_type}_limit"
    current_key = resource_type
    
    limit = plan_config.get(limit_key, 0)
    current = getattr(usage, current_key, 0)
    
    # -1 means unlimited
    if limit == -1:
        return True
    
    return (current + amount) <= limit


def increment_usage(user: User, db: Session, resource_type: str, amount: int = 1):
    """Increment usage counter for a resource."""
    now = datetime.utcnow()
    period_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    period_end = (period_start + timedelta(days=32)).replace(day=1) - timedelta(seconds=1)
    
    usage = db.query(UsageTracking).filter(
        UsageTracking.user_id == user.id,
        UsageTracking.period_start >= period_start,
        UsageTracking.period_end <= period_end
    ).first()
    
    if not usage:
        usage = UsageTracking(
            user_id=user.id,
            period_start=period_start,
            period_end=period_end,
            api_calls=0,
            compute_minutes=0,
            storage_gb=0.0,
            bandwidth_gb=0.0
        )
        db.add(usage)
    
    # Increment the specific resource
    current_value = getattr(usage, resource_type, 0)
    setattr(usage, resource_type, current_value + amount)
    
    db.commit()

