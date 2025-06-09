from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime
import uuid


@dataclass
class ExecutionContext:
    """Context information for agent execution."""
    user_id: str
    agent_id: str
    task_id: str
    conversation_id: Optional[str] = None
    session_id: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        if self.session_id is None:
            self.session_id = str(uuid.uuid4())


@dataclass
class TaskAnalysis:
    """Result of task analysis."""
    task_type: str
    complexity: str  # simple, medium, complex
    required_tools: List[str]
    estimated_steps: int
    estimated_duration: int  # seconds
    dependencies: List[str]
    risks: List[str]
    confidence: float


@dataclass
class ExecutionStep:
    """Individual step in execution plan."""
    id: str
    description: str
    tool_name: str
    parameters: Dict[str, Any]
    dependencies: List[str]
    timeout: int
    retry_count: int = 0
    max_retries: int = 3


@dataclass
class ExecutionPlan:
    """Complete execution plan for a task."""
    task_id: str
    steps: List[ExecutionStep]
    total_estimated_time: int
    parallel_groups: List[List[str]]  # Steps that can run in parallel
    created_at: datetime
    
    def get_next_step(self, completed_steps: List[str]) -> Optional[ExecutionStep]:
        """Get the next step that can be executed."""
        for step in self.steps:
            if step.id not in completed_steps:
                # Check if all dependencies are completed
                if all(dep in completed_steps for dep in step.dependencies):
                    return step
        return None


@dataclass
class StepResult:
    """Result of executing a single step."""
    step_id: str
    success: bool
    output: Any
    error: Optional[str] = None
    execution_time: float = 0.0
    metadata: Dict[str, Any] = None
    artifacts: List[str] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        if self.artifacts is None:
            self.artifacts = []


@dataclass
class TaskResult:
    """Final result of task execution."""
    task_id: str
    success: bool
    output: Any
    error: Optional[str] = None
    execution_time: float = 0.0
    steps_completed: int = 0
    total_steps: int = 0
    artifacts: List[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.artifacts is None:
            self.artifacts = []
        if self.metadata is None:
            self.metadata = {}


@dataclass
class ToolResult:
    """Result of tool execution."""
    tool_name: str
    success: bool
    output: Any
    error: Optional[str] = None
    execution_time: float = 0.0
    metadata: Dict[str, Any] = None
    artifacts: List[str] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        if self.artifacts is None:
            self.artifacts = []


@dataclass
class Memory:
    """Memory item for agent context."""
    id: str
    content: str
    memory_type: str
    embedding: Optional[List[float]] = None
    metadata: Dict[str, Any] = None
    relevance_score: float = 0.0
    created_at: datetime = None
    accessed_at: datetime = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.accessed_at is None:
            self.accessed_at = datetime.utcnow()


@dataclass
class AgentState:
    """Current state of an agent."""
    agent_id: str
    status: str  # idle, thinking, executing, waiting
    current_task_id: Optional[str] = None
    current_step_id: Optional[str] = None
    progress: float = 0.0
    last_activity: datetime = None
    memory_context: List[Memory] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.last_activity is None:
            self.last_activity = datetime.utcnow()
        if self.memory_context is None:
            self.memory_context = []
        if self.metadata is None:
            self.metadata = {}


class RecoveryAction:
    """Action to take for error recovery."""
    RETRY = "retry"
    SKIP = "skip"
    ABORT = "abort"
    FALLBACK = "fallback"


@dataclass
class ValidationResult:
    """Result of parameter validation."""
    valid: bool
    errors: List[str] = None
    warnings: List[str] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if self.warnings is None:
            self.warnings = []

