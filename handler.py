import json
import os
import urllib.request
import urllib.parse
from datetime import datetime
from time import sleep

def get_environment_variables():
    """Valida e retorna as variáveis de ambiente necessárias"""
    groq_api_key = os.environ.get('GROQ_API_KEY')
    telegram_bot_token = os.environ.get('TELEGRAM_BOT_TOKEN')
    telegram_chat_id = os.environ.get('TELEGRAM_CHAT_ID')
    missing_vars = []
    if not groq_api_key:
        missing_vars.append('GROQ_API_KEY')
    if not telegram_bot_token:
        missing_vars.append('TELEGRAM_BOT_TOKEN')
    if not telegram_chat_id:
        missing_vars.append('TELEGRAM_CHAT_ID')
    
    if missing_vars:
        raise ValueError(f"Variáveis não configuradas: {', '.join(missing_vars)}")
    
    return groq_api_key, telegram_bot_token, telegram_chat_id

def create_questions_prompt():
    """Retorna o prompt para geração das questões"""
    return """Quero que você atue como um gerador de questões no estilo da certificação Databricks Certified Machine Learning Associate. Gere 4 questões de prática (1 por seção), cada uma seguindo a estrutura abaixo:

Pergunta: (enunciado no estilo da prova, em português)
Alternativas: 4 opções (A, B, C, D)
Resposta correta: indique a alternativa correta
Explicação: descreva por que essa alternativa é correta e por que as outras estão erradas.

Regras importantes:
- Gere exatamente 1 questão para cada seção do exame:
  * Section 1: Databricks Machine Learning
  * Section 2: Data Processing
  * Section 3: Model Development
  * Section 4: Model Deployment
- Em cada questão, inclua no início do enunciado o rótulo da seção (exemplo: "Seção 1 - Databricks Machine Learning").
- Use conceitos e ferramentas do ecossistema Databricks em escopo (Unity Catalog, Feature Store, MLflow, AutoML, Spark, Hyperopt, Model Serving, Delta Live Tables, etc.).
- Estilo deve ser similar ao exame: cenários práticos, alternativas plausíveis e apenas 1 correta.
- Mantenha o formato exatamente como: Pergunta, Alternativas, Resposta correta, Explicação."""

def call_groq_api(api_key, prompt, model='openai/gpt-oss-120b'):
    """Chama a API do GROQ e retorna o conteúdo gerado"""

    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        
        "temperature": 0.7,
        "max_tokens": 4000,
        "top_p": 1,
        "stream": False
    }
    
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json',
         'User-Agent': 'Mozilla/5.0'
    }
    
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers=headers)
    
    with urllib.request.urlopen(req, timeout=30) as response:
        if response.status == 200:
            result = json.loads(response.read().decode('utf-8'))
            return result['choices'][0]['message']['content']
        else:
            raise Exception(f"Erro na API do GROQ. Status: {response.status}")

def get_rule_name(event):
    """Extrai o nome da regra do evento para personalizar a mensagem"""
    default = "📚 Questões Databricks ML"
    
    try:
        if not event.get('resources'):
            return default

        resource = event['resources'][0]
        if 'noon' in resource:
            return "☀️ Questões do Meio-dia (12:00)"
        elif 'evening' in resource:
            return "🌆 Questões Vespertinas (18:00)"
        elif 'night' in resource:
            return "🌙 Questões Noturnas (22:00)"
        else:
            return default
    except Exception:
        return default

def create_telegram_message(questions_content, rule_name, timestamp):
    """Cria a mensagem formatada para o Telegram"""
    return f"""🎯 **{rule_name}**

🏆 **Databricks Certified Machine Learning Associate**
📅 {timestamp}

{questions_content}

---
💡 Bons estudos! 🚀"""


def split_long_message(message, max_length=4000):
    """
    Divide mensagens longas em partes menores para envio no Telegram.
    - max_length: limite de caracteres por mensagem (Telegram suporta até 4096)
    """
    if len(message) <= max_length:
        return [message]

    messages = []
    # Tenta dividir por 'Questão' se existir
    if "Questão" in message:
        parts = message.split('Questão')
        header = parts[0] if parts else ""
        current_message = header

        for i, part in enumerate(parts[1:], 1):
            part_text = f"Questão{part}"
            if len(current_message) + len(part_text) <= max_length:
                current_message += part_text
            else:
                messages.append(current_message)
                current_message = part_text
        if current_message:
            messages.append(current_message)
    else:
        # Se não houver 'Questão', divide por blocos de max_length
        for i in range(0, len(message), max_length):
            messages.append(message[i:i + max_length])
    return messages


