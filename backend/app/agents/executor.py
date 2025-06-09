import asyncio
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
import structlog

from app.models.agent import AgentTask, TaskStatus, ExecutionContext, ToolResult
from app.tools.base import tool_registry
from app.core.database import get_db
from app.models.database import Task, Agent, User
from sqlalchemy.orm import Session

logger = structlog.get_logger()


class TaskExecutor:
    """Handles the execution of agent tasks with tool integration."""
    
    def __init__(self):
        self.running_tasks: Dict[str, asyncio.Task] = {}
    
    async def execute_task(self, task_id: str, agent_id: str, user_id: str, 
                          instructions: str, context: Dict[str, Any] = None) -> str:
        """Execute a task asynchronously."""
        
        # Create execution context
        exec_context = ExecutionContext(
            user_id=user_id,
            agent_id=agent_id,
            task_id=task_id,
            context=context or {}
        )
        
        # Start task execution
        task_coroutine = self._run_task(exec_context, instructions)
        asyncio_task = asyncio.create_task(task_coroutine)
        self.running_tasks[task_id] = asyncio_task
        
        return task_id
    
    async def _run_task(self, context: ExecutionContext, instructions: str):
        """Internal task execution logic."""
        db = next(get_db())
        
        try:
            # Update task status to running
            task = db.query(Task).filter(Task.id == context.task_id).first()
            if task:
                task.status = TaskStatus.RUNNING.value
                task.started_at = datetime.utcnow()
                db.commit()
            
            logger.info("Starting task execution", task_id=context.task_id)
            
            # Parse instructions and create execution plan
            execution_plan = await self._create_execution_plan(instructions, context)
            
            # Execute plan steps
            results = []
            for step in execution_plan:
                step_result = await self._execute_step(step, context, db)
                results.append(step_result)
                
                # Update progress
                progress = len(results) / len(execution_plan)
                if task:
                    task.progress = progress
                    db.commit()
            
            # Mark task as completed
            if task:
                task.status = TaskStatus.COMPLETED.value
                task.completed_at = datetime.utcnow()
                task.result = {"results": [r.dict() for r in results]}
                db.commit()
            
            logger.info("Task completed successfully", task_id=context.task_id)
            
        except Exception as e:
            logger.error("Task execution failed", task_id=context.task_id, error=str(e))
            
            # Mark task as failed
            if task:
                task.status = TaskStatus.FAILED.value
                task.error = str(e)
                task.completed_at = datetime.utcnow()
                db.commit()
        
        finally:
            # Clean up
            if context.task_id in self.running_tasks:
                del self.running_tasks[context.task_id]
            db.close()
    
    async def _create_execution_plan(self, instructions: str, context: ExecutionContext) -> List[Dict[str, Any]]:
        """Create an execution plan from instructions."""
        # This is a simplified version - in a real implementation,
        # you would use an LLM to parse instructions and create a plan
        
        # For now, create a simple plan based on keywords
        plan = []
        
        if "search" in instructions.lower():
            plan.append({
                "tool": "web_search",
                "parameters": {"query": instructions},
                "description": "Search for information"
            })
        
        if "calculate" in instructions.lower():
            plan.append({
                "tool": "calculator",
                "parameters": {"expression": instructions},
                "description": "Perform calculation"
            })
        
        if "file" in instructions.lower():
            plan.append({
                "tool": "file_operations",
                "parameters": {"operation": "read", "path": "/tmp/example.txt"},
                "description": "File operation"
            })
        
        # Default plan if no specific tools detected
        if not plan:
            plan.append({
                "tool": "text_processor",
                "parameters": {"text": instructions},
                "description": "Process text input"
            })
        
        return plan
    
    async def _execute_step(self, step: Dict[str, Any], context: ExecutionContext, db: Session) -> ToolResult:
        """Execute a single step in the plan."""
        tool_name = step["tool"]
        parameters = step["parameters"]
        
        # Get tool from registry
        tool = tool_registry.get_tool(tool_name)
        if not tool:
            return ToolResult(
                success=False,
                output=None,
                error=f"Tool '{tool_name}' not found",
                execution_time=0.0
            )
        
        # Validate parameters
        validation = tool.validate_parameters(parameters)
        if not validation.valid:
            return ToolResult(
                success=False,
                output=None,
                error=f"Invalid parameters: {validation.errors}",
                execution_time=0.0
            )
        
        # Execute tool
        try:
            result = await tool.execute(parameters, context)
            logger.info("Tool executed successfully", 
                       tool=tool_name, 
                       task_id=context.task_id)
            return result
        except Exception as e:
            logger.error("Tool execution failed", 
                        tool=tool_name, 
                        task_id=context.task_id, 
                        error=str(e))
            return ToolResult(
                success=False,
                output=None,
                error=str(e),
                execution_time=0.0
            )
    
    async def cancel_task(self, task_id: str) -> bool:
        """Cancel a running task."""
        if task_id in self.running_tasks:
            task = self.running_tasks[task_id]
            task.cancel()
            
            # Update database
            db = next(get_db())
            try:
                db_task = db.query(Task).filter(Task.id == task_id).first()
                if db_task:
                    db_task.status = TaskStatus.CANCELLED.value
                    db_task.completed_at = datetime.utcnow()
                    db.commit()
            finally:
                db.close()
            
            return True
        return False
    
    def get_task_status(self, task_id: str) -> Optional[str]:
        """Get the status of a task."""
        if task_id in self.running_tasks:
            task = self.running_tasks[task_id]
            if task.done():
                return "completed" if not task.cancelled() else "cancelled"
            return "running"
        return None


# Global task executor instance
task_executor = TaskExecutor()

