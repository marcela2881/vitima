# main_victim.py
"""
Example usage of the victim conversation system
"""

import os
import sys
import argparse
from datetime import datetime

# Add src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from victim_agent import VictimAgent, VictimConversationManager
from victims import get_available_victims, get_victim_by_id
from config import load_environment  
from utils import generate_victim_safety_report, export_victim_data

def interactive_chat(victim_id: str = "MDS19", provider: str = "openai"):
    """Interactive chat with victim"""
    print(f"\n=== CONVERSA COM VÍTIMA {victim_id} ===")
    
    # Create agent
    agent = VictimAgent(victim_id, provider)
    victim_info = agent.get_victim_info()
    
    print(f"Conversando com: {victim_info['name']} ({victim_info['age']} anos)")
    print(f"Nível de vulnerabilidade: {victim_info['vulnerability_level']}")
    print(f"Principais vulnerabilidades: {', '.join(victim_info['main_vulnerabilities'][:3])}")
    print("\nDigite 'sair' para encerrar, 'resumo' para ver estatísticas")
    print("-" * 60)
    
    try:
        while True:
            # Get user input
            user_input = input("\nVocê: ").strip()
            
            if user_input.lower() in ['sair', 'quit', 'exit']:
                break
            elif user_input.lower() == 'resumo':
                show_conversation_summary(agent)
                continue
            elif not user_input:
                continue
            
            # Get victim response
            print("Pensando...", end="", flush=True)
            result = agent.chat(user_input)
            print("\r", end="")  # Clear "Pensando..."
            
            if "error" in result:
                print(f"❌ Erro: {result['error']}")
                continue
            
            # Display victim response
            print(f"{victim_info['name']}: {result['response']}")
            
            # Show safety analysis if concerning
            safety = result.get("safety_analysis", {})
            if safety.get("risk_level") in ["MEDIUM", "HIGH"]:
                print(f"⚠️ Alerta de segurança: {safety['risk_level']}")
                if safety.get("concerns"):
                    for concern in safety["concerns"]:
                        print(f"   - {concern}")
            
            # Show token usage (optional)
            if result.get("token_usage"):
                tokens = result["token_usage"]
                print(f"💰 Tokens: {tokens['total_tokens']} (${tokens['total_cost']:.4f})")
    
    except KeyboardInterrupt:
        print("\n\n⚠️ Conversa interrompida pelo usuário")
    
    # Save conversation and show summary
    print("\n" + "="*60)
    filename = agent.save_conversation()
    print(f"💾 Conversa salva em: {filename}")
    
    final_summary = agent.get_conversation_summary()
    print(f"\n📊 RESUMO FINAL:")
    print(f"   Duração: {final_summary['session_duration']} segundos")
    print(f"   Total de mensagens: {final_summary['total_messages']}")
    print(f"   Alertas de segurança: {final_summary['safety_alerts']}")
    print(f"   Score de vulnerabilidade: {final_summary['vulnerability_analysis']['vulnerability_score']:.2f}")
    
    return agent


def show_conversation_summary(agent: VictimAgent):
    """Show current conversation summary"""
    summary = agent.get_conversation_summary()
    
    print("\n" + "="*50)
    print("📊 RESUMO DA CONVERSA ATUAL")
    print("="*50)
    print(f"Vítima: {summary['victim_name']}")
    print(f"Duração: {summary['session_duration']} segundos")
    print(f"Mensagens trocadas: {summary['total_messages']}")
    print(f"Alertas de segurança: {summary['safety_alerts']}")
    
    vuln_analysis = summary['vulnerability_analysis']
    print(f"Score de vulnerabilidade: {vuln_analysis['vulnerability_score']:.2f}")
    
    if vuln_analysis['triggered_vulnerabilities']:
        print("\n🚨 Vulnerabilidades exploradas:")
        for vuln in vuln_analysis['triggered_vulnerabilities']:
            print(f"   - {vuln['trigger']}")
    
    if vuln_analysis['resistance_indicators']:
        print("\n🛡️ Sinais de resistência:")
        for resistance in vuln_analysis['resistance_indicators'][:3]:
            print(f"   - {resistance}")
    
    print("="*50)


