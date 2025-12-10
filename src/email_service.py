# src/email_service.py
import os
import resend
import markdown
from datetime import datetime

def send_daily_briefing(content_markdown, recipients):
    resend.api_key = os.environ["RESEND_API_KEY"]
    
    # Converte Markdown para HTML para renderizar bem no Outlook/Gmail
    html_content = markdown.markdown(content_markdown)
    
    # Wrapper HTML com Branding CRIVO
    full_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{
                font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
                background-color: #fcefe9; /* Fundo suave */
                color: #1a1a1a;
                margin: 0;
                padding: 20px;
            }}
            .container {{
                max-width: 600px;
                margin: 0 auto;
                background-color: #ffffff;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                overflow: hidden;
            }}
            .header {{
                background-color: #1a3c34; /* Crivo Dark Green */
                padding: 40px 20px;
                text-align: center;
            }}
            .brand-name {{
                color: #ffffff;
                font-size: 32px;
                font-weight: 700;
                letter-spacing: 1px;
                margin: 0;
            }}
            .brand-subtitle {{
                color: #a3d9c9; /* Light Green Accent */
                font-size: 14px;
                text-transform: uppercase;
                letter-spacing: 2px;
                margin-top: 5px;
            }}
            .content {{
                padding: 40px 30px;
                line-height: 1.6;
            }}
            /* Estilos para o Markdown convertido */
            h3 {{
                color: #1a3c34;
                font-size: 20px;
                margin-top: 30px;
                margin-bottom: 10px;
                border-bottom: 2px solid #a3d9c9;
                padding-bottom: 5px;
            }}
            ul {{
                padding-left: 20px;
                margin-bottom: 20px;
            }}
            li {{
                margin-bottom: 8px;
                color: #444;
            }}
            strong {{
                color: #1a3c34; /* Destaque em verde escuro */
            }}
            a {{
                color: #2c5f53;
                text-decoration: none;
                font-weight: 600;
                border-bottom: 1px dotted #2c5f53;
            }}
            a:hover {{
                color: #1a3c34;
                border-bottom: 1px solid #1a3c34;
            }}
            .footer {{
                background-color: #f4f4f4;
                padding: 20px;
                text-align: center;
                font-size: 11px;
                color: #888;
                border-top: 1px solid #eaeaea;
            }}
            .tag {{
                display: inline-block;
                background-color: #e8f5f1;
                color: #1a3c34;
                padding: 2px 8px;
                border-radius: 4px;
                font-size: 11px;
                font-weight: bold;
                text-transform: uppercase;
                margin-right: 5px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <!-- Branding Texto Fixo -->
                <div class="brand-name">crivo</div>
                <div class="brand-subtitle">AI ASSISTANT</div>
            </div>
            
            <div class="content">
                <!-- Data Dynamica -->
                <p style="text-align: right; color: #999; font-size: 12px; margin-top: 0;">
                    {datetime.now().strftime('%d de %B, %Y')}
                </p>
                
                {html_content}
            </div>

            <div class="footer">
                <p>Este relatório foi gerado por Inteligência Artificial e revisado automaticamente.</p>
                <p>&copy; {datetime.now().year} Crivo Ventures. Todos os direitos reservados.</p>
            </div>
        </div>
    </body>
    </html>
    """

    params = {
        "from": "Intelligence Bot <onboarding@resend.dev>", # Configure seu domínio no Resend depois
        "to": recipients,
        "subject": f"Briefing: {datetime.now().strftime('%d/%m')}",
        "html": full_html
    }

    try:
        email = resend.Emails.send(params)
        print(f"✅ E-mail enviado com sucesso. ID: {email['id']}")
        return True
    except Exception as e:
        error_msg = f"❌ Erro CRÍTICO ao enviar e-mail. Detalhes: {str(e)}"
        print(error_msg)
        with open("error.txt", "w", encoding="utf-8") as f:
            f.write(str(e))
        return False
