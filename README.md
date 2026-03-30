# Databricks ML Associate Question Generator

> Gera automaticamente questões no estilo da certificação **Databricks Certified Machine Learning Associate** e envia para um grupo do Telegram, utilizando AWS Lambda, Serverless Framework e a API do Groq.

---

## Visão Geral

Este projeto automatiza a geração e envio de questões de prática para a certificação Databricks ML Associate. Ele utiliza um modelo LLM hospedado na Groq para criar questões realistas, e envia as questões para um grupo do Telegram em horários programados via AWS Lambda.

---

## Arquitetura

![Desenho da Arquitetura](assets/solution_architecture.drawio.png)

> **Adicione o desenho da arquitetura no arquivo acima.**

---

## Como funciona?

- **Geração das questões:**
  - Um prompt customizado é enviado para a API da Groq, solicitando questões no formato do exame.
  - O modelo retorna questões, alternativas, resposta correta e explicações.
- **Envio para Telegram:**
  - As questões são formatadas e enviadas para o grupo do Telegram via bot.
- **Agendamento:**
  - O envio é feito automaticamente em horários pré-definidos usando eventos CloudWatch (cron) na AWS Lambda.

---

## Deploy

1. **Pré-requisitos:**
   - AWS CLI configurado
   - Node.js e npm
   - Serverless Framework (`npm install -g serverless`)

2. **Configuração das variáveis de ambiente:**
   - Crie um arquivo `.env` com:
     ```env
     GROQ_API_KEY=xxxxxx
     TELEGRAM_BOT_TOKEN=xxxxxx
     TELEGRAM_CHAT_ID=xxxxxx
     ```

3. **Deploy:**
   ```bash
   sls deploy
   ```

---

## Variáveis de Ambiente

- `GROQ_API_KEY`: Chave de API do Groq (LLM)
- `TELEGRAM_BOT_TOKEN`: Token do bot do Telegram
- `TELEGRAM_CHAT_ID`: ID do grupo ou usuário no Telegram

---

## Agendamento (CloudWatch Events)

Os horários de envio das questões são configurados no `serverless.yml`:

- 12:00 (meio-dia)
- 18:00 (tarde)
- 22:00 (noite)

---

## Estrutura do Projeto

- `handler.py`: Função principal (Lambda)
- `serverless.yml`: Configuração do Serverless Framework
---

## Exemplo de Questão Gerada

```
Pergunta: Seção 1 - Databricks Machine Learning. Uma equipe deseja centralizar o gerenciamento de features para múltiplos workspaces e registrar modelos com governança unificada. Qual abordagem é a mais adequada no Databricks?
Alternativas:
A) Criar tabelas de feature store no Unity Catalog em nível de conta e registrar modelos no Unity Catalog Model Registry.
B) Manter tabelas de features e modelos apenas em cada workspace, sem catálogo central.
C) Armazenar features em arquivos locais do cluster e versionar modelos manualmente.
D) Treinar modelos sem feature store e sem registro de modelos.
Resposta correta: A
Explicação: A alternativa A permite governança centralizada, compartilhamento entre workspaces e melhor rastreabilidade via Unity Catalog. As demais não oferecem governança central robusta nem colaboração adequada em escala.
```

---
