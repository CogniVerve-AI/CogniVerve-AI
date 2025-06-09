from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from app.models.agent import ExecutionContext, ToolResult, ValidationResult


class Tool(ABC):
    """Abstract base class for all tools."""
    
    def __init__(self, name: str, description: str, category: str = "general"):
        self.name = name
        self.description = description
        self.category = category
        self.required_permissions = []
    
    @abstractmethod
    async def execute(self, parameters: Dict[str, Any], context: ExecutionContext) -> ToolResult:
        """Execute the tool with given parameters."""
        pass
    
    @abstractmethod
    def get_schema(self) -> Dict[str, Any]:
        """Return JSON schema for tool parameters."""
        pass
    
    def validate_parameters(self, parameters: Dict[str, Any]) -> ValidationResult:
        """Validate input parameters against schema."""
        # Basic validation - can be overridden by specific tools
        schema = self.get_schema()
        required = schema.get("required", [])
        properties = schema.get("properties", {})
        
        errors = []
        warnings = []
        
        # Check required parameters
        for param in required:
            if param not in parameters:
                errors.append(f"Missing required parameter: {param}")
        
        # Check parameter types
        for param, value in parameters.items():
            if param in properties:
                expected_type = properties[param].get("type")
                if expected_type and not self._validate_type(value, expected_type):
                    errors.append(f"Parameter {param} has invalid type. Expected {expected_type}")
        
        return ValidationResult(valid=len(errors) == 0, errors=errors, warnings=warnings)
    
    def _validate_type(self, value: Any, expected_type: str) -> bool:
        """Validate value type."""
        type_mapping = {
            "string": str,
            "integer": int,
            "number": (int, float),
            "boolean": bool,
            "array": list,
            "object": dict
        }
        
        expected_python_type = type_mapping.get(expected_type)
        if expected_python_type:
            return isinstance(value, expected_python_type)
        return True


class ToolRegistry:
    """Registry for managing available tools."""
    
    def __init__(self):
        self._tools: Dict[str, Tool] = {}
        self._categories: Dict[str, List[str]] = {}
    
    def register_tool(self, tool: Tool) -> None:
        """Register a new tool."""
        self._tools[tool.name] = tool
        
        # Update categories
        if tool.category not in self._categories:
            self._categories[tool.category] = []
        if tool.name not in self._categories[tool.category]:
            self._categories[tool.category].append(tool.name)
    
    def get_tool(self, name: str) -> Optional[Tool]:
        """Get tool by name."""
        return self._tools.get(name)
    
    def get_tools_by_category(self, category: str) -> List[Tool]:
        """Get all tools in a category."""
        tool_names = self._categories.get(category, [])
        return [self._tools[name] for name in tool_names if name in self._tools]
    
    def get_all_tools(self) -> List[Tool]:
        """Get all registered tools."""
        return list(self._tools.values())
    
    def search_tools(self, query: str, context: str = "") -> List[Tool]:
        """Find relevant tools for a query."""
        query_lower = query.lower()
        relevant_tools = []
        
        for tool in self._tools.values():
            # Search in name and description
            if (query_lower in tool.name.lower() or 
                query_lower in tool.description.lower() or
                query_lower in tool.category.lower()):
                relevant_tools.append(tool)
        
        return relevant_tools
    
    def validate_tool_access(self, user_permissions: List[str], tool: Tool) -> bool:
        """Check if user has permissions to use tool."""
        if not tool.required_permissions:
            return True
        
        return all(perm in user_permissions for perm in tool.required_permissions)
    
    def get_tool_schemas(self) -> Dict[str, Dict[str, Any]]:
        """Get schemas for all tools."""
        return {name: tool.get_schema() for name, tool in self._tools.items()}


# Global tool registry instance
tool_registry = ToolRegistry()

