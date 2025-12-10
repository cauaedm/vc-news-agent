# src/debug_gemini.py
import os
import google.generativeai as genai
from dotenv import load_dotenv

# Carrega .env
load_dotenv()

def verify_gemini():
    print("🤖 VALIDANDO SETUP FINAL DO GEMINI (gemini-2.0-flash)...\n")

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("❌ CRÍTICO: GEMINI_API_KEY não encontrada.")
        return

    genai.configure(api_key=api_key)
    
    model_name = 'gemma-3-12b-it'
    print(f"👉 Conectando ao modelo: {model_name}")

    try:
        model = genai.GenerativeModel(model_name)
        
        # Teste com contexto similar ao real
        prompt = """
        Atue como um analista financeiro. Resuma esta notícia fictícia em 1 frase:
        'A Startup TechNova levantou 500 milhões de dólares para criar fazendas de servidores subaquáticos.'
        """
        
        print("\n📝 Enviando prompt de teste...")
        response = model.generate_content(prompt)
        
        if response.text:
            print(f"\n✅ SUCESSO! Resposta gerada:\n{'-'*20}\n{response.text}\n{'-'*20}")
        else:
            print("⚠️ Resposta vazia recebida.")
            print(f"Feedback: {response.prompt_feedback}")
            
    except Exception as e:
        print(f"\n❌ ERRO FATAL: {e}")

if __name__ == "__main__":
    verify_gemini()
