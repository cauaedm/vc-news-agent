import sys
import os
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# Adicionar o diretório pai ao path para importar src
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.email_service import send_daily_briefing
from src.config import EMAIL_TO

# Conteúdo de teste (Markdown)
markdown_content = """
# Resumo do Dia: Teste de Interface

Este é um e-mail de teste para validar a nova interface visual.

### Startup X levanta R$ 20M
Uma nova proptech focada em aluguel sem fiador acaba de captar sua série A.
* **Round**: Série A
* **Investidores**: VCs Tier 1
* [Ler Matéria Completa](https://example.com)

### Queda nos juros impulsiona setor
Com a nova taxa Selic, o mercado de venture capital volta a aquecer no Brasil, trazendo novas oportunidades para founders e investidores.

### Destaques Rápidos
1. **Fintech Y** lança cartão de crédito corporativo.
2. **SaaS Z** integra com WhatsApp Business API.
3. Evento de startups acontece em SP na próxima semana.

> "A inovação é o que distingue um líder de um seguidor." - Steve Jobs

---
*Este é apenas um teste de layout.*
"""

def test_email():
    recipients = EMAIL_TO
    # Se passar um argumento, usa como e-mail de teste
    if len(sys.argv) > 1:
        recipients = [sys.argv[1]]
    
    print(f"📧 Iniciando teste de envio...")
    print(f"👥 Destinatários: {recipients}")
    
    success = send_daily_briefing(markdown_content, recipients)
    
    if success:
        print("✅ Teste concluído com sucesso! Verifique sua caixa de entrada.")
    else:
        print("❌ Falha no teste de envio.")

if __name__ == "__main__":
    test_email()
