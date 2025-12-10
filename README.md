# VC News Agent

Micro-pipeline de dados para inteligência de Venture Capital.
Rastreia sinais de mercado, startups em captação e movimentações de VC usando CrewAI, Tavily e GPT-4o-mini.

## Estrutura

- `src/`: Código fonte do pipeline.
- `.github/workflows/`: Automação via GitHub Actions.

## Configuração Local

1.  Instale as dependências:
    ```bash
    pip install -r requirements.txt
    ```

2.  Configure as chaves no arquivo `.env`:
    ```env
    OPENAI_API_KEY="sk-..."
    TAVILY_API_KEY="tvly-..."
    RESEND_API_KEY="re_..."
    ```

3.  Execute manualmente:
    ```bash
    python src/main.py
    ```

## Deploy

O projeto roda automaticamente seg-sex via GitHub Actions.
Configure as secrets no GitHub: `OPENAI_API_KEY`, `TAVILY_API_KEY`, `RESEND_API_KEY`.
