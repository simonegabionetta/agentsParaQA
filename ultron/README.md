# Ultron QA

Lê um card do gerenciador de tarefas e o diff de um Pull Request no GitHub, analisa tudo com IA e posta direto no card uma tabela de casos de teste, checklist de validação e resumo das alterações.

---

## Como funciona

1. Busca o título e descrição do card (Jira, Linear ou GitHub Issues)
2. Busca o diff completo do PR via API do GitHub
3. Envia o contexto do card + diff para o LLM
4. Formata o resultado em Markdown estruturado
5. Posta o comentário diretamente no card

O comentário gerado contém:
- **Resumo das alterações** — o que mudou e qual impacto funcional
- **Tabela de casos de teste** — com cenário, pré-condição, passos, resultado esperado e prioridade
- **Checklist de validação** — checkboxes prontos para marcar durante a execução
- **Pontos de atenção** — riscos concretos identificados no diff

---

## Como chamar o Ultron

Fale naturalmente — o Ultron entende a frase e extrai card, PR(s) e perfil automaticamente.

**Linux / Mac:**
```bash
./ultron.sh Rode o Ultron no card PROJ-42, pr 87, MANUAL
./ultron.sh Rode o Ultron no card PROJ-42, pr 87, 88, TECNICO
./ultron.sh card PROJ-42 pr 87
./ultron.sh card PROJ-42 pr 87 88 --dry-run
```

**Windows:**
```bat
ultron.bat Rode o Ultron no card PROJ-42, pr 87, MANUAL
ultron.bat card PROJ-42 pr 87 88 TECNICO
```

O que o parser entende:
- **card** seguido de um ID → `PROJ-42`, `ABC-123`, `#42`
- **pr** seguido de números → `87` ou `87, 88, 89`
- **MANUAL** ou **TECNICO** em qualquer posição → perfil (padrão: MANUAL)
- **--dry-run** → exibe o comentário no terminal sem postar

Na primeira execução o script cria o ambiente e instala tudo (~1 minuto). Depois é instantâneo.

> Só precisa existir um `.env` preenchido na pasta. Copie de `.env.example` antes de rodar pela primeira vez.

---

## Pré-requisitos

- **Python 3.11 ou superior** — verifique com `python --version`
- GitHub Personal Access Token (para ler PRs)
- Conta no gerenciador de tarefas (Jira, Linear ou GitHub Issues)
- Chave de API de ao menos um provedor de IA

## Instalação manual (alternativa ao script)

```bash
# 1. Crie e ative o ambiente virtual
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

# 2. Instale as dependências
pip install -r requirements.txt

# 3. Copie e preencha o arquivo de configuração
cp .env.example .env
# Abra o .env e preencha: LLM_PROVIDER + chave, GITHUB_TOKEN, GITHUB_REPO e PM_PROVIDER
```

---

## Configuração (`.env`)

### LLM

```env
LLM_PROVIDER=anthropic    # anthropic | openai | gemini | groq | ollama
LLM_MODEL=                # deixe vazio para usar o padrão

ANTHROPIC_API_KEY=
OPENAI_API_KEY=
GEMINI_API_KEY=
GROQ_API_KEY=
```

### GitHub

```env
GITHUB_TOKEN=ghp_...           # Personal Access Token com permissão repo (leitura)
GITHUB_REPO=org/repositorio    # ex: minha-empresa/backend-api
```

Crie o token em: `github.com → Settings → Developer settings → Personal access tokens`
Permissões mínimas: `repo` (read-only é suficiente).

### Gerenciador de tarefas

```env
PM_PROVIDER=jira    # jira | linear | github
```

**Jira:**
```env
JIRA_BASE_URL=https://suaempresa.atlassian.net
JIRA_EMAIL=seu@email.com
JIRA_API_TOKEN=...
```
Crie o token em: `id.atlassian.net → Segurança → Tokens de API`

**Linear:**
```env
LINEAR_API_KEY=lin_api_...
```
Crie em: `linear.app → Settings → API`

**GitHub Issues:** usa o `GITHUB_TOKEN` já configurado acima, sem configuração extra.

---

## Como usar

> **Recomendado na primeira vez:** use `--dry-run` para ver o comentário gerado no terminal antes de postar no card. Assim você valida que a configuração está correta sem risco de postar algo errado.

```bash
source .venv/bin/activate
python main.py analyze --card <ID> --pr <número> [opções]
```

### Opções

| Opção | Descrição |
|-------|-----------|
| `--card ID` | ID do card (ex: `PROJ-42`, `#15`) |
| `--pr N` | Número do PR no GitHub |
| `--prs N1,N2` | Múltiplos PRs separados por vírgula |
| `--base branch` | Branch base para o diff (padrão: base do PR) |
| `--dry-run` | Exibe o comentário no terminal sem postar |

### Exemplos

```bash
# Analisa PR 87 e comenta no card PROJ-42
python main.py analyze --card PROJ-42 --pr 87

# Múltiplos PRs (ex: front-end + back-end)
python main.py analyze --card PROJ-42 --prs 87,88

# Ver o comentário antes de postar
python main.py analyze --card PROJ-42 --pr 87 --dry-run

# Diff contra branch específica
python main.py analyze --card PROJ-42 --pr 87 --base develop

# GitHub Issues
python main.py analyze --card "#42" --pr 87
```

---

## Exemplo de comentário gerado

```markdown
## Ultron QA — Análise automática

> Card PROJ-42 · PR(s): #87

---

### Resumo das Alterações
Adicionada validação de CPF no cadastro de usuário. O campo agora rejeita
valores com menos de 11 dígitos e exibe mensagem de erro inline. O fluxo
de criação de conta foi alterado para bloquear o submit enquanto o CPF
for inválido.

---

### Casos de Teste Sugeridos

| # | Cenário | Pré-condição | Passos | Resultado Esperado | Prioridade |
|---|---------|-------------|--------|--------------------|-----------|
| CT-01 | CPF válido no cadastro | Página de cadastro aberta | 1. Preencher CPF válido (ex: 123.456.789-09) 2. Clicar em Continuar | Avança para próximo passo | Alta |
| CT-02 | CPF com menos de 11 dígitos | Página de cadastro aberta | 1. Preencher CPF incompleto 2. Clicar fora do campo | Exibe mensagem de erro inline | Alta |
...

---

### Checklist de Validação

- [ ] CPF válido aceito no fluxo feliz
- [ ] CPF inválido exibe mensagem de erro
- [ ] Botão submit desabilitado com CPF inválido
- [ ] Máscara de CPF aplicada durante digitação
...

---

### Pontos de Atenção
- Verificar se a validação ocorre só no front ou também no back-end
- Testar comportamento com CPFs válidos mas de pessoas físicas inexistentes
```

---

## Gerenciadores suportados

| Provedor | Busca card | Posta comentário |
|----------|-----------|-----------------|
| Jira | Título + descrição ADF | Comentário via REST API v3 |
| Linear | Título + descrição Markdown | Comentário via GraphQL |
| GitHub Issues | Título + body | Comentário via REST API |
