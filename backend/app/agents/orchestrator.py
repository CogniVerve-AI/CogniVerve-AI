import asyncio
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from app.models.agent import (
    ExecutionContext, TaskAnalysis, ExecutionPlan, ExecutionStep, 
    StepResult, TaskResult, AgentState, RecoveryAction
)
from app.tools.base import tool_registry
from app.core.logging import get_logger

logger = get_logger(__name__)


class TaskPlanner:
    """Plans task execution by analyzing requirements and creating execution steps."""
    
    async def analyze_task(self, description: str, context: ExecutionContext) -> TaskAnalysis:
        """Analyze task to understand requirements and complexity."""
        # This is a simplified analysis - in production, use LLM for better analysis
        
        # Determine task type based on keywords
        task_type = self._determine_task_type(description)
        
        # Estimate complexity
        complexity = self._estimate_complexity(description)
        
        # Identify required tools
        required_tools = self._identify_required_tools(description)
        
        # Estimate steps and duration
        estimated_steps = len(required_tools) + 1  # +1 for planning
        estimated_duration = estimated_steps * 30  # 30 seconds per step
        
        return TaskAnalysis(
            task_type=task_type,
            complexity=complexity,
            required_tools=required_tools,
            estimated_steps=estimated_steps,
            estimated_duration=estimated_duration,
            dependencies=[],
            risks=[],
            confidence=0.8
        )
    
    async def create_plan(self, analysis: TaskAnalysis, context: ExecutionContext) -> ExecutionPlan:
        """Create detailed execution plan based on analysis."""
        steps = []
        
        # Create steps for each required tool
        for i, tool_name in enumerate(analysis.required_tools):
            step = ExecutionStep(
                id=f"step_{i+1}",
                description=f"Execute {tool_name}",
                tool_name=tool_name,
                parameters={},  # Will be filled by executor
                dependencies=[f"step_{i}"] if i > 0 else [],
                timeout=60
            )
            steps.append(step)
        
        return ExecutionPlan(
            task_id=context.task_id,
            steps=steps,
            total_estimated_time=analysis.estimated_duration,
            parallel_groups=[],
            created_at=datetime.utcnow()
        )
    
    def _determine_task_type(self, description: str) -> str:
        """Determine task type from description."""
        description_lower = description.lower()
        
        if any(word in description_lower for word in ["search", "find", "research"]):
            return "research"
        elif any(word in description_lower for word in ["write", "create", "generate"]):
            return "creation"
        elif any(word in description_lower for word in ["analyze", "calculate", "compute"]):
            return "analysis"
        elif any(word in description_lower for word in ["file", "read", "save"]):
            return "file_operation"
        else:
            return "general"
    
    def _estimate_complexity(self, description: str) -> str:
        """Estimate task complexity."""
        word_count = len(description.split())
        
        if word_count < 10:
            return "simple"
        elif word_count < 30:
            return "medium"
        else:
            return "complex"
    
    def _identify_required_tools(self, description: str) -> List[str]:
        """Identify tools needed for the task."""
        description_lower = description.lower()
        required_tools = []
        
        # Simple keyword matching - in production, use LLM for better tool selection
        if any(word in description_lower for word in ["search", "find", "research"]):
            required_tools.append("web_search")
        
        if any(word in description_lower for word in ["read", "file", "document"]):
            required_tools.append("file_read")
        
        if any(word in description_lower for word in ["write", "save", "create file"]):
            required_tools.append("file_write")
        
        if any(word in description_lower for word in ["calculate", "math", "compute"]):
            required_tools.append("calculator")
        
        # Default to web search if no specific tools identified
        if not required_tools:
            required_tools.append("web_search")
        
        return required_tools


class TaskExecutor:
    """Executes individual steps in a task plan."""
    
    async def execute_step(self, step: ExecutionStep, context: ExecutionContext) -> StepResult:
        """Execute a single step."""
        start_time = datetime.utcnow()
        
        try:
            # Get the tool
            tool = tool_registry.get_tool(step.tool_name)
            if not tool:
                raise ValueError(f"Tool not found: {step.tool_name}")
            
            # Validate parameters
            validation = tool.validate_parameters(step.parameters)
            if not validation.valid:
                raise ValueError(f"Invalid parameters: {validation.errors}")
            
            # Execute the tool
            result = await asyncio.wait_for(
                tool.execute(step.parameters, context),
                timeout=step.timeout
            )
            
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            return StepResult(
                step_id=step.id,
                success=result.success,
                output=result.output,
                error=result.error,
                execution_time=execution_time,
                metadata=result.metadata,
                artifacts=result.artifacts
            )
            
        except asyncio.TimeoutError:
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            return StepResult(
                step_id=step.id,
                success=False,
                output=None,
                error=f"Step timed out after {step.timeout} seconds",
                execution_time=execution_time
            )
        except Exception as e:
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            return StepResult(
                step_id=step.id,
                success=False,
                output=None,
                error=str(e),
                execution_time=execution_time
            )


