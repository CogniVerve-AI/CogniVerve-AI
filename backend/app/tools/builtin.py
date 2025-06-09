from app.tools.base import tool_registry, BaseTool, ToolResult, ParameterValidation
from typing import Dict, Any
import asyncio
import time
import json
import httpx
import os
import tempfile


class WebSearchTool(BaseTool):
    """Tool for searching the web."""
    
    name = "web_search"
    display_name = "Web Search"
    description = "Search the web for information"
    category = "information"
    
    def get_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query"
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of results",
                    "default": 5,
                    "minimum": 1,
                    "maximum": 20
                }
            },
            "required": ["query"]
        }
    
    def validate_parameters(self, parameters: Dict[str, Any]) -> ParameterValidation:
        errors = []
        
        if "query" not in parameters:
            errors.append("query is required")
        elif not isinstance(parameters["query"], str) or not parameters["query"].strip():
            errors.append("query must be a non-empty string")
        
        if "max_results" in parameters:
            max_results = parameters["max_results"]
            if not isinstance(max_results, int) or max_results < 1 or max_results > 20:
                errors.append("max_results must be an integer between 1 and 20")
        
        return ParameterValidation(valid=len(errors) == 0, errors=errors)
    
    async def execute(self, parameters: Dict[str, Any], context) -> ToolResult:
        start_time = time.time()
        
        try:
            query = parameters["query"]
            max_results = parameters.get("max_results", 5)
            
            # Simulate web search (in real implementation, use search API)
            await asyncio.sleep(0.5)  # Simulate API call
            
            results = [
                {
                    "title": f"Search result {i+1} for '{query}'",
                    "url": f"https://example.com/result-{i+1}",
                    "snippet": f"This is a sample search result snippet for query '{query}'. It contains relevant information about the topic."
                }
                for i in range(max_results)
            ]
            
            execution_time = time.time() - start_time
            
            return ToolResult(
                success=True,
                output=results,
                execution_time=execution_time,
                metadata={"query": query, "result_count": len(results)}
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            return ToolResult(
                success=False,
                output=None,
                error=str(e),
                execution_time=execution_time
            )


class CalculatorTool(BaseTool):
    """Tool for performing calculations."""
    
    name = "calculator"
    display_name = "Calculator"
    description = "Perform mathematical calculations"
    category = "computation"
    
    def get_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "Mathematical expression to evaluate"
                }
            },
            "required": ["expression"]
        }
    
    def validate_parameters(self, parameters: Dict[str, Any]) -> ParameterValidation:
        errors = []
        
        if "expression" not in parameters:
            errors.append("expression is required")
        elif not isinstance(parameters["expression"], str) or not parameters["expression"].strip():
            errors.append("expression must be a non-empty string")
        
        return ParameterValidation(valid=len(errors) == 0, errors=errors)
    
    async def execute(self, parameters: Dict[str, Any], context) -> ToolResult:
        start_time = time.time()
        
        try:
            expression = parameters["expression"]
            
            # Simple expression evaluation (in production, use safer evaluation)
            # This is a simplified version - use ast.literal_eval or similar for safety
            allowed_chars = set("0123456789+-*/()., ")
            if not all(c in allowed_chars for c in expression):
                raise ValueError("Expression contains invalid characters")
            
            result = eval(expression)
            execution_time = time.time() - start_time
            
            return ToolResult(
                success=True,
                output={"expression": expression, "result": result},
                execution_time=execution_time,
                metadata={"expression": expression}
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            return ToolResult(
                success=False,
                output=None,
                error=f"Calculation error: {str(e)}",
                execution_time=execution_time
            )


class FileOperationsTool(BaseTool):
    """Tool for file operations."""
    
    name = "file_operations"
    display_name = "File Operations"
    description = "Read, write, and manage files"
    category = "file_system"
    
    def get_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "enum": ["read", "write", "list", "create_temp"],
                    "description": "File operation to perform"
                },
                "path": {
                    "type": "string",
                    "description": "File or directory path"
                },
                "content": {
                    "type": "string",
                    "description": "Content to write (for write operation)"
                }
            },
            "required": ["operation"]
        }
    
    def validate_parameters(self, parameters: Dict[str, Any]) -> ParameterValidation:
        errors = []
        
        operation = parameters.get("operation")
        if not operation:
            errors.append("operation is required")
        elif operation not in ["read", "write", "list", "create_temp"]:
            errors.append("operation must be one of: read, write, list, create_temp")
        
        if operation in ["read", "write", "list"] and not parameters.get("path"):
            errors.append("path is required for this operation")
        
        if operation == "write" and not parameters.get("content"):
            errors.append("content is required for write operation")
        
        return ParameterValidation(valid=len(errors) == 0, errors=errors)
    
    async def execute(self, parameters: Dict[str, Any], context) -> ToolResult:
        start_time = time.time()
        
        try:
            operation = parameters["operation"]
            
            if operation == "create_temp":
                # Create temporary file
                with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
                    content = parameters.get("content", "Temporary file created by CogniVerve-AI")
                    f.write(content)
                    temp_path = f.name
                
                execution_time = time.time() - start_time
                return ToolResult(
                    success=True,
                    output={"path": temp_path, "content": content},
                    execution_time=execution_time,
                    metadata={"operation": operation, "path": temp_path}
                )
            
            elif operation == "read":
                path = parameters["path"]
                # For security, only allow reading from temp directory
                if not path.startswith("/tmp/"):
                    raise ValueError("Can only read files from /tmp/ directory")
                
                try:
                    with open(path, 'r') as f:
                        content = f.read()
                    
                    execution_time = time.time() - start_time
                    return ToolResult(
                        success=True,
                        output={"path": path, "content": content},
                        execution_time=execution_time,
                        metadata={"operation": operation, "path": path}
                    )
                except FileNotFoundError:
                    raise ValueError(f"File not found: {path}")
            
            elif operation == "write":
                path = parameters["path"]
                content = parameters["content"]
                
                # For security, only allow writing to temp directory
                if not path.startswith("/tmp/"):
                    raise ValueError("Can only write files to /tmp/ directory")
                
                with open(path, 'w') as f:
                    f.write(content)
                
                execution_time = time.time() - start_time
                return ToolResult(
                    success=True,
                    output={"path": path, "bytes_written": len(content)},
                    execution_time=execution_time,
                    metadata={"operation": operation, "path": path}
                )
            
            elif operation == "list":
                path = parameters["path"]
                
                # For security, only allow listing temp directory
                if not path.startswith("/tmp/"):
                    raise ValueError("Can only list files in /tmp/ directory")
                
                if os.path.isdir(path):
                    files = os.listdir(path)
                    execution_time = time.time() - start_time
                    return ToolResult(
                        success=True,
                        output={"path": path, "files": files},
                        execution_time=execution_time,
                        metadata={"operation": operation, "path": path}
                    )
                else:
                    raise ValueError(f"Directory not found: {path}")
            
        except Exception as e:
            execution_time = time.time() - start_time
            return ToolResult(
                success=False,
                output=None,
                error=str(e),
                execution_time=execution_time
            )


