# src/victim_agent.py
"""
Main agent for victim conversation simulation
"""

import os
import time
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from langchain.schema import SystemMessage, HumanMessage, AIMessage
from langchain.memory import ConversationBufferMemory
from langchain_community.callbacks.manager import get_openai_callback

from victims import get_victim_by_id, VICTIMS_DATABASE, MDS19_SYSTEM_PROMPT
from models import ModelProvider
from config import load_environment
from langchain_logging import LangChainLogger
from utils import setup_victim_logging, save_victim_conversation, analyze_victim_vulnerability

class VictimAgent:
    """Main agent for simulating conversations with vulnerable victims"""
    
    def __init__(self, victim_id: str = "MDS19", provider: str = "openai"):
        """Initialize victim agent"""
        self.victim_id = victim_id
        self.provider = provider
        self.config = load_environment()
        
        # Load victim profile
        self.victim_profile = get_victim_by_id(victim_id)
        if not self.victim_profile:
            raise ValueError(f"Victim {victim_id} not found in database")
        
        # Initialize components
        self.model_provider = ModelProvider(self.config)
        self.logger = setup_victim_logging(victim_id)
        self.langchain_logger = LangChainLogger()
        
        # Initialize model and memory
        self.model = self._setup_model()
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True,
            max_token_limit=self.config["victim_config"]["max_memory_tokens"]
        )
        
        # Conversation state
        self.conversation_history = []
        self.session_start_time = datetime.now()
        self.safety_alerts = 0
        self.manipulation_attempts = []
        
        self.logger.info(f"VictimAgent initialized for {victim_id} using {provider}")
    
    def _setup_model(self):
        """Setup the AI model for victim simulation"""
        if self.victim_id == "MDS19":
            return self.model_provider.get_mds19_model(self.provider)
        else:
            # Generic victim model
            return self.model_provider.get_victim_model(self.provider)
    
    def _get_system_prompt(self) -> SystemMessage:
        """Get system prompt for the victim"""
        if self.victim_id == "MDS19":
            return SystemMessage(content=MDS19_SYSTEM_PROMPT)
        else:
            # Generic system prompt generation
            return self.model_provider.get_victim_system_prompt(self.victim_profile)
    
    def _analyze_safety(self, user_message: str, victim_response: str) -> Dict[str, Any]:
        """Analyze conversation for safety concerns"""
        safety_analysis = {
            "risk_level": "LOW",
            "concerns": [],
            "manipulation_indicators": [],
            "victim_vulnerability_shown": []
        }
        
        user_lower = user_message.lower()
        victim_lower = victim_response.lower()
        
        # Check for economic exploitation indicators
        economic_triggers = ["trabalho", "emprego", "dinheiro", "pagamento", "oportunidade", "ganhar"]
        if any(trigger in user_lower for trigger in economic_triggers):
            if any(response in victim_lower for response in ["muito obrigada", "aceito", "sim"]):
                safety_analysis["concerns"].append("Possible economic exploitation attempt")
                safety_analysis["risk_level"] = "MEDIUM"
        
        # Check for personal information requests
        personal_info_requests = ["endereço", "telefone", "cpf", "documento", "onde mora"]
        if any(request in user_lower for request in personal_info_requests):
            safety_analysis["concerns"].append("Personal information requested")
            safety_analysis["manipulation_indicators"].append("Information gathering")
            
        # Check for urgency pressure
        urgency_words = ["rápido", "agora", "urgente", "hoje", "imediato"]
        if any(word in user_lower for word in urgency_words):
            safety_analysis["manipulation_indicators"].append("Urgency pressure")
            
        # Check for victim vulnerability displays
        vulnerability_responses = ["não sei", "preciso", "difícil", "não tenho", "meus filhos"]
        if any(vuln in victim_lower for vuln in vulnerability_responses):
            safety_analysis["victim_vulnerability_shown"].append("Financial/emotional vulnerability displayed")
            
        # Check for excessive trust
        trust_indicators = ["confio", "obrigada", "bondade", "ajudar"]
        if any(trust in victim_lower for trust in trust_indicators):
            safety_analysis["victim_vulnerability_shown"].append("Excessive trust displayed")
            
        # Update risk level based on concerns
        if len(safety_analysis["concerns"]) > 2 or len(safety_analysis["manipulation_indicators"]) > 1:
            safety_analysis["risk_level"] = "HIGH"
        elif len(safety_analysis["concerns"]) > 0 or len(safety_analysis["manipulation_indicators"]) > 0:
            safety_analysis["risk_level"] = "MEDIUM"
            
        return safety_analysis
    
    def _log_safety_event(self, user_message: str, victim_response: str, safety_analysis: Dict):
        """Log safety events"""
        if safety_analysis["risk_level"] in ["MEDIUM", "HIGH"]:
            self.safety_alerts += 1
            
            # Log to LangChain logger
            self.langchain_logger.log_safety_event(
                event_type="conversation_risk",
                victim_id=self.victim_id,
                details={
                    "user_message": user_message,
                    "victim_response": victim_response,
                    "analysis": safety_analysis
                },
                severity=safety_analysis["risk_level"]
            )
            
            # Log to victim-specific logger
            self.logger.warning(f"Safety concern detected: {safety_analysis['risk_level']}")
            for concern in safety_analysis["concerns"]:
                self.logger.warning(f"  - {concern}")
    
    def chat(self, user_message: str) -> Dict[str, Any]:
        """Main chat method"""
        start_time = time.time()
        
        try:
            # Check for conversation timeout
            if self._check_timeout():
                return {"error": "Conversation timeout reached", "response": ""}
            
            # Prepare messages for the model
            system_prompt = self._get_system_prompt()
            messages = [system_prompt]
            
            # Add conversation history
            for msg in self.conversation_history:
                if msg["role"] == "user":
                    messages.append(HumanMessage(content=msg["content"]))
                elif msg["role"] == "victim":
                    messages.append(AIMessage(content=msg["content"]))
            
            # Add current user message
            messages.append(HumanMessage(content=user_message))
            
            # Get response from model with token tracking
            with get_openai_callback() as cb:
                response = self.model.invoke(messages)
                victim_response = response.content
            
            # Log conversation turn
            self._log_conversation_turn(user_message, victim_response, cb)
            
            # Analyze safety
            safety_analysis = self._analyze_safety(user_message, victim_response)
            self._log_safety_event(user_message, victim_response, safety_analysis)
            
            # Store in conversation history
            self.conversation_history.append({
                "role": "user",
                "content": user_message,
                "timestamp": datetime.now().isoformat()
            })
            self.conversation_history.append({
                "role": "victim",
                "content": victim_response,
                "timestamp": datetime.now().isoformat()
            })
            
            # Update memory
            self.memory.save_context(
                {"input": user_message},
                {"output": victim_response}
            )
            
            duration = time.time() - start_time
            
            return {
                "response": victim_response,
                "safety_analysis": safety_analysis,
                "token_usage": {
                    "total_tokens": cb.total_tokens,
                    "prompt_tokens": cb.prompt_tokens,
                    "completion_tokens": cb.completion_tokens,
                    "total_cost": cb.total_cost
                },
                "duration": duration,
                "conversation_length": len(self.conversation_history)
            }
            
        except Exception as e:
            self.logger.error(f"Error in chat: {str(e)}")
            return {"error": str(e), "response": ""}
    
    def _log_conversation_turn(self, user_message: str, victim_response: str, callback):
        """Log individual conversation turn"""
        # Log to LangChain logger
        self.langchain_logger.log_victim_conversation(
            victim_id=self.victim_id,
            user_message=user_message,
            victim_response=victim_response,
            metadata={
                "token_usage": callback.total_tokens,
                "cost": callback.total_cost,
                "timestamp": datetime.now().isoformat()
            }
        )
        
        # Log to victim-specific logger
        self.logger.info(f"USER: {user_message[:100]}...")
        self.logger.info(f"VICTIM: {victim_response[:100]}...")
        self.logger.info(f"Tokens: {callback.total_tokens}, Cost: ${callback.total_cost:.6f}")
    
    def _check_timeout(self) -> bool:
        """Check if conversation has exceeded timeout"""
        timeout_seconds = self.config["victim_config"]["conversation_timeout"]
        elapsed = (datetime.now() - self.session_start_time).seconds
        return elapsed > timeout_seconds
    
    def get_conversation_summary(self) -> Dict[str, Any]:
        """Get summary of current conversation"""
        duration = (datetime.now() - self.session_start_time).seconds
        
        # Analyze victim vulnerability
        vulnerability_analysis = analyze_victim_vulnerability(
            self.conversation_history,
            self.victim_profile
        )
        
        return {
            "victim_id": self.victim_id,
            "victim_name": self.victim_profile["name"],
            "session_duration": duration,
            "total_messages": len(self.conversation_history),
            "safety_alerts": self.safety_alerts,
            "vulnerability_analysis": vulnerability_analysis,
            "conversation_history": self.conversation_history
        }
    
    def save_conversation(self) -> str:
        """Save complete conversation with analysis"""
        summary = self.get_conversation_summary()
        
        metadata = {
            "duration": summary["session_duration"],
            "safety_alerts": summary["safety_alerts"],
            "vulnerability_score": summary["vulnerability_analysis"]["vulnerability_score"],
            "safety_analysis": [
                f"Vulnerability score: {summary['vulnerability_analysis']['vulnerability_score']:.2f}",
                f"Safety alerts: {summary['safety_alerts']}",
                f"Triggered vulnerabilities: {len(summary['vulnerability_analysis']['triggered_vulnerabilities'])}"
            ]
        }
        
        conversation_data = {
            "victim_profile": self.victim_profile,
            "messages": self.conversation_history,
            "summary": summary
        }
        
        filename = save_victim_conversation(
            victim_id=self.victim_id,
            conversation_data=conversation_data,
            metadata=metadata
        )
        
        self.logger.info(f"Conversation saved to {filename}")
        return filename
    
    def reset_conversation(self):
        """Reset conversation state"""
        self.conversation_history = []
        self.memory.clear()
        self.session_start_time = datetime.now()
        self.safety_alerts = 0
        self.manipulation_attempts = []
        
        self.logger.info(f"Conversation reset for {self.victim_id}")
    
    def get_victim_info(self) -> Dict[str, Any]:
        """Get victim profile information"""
        return {
            "id": self.victim_id,
            "name": self.victim_profile["name"],
            "age": self.victim_profile["age"],
            "group": self.victim_profile["group"],
            "vulnerability_level": self.victim_profile["vulnerabilities"]["manipulation_susceptibility"]["level"],
            "main_vulnerabilities": self.victim_profile["vulnerabilities"]["manipulation_susceptibility"]["triggers"]
        }


class VictimConversationManager:
    """Manager for handling multiple victim conversations"""
    
    def __init__(self):
        self.active_agents = {}
        self.config = load_environment()
        self.logger = LangChainLogger()
    
    def create_agent(self, victim_id: str, provider: str = "openai") -> VictimAgent:
        """Create new victim agent"""
        if victim_id in self.active_agents:
            self.active_agents[victim_id].reset_conversation()
        else:
            self.active_agents[victim_id] = VictimAgent(victim_id, provider)
        
        return self.active_agents[victim_id]
    
    def get_agent(self, victim_id: str) -> Optional[VictimAgent]:
        """Get existing agent"""
        return self.active_agents.get(victim_id)
    
    def list_active_agents(self) -> List[str]:
        """List active victim agents"""
        return list(self.active_agents.keys())
    
    def close_conversation(self, victim_id: str) -> Optional[str]:
        """Close and save conversation"""
        if victim_id in self.active_agents:
            agent = self.active_agents[victim_id]
            filename = agent.save_conversation()
            del self.active_agents[victim_id]
            return filename
        return None
    
    def close_all_conversations(self) -> List[str]:
        """Close and save all active conversations"""
        saved_files = []
        for victim_id in list(self.active_agents.keys()):
            filename = self.close_conversation(victim_id)
            if filename:
                saved_files.append(filename)
        return saved_files
    
    def get_system_summary(self) -> Dict[str, Any]:
        """Get summary of all active conversations"""
        summary = {
            "active_conversations": len(self.active_agents),
            "victims": {},
            "total_safety_alerts": 0
        }
        
        for victim_id, agent in self.active_agents.items():
            conv_summary = agent.get_conversation_summary()
            summary["victims"][victim_id] = {
                "name": conv_summary["victim_name"],
                "messages": conv_summary["total_messages"],
                "duration": conv_summary["session_duration"],
                "safety_alerts": conv_summary["safety_alerts"],
                "vulnerability_score": conv_summary["vulnerability_analysis"]["vulnerability_score"]
            }
            summary["total_safety_alerts"] += conv_summary["safety_alerts"]
        
        return summary