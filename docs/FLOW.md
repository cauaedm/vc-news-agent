# Fluxo da Aplicação: VC News Agent

Este documento descreve como o agente de inteligência de VC opera, detalhando a responsabilidade de cada tecnologia na ordem de execução.

## Visão Geral do Processo

1. **Github Actions** inicia o processo (agendamento).
2. **Tavily** busca notícias relevantes.
3. **Crawl4AI** acessa e lê o conteúdo das páginas.
4. **Gemini** analisa e escreve a newsletter.
5. **Resend** formata e envia o e-mail.

---

## 1. Github Actions (Automação e Infraestrutura)

O **Github Actions** é o orquestrador que garante que o agente rode automaticamente todos os dias úteis.

- **Arquivo**: `.github/workflows/daily_briefing.yml`
- **Gatilho**: Agendado para rodar de segunda a sexta às **08:00 BRT** (11:00 UTC).
- **Execução**:
    1. Sobe uma máquina virtual Ubuntu.
    2. Instala Python e dependências (incluindo o navegador para o crawler).
    3. Carrega as chaves de API seguras (`secrets`).
    4. Executa o script principal: `python src/main.py`.

## 2. Tavily (Busca e Curadoria Inicial)

O **Tavily** atua como o pesquisador inicial, focado em encontrar links relevantes.

- **Função**: `search_news` em `src/main.py`.
- **Parametrização**:
    - Busca por tópicos definidos (ex: "Rodadas de investimento Seed Brasil").
    - Restringe a busca apenas a **fontes confiáveis** (ex: Startups.com.br, NeoFeed).
    - Filtra resultados para obter apenas notícias dos últimos 2 dias.
- **Saída**: Uma lista de URLs e metadados (título, data) de potenciais notícias.

*Nota: O agente aplica um filtro de data rigoroso (hoje/ontem) logo após receber os dados do Tavily para garantir frescor.*

## 3. Crawl4AI (Leitura Profunda)

O **Crawl4AI** é o componente de navegação que acessa cada link aprovado para ler o conteúdo completo.

- **Função**: `crawl_urls` em `src/main.py`.
- **Processo**:
    - Recebe as URLs filtradas.
    - Navega até a página de cada notícia simulando um usuário real.
    - Extrai o texto principal e converte para **Markdown**.
    - Limita o conteúdo (ex: 6000 caracteres) para otimizar o processamento da IA.
- **Saída**: O conteúdo textual completo de cada notícia validada.

## 4. Gemini (Inteligência e Redação)

O **Gemini (Google DeepMind)** é o "analista sênior" que lê o conteúdo bruto e escreve o relatório final.

- **Função**: `generate_newsletter` em `src/main.py`.
- **Modelo**: `gemini-2.5-flash` (rápido e eficiente).
- **Processo**:
    - Recebe o texto de todas as notícias raspadas.
    - Segue um prompt complexo para atuar como analista de VC.
    - Identifica: Startups, Founders, Investidores e Valores.
    - Ignora conteúdo irrelevante (como anúncios ou políticas de privacidade).
    - Escreve a newsletter formatada em Markdown com o estilo "VC Daily".
- **Saída**: O texto final da newsletter em Markdown.

## 5. Resend (Entrega e Design)

O **Resend** é o serviço de e-mail transacional que entrega a newsletter na caixa de entrada dos sócios.

- **Função**: `send_daily_briefing` em `src/email_service.py`.
- **Processo**:
        - Recebe o Markdown gerado pelo Gemini.
        - Converte o Markdown para **HTML**.
        - Aplica um template de e-mail com a identidade visual da **Crivo** (cores, logo, rodapé).
        - Envia o e-mail para a lista de destinatários configurada.
- **Resultado**: Os destinatários recebem o "VC Daily" pronto para leitura.
