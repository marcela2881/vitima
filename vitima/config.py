import os
from dotenv import load_dotenv

def load_environment():
    """Carrega variáveis de ambiente do arquivo .env"""
    load_dotenv()
    
    required_vars = ["OPENAI_API_KEY", "GROQ_API_KEY"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        raise EnvironmentError(f"Variáveis de ambiente obrigatórias não definidas: {', '.join(missing_vars)}")
    
    # Definir variáveis de ambiente para LangChain
    os.environ["LANGCHAIN_PROJECT"] = os.getenv("LANGCHAIN_PROJECT", "victim_simulation")
    os.environ["LANGCHAIN_TRACING_V2"] = os.getenv("LANGCHAIN_TRACING_V2", "true")
    
    # Configurar a chave de API LangChain se fornecida
    if os.getenv("LANGCHAIN_API_KEY"):
        os.environ["LANGCHAIN_API_KEY"] = os.getenv("LANGCHAIN_API_KEY")
    
    # Configurar o nome da sessão com base no timestamp
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    os.environ["LANGCHAIN_SESSION"] = f"victim_conversation_{timestamp}"
    
    print(f"LangChain configurado: Projeto={os.environ['LANGCHAIN_PROJECT']}, Sessão={os.environ['LANGCHAIN_SESSION']}")
    
    # Carregar configurações do modelo cérebro
    cerebro_provider = os.getenv("CEREBRO_PROVIDER", "openai").strip().lower()
    cerebro_model = os.getenv("CEREBRO_MODEL", "gpt-4o").strip()
    
    # Carregar lista de modelos alvo
    target_models_str = os.getenv("TARGET_MODELS", "llama3-8b-8192,gpt-3.5-turbo")
    target_models = [model.strip() for model in target_models_str.split(",") if model.strip()]
    
    # Configurações específicas para o sistema de vítimas
    victim_config = {
        "default_victim": os.getenv("DEFAULT_VICTIM", "MDS19"),
        "conversation_memory_type": os.getenv("MEMORY_TYPE", "buffer").lower(),
        "max_memory_tokens": int(os.getenv("MAX_MEMORY_TOKENS", "2000")),
        "temperature": float(os.getenv("VICTIM_TEMPERATURE", "0.8")),
        "max_tokens": int(os.getenv("VICTIM_MAX_TOKENS", "500")),
        "enable_safety_checks": os.getenv("ENABLE_SAFETY_CHECKS", "true").lower() == "true",
        "log_conversations": os.getenv("LOG_CONVERSATIONS", "true").lower() == "true",
        "conversation_timeout": int(os.getenv("CONVERSATION_TIMEOUT", "1800")),  # 30 minutos
    }
    
    return {
        # Configurações originais
        "openai_api_key": os.getenv("OPENAI_API_KEY"),
        "groq_api_key": os.getenv("GROQ_API_KEY"),
        "google_api_key": os.getenv("GOOGLE_API_KEY"),
        "anthropic_api_key": os.getenv("ANTHROPIC_API_KEY"),
        "max_interacoes": int(os.getenv("MAX_INTERACOES", "50")),
        "tema_padrao": os.getenv("TEMA_PADRAO", "diferenças de idade em relacionamentos"),
        "cerebro_provider": cerebro_provider,
        "cerebro_model": cerebro_model,
        "target_models": target_models,
        "avaliacao_etica": os.getenv("AVALIACAO_ETICA", "true").lower() == "true",
        "logs_detalhados": os.getenv("LOGS_DETALHADOS", "true").lower() == "true",
        
        # Novas configurações para vítimas
        "victim_config": victim_config,
        
        # Configurações de segurança
        "safety_config": {
            "block_harmful_content": os.getenv("BLOCK_HARMFUL_CONTENT", "true").lower() == "true",
            "log_security_events": os.getenv("LOG_SECURITY_EVENTS", "true").lower() == "true",
            "max_conversation_length": int(os.getenv("MAX_CONVERSATION_LENGTH", "100")),
            "enable_content_filtering": os.getenv("ENABLE_CONTENT_FILTERING", "true").lower() == "true"
        }
    }

def get_victim_model_config(provider="openai"):
    """Retorna configuração específica do modelo para vítimas"""
    base_config = {
        "temperature": float(os.getenv("VICTIM_TEMPERATURE", "0.8")),
        "max_tokens": int(os.getenv("VICTIM_MAX_TOKENS", "500")),
        "top_p": float(os.getenv("VICTIM_TOP_P", "0.9")),
        "frequency_penalty": float(os.getenv("VICTIM_FREQUENCY_PENALTY", "0.1")),
        "presence_penalty": float(os.getenv("VICTIM_PRESENCE_PENALTY", "0.1"))
    }
    
    if provider == "openai":
        base_config.update({
            "model": os.getenv("VICTIM_OPENAI_MODEL", "gpt-4o-mini")
        })
    elif provider == "groq":
        base_config.update({
            "model": os.getenv("VICTIM_GROQ_MODEL", "llama3-8b-8192")
        })
    elif provider == "anthropic":
        base_config.update({
            "model": os.getenv("VICTIM_ANTHROPIC_MODEL", "claude-3-haiku-20240307")
        })
    
    return base_config