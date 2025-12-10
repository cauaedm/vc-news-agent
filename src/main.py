# src/main.py
import asyncio
import os
import json
import google.generativeai as genai
from tavily import TavilyClient
from crawl4ai import AsyncWebCrawler
# from openai import OpenAI # Removed OpenAI
from config import TRUSTED_SOURCES, SEARCH_TOPIC, EMAIL_TO
from email_service import send_daily_briefing
from dotenv import load_dotenv

# Carrega .env
load_dotenv()

async def crawl_urls(urls):
    """Crawl URLs using Crawl4AI."""
    print(f"🕷️ Crawling {len(urls)} URLs...")
    results = []
    async with AsyncWebCrawler(verbose=True) as crawler:
        for url in urls:
            try:
                result = await crawler.arun(url=url)
                if result.success:
                     # Limita o tamanho do conteúdo para não estourar o contexto do LLM
                    content_snippet = result.markdown[:4000] # Reduzido para 4k para evitar Rate Limit
                    results.append({"url": url, "content": content_snippet})
                    print(f"✅ Crawled: {url}")
                else:
                    print(f"❌ Failed to crawl {url}: {result.error_message}")
            except Exception as e:
                print(f"⚠️ Error processing {url}: {e}")
    return results

def generate_newsletter(articles):
    """Summarize articles using Google Gemini."""
    print("🧠 Generating analysis with Google Gemini...")
    
    genai.configure(api_key=os.environ["GEMINI_API_KEY"])
    model = genai.GenerativeModel('gemma-3-12b-it') # Usando modelo confirmado disponível

    # Monta o prompt
    articles_text = ""
    for i, article in enumerate(articles):
        articles_text += f"\n\n--- Article {i+1} ({article['url']}) ---\n{article['content']}"

    prompt = f"""
    Atue como um analista de Venture Capital especializado no mercado Brasileiro (LatAm). 
    Analise os artigos abaixo e identifique **novas rodadas de investimento (Seed/Pre-Seed)** e **novas startups** promissoras.

    **Filtros de Qualidade:**
    - Priorize empresas brasileiras ou com operação no Brasil.
    - Busque detalhes específicos: Founders, Quem investiu (VCs), Valuation.
    - Ignore notícias genéricas de mercado ou anúncios corporativos sem deal flow.

    **Formato de Saída (Markdown):**
    Para cada deal relevante encontrado, estuture assim:

    ### 🇧🇷 [Nome da Startup] - [Tipo da Rodada: Pre-Seed/Seed/Series A]
    - **O Deal:** Resumo de 1 linha sobre o aporte (Valor captado).
    - **Quem são:** Descrição curta do que a empresa faz.
    - **Founders:** [Nomes dos fundadores]
    - **Investidores (VCs):** [Lista de fundos que entraram]
    - **Valuation:** [Valor se disponível, ou "Não divulgado"]
    - **Tese:** Por que isso é interessante? (1 linha)
    - [Fonte Original](URL)

    **Sinais Fracos (Early Stage):**
    - Liste brevemente startups que acabaram de nascer ou estão em stealth, se houver menção.

    Artigos para análise:
    {articles_text}
    """

    try:
        response = model.generate_content(prompt)
        if not response.text:
            raise ValueError("Gemini returned empty response")
        return response.text
    except Exception as e:
        print(f"❌ Erro na geração com Gemini: {e}")
        print("⚠️ Falling back to raw crawl data...")
        
        # Fallback: Monta um email com os dados brutos do Crawl4AI
        fallback_content = "# ⚠️ Gemini Failed - Raw Crawl Data\n\n"
        fallback_content += "> O modelo de IA falhou ao gerar o resumo. Abaixo estão os dados extraídos automaticamente.\n\n"
        
        for article in articles:
            # Limita o tamanho de cada artigo no fallback para não ficar gigante
            snippet = article['content'][:500].replace('\n', ' ') + "..."
            fallback_content += f"### [{article['url']}]({article['url']})\n"
            fallback_content += f"{snippet}\n\n"
            
        return fallback_content

async def run_pipeline(dry_run=False):
    print(f"🚀 Starting VC Intelligence Pipeline (Gemini Powered) {'[DRY RUN MODE]' if dry_run else ''} ...")
    
    # 1. Search with Tavily
    if dry_run:
        print("🔍 [DRY RUN] Skipping Tavily Search. Using mock URLs.")
        urls = ["https://techcrunch.com/mock-article-1", "https://venturebeat.com/mock-article-2"]
    else:
        tavily = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])
        print(f"🔍 Searching for: {SEARCH_TOPIC}")
        print(f"🎯 Strict Mode: Searching only in {len(TRUSTED_SOURCES)} trusted domains (Last 24h).")
        
        search_response = tavily.search(
            query=SEARCH_TOPIC,
            topic="news", # Força busca de notícias recentes
            include_domains=TRUSTED_SOURCES,
            days=1, # Apenas notícias de ontem para hoje
            max_results=5 # Reduzido para evitar Rate Limit
        )
        urls = [result['url'] for result in search_response['results']]
        
    print(f"🔗 Found {len(urls)} relevant URLs.")

    # 2. Crawl Content
    if dry_run:
        print("🕷️ [DRY RUN] Skipping Crawl. Using mock content.")
        crawled_data = [
            {"url": "https://techcrunch.com/mock-article-1", "content": "# Mock Article 1\nStartup raises $50M."},
            {"url": "https://venturebeat.com/mock-article-2", "content": "# Mock Article 2\nAI Company acquired."}
        ]
    else:
        crawled_data = await crawl_urls(urls)
    
    if not crawled_data:
        print("❌ No content crawled. Aborting.")
        return

     # 3. Summarize
    if dry_run:
         print("🧠 [DRY RUN] Skipping Gemini Generation. Using mock summary.")
         import textwrap
         newsletter_md = textwrap.dedent("""
          ### [MOCK] Startup Mock Captou $50M
          - **O que aconteceu:** Rodada fictícia para teste.
          - **Por que importa:** Validação do modo dry-run.
          - [Ler Fonte](https://mock.com)
          """)
    else:
        newsletter_md = generate_newsletter(crawled_data)
    
    # 4. Send Email
    print("📧 Sending email...")
    # No dry-run for email as requested? "funcionalidades pré-envio". The user wants to test PRE-sending. 
    # But usually dry-run implies *not* sending or sending to safe target.
    # The user said: "gera um teste para as funcionalidades pré-envio para não consumir todas os créditos de chamadas às apis"
    # This implies they WANT to verify the flow, maybe even send the email, but avoid Tavily/Gemini usage.
    # So I will SEND the email even in dry-run, because sending is cheap/free (Resend) and verifies the final delivery.
    
    if send_daily_briefing(newsletter_md, EMAIL_TO):
        print("🎉 Pipeline completed successfully!")
    else:
        print("⚠️ Pipeline finished but email failed.")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="VC News Agent Pipeline")
    parser.add_argument("--dry-run", action="store_true", help="Run in test mode without using API credits (mocks Search and Summary)")
    args = parser.parse_args()

    asyncio.run(run_pipeline(dry_run=args.dry_run))
