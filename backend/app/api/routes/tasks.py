from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional

from app.core.database import get_db
from app.models.database import Task, User, Agent
from app.models.schemas import (
    TaskCreate, TaskUpdate, TaskResponse, APIResponse, PaginatedResponse
)
from app.api.dependencies import get_current_user
from app.agents.executor import task_executor
from app.agents.manager import agent_manager

router = APIRouter()


@router.post("/", response_model=APIResponse)
async def create_task(
    task_data: TaskCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create and start a new task."""
    # Verify agent exists and user has access
    agent = db.query(Agent).filter(
        Agent.id == task_data.agent_id,
        (Agent.user_id == current_user.id) | (Agent.is_public == True)
    ).first()
    
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found"
        )
    
    # Create task record
    db_task = Task(
        title=task_data.title,
        description=task_data.description,
        agent_id=task_data.agent_id,
        user_id=current_user.id,
        status="pending",
        metadata=task_data.metadata or {}
    )
    
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    
    # Start task execution in background
    background_tasks.add_task(
        task_executor.execute_task,
        task_id=db_task.id,
        agent_id=task_data.agent_id,
        user_id=current_user.id,
        instructions=task_data.description,
        context=task_data.metadata or {}
    )
    
    return APIResponse(
        success=True,
        message="Task created and started",
        data=TaskResponse.from_orm(db_task)
    )


@router.get("/", response_model=PaginatedResponse)
async def list_tasks(
    page: int = 1,
    size: int = 10,
    status_filter: str = None,
    agent_id: str = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List user's tasks."""
    offset = (page - 1) * size
    
    tasks_query = db.query(Task).filter(Task.user_id == current_user.id)
    
    if status_filter:
        tasks_query = tasks_query.filter(Task.status == status_filter)
    
    if agent_id:
        tasks_query = tasks_query.filter(Task.agent_id == agent_id)
    
    total = tasks_query.count()
    tasks = tasks_query.order_by(Task.created_at.desc()).offset(offset).limit(size).all()
    
    return PaginatedResponse(
        items=[TaskResponse.from_orm(task) for task in tasks],
        total=total,
        page=page,
        size=size,
        pages=(total + size - 1) // size
    )


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get task by ID."""
    task = db.query(Task).filter(
        Task.id == task_id,
        Task.user_id == current_user.id
    ).first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    return TaskResponse.from_orm(task)


@router.put("/{task_id}", response_model=APIResponse)
async def update_task(
    task_id: str,
    task_data: TaskUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update task."""
    task = db.query(Task).filter(
        Task.id == task_id,
        Task.user_id == current_user.id
    ).first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    # Update fields
    update_data = task_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(task, field, value)
    
    db.commit()
    db.refresh(task)
    
    return APIResponse(
        success=True,
        message="Task updated successfully",
        data=TaskResponse.from_orm(task)
    )


@router.post("/{task_id}/cancel", response_model=APIResponse)
async def cancel_task(
    task_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Cancel a running task."""
    task = db.query(Task).filter(
        Task.id == task_id,
        Task.user_id == current_user.id
    ).first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    if task.status not in ["pending", "running"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Task cannot be cancelled"
        )
    
    # Cancel the task
    success = await task_executor.cancel_task(task_id)
    
    if success:
        return APIResponse(
            success=True,
            message="Task cancelled successfully"
        )
    else:
        # Update database if executor couldn't cancel
        task.status = "cancelled"
        db.commit()
        
        return APIResponse(
            success=True,
            message="Task marked as cancelled"
        )


@router.get("/{task_id}/logs", response_model=APIResponse)
async def get_task_logs(
    task_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get task execution logs."""
    task = db.query(Task).filter(
        Task.id == task_id,
        Task.user_id == current_user.id
    ).first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    # In a real implementation, you would fetch logs from a logging system
    # For now, return basic task information
    logs = [
        {
            "timestamp": task.created_at.isoformat(),
            "level": "INFO",
            "message": f"Task '{task.title}' created"
        },
        {
            "timestamp": task.started_at.isoformat() if task.started_at else None,
            "level": "INFO",
            "message": f"Task execution started"
        }
    ]
    
    if task.completed_at:
        logs.append({
            "timestamp": task.completed_at.isoformat(),
            "level": "INFO" if task.status == "completed" else "ERROR",
            "message": f"Task {task.status}"
        })
    
    return APIResponse(
        success=True,
        message="Task logs retrieved",
        data={"logs": logs}
    )


@router.get("/{task_id}/artifacts", response_model=APIResponse)
async def get_task_artifacts(
    task_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get task artifacts (files, outputs, etc.)."""
    task = db.query(Task).filter(
        Task.id == task_id,
        Task.user_id == current_user.id
    ).first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    # Extract artifacts from task result
    artifacts = []
    if task.result:
        result_data = task.result
        if isinstance(result_data, dict) and "results" in result_data:
            for result in result_data["results"]:
                if result.get("success") and result.get("output"):
                    artifacts.append({
                        "type": "output",
                        "content": result["output"],
                        "metadata": result.get("metadata", {})
                    })
    
    return APIResponse(
        success=True,
        message="Task artifacts retrieved",
        data={"artifacts": artifacts}
    )


@router.get("/{task_id}/status", response_model=APIResponse)
async def get_task_status(
    task_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get real-time task status."""
    task = db.query(Task).filter(
        Task.id == task_id,
        Task.user_id == current_user.id
    ).first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    # Check if task is running in executor
    executor_status = task_executor.get_task_status(task_id)
    
    status_data = {
        "task_id": task_id,
        "status": executor_status or task.status,
        "progress": task.progress or 0.0,
        "created_at": task.created_at.isoformat(),
        "started_at": task.started_at.isoformat() if task.started_at else None,
        "completed_at": task.completed_at.isoformat() if task.completed_at else None,
        "error": task.error
    }
    
    return APIResponse(
        success=True,
        message="Task status retrieved",
        data=status_data
    )

