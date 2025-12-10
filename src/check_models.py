import os
from openai import OpenAI
from dotenv import load_dotenv

# Carrega .env
load_dotenv()

def check_models():
    try:
        print("🔑 Testing OpenAI API Key...")
        client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
        
        # Tenta listar os modelos
        models = client.models.list()
        
        print(f"✅ Sucesso! Você tem acesso a {len(models.data)} modelos.")
        print("Alguns modelos disponíveis:")
        
        # Filtra apenas gpt visualmente para facilitar
        gpt_models = [m.id for m in models.data if 'gpt' in m.id]
        for model in sorted(gpt_models):
            print(f"- {model}")
            
    except Exception as e:
        print(f"❌ Erro ao acessar API: {e}")

if __name__ == "__main__":
    check_models()
