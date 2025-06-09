from pydantic import BaseModel, EmailStr, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


# Base response models
class APIResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Any] = None


class PaginatedResponse(BaseModel):
    items: List[Any]
    total: int
    page: int
    size: int
    pages: int


# Authentication models
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    full_name: Optional[str] = None
    password: str
    
    @validator('username')
    def username_alphanumeric(cls, v):
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('Username must be alphanumeric (with _ and - allowed)')
        if len(v) < 3:
            raise ValueError('Username must be at least 3 characters long')
        return v
    
    @validator('password')
    def password_strength(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v


class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    full_name: Optional[str]
    is_active: bool
    is_admin: bool
    subscription_type: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str
    expires_in: int


# Agent models
class AgentCreate(BaseModel):
    name: str
    description: Optional[str] = None
    instructions: Optional[str] = None
    model: str = "gpt-3.5-turbo"
    temperature: float = 0.7
    tools: Optional[List[str]] = None
    is_public: bool = False
    
    @validator('temperature')
    def temperature_range(cls, v):
        if not 0.0 <= v <= 2.0:
            raise ValueError('Temperature must be between 0.0 and 2.0')
        return v


class AgentUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    instructions: Optional[str] = None
    model: Optional[str] = None
    temperature: Optional[float] = None
    tools: Optional[List[str]] = None
    is_public: Optional[bool] = None
    
    @validator('temperature')
    def temperature_range(cls, v):
        if v is not None and not 0.0 <= v <= 2.0:
            raise ValueError('Temperature must be between 0.0 and 2.0')
        return v


class AgentResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    instructions: Optional[str]
    model: str
    temperature: float
    tools: Optional[List[str]]
    is_public: bool
    user_id: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Task models
class TaskCreate(BaseModel):
    title: str
    description: str
    agent_id: str
    metadata: Optional[Dict[str, Any]] = None


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskResponse(BaseModel):
    id: str
    title: str
    description: str
    status: str
    progress: Optional[float]
    result: Optional[Dict[str, Any]]
    error: Optional[str]
    agent_id: str
    user_id: str
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    metadata: Optional[Dict[str, Any]]
    
    class Config:
        from_attributes = True


# Conversation models
class ConversationCreate(BaseModel):
    title: Optional[str] = None
    agent_id: str


class ConversationUpdate(BaseModel):
    title: Optional[str] = None


class ConversationResponse(BaseModel):
    id: str
    title: Optional[str]
    agent_id: str
    user_id: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Message models
class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class MessageCreate(BaseModel):
    content: str
    role: MessageRole = MessageRole.USER
    metadata: Optional[Dict[str, Any]] = None


class MessageResponse(BaseModel):
    id: str
    content: str
    role: str
    metadata: Optional[Dict[str, Any]]
    conversation_id: str
    created_at: datetime
    
    class Config:
        from_attributes = True


# Tool models
class ToolCreate(BaseModel):
    name: str
    display_name: str
    description: str
    category: str
    schema: Dict[str, Any]
    code: Optional[str] = None


class ToolUpdate(BaseModel):
    display_name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    schema: Optional[Dict[str, Any]] = None
    code: Optional[str] = None
    is_active: Optional[bool] = None


class ToolResponse(BaseModel):
    id: str
    name: str
    display_name: str
    description: str
    category: str
    schema: Dict[str, Any]
    is_active: bool
    is_builtin: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Subscription models
class SubscriptionPlan(str, Enum):
    FREE = "free"
    BASIC = "basic"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class SubscriptionCreate(BaseModel):
    plan: SubscriptionPlan
    billing_cycle: str = "monthly"  # monthly, yearly


class SubscriptionResponse(BaseModel):
    id: str
    user_id: str
    plan: str
    status: str
    billing_cycle: str
    current_period_start: datetime
    current_period_end: datetime
    created_at: datetime
    
    class Config:
        from_attributes = True


# Usage tracking models
class UsageResponse(BaseModel):
    user_id: str
    period_start: datetime
    period_end: datetime
    api_calls: int
    compute_minutes: int
    storage_gb: float
    bandwidth_gb: float
    
    class Config:
        from_attributes = True

