from typing import List
from app.tools.base import tool_registry
from app.tools.builtin import WebSearchTool, FileReadTool, FileWriteTool, CalculatorTool


def register_builtin_tools():
    """Register all built-in tools."""
    tools = [
        WebSearchTool(),
        FileReadTool(),
        FileWriteTool(),
        CalculatorTool(),
    ]
    
    for tool in tools:
        tool_registry.register_tool(tool)


def get_available_tools() -> List[str]:
    """Get list of available tool names."""
    return [tool.name for tool in tool_registry.get_all_tools()]


def get_tools_by_category(category: str) -> List[str]:
    """Get tools in a specific category."""
    tools = tool_registry.get_tools_by_category(category)
    return [tool.name for tool in tools]

