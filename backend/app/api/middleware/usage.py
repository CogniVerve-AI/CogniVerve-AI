from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.database import User
from app.api.dependencies import get_current_user
from app.api.routes.billing import check_usage_limits, increment_usage


class UsageLimiter:
    """Middleware for enforcing usage limits."""
    
    def __init__(self, resource_type: str, amount: int = 1):
        self.resource_type = resource_type
        self.amount = amount
    
    def __call__(self, 
                 current_user: User = Depends(get_current_user),
                 db: Session = Depends(get_db)):
        """Check usage limits before allowing request."""
        
        if not check_usage_limits(current_user, db, self.resource_type, self.amount):
            plan = current_user.subscription_type or "free"
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Usage limit exceeded for {self.resource_type}. Upgrade your plan to continue.",
                headers={"X-RateLimit-Limit-Type": self.resource_type, "X-Current-Plan": plan}
            )
        
        # Increment usage after successful check
        increment_usage(current_user, db, self.resource_type, self.amount)
        
        return current_user


# Usage limiters for different resources
api_call_limiter = UsageLimiter("api_calls", 1)
compute_limiter = UsageLimiter("compute_minutes", 1)
storage_limiter = UsageLimiter("storage_gb", 1)


def require_plan(min_plan: str):
    """Dependency to require minimum subscription plan."""
    
    plan_hierarchy = {
        "free": 0,
        "basic": 1,
        "pro": 2,
        "enterprise": 3
    }
    
    def _require_plan(current_user: User = Depends(get_current_user)):
        user_plan = current_user.subscription_type or "free"
        user_level = plan_hierarchy.get(user_plan, 0)
        required_level = plan_hierarchy.get(min_plan, 0)
        
        if user_level < required_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"This feature requires {min_plan} plan or higher. Current plan: {user_plan}",
                headers={"X-Required-Plan": min_plan, "X-Current-Plan": user_plan}
            )
        
        return current_user
    
    return _require_plan


# Plan-specific dependencies
require_basic = require_plan("basic")
require_pro = require_plan("pro")
require_enterprise = require_plan("enterprise")

