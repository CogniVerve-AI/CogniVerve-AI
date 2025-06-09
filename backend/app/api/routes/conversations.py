from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.models.database import Conversation, Message, User
from app.models.schemas import (
    ConversationCreate, ConversationUpdate, ConversationResponse,
    MessageCreate, MessageResponse, APIResponse, PaginatedResponse
)
from app.api.dependencies import get_current_user

router = APIRouter()


@router.post("/", response_model=APIResponse)
async def create_conversation(
    conversation_data: ConversationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new conversation."""
    db_conversation = Conversation(
        title=conversation_data.title,
        user_id=current_user.id,
        agent_id=conversation_data.agent_id
    )
    
    db.add(db_conversation)
    db.commit()
    db.refresh(db_conversation)
    
    return APIResponse(
        success=True,
        message="Conversation created successfully",
        data=ConversationResponse.from_orm(db_conversation)
    )


@router.get("/", response_model=PaginatedResponse)
async def list_conversations(
    page: int = 1,
    size: int = 10,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List user's conversations."""
    offset = (page - 1) * size
    
    conversations_query = db.query(Conversation).filter(Conversation.user_id == current_user.id)
    total = conversations_query.count()
    conversations = conversations_query.order_by(Conversation.updated_at.desc()).offset(offset).limit(size).all()
    
    return PaginatedResponse(
        items=[ConversationResponse.from_orm(conv) for conv in conversations],
        total=total,
        page=page,
        size=size,
        pages=(total + size - 1) // size
    )


@router.get("/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get conversation by ID."""
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id
    ).first()
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    return ConversationResponse.from_orm(conversation)


@router.put("/{conversation_id}", response_model=APIResponse)
async def update_conversation(
    conversation_id: str,
    conversation_data: ConversationUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update conversation."""
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id
    ).first()
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    # Update fields
    update_data = conversation_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(conversation, field, value)
    
    db.commit()
    db.refresh(conversation)
    
    return APIResponse(
        success=True,
        message="Conversation updated successfully",
        data=ConversationResponse.from_orm(conversation)
    )


@router.delete("/{conversation_id}", response_model=APIResponse)
async def delete_conversation(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete conversation."""
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id
    ).first()
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    db.delete(conversation)
    db.commit()
    
    return APIResponse(
        success=True,
        message="Conversation deleted successfully"
    )


@router.post("/{conversation_id}/messages", response_model=APIResponse)
async def create_message(
    conversation_id: str,
    message_data: MessageCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add a message to conversation."""
    # Verify conversation exists and belongs to user
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id
    ).first()
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    # Create message
    db_message = Message(
        content=message_data.content,
        role=message_data.role.value,
        metadata=message_data.metadata,
        conversation_id=conversation_id
    )
    
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    
    return APIResponse(
        success=True,
        message="Message created successfully",
        data=MessageResponse.from_orm(db_message)
    )


@router.get("/{conversation_id}/messages", response_model=PaginatedResponse)
async def list_messages(
    conversation_id: str,
    page: int = 1,
    size: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List messages in conversation."""
    # Verify conversation exists and belongs to user
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id
    ).first()
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    offset = (page - 1) * size
    
    messages_query = db.query(Message).filter(Message.conversation_id == conversation_id)
    total = messages_query.count()
    messages = messages_query.order_by(Message.created_at.asc()).offset(offset).limit(size).all()
    
    return PaginatedResponse(
        items=[MessageResponse.from_orm(msg) for msg in messages],
        total=total,
        page=page,
        size=size,
        pages=(total + size - 1) // size
    )

