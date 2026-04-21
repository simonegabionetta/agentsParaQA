# agentsParaQA

Suite de agentes de IA para times de QA. Dois agentes independentes com foco em coberturas diferentes do ciclo de qualidade.

---

## Agentes

### RoboCop QA
Navega qualquer aplicação web com Playwright, lê todas as telas e gera um documento `.docx` com casos de teste organizados por página.

**Quando usar:** quando o QA precisa cobrir um sistema do zero ou mapear telas que nunca foram testadas formalmente.

```
robocopQA/
```

---

### Ultron
Lê um card do seu gerenciador de tarefas (Jira, Linear ou GitHub Issues) e o diff de um Pull Request no GitHub, analisa tudo com IA e posta no próprio card uma tabela de casos de teste, checklist e resumo das alterações.

**Quando usar:** no dia a dia de sprint, quando o dev abre um PR e o QA precisa saber o que testar.

```
ultron/
```

---

## Comparativo rápido

| | RoboCop QA | Ultron |
|---|---|---|
| Entrada | URL do sistema | Número do card + PR |
| O que analisa | Front-end ao vivo (Playwright) | Código alterado (git diff) |
| Saída | Arquivo `.docx` em `reports/` | Comentário no card |
| Quando usar | Cobertura inicial / regressão | Revisão de PR / sprint |
| Precisa de GitHub? | Não | Sim |
| Precisa de PM? | Não | Sim |

---

## Configuração dos provedores de IA

Ambos os agentes usam [LiteLLM](https://github.com/BerriAI/litellm) e suportam os mesmos provedores:

| Provedor | Variável de chave | Modelo padrão |
|----------|------------------|---------------|
| Anthropic (Claude) | `ANTHROPIC_API_KEY` | `claude-opus-4-5` |
| OpenAI (ChatGPT) | `OPENAI_API_KEY` | `gpt-4o` |
| Google Gemini | `GEMINI_API_KEY` | `gemini/gemini-1.5-pro` |
| Groq | `GROQ_API_KEY` | `groq/llama-3.1-70b-versatile` |
| Ollama (local) | — | `ollama/llama3` |

Configure `LLM_PROVIDER` e a chave correspondente no `.env` de cada agente.

---

## Requisitos

- **Python 3.11+** — verifique com `python --version`
- Chave de API de ao menos um provedor de IA (Claude, OpenAI, Gemini, Groq ou Ollama local)
- **Apenas Ultron:** GitHub Personal Access Token + conta no gerenciador de tarefas

## Instalação rápida

```bash
# RoboCop
cd robocopQA
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
cp .env.example .env

# Ultron
cd ../ultron
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Cada agente tem seu próprio `README.md` com exemplos detalhados.
