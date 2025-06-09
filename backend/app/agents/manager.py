import asyncio
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
import structlog

from app.models.agent import AgentTask, TaskStatus, ExecutionContext
from app.agents.executor import task_executor
from app.core.database import get_db
from app.models.database import Task, Agent, User, Conversation, Message
from sqlalchemy.orm import Session

logger = structlog.get_logger()


class AgentManager:
    """Manages agent instances and their interactions."""
    
    def __init__(self):
        self.active_agents: Dict[str, Dict[str, Any]] = {}
    
    async def create_agent_session(self, agent_id: str, user_id: str, 
                                  conversation_id: Optional[str] = None) -> str:
        """Create a new agent session."""
        session_id = f"{agent_id}_{user_id}_{datetime.utcnow().timestamp()}"
        
        db = next(get_db())
        try:
            # Get agent configuration
            agent = db.query(Agent).filter(Agent.id == agent_id).first()
            if not agent:
                raise ValueError(f"Agent {agent_id} not found")
            
            # Create session
            self.active_agents[session_id] = {
                "agent_id": agent_id,
                "user_id": user_id,
                "conversation_id": conversation_id,
                "agent_config": {
                    "name": agent.name,
                    "description": agent.description,
                    "instructions": agent.instructions,
                    "tools": agent.tools or [],
                    "model": agent.model,
                    "temperature": agent.temperature
                },
                "context": {},
                "created_at": datetime.utcnow()
            }
            
            logger.info("Agent session created", 
                       session_id=session_id, 
                       agent_id=agent_id)
            
            return session_id
            
        finally:
            db.close()
    
    async def process_message(self, session_id: str, message: str, 
                            message_type: str = "user") -> Dict[str, Any]:
        """Process a message through an agent session."""
        if session_id not in self.active_agents:
            raise ValueError(f"Agent session {session_id} not found")
        
        session = self.active_agents[session_id]
        db = next(get_db())
        
        try:
            # Save user message if conversation exists
            if session["conversation_id"]:
                user_message = Message(
                    content=message,
                    role="user",
                    conversation_id=session["conversation_id"]
                )
                db.add(user_message)
                db.commit()
            
            # Process message based on type
            if message_type == "task":
                # Create and execute task
                task_id = await self._create_task(session, message, db)
                response = {
                    "type": "task_created",
                    "task_id": task_id,
                    "message": f"Task created and started: {task_id}"
                }
            else:
                # Generate conversational response
                response = await self._generate_response(session, message)
            
            # Save agent response if conversation exists
            if session["conversation_id"] and response.get("message"):
                agent_message = Message(
                    content=response["message"],
                    role="assistant",
                    metadata={"response_type": response.get("type", "text")},
                    conversation_id=session["conversation_id"]
                )
                db.add(agent_message)
                db.commit()
            
            return response
            
        finally:
            db.close()
    
    async def _create_task(self, session: Dict[str, Any], instructions: str, 
                          db: Session) -> str:
        """Create and start a new task."""
        # Create task record
        task = Task(
            title=instructions[:100] + "..." if len(instructions) > 100 else instructions,
            description=instructions,
            agent_id=session["agent_id"],
            user_id=session["user_id"],
            status=TaskStatus.PENDING.value,
            metadata={"session_id": session.get("session_id")}
        )
        
        db.add(task)
        db.commit()
        db.refresh(task)
        
        # Start task execution
        await task_executor.execute_task(
            task_id=task.id,
            agent_id=session["agent_id"],
            user_id=session["user_id"],
            instructions=instructions,
            context=session["context"]
        )
        
        return task.id
    
    async def _generate_response(self, session: Dict[str, Any], 
                               message: str) -> Dict[str, Any]:
        """Generate a conversational response."""
        # This is a simplified response generator
        # In a real implementation, you would integrate with an LLM
        
        agent_config = session["agent_config"]
        agent_name = agent_config["name"]
        
        # Simple keyword-based responses
        if "hello" in message.lower() or "hi" in message.lower():
            response_text = f"Hello! I'm {agent_name}, your AI assistant. How can I help you today?"
        elif "help" in message.lower():
            response_text = f"I'm {agent_name}, and I can help you with various tasks. You can ask me to search for information, perform calculations, manage files, and more. What would you like me to do?"
        elif "task" in message.lower():
            response_text = "I can execute tasks for you! Just describe what you need me to do, and I'll break it down into steps and execute them."
        elif "tools" in message.lower():
            available_tools = agent_config.get("tools", [])
            if available_tools:
                response_text = f"I have access to these tools: {', '.join(available_tools)}. What would you like me to do with them?"
            else:
                response_text = "I have access to various built-in tools for web search, calculations, file operations, and more."
        else:
            response_text = f"I understand you said: '{message}'. As {agent_name}, I'm ready to help you with tasks. Would you like me to execute this as a task, or do you have questions about my capabilities?"
        
        return {
            "type": "text",
            "message": response_text,
            "agent": agent_name
        }
    
    def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get information about an agent session."""
        if session_id in self.active_agents:
            session = self.active_agents[session_id].copy()
            # Remove sensitive information
            session.pop("context", None)
            return session
        return None
    
    def close_session(self, session_id: str) -> bool:
        """Close an agent session."""
        if session_id in self.active_agents:
            del self.active_agents[session_id]
            logger.info("Agent session closed", session_id=session_id)
            return True
        return False
    
    def list_active_sessions(self, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """List active agent sessions."""
        sessions = []
        for session_id, session in self.active_agents.items():
            if user_id is None or session["user_id"] == user_id:
                session_info = {
                    "session_id": session_id,
                    "agent_id": session["agent_id"],
                    "agent_name": session["agent_config"]["name"],
                    "created_at": session["created_at"],
                    "conversation_id": session.get("conversation_id")
                }
                sessions.append(session_info)
        return sessions


# Global agent manager instance
agent_manager = AgentManager()

