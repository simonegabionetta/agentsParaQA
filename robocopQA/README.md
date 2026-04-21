# RoboCop QA

Navega o front-end de qualquer aplicação web com Playwright, lê cada tela e gera um documento `.docx` com casos de teste prontos para execução.

---

## Como funciona

1. Abre o browser (headless por padrão) e acessa a URL informada
2. Percorre as rotas, coleta elementos, formulários, botões e tabelas de cada página
3. Envia o contexto de cada tela para o LLM
4. Gera casos de teste organizados por página com prioridade, pré-condições e passos
5. Salva tudo em `reports/casos_de_teste_<dominio>_<data>.docx`

---

## Comando rápido (primeira vez e todo dia)

**Linux / Mac:**
```bash
./robocop.sh crawl https://app.com
```

**Windows:**
```bat
robocop.bat crawl https://app.com
```

O script cria o ambiente virtual, instala dependências e roda o agente automaticamente. Na primeira execução demora ~2 minutos. Depois é instantâneo.

> Só precisa existir um `.env` preenchido na pasta. Copie de `.env.example` antes de rodar pela primeira vez.

---

## Pré-requisitos

- **Python 3.11 ou superior** — verifique com `python --version`
- Acesso à internet para o Playwright baixar o Chromium
- Chave de API de ao menos um provedor de IA (veja seção Configuração)

## Instalação manual (alternativa ao script)

```bash
# 1. Crie e ative o ambiente virtual
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

# 2. Instale as dependências
pip install -r requirements.txt

# 3. Instale o browser
playwright install chromium

# 4. (Opcional) Para geração de .docx com Node.js
npm install -g docx

# 5. Copie o arquivo de configuração
cp .env.example .env
# Abra o .env e preencha LLM_PROVIDER e a chave correspondente
```

---

## Configuração (`.env`)

```env
LLM_PROVIDER=anthropic    # anthropic | openai | gemini | groq | ollama
LLM_MODEL=                # deixe vazio para usar o padrão do provedor

ANTHROPIC_API_KEY=
OPENAI_API_KEY=
GEMINI_API_KEY=
GROQ_API_KEY=
```

| Provedor | Modelo padrão | Onde gerar a chave |
|----------|---------------|--------------------|
| `anthropic` | `claude-opus-4-5` | console.anthropic.com/settings/keys |
| `openai` | `gpt-4o` | platform.openai.com/api-keys |
| `gemini` | `gemini/gemini-1.5-pro` | aistudio.google.com/apikey |
| `groq` | `groq/llama-3.1-70b-versatile` | console.groq.com/keys |
| `ollama` | `ollama/llama3` | roda localmente, sem chave |

---

## Como usar

> **Dica:** na primeira vez, use `--dry-run` para validar que tudo está funcionando antes de gerar o arquivo.

```bash
source .venv/bin/activate
python main.py crawl <URL> [opções]
```

### Opções

| Opção | Descrição | Padrão |
|-------|-----------|--------|
| `URL` | URL inicial do site | obrigatório |
| `--email` | E-mail para login | — |
| `--senha` | Senha para login | — |
| `--login-click "Texto"` | Clica em um botão para entrar | — |
| `--login-clicks "A,B,C"` | Roda para vários perfis em sequência | — |
| `--perfil MANUAL\|TECNICO` | Nível de detalhe dos casos | `MANUAL` |
| `--max-paginas N` | Máximo de páginas a explorar | `15` |
| `--output arquivo.docx` | Nome do arquivo de saída | automático |
| `--dry-run` | Exibe no terminal sem gerar arquivo | — |

### Exemplos

```bash
# Site público
python main.py crawl https://exemplo.com

# Login com formulário
python main.py crawl https://app.com --email qa@empresa.com --senha s3cr3t

# Múltiplos perfis de acesso
python main.py crawl https://app.com --login-clicks "Admin,Cliente,Motorista"

# Casos técnicos com mais páginas
python main.py crawl https://app.com --email qa@empresa.com --senha s3cr3t \
  --perfil TECNICO --max-paginas 30

# Só visualizar no terminal
python main.py crawl https://exemplo.com --dry-run
```

Relatórios salvos em `reports/`.

---

## Perfis de saída

**MANUAL** — linguagem orientada ao usuário, sem referências técnicas. Qualquer QA sem background de dev consegue executar.

**TECNICO** — inclui seletores, endpoints e detalhes de implementação. Para QAs de automação ou devs.

---

## Customização

Edite `consulta.md` para ajustar o raciocínio do agente — tipos de sistema reconhecidos, padrões de priorização, formato de saída. Nenhum código precisa mudar.

---

## Se o `.docx` falhar

```bash
python md_to_docx.py
```

Converte o último `.md` gerado para `.docx` como fallback.
