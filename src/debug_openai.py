# src/debug_openai.py
import os
from openai import OpenAI
from dotenv import load_dotenv

# Carrega .env
load_dotenv()

def verify_openai():
    print("🤖 VALIDANDO SETUP FINAL DA OPENAI (gpt-4o-mini)...\n")

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("❌ CRÍTICO: OPENAI_API_KEY não encontrada.")
        return

    client = OpenAI(api_key=api_key)
    
    model_name = 'gpt-4o-mini'
    print(f"👉 Conectando ao modelo: {model_name}")

    try:
        # Teste com contexto similar ao real
        prompt = """
        Atue como um analista financeiro. Resuma esta notícia fictícia em 1 frase:
        'A Startup TechNova levantou 500 milhões de dólares para criar fazendas de servidores subaquáticos.'
        """
        
        print("\n📝 Enviando prompt de teste...")
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ]
        )
        
        result_text = response.choices[0].message.content
        
        if result_text:
            print(f"\n✅ SUCESSO! Resposta gerada:\n{'-'*20}\n{result_text}\n{'-'*20}")
        else:
            print("⚠️ Resposta vazia recebida.")
            
    except Exception as e:
        print(f"\n❌ ERRO FATAL: {e}")

if __name__ == "__main__":
    verify_openai()