def send_telegram_message(message, bot_token, chat_id):
    """
    Envia mensagem para o Telegram, dividindo se necessário.
    """
    messages = split_long_message(message)

    for msg in messages:
        # Limpeza de caracteres que quebram Markdown
        cleaned_msg = (
            msg.replace('–', '-')
               .replace('‑', '-')
               .replace('‘', "'")
               .replace('’', "'")
        )

        data = json.dumps({
            "chat_id": chat_id,
            "text": cleaned_msg
        }).encode("utf-8")

        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})

        try:
            with urllib.request.urlopen(req, timeout=10) as response:
                response_data = response.read().decode("utf-8")
                # opcional: print(response_data)
        except Exception as e:
            print(f"Erro ao enviar mensagem: {e}")

        sleep(1)  # evita limite de requisições do Telegram



def create_success_response(timestamp, rule_name, telegram_sent=True, questions=None):
    """Cria resposta de sucesso padronizada"""
    if telegram_sent:
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Questões geradas e enviadas para o Telegram com sucesso',
                'timestamp': timestamp,
                'telegram_sent': True,
                'rule_name': rule_name
            }, ensure_ascii=False, indent=2)
        }
    else:
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Questões geradas, mas falha ao enviar para o Telegram',
                'timestamp': timestamp,
                'telegram_sent': False,
                'questions': questions,
                'rule_name': rule_name
            }, ensure_ascii=False, indent=2)
        }

def create_error_response(status_code, error_message, details=None):
    """Cria resposta de erro padronizada"""
    response_body = {'error': error_message}
    if details:
        response_body['details'] = details
    
    return {
        'statusCode': status_code,
        'body': json.dumps(response_body)
    }

def generate_questions(event, context):
    """Função principal - gera questões e envia para o Telegram"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    try:
        # Validar variáveis de ambiente
        groq_api_key, telegram_bot_token, telegram_chat_id = get_environment_variables()
        
        # Gerar questões
        print(f"[{timestamp}] Iniciando geração de questões...")
        prompt = create_questions_prompt()
        questions_content = call_groq_api(groq_api_key, prompt, 'openai/gpt-oss-120b')
        print(f"[{timestamp}] Questões geradas com sucesso")
        
        # Preparar mensagem para Telegram
        rule_name = get_rule_name(event)
        telegram_message = create_telegram_message(questions_content, rule_name, timestamp)
        
        # Enviar para Telegram
        try:
            send_telegram_message(telegram_message, telegram_bot_token, telegram_chat_id)
            print(f"[{timestamp}] Questões enviadas para o Telegram com sucesso!")
            return create_success_response(timestamp, rule_name, telegram_sent=True)
        
        except Exception as telegram_error:
            print(f"[{timestamp}] Erro ao enviar para Telegram: {str(telegram_error)}")
            return create_success_response(timestamp, rule_name, telegram_sent=False, questions=questions_content)
    
    except ValueError as env_error:
        print(f"[{timestamp}] Erro de configuração: {str(env_error)}")
        return create_error_response(500, str(env_error))
    
    except urllib.error.HTTPError as http_error:
        error_body = http_error.read().decode('utf-8') if http_error.fp else "Sem detalhes"
        print(f"[{timestamp}] Erro HTTP: {http_error.code} - {http_error.reason}")
        return create_error_response(http_error.code, f"Erro HTTP: {http_error.reason}", error_body)
    
    except urllib.error.URLError as url_error:
        print(f"[{timestamp}] Erro de conexão: {str(url_error.reason)}")
        return create_error_response(502, f"Erro de conexão: {str(url_error.reason)}")
    
    except Exception as general_error:
        print(f"[{timestamp}] Erro inesperado: {str(general_error)}")
        return create_error_response(500, f"Erro inesperado: {str(general_error)}")

def lambda_handler(event, context):
    return generate_questions(event, context)