class AgentOrchestrator:
    """Main orchestrator that manages agent execution lifecycle."""
    
    def __init__(self):
        self.planner = TaskPlanner()
        self.executor = TaskExecutor()
        self.active_tasks: Dict[str, AgentState] = {}
    
    async def execute_task(self, task_description: str, context: ExecutionContext) -> TaskResult:
        """Execute a complete task using the agent loop."""
        start_time = datetime.utcnow()
        completed_steps = []
        all_artifacts = []
        execution_log = []
        
        try:
            # Update agent state
            self.active_tasks[context.task_id] = AgentState(
                agent_id=context.agent_id,
                status="thinking",
                current_task_id=context.task_id
            )
            
            # Step 1: Analyze the task
            logger.info("Analyzing task", task_id=context.task_id, description=task_description)
            analysis = await self.planner.analyze_task(task_description, context)
            
            execution_log.append({
                "step": "analysis",
                "timestamp": datetime.utcnow().isoformat(),
                "result": {
                    "task_type": analysis.task_type,
                    "complexity": analysis.complexity,
                    "estimated_steps": analysis.estimated_steps
                }
            })
            
            # Step 2: Create execution plan
            logger.info("Creating execution plan", task_id=context.task_id)
            plan = await self.planner.create_plan(analysis, context)
            
            execution_log.append({
                "step": "planning",
                "timestamp": datetime.utcnow().isoformat(),
                "result": {
                    "total_steps": len(plan.steps),
                    "estimated_time": plan.total_estimated_time
                }
            })
            
            # Step 3: Execute plan steps
            self.active_tasks[context.task_id].status = "executing"
            
            for i, step in enumerate(plan.steps):
                # Check if step can be executed (dependencies met)
                if not all(dep in completed_steps for dep in step.dependencies):
                    continue
                
                logger.info("Executing step", task_id=context.task_id, step_id=step.id)
                self.active_tasks[context.task_id].current_step_id = step.id
                self.active_tasks[context.task_id].progress = i / len(plan.steps)
                
                # Execute step with retry logic
                step_result = await self._execute_step_with_retry(step, context)
                
                execution_log.append({
                    "step": step.id,
                    "timestamp": datetime.utcnow().isoformat(),
                    "success": step_result.success,
                    "execution_time": step_result.execution_time,
                    "error": step_result.error
                })
                
                if step_result.success:
                    completed_steps.append(step.id)
                    if step_result.artifacts:
                        all_artifacts.extend(step_result.artifacts)
                else:
                    # Handle step failure
                    recovery_action = await self._handle_step_failure(step, step_result, context)
                    if recovery_action == RecoveryAction.ABORT:
                        raise Exception(f"Step {step.id} failed: {step_result.error}")
            
            # Task completed successfully
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            self.active_tasks[context.task_id].status = "completed"
            
            return TaskResult(
                task_id=context.task_id,
                success=True,
                output={"message": "Task completed successfully", "steps_completed": len(completed_steps)},
                execution_time=execution_time,
                steps_completed=len(completed_steps),
                total_steps=len(plan.steps),
                artifacts=all_artifacts,
                metadata={"execution_log": execution_log}
            )
            
        except Exception as e:
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            self.active_tasks[context.task_id].status = "failed"
            
            logger.error("Task execution failed", task_id=context.task_id, error=str(e))
            
            return TaskResult(
                task_id=context.task_id,
                success=False,
                output=None,
                error=str(e),
                execution_time=execution_time,
                steps_completed=len(completed_steps),
                total_steps=len(plan.steps) if 'plan' in locals() else 0,
                artifacts=all_artifacts,
                metadata={"execution_log": execution_log}
            )
        finally:
            # Clean up agent state
            if context.task_id in self.active_tasks:
                del self.active_tasks[context.task_id]
    
    async def _execute_step_with_retry(self, step: ExecutionStep, context: ExecutionContext) -> StepResult:
        """Execute step with retry logic."""
        for attempt in range(step.max_retries + 1):
            step.retry_count = attempt
            result = await self.executor.execute_step(step, context)
            
            if result.success:
                return result
            
            if attempt < step.max_retries:
                logger.warning(
                    "Step failed, retrying",
                    task_id=context.task_id,
                    step_id=step.id,
                    attempt=attempt + 1,
                    error=result.error
                )
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
        
        return result
    
    async def _handle_step_failure(self, step: ExecutionStep, result: StepResult, context: ExecutionContext) -> str:
        """Handle step failure and determine recovery action."""
        # Simple recovery logic - can be enhanced with LLM-based decision making
        if "timeout" in result.error.lower():
            return RecoveryAction.RETRY
        elif "not found" in result.error.lower():
            return RecoveryAction.SKIP
        else:
            return RecoveryAction.ABORT
    
    def get_agent_state(self, task_id: str) -> Optional[AgentState]:
        """Get current state of an agent."""
        return self.active_tasks.get(task_id)


# Global orchestrator instance
orchestrator = AgentOrchestrator()

