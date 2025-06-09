from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any

from app.core.database import get_db
from app.models.database import Tool as DBTool, User
from app.models.schemas import ToolCreate, ToolUpdate, ToolResponse, APIResponse, PaginatedResponse
from app.tools.base import tool_registry
from app.api.dependencies import get_current_user

router = APIRouter()


@router.get("/", response_model=PaginatedResponse)
async def list_tools(
    page: int = 1,
    size: int = 20,
    category: str = None,
    search: str = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List available tools."""
    offset = (page - 1) * size
    
    tools_query = db.query(DBTool).filter(DBTool.is_active == True)
    
    if category:
        tools_query = tools_query.filter(DBTool.category == category)
    
    if search:
        tools_query = tools_query.filter(
            DBTool.name.ilike(f"%{search}%") |
            DBTool.display_name.ilike(f"%{search}%") |
            DBTool.description.ilike(f"%{search}%")
        )
    
    total = tools_query.count()
    tools = tools_query.offset(offset).limit(size).all()
    
    return PaginatedResponse(
        items=[ToolResponse.from_orm(tool) for tool in tools],
        total=total,
        page=page,
        size=size,
        pages=(total + size - 1) // size
    )


@router.get("/{tool_name}", response_model=ToolResponse)
async def get_tool(
    tool_name: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get tool details by name."""
    tool = db.query(DBTool).filter(
        DBTool.name == tool_name,
        DBTool.is_active == True
    ).first()
    
    if not tool:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tool not found"
        )
    
    return ToolResponse.from_orm(tool)


@router.get("/{tool_name}/schema", response_model=APIResponse)
async def get_tool_schema(
    tool_name: str,
    current_user: User = Depends(get_current_user)
):
    """Get tool parameter schema."""
    tool = tool_registry.get_tool(tool_name)
    
    if not tool:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tool not found"
        )
    
    return APIResponse(
        success=True,
        message="Tool schema retrieved successfully",
        data={"schema": tool.get_schema()}
    )


@router.post("/{tool_name}/test", response_model=APIResponse)
async def test_tool(
    tool_name: str,
    parameters: Dict[str, Any],
    current_user: User = Depends(get_current_user)
):
    """Test tool execution with given parameters."""
    tool = tool_registry.get_tool(tool_name)
    
    if not tool:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tool not found"
        )
    
    # Validate parameters
    validation = tool.validate_parameters(parameters)
    if not validation.valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid parameters: {validation.errors}"
        )
    
    # Create test execution context
    from app.models.agent import ExecutionContext
    context = ExecutionContext(
        user_id=current_user.id,
        agent_id="test",
        task_id="test"
    )
    
    try:
        # Execute tool
        result = await tool.execute(parameters, context)
        
        return APIResponse(
            success=True,
            message="Tool executed successfully",
            data={
                "result": result.output,
                "success": result.success,
                "error": result.error,
                "execution_time": result.execution_time,
                "metadata": result.metadata
            }
        )
    except Exception as e:
        return APIResponse(
            success=False,
            message="Tool execution failed",
            data={"error": str(e)}
        )


@router.get("/categories/list", response_model=APIResponse)
async def list_tool_categories(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all tool categories."""
    categories = db.query(DBTool.category).filter(DBTool.is_active == True).distinct().all()
    category_list = [cat[0] for cat in categories if cat[0]]
    
    return APIResponse(
        success=True,
        message="Tool categories retrieved successfully",
        data={"categories": category_list}
    )


@router.post("/custom", response_model=APIResponse)
async def upload_custom_tool(
    tool_data: ToolCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload a custom tool (placeholder for future implementation)."""
    # This is a placeholder for custom tool upload functionality
    # In a full implementation, this would handle custom tool code upload and validation
    
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Custom tool upload not yet implemented"
    )