class TextProcessorTool(BaseTool):
    """Tool for text processing operations."""
    
    name = "text_processor"
    display_name = "Text Processor"
    description = "Process and analyze text"
    category = "text"
    
    def get_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "Text to process"
                },
                "operation": {
                    "type": "string",
                    "enum": ["count_words", "count_chars", "uppercase", "lowercase", "reverse"],
                    "description": "Text operation to perform",
                    "default": "count_words"
                }
            },
            "required": ["text"]
        }
    
    def validate_parameters(self, parameters: Dict[str, Any]) -> ParameterValidation:
        errors = []
        
        if "text" not in parameters:
            errors.append("text is required")
        elif not isinstance(parameters["text"], str):
            errors.append("text must be a string")
        
        operation = parameters.get("operation", "count_words")
        valid_operations = ["count_words", "count_chars", "uppercase", "lowercase", "reverse"]
        if operation not in valid_operations:
            errors.append(f"operation must be one of: {', '.join(valid_operations)}")
        
        return ParameterValidation(valid=len(errors) == 0, errors=errors)
    
    async def execute(self, parameters: Dict[str, Any], context) -> ToolResult:
        start_time = time.time()
        
        try:
            text = parameters["text"]
            operation = parameters.get("operation", "count_words")
            
            if operation == "count_words":
                result = len(text.split())
            elif operation == "count_chars":
                result = len(text)
            elif operation == "uppercase":
                result = text.upper()
            elif operation == "lowercase":
                result = text.lower()
            elif operation == "reverse":
                result = text[::-1]
            
            execution_time = time.time() - start_time
            
            return ToolResult(
                success=True,
                output={"operation": operation, "result": result, "original_text": text},
                execution_time=execution_time,
                metadata={"operation": operation, "text_length": len(text)}
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            return ToolResult(
                success=False,
                output=None,
                error=str(e),
                execution_time=execution_time
            )


def register_builtin_tools():
    """Register all built-in tools."""
    tools = [
        WebSearchTool(),
        CalculatorTool(),
        FileOperationsTool(),
        TextProcessorTool()
    ]
    
    for tool in tools:
        tool_registry.register_tool(tool)

