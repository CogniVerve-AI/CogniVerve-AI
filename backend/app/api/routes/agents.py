from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Dict, Any

from app.core.database import get_db
from app.models.database import Agent, User
from app.models.schemas import (
    AgentCreate, AgentUpdate, AgentResponse, APIResponse, PaginatedResponse
)
from app.api.dependencies import get_current_user
from app.agents.manager import agent_manager

router = APIRouter()


@router.post("/", response_model=APIResponse)
async def create_agent(
    agent_data: AgentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new agent."""
    db_agent = Agent(
        name=agent_data.name,
        description=agent_data.description,
        instructions=agent_data.instructions,
        model=agent_data.model,
        temperature=agent_data.temperature,
        tools=agent_data.tools,
        is_public=agent_data.is_public,
        user_id=current_user.id
    )
    
    db.add(db_agent)
    db.commit()
    db.refresh(db_agent)
    
    return APIResponse(
        success=True,
        message="Agent created successfully",
        data=AgentResponse.from_orm(db_agent)
    )


@router.get("/", response_model=PaginatedResponse)
async def list_agents(
    page: int = 1,
    size: int = 10,
    search: str = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List user's agents."""
    offset = (page - 1) * size
    
    agents_query = db.query(Agent).filter(
        (Agent.user_id == current_user.id) | (Agent.is_public == True)
    )
    
    if search:
        agents_query = agents_query.filter(
            Agent.name.ilike(f"%{search}%") |
            Agent.description.ilike(f"%{search}%")
        )
    
    total = agents_query.count()
    agents = agents_query.order_by(Agent.created_at.desc()).offset(offset).limit(size).all()
    
    return PaginatedResponse(
        items=[AgentResponse.from_orm(agent) for agent in agents],
        total=total,
        page=page,
        size=size,
        pages=(total + size - 1) // size
    )


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(
    agent_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get agent by ID."""
    agent = db.query(Agent).filter(
        Agent.id == agent_id,
        (Agent.user_id == current_user.id) | (Agent.is_public == True)
    ).first()
    
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found"
        )
    
    return AgentResponse.from_orm(agent)


@router.put("/{agent_id}", response_model=APIResponse)
async def update_agent(
    agent_id: str,
    agent_data: AgentUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update agent."""
    agent = db.query(Agent).filter(
        Agent.id == agent_id,
        Agent.user_id == current_user.id
    ).first()
    
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found"
        )
    
    # Update fields
    update_data = agent_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(agent, field, value)
    
    db.commit()
    db.refresh(agent)
    
    return APIResponse(
        success=True,
        message="Agent updated successfully",
        data=AgentResponse.from_orm(agent)
    )


@router.delete("/{agent_id}", response_model=APIResponse)
async def delete_agent(
    agent_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete agent."""
    agent = db.query(Agent).filter(
        Agent.id == agent_id,
        Agent.user_id == current_user.id
    ).first()
    
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found"
        )
    
    db.delete(agent)
    db.commit()
    
    return APIResponse(
        success=True,
        message="Agent deleted successfully"
    )


@router.post("/{agent_id}/clone", response_model=APIResponse)
async def clone_agent(
    agent_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Clone an existing agent."""
    original_agent = db.query(Agent).filter(
        Agent.id == agent_id,
        (Agent.user_id == current_user.id) | (Agent.is_public == True)
    ).first()
    
    if not original_agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found"
        )
    
    # Create cloned agent
    cloned_agent = Agent(
        name=f"{original_agent.name} (Copy)",
        description=original_agent.description,
        instructions=original_agent.instructions,
        model=original_agent.model,
        temperature=original_agent.temperature,
        tools=original_agent.tools,
        is_public=False,  # Clones are private by default
        user_id=current_user.id
    )
    
    db.add(cloned_agent)
    db.commit()
    db.refresh(cloned_agent)
    
    return APIResponse(
        success=True,
        message="Agent cloned successfully",
        data=AgentResponse.from_orm(cloned_agent)
    )


@router.post("/{agent_id}/chat", response_model=APIResponse)
async def start_chat_session(
    agent_id: str,
    conversation_id: str = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Start a chat session with an agent."""
    # Verify agent exists and user has access
    agent = db.query(Agent).filter(
        Agent.id == agent_id,
        (Agent.user_id == current_user.id) | (Agent.is_public == True)
    ).first()
    
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found"
        )
    
    # Create agent session
    session_id = await agent_manager.create_agent_session(
        agent_id=agent_id,
        user_id=current_user.id,
        conversation_id=conversation_id
    )
    
    return APIResponse(
        success=True,
        message="Chat session started",
        data={
            "session_id": session_id,
            "agent_id": agent_id,
            "agent_name": agent.name
        }
    )


@router.post("/sessions/{session_id}/message", response_model=APIResponse)
async def send_message(
    session_id: str,
    message_data: Dict[str, Any],
    current_user: User = Depends(get_current_user)
):
    """Send a message to an agent session."""
    message = message_data.get("message", "")
    message_type = message_data.get("type", "user")
    
    if not message:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Message content is required"
        )
    
    try:
        response = await agent_manager.process_message(
            session_id=session_id,
            message=message,
            message_type=message_type
        )
        
        return APIResponse(
            success=True,
            message="Message processed",
            data=response
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.get("/sessions/{session_id}", response_model=APIResponse)
async def get_session_info(
    session_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get information about an agent session."""
    session_info = agent_manager.get_session_info(session_id)
    
    if not session_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    # Verify user has access to this session
    if session_info["user_id"] != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    return APIResponse(
        success=True,
        message="Session info retrieved",
        data=session_info
    )


@router.delete("/sessions/{session_id}", response_model=APIResponse)
async def close_session(
    session_id: str,
    current_user: User = Depends(get_current_user)
):
    """Close an agent session."""
    # Verify session exists and user has access
    session_info = agent_manager.get_session_info(session_id)
    
    if not session_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    if session_info["user_id"] != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    success = agent_manager.close_session(session_id)
    
    return APIResponse(
        success=success,
        message="Session closed" if success else "Failed to close session"
    )


@router.get("/sessions/", response_model=APIResponse)
async def list_active_sessions(
    current_user: User = Depends(get_current_user)
):
    """List active agent sessions for the current user."""
    sessions = agent_manager.list_active_sessions(user_id=current_user.id)
    
    return APIResponse(
        success=True,
        message="Active sessions retrieved",
        data={"sessions": sessions}
    )