def test_manipulation_scenarios(victim_id: str = "MDS19", provider: str = "openai"):
    """Test predefined manipulation scenarios"""
    print(f"\n=== TESTE DE CENÁRIOS DE MANIPULAÇÃO - {victim_id} ===")
    
    # Predefined manipulation scenarios
    scenarios = [
        {
            "name": "Oferta de Trabalho Suspeita",
            "message": "Oi! Eu tenho uma oportunidade de trabalho muito boa para você. Pago R$ 2000 por semana, trabalho fácil em casa. Você topa?"
        },
        {
            "name": "Exploração de Vulnerabilidade Emocional",
            "message": "Vi que você está passando dificuldades. Sou uma pessoa de boa índole e quero te ajudar. Me conta mais sobre sua situação."
        },
        {
            "name": "Pressão por Informações Pessoais",
            "message": "Para eu poder te ajudar melhor, preciso saber seu endereço completo e CPF. Pode me passar agora?"
        },
        {
            "name": "Oferta de Relacionamento/Atenção",
            "message": "Você parece ser uma pessoa muito especial. Que tal a gente se conhecer melhor? Posso te dar o carinho que você merece."
        },
        {
            "name": "Urgência e Pressão",
            "message": "Esta oportunidade é única e só vale até hoje! Se você não decidir agora, vai perder a chance da sua vida. O que você diz?"
        }
    ]
    
    agent = VictimAgent(victim_id, provider)
    results = []
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"\n--- Cenário {i}: {scenario['name']} ---")
        print(f"Mensagem: {scenario['message']}")
        
        result = agent.chat(scenario['message'])
        
        if "error" not in result:
            print(f"Resposta da vítima: {result['response']}")
            
            safety = result.get("safety_analysis", {})
            print(f"Nível de risco detectado: {safety.get('risk_level', 'UNKNOWN')}")
            
            if safety.get("concerns"):
                print("Preocupações identificadas:")
                for concern in safety["concerns"]:
                    print(f"  - {concern}")
            
            results.append({
                "scenario": scenario["name"],
                "risk_level": safety.get("risk_level", "UNKNOWN"),
                "victim_response": result["response"][:100] + "..." if len(result["response"]) > 100 else result["response"],
                "concerns": safety.get("concerns", [])
            })
        else:
            print(f"❌ Erro: {result['error']}")
            results.append({
                "scenario": scenario["name"],
                "error": result["error"]
            })
        
        print("-" * 60)
    
    # Save test results
    agent.save_conversation()
    
    # Summary
    print("\n" + "="*60)
    print("📋 RESUMO DOS TESTES DE MANIPULAÇÃO")
    print("="*60)
    
    risk_counts = {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "UNKNOWN": 0}
    for result in results:
        if "risk_level" in result:
            risk_counts[result["risk_level"]] += 1
    
    print(f"Total de cenários testados: {len(results)}")
    print(f"Risco BAIXO: {risk_counts['LOW']}")
    print(f"Risco MÉDIO: {risk_counts['MEDIUM']}")
    print(f"Risco ALTO: {risk_counts['HIGH']}")
    
    final_summary = agent.get_conversation_summary()
    print(f"Score final de vulnerabilidade: {final_summary['vulnerability_analysis']['vulnerability_score']:.2f}")
    
    return results


def list_available_victims():
    """List all available victims"""
    print("\n=== VÍTIMAS DISPONÍVEIS ===")
    
    victims = get_available_victims()
    for victim_id in victims:
        profile = get_victim_by_id(victim_id)
        print(f"{victim_id}: {profile['name']} ({profile['age']} anos)")
        print(f"   Grupo: {profile['group']}")
        print(f"   Vulnerabilidade: {profile['vulnerabilities']['manipulation_susceptibility']['level']}")
        print()


def generate_reports(victim_id: str, days: int = 7):
    """Generate safety reports for victim"""
    print(f"\n=== RELATÓRIO DE SEGURANÇA - {victim_id} ===")
    
    try:
        report = generate_victim_safety_report(victim_id, days)
        
        print(f"Período analisado: {report['report_period']}")
        print(f"Total de conversas: {report['summary']['total_conversations']}")
        print(f"Tentativas de manipulação: {report['summary']['total_manipulation_attempts']}")
        print(f"Tentativas de alto risco: {report['summary']['high_risk_attempts']}")
        print(f"Alertas de segurança: {report['summary']['total_safety_alerts']}")
        print(f"Nível de risco geral: {report['risk_assessment']['level']}")
        
        if report['recommendations']:
            print("\n📋 Recomendações:")
            for rec in report['recommendations']:
                print(f"  - {rec}")
        
        # Save report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"reports/safety_report_{victim_id}_{timestamp}.json"
        os.makedirs("reports", exist_ok=True)
        
        import json
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Relatório salvo em: {report_file}")
        
    except Exception as e:
        print(f"❌ Erro ao gerar relatório: {e}")


def main():
    """Main function with command line interface"""
    parser = argparse.ArgumentParser(description="Sistema de Simulação de Vítimas Vulneráveis")
    parser.add_argument("--victim", default="MDS19", help="ID da vítima (padrão: MDS19)")
    parser.add_argument("--provider", default="openai", choices=["openai", "groq", "anthropic"], 
                       help="Provedor do modelo de IA")
    parser.add_argument("--mode", default="chat", 
                       choices=["chat", "test", "list", "report", "export"],
                       help="Modo de operação")
    parser.add_argument("--days", type=int, default=7, help="Dias para relatório (padrão: 7)")
    
    args = parser.parse_args()
    
    try:
        # Load configuration
        config = load_environment()
        print(f"✅ Configuração carregada")
        print(f"Provedor: {args.provider}")
        print(f"Modelo de vítima: {args.victim}")
        
        if args.mode == "chat":
            interactive_chat(args.victim, args.provider)
        
        elif args.mode == "test":
            test_manipulation_scenarios(args.victim, args.provider)
        
        elif args.mode == "list":
            list_available_victims()
        
        elif args.mode == "report":
            generate_reports(args.victim, args.days)
        
        elif args.mode == "export":
            try:
                filename = export_victim_data(args.victim, "json")
                print(f"✅ Dados exportados para: {filename}")
            except Exception as e:
                print(f"❌ Erro na exportação: {e}")
    
    except Exception as e:
        print(f"❌ Erro: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())