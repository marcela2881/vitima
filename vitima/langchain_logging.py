import os
import time
import json
from datetime import datetime
from langchain.globals import set_debug

def enable_langchain_debugging():
    """Ativa o modo debug do LangChain para exibir logs detalhados"""
    # Configura variáveis de ambiente para o LangChain
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_PROJECT"] = os.environ.get("LANGCHAIN_PROJECT", "victim_simulation")
    
    # Define um nome de sessão baseado no timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    os.environ["LANGCHAIN_SESSION"] = f"debug_session_{timestamp}"
    
    # Ativa logs verbosos
    set_debug(False)
    
    print(f"\n🔍 LangChain debugging configured:")
    print(f"   - Project: {os.environ['LANGCHAIN_PROJECT']}")
    print(f"   - Session: {os.environ['LANGCHAIN_SESSION']}")
    
    return "LangChain debugging configured"

class LangChainLogger:
    """Classe para registrar eventos do LangChain em arquivo local"""
    
    def __init__(self, log_dir="langchain_logs"):
        self.log_dir = log_dir
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_entries = []
        self.conversation_logs = {}  # Armazenar conversas por modelo
        
        # Criar diretório se não existir
        os.makedirs(log_dir, exist_ok=True)
        
    def log_model_interaction(self, model_name, prompt, response, interaction_num=0, metadata=None):
        """Registra uma interação com modelo de IA"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "model": model_name,
            "interaction_number": interaction_num,
            "prompt": prompt,
            "response": response,
            "metadata": metadata or {}
        }
        
        # Adicionar à lista de entradas
        self.log_entries.append(entry)
        
        # Adicionar à conversa específica do modelo
        if model_name not in self.conversation_logs:
            self.conversation_logs[model_name] = []
        
        self.conversation_logs[model_name].append(entry)
        
        return len(self.log_entries)

    def log_victim_conversation(self, victim_id, user_message, victim_response, metadata=None):
        """Registra uma conversa específica com vítima"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "entry_type": "victim_conversation",
            "victim_id": victim_id,
            "user_message": user_message,
            "victim_response": victim_response,
            "message_length": len(victim_response),
            "metadata": metadata or {}
        }
        
        # Adicionar à lista de entradas
        self.log_entries.append(entry)
        
        # Adicionar à conversa específica da vítima
        conversation_key = f"victim_{victim_id}"
        if conversation_key not in self.conversation_logs:
            self.conversation_logs[conversation_key] = []
        
        self.conversation_logs[conversation_key].append(entry)
        
        # Salvar imediatamente para preservar dados
        self._save_victim_conversation_immediately(victim_id, entry)
        
        return len(self.log_entries)

    def log_safety_event(self, event_type, victim_id=None, details=None, severity="LOW"):
        """Registra eventos de segurança"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "entry_type": "safety_event",
            "event_type": event_type,
            "victim_id": victim_id,
            "severity": severity,
            "details": details or {},
            "session_id": self.session_id
        }
        
        self.log_entries.append(entry)
        
        # Salvar evento de segurança imediatamente
        self._save_safety_event_immediately(entry)
        
        return len(self.log_entries)

    def log_manipulation_attempt(self, victim_id, attempt_type, user_message, victim_response, risk_level="UNKNOWN"):
        """Registra tentativas de manipulação"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "entry_type": "manipulation_attempt",
            "victim_id": victim_id,
            "attempt_type": attempt_type,
            "user_message": user_message,
            "victim_response": victim_response,
            "risk_level": risk_level,
            "session_id": self.session_id
        }
        
        self.log_entries.append(entry)
        
        # Salvar tentativa de manipulação imediatamente
        self._save_manipulation_attempt_immediately(entry)
        
        return len(self.log_entries)
        
    def log_evaluation(self, target_model, response, evaluation_result, metadata=None):
        """Registra uma avaliação ética"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "entry_type": "ethics_evaluation",
            "target_model": target_model,
            "evaluated_response": response,
            "is_appropriate": evaluation_result.get("is_appropriate", True),
            "evaluation_text": evaluation_result.get("evaluation_text", ""),
            "metadata": metadata or {}
        }
        
        # Adicionar informação mais estruturada
        try:
            eval_text = evaluation_result.get("evaluation_text", "")
            
            # Extrair classificação
            if "PROBLEMÁTICA" in eval_text:
                classification = "PROBLEMÁTICA"
            else:
                classification = "APROPRIADA"
                
            # Extrair gravidade
            severity = "DESCONHECIDA"
            if "Gravidade: BAIXA" in eval_text:
                severity = "BAIXA"
            elif "Gravidade: MÉDIA" in eval_text:
                severity = "MÉDIA"
            elif "Gravidade: ALTA" in eval_text:
                severity = "ALTA"
                
            # Adicionar esses campos estruturados
            entry["classification"] = classification
            entry["severity"] = severity
            
            # Tentar extrair explicação e recomendação
            explanation_match = eval_text.find("Explicação:")
            recommendation_match = eval_text.find("Recomendação:")
            
            if explanation_match > 0 and recommendation_match > 0:
                explanation = eval_text[explanation_match + 12:recommendation_match].strip()
                recommendation = eval_text[recommendation_match + 14:].strip()
                
                entry["explanation"] = explanation
                entry["recommendation"] = recommendation
        except Exception:
            # Se houver erro na extração, continuamos com os dados básicos
            pass
        
        # Adicionar à lista de entradas
        self.log_entries.append(entry)
        
        # Adicionar à conversa específica do modelo
        interaction_num = metadata.get("interaction", 0) if metadata else 0
        if target_model not in self.conversation_logs:
            self.conversation_logs[target_model] = []
            
        # Encontrar a posição correta para inserir a avaliação
        for i, log_entry in enumerate(self.conversation_logs[target_model]):
            if (log_entry.get("interaction_number") == interaction_num and 
                log_entry.get("entry_type") != "ethics_evaluation"):
                # Inserir após a interação correspondente
                self.conversation_logs[target_model].insert(i+1, entry)
                break
        else:
            # Se não encontrar, adicionar ao final
            self.conversation_logs[target_model].append(entry)
        
        # Salvar imediatamente após cada avaliação
        self._save_evaluation_immediately(entry)
        
        return len(self.log_entries)

    def _save_victim_conversation_immediately(self, victim_id, entry):
        """Salva uma conversa com vítima imediatamente"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]  # milliseconds
            conv_dir = os.path.join(self.log_dir, "victim_conversations", victim_id)
            os.makedirs(conv_dir, exist_ok=True)
            
            filename = os.path.join(conv_dir, f"conversation_{timestamp}.json")
            
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(entry, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Warning: Could not save victim conversation immediately: {e}")

    def _save_safety_event_immediately(self, entry):
        """Salva evento de segurança imediatamente"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safety_dir = os.path.join(self.log_dir, "safety_events")
            os.makedirs(safety_dir, exist_ok=True)
            
            severity = entry.get("severity", "unknown")
            filename = os.path.join(safety_dir, f"safety_{severity}_{timestamp}.json")
            
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(entry, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Warning: Could not save safety event immediately: {e}")

    def _save_manipulation_attempt_immediately(self, entry):
        """Salva tentativa de manipulação imediatamente"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            manipulation_dir = os.path.join(self.log_dir, "manipulation_attempts")
            os.makedirs(manipulation_dir, exist_ok=True)
            
            victim_id = entry.get("victim_id", "unknown")
            risk_level = entry.get("risk_level", "unknown")
            filename = os.path.join(manipulation_dir, f"manipulation_{victim_id}_{risk_level}_{timestamp}.json")
            
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(entry, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Warning: Could not save manipulation attempt immediately: {e}")
        
    def _save_evaluation_immediately(self, entry):
        """Salva uma avaliação ética imediatamente em um arquivo dedicado"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            target_model = entry.get("target_model", "unknown")
            eval_dir = os.path.join(self.log_dir, "evaluations")
            os.makedirs(eval_dir, exist_ok=True)
            
            filename = os.path.join(eval_dir, f"eval_{target_model}_{timestamp}.json")
            
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(entry, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Warning: Could not save evaluation immediately: {e}")

    def get_victim_conversation_summary(self, victim_id):
        """Retorna resumo da conversa com uma vítima específica"""
        conversation_key = f"victim_{victim_id}"
        if conversation_key not in self.conversation_logs:
            return None
            
        conversations = self.conversation_logs[conversation_key]
        return {
            "victim_id": victim_id,
            "total_messages": len(conversations),
            "first_message": conversations[0]["timestamp"] if conversations else None,
            "last_message": conversations[-1]["timestamp"] if conversations else None,
            "total_characters": sum(len(c.get("victim_response", "")) for c in conversations)
        }

    def get_safety_events_summary(self):
        """Retorna resumo dos eventos de segurança"""
        safety_events = [e for e in self.log_entries if e.get("entry_type") == "safety_event"]
        
        severity_counts = {}
        event_type_counts = {}
        
        for event in safety_events:
            severity = event.get("severity", "UNKNOWN")
            event_type = event.get("event_type", "UNKNOWN")
            
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
            event_type_counts[event_type] = event_type_counts.get(event_type, 0) + 1
        
        return {
            "total_events": len(safety_events),
            "by_severity": severity_counts,
            "by_type": event_type_counts
        }
    
    def save_conversation_log(self, model_name):
        """Salva o log de conversa para um modelo específico"""
        if model_name not in self.conversation_logs:
            return None
            
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            conv_dir = os.path.join(self.log_dir, "conversations")
            os.makedirs(conv_dir, exist_ok=True)
            
            filename = os.path.join(conv_dir, f"conversation_{model_name}_{timestamp}.json")
            
            # Formatar como uma conversa estruturada
            conversation_structured = {
                "model": model_name,
                "timestamp": datetime.now().isoformat(),
                "session_id": self.session_id,
                "interactions": []
            }
            
            # Organizar as interações
            for entry in self.conversation_logs[model_name]:
                if entry.get("entry_type") == "ethics_evaluation":
                    # Esta é uma avaliação ética
                    conversation_structured["interactions"].append({
                        "type": "evaluation",
                        "content": entry.get("evaluation_text", ""),
                        "is_appropriate": entry.get("is_appropriate", True),
                        "metadata": entry.get("metadata", {})
                    })
                elif entry.get("entry_type") == "victim_conversation":
                    # Esta é uma conversa com vítima
                    conversation_structured["interactions"].append({
                        "type": "victim_conversation",
                        "victim_id": entry.get("victim_id"),
                        "user_message": entry.get("user_message"),
                        "victim_response": entry.get("victim_response"),
                        "metadata": entry.get("metadata", {})
                    })
                else:
                    # Esta é uma interação normal
                    conversation_structured["interactions"].append({
                        "type": "interaction",
                        "speaker": entry.get("model"),
                        "content": entry.get("response", ""),
                        "interaction_number": entry.get("interaction_number", 0)
                    })
            
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(conversation_structured, f, indent=2, ensure_ascii=False)
                
            return filename
        except Exception as e:
            print(f"Warning: Could not save conversation log for {model_name}: {e}")
            return None
        
    def save_logs(self, filename=None):
        """Salva logs em arquivo JSON"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = os.path.join(self.log_dir, f"langchain_log_{timestamp}.json")
            
        # Preparar dados para salvar
        log_data = {
            "session_id": self.session_id,
            "timestamp": datetime.now().isoformat(),
            "entries": self.log_entries,
            "conversations_by_model": self.conversation_logs,
            "summary": {
                "total_entries": len(self.log_entries),
                "safety_events": self.get_safety_events_summary(),
                "victim_conversations": [
                    self.get_victim_conversation_summary(key.replace("victim_", ""))
                    for key in self.conversation_logs.keys() 
                    if key.startswith("victim_")
                ]
            }
        }
        
        # Salvar no arquivo
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(log_data, f, indent=2, ensure_ascii=False)
            
        # Salvar também logs de conversa individuais
        for model_name in self.conversation_logs:
            self.save_conversation_log(model_name)
            
        print(f"\n📝 LangChain logs saved to: {filename}")
        return filename

# Função para criar um decorador de rastreamento
def track_usage(func):
    """Decorador para rastrear uso de APIs de IA"""
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        duration = time.time() - start_time
        
        # Registrar uso
        print(f"📊 Call to {func.__name__} completed in {duration:.2f}s")
        
        return result
    return wrapper

# Compatibilidade com código existente
class EthicsEvaluationTracker:
    """Versão legada do rastreador de avaliações éticas (mantida para compatibilidade)"""
    
    def __init__(self, project_name="victim_simulation"):
        self.project_name = project_name
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.evaluations = []
        
        # Configurar variáveis de ambiente para LangChain
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        os.environ["LANGCHAIN_PROJECT"] = project_name
        os.environ["LANGCHAIN_SESSION"] = f"ethics_eval_{self.session_id}"
        
    def log_evaluation(self, target_model, response_content, ethics_result):
        """Registra uma avaliação ética"""
        evaluation_data = {
            "timestamp": datetime.now().isoformat(),
            "target_model": target_model,
            "response": response_content,
            "is_appropriate": ethics_result.get("is_appropriate", True),
            "evaluation": ethics_result.get("evaluation_text", ""),
            "session_id": self.session_id
        }
        
        self.evaluations.append(evaluation_data)
        return f"eval_{len(self.evaluations)}"
        
    def save_to_file(self, filename=None):
        """Salva as avaliações em arquivo"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            directory = "langchain_logs"
            os.makedirs(directory, exist_ok=True)
            filename = os.path.join(directory, f"ethics_evaluations_{timestamp}.json")
            
        output_data = {
            "session_id": self.session_id,
            "project": self.project_name,
            "timestamp": datetime.now().isoformat(),
            "evaluations": self.evaluations
        }
        
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
            
        return filename

# Manter função legada para compatibilidade
def enable_langchain_tracking():
    return enable_langchain_debugging()

# Decorador para compatibilidade com código existente
def token_usage_tracking(func):
    try:
        from langchain.callbacks import get_openai_callback
        
        def wrapper(*args, **kwargs):
            with get_openai_callback() as cb:
                result = func(*args, **kwargs)
                
                print(f"\n=== Token Usage Stats ===")
                print(f"Total Tokens: {cb.total_tokens}")
                print(f"Prompt Tokens: {cb.prompt_tokens}")
                print(f"Completion Tokens: {cb.completion_tokens}")
                print(f"Total Cost (USD): ${cb.total_cost:.6f}")
                
                # Adicionar informações de uso ao resultado (se for um dicionário)
                if isinstance(result, dict):
                    result["token_usage"] = {
                        "total_tokens": cb.total_tokens,
                        "prompt_tokens": cb.prompt_tokens,
                        "completion_tokens": cb.completion_tokens,
                        "total_cost_usd": cb.total_cost
                    }
                    
                return result
        return wrapper
    except ImportError:
        # Fallback caso a biblioteca não esteja disponível
        return track_usage(func)