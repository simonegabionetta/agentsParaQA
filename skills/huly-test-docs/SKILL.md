---
name: huly-test-docs
description: 'Generate complete test documentation from a Huly card: testing-strategy.md (risk-based strategy), testing-case-manual.md (manual test cases). Suites (Web, API, E2E) generated dynamically — only when the card justifies them. Integração suite is never generated. One test case per acceptance criterion — no more, no less. API cases based on card AND Swagger only; never invented. Cases without mapped acceptance criteria go to Future Candidates. Each case in Portuguese for junior QA, with layer tag and action verb title derived from the source card ID (e.g. card ATD-504 → ATD-504-CT01 [UI] Deve salvar cadastro), flow, classification (Smoke/Regression/Functional), automation indication, and observations. Generates pre-test checklist with required test data and environment confirmation. Use when user pastes a Huly card and wants strategy and test cases ready for Huly Test Management.'
---

# Huly Test Docs

Transforms a Huly card text into two complete test documents ready for Huly Test Management.

> 🇧🇷 **LANGUAGE RULE — MANDATORY:** All output, responses, documents, labels, questions, observations, and any other generated content MUST be written exclusively in **Portuguese (Brazil)**. No exceptions. Do not use English in any part of the response.

## ⚡ Regras de Economia de Contexto (Token) — OBRIGATÓRIAS

Padrões fixos para esta skill — não precisam ser solicitados a cada uso:

1. **NÃO gerar `testing-strategy.md` por padrão.** Gere apenas `testing-case-manual.md`. Só gere a estratégia se o usuário pedir explicitamente (ex.: "com estratégia", "gere a estratégia também").
2. **Leitura enxuta do card.** Ao ler o card pelo MCP do Huly (`get_issue`), retenha apenas **título, descrição e critérios de aceite**. NÃO despeje o JSON completo da resposta (ignore `structuredContent`/metadados) no contexto nem na conversa.
3. **Não listar todas as ferramentas do MCP.** Use diretamente as ferramentas necessárias (`get_issue`, `add_comment`, `add_issue_label`, Test Management). Nunca despeje o `tools/list` completo.
4. **Delegar leitura pesada a subagent.** Para vasculhar código/repositório, prefira o subagent (ex.: Ultron/Explore), que trabalha em contexto próprio e devolve só o resumo.

> Se o usuário pedir explicitamente um artefato opcional, gere-o normalmente — estas regras definem apenas o comportamento **padrão**.

## Expected Inputs

The user pastes the card text. It may contain any combination of:
- Title
- Description
- Acceptance criteria
- Additional context

> Incomplete card? Do not block. Generate what is possible and flag what is missing with ⚠️.

---

## Execution Flow

1. Read and interpret the pasted card
2. Extract: objective, acceptance criteria, business rules (explicit or implicit)
3. Identify what is **missing** for complete coverage
4. Identify if the card involves E2E flows (UI → API → backend/integrations)
5. **Classify business criticality and test risk** (see Priority Rules section)
6. **Decide which suites to generate** (see Suite Decision Rules section)
7. Generate `testing-strategy.md` **— SOMENTE se o usuário pedir explicitamente** (ver Regras de Economia de Contexto). Por padrão, pule este passo.
8. Generate `testing-case-manual.md` — open with the priority block, then write only the decided suites, starting from highest priority flows
9. List open questions classified by recipient (PO or Dev)

---

## Document 1 — testing-strategy.md

Generate in Portuguese using this exact structure:

```
# Estratégia de Teste — [Card Title]

## Objetivo
What will be tested and why.

## Escopo
### Dentro do escopo
- ...

### Fora do escopo
- ...

## Ambiente de Teste
Indicate which environment(s) apply. If not informed in the card, include both and flag with ⚠️:
- [ ] DEV
- [ ] Staging

⚠️ [Dev] Em qual ambiente o código está disponível para teste?

## ✅ Checklist — Antes de começar a testar

### Massa de Dados necessária
Identify from the card ALL data that must exist in the system before testing starts.
For each item, identify who is responsible and flag with ⚠️ if not confirmed.
Be specific — name exact user profiles, records, configurations needed.

Exemplo de formato:
- [ ] Usuário com perfil [X] cadastrado no ambiente → ⚠️ [Dev] confirmar se existe no Staging
- [ ] Usuário sem permissão [X] cadastrado no ambiente → ⚠️ [Dev] confirmar se existe no Staging
- [ ] Registro de [X] criado previamente → ⚠️ [Dev] confirmar ou criar via Hoppscotch
- [ ] Configuração [X] ativa no ambiente → ⚠️ [Dev] confirmar

⚠️ [Dev] Confirmar se todos os dados acima estão disponíveis no ambiente antes de iniciar os testes.

### Perguntas para o PO
List ALL questions about business rules or expected behavior that are missing from the card:
⚠️ [PO] ...

### Perguntas para o Dev
List ALL technical questions about endpoints, integrations or system behavior:
⚠️ [Dev] ...

### Acesso e ferramentas necessárias
- [ ] Acesso ao ambiente de Staging confirmado
- [ ] Hoppscotch disponível para testes de API (se aplicável)
- [ ] Figma do card consultado (se aplicável)
- [ ] Datadog disponível para monitorar logs (se aplicável)

## Tipos de teste
List only the suites that will be generated for this card (see Suite Decision Rules).

| Suite | Motivo |
|---|---|
| Web | ... |
| API | ... |
| E2E | ... |

> ⚠️ Only include rows for suites that will actually be generated (Web, API, E2E only).
> ⛔ The Integração suite is never generated.
> If E2E was not identified, remove the E2E row and add: "Não identificados fluxos E2E neste card."

## Riscos identificados
| Risco | Impacto | Prioridade |
|---|---|---|
| ... | Alto/Médio/Baixo | Alta/Média/Baixa |

## Dependências
- Systems, integrations or data needed to run the tests

## Como manter
- When to update this documentation
- What to review when the feature changes
```

---

## Suite Decision Rules — Which suites to generate

Before writing any test case, decide which suites apply to this card.
Generate a suite ONLY if the condition is met. If the condition is not met, skip the suite entirely — do not generate empty suites.

| Suite | Generate when... | Skip when... |
|---|---|---|
| **Web (UI)** | Card has any screen, form, button, visual behavior, or user interaction | Card is purely backend with no interface changes |
| **API** | Card creates, edits, deletes, or reads data via endpoint | Card is purely visual with no data change |
| **E2E** | User action on screen triggers API call that changes data or state | Card only affects one layer (only UI or only API) |

> 💡 Most cards will generate **Web + API** or **Web + API + E2E**.
> ⛔ The **Integração** suite is **never generated** — do not include it under any circumstance.

---

## Case Filter Rule — Which cases to write

**REGRA FUNDAMENTAL: Um caso de teste por critério de aceitação.**
Cada critério de aceitação do card deve gerar exatamente um caso de teste na camada correspondente (Web, API ou E2E).
Não escreva mais de um caso para o mesmo critério de aceitação — e não escreva casos sem critério mapeado.

For each potential test case, apply this filter before writing it.
**Write the case only if it passes at least one criterion:**

| Criterion | Write? |
|---|---|
| It is directly mapped to an acceptance criterion in the card | ✅ Yes — mandatory |
| It is the main happy path AND maps to an acceptance criterion | ✅ Yes |
| None of the above (no acceptance criterion mapped) | 🔵 Do not write now |

For cases that do not pass the filter, add at the end of the suite:

```
### 🔵 Candidatos Futuros — [Camada: UI | API | E2E]
Cases identified but not prioritized in this cycle:
- [Case title] — Motivo: sem critério de aceite mapeado no card
```

> ⛔ Do NOT write cases based on assumptions, generic best practices, or experience.
> If a business rule is not in the card, log it as `⚠️ [PO]` — do not create a case for it.

---

## Document 2 — testing-case-manual.md

> 🚫 **REGRA CRÍTICA — NÃO INVENTE CASOS DE TESTE**
> Os casos de teste devem cobrir **somente** o que está explicitamente descrito nos critérios de aceitação do card.
> Não adicione casos baseados em suposições, boas práticas genéricas ou experiência própria.
> Se uma regra de negócio não está no card, registre como `⚠️ [PO]` em vez de inventar um caso.
> **Um caso de teste por critério de aceitação — sem exceção.**

Decide quais camadas se aplicam ao card (Web, API e/ou E2E) usando as Suite Decision Rules — isso continua guiando **quais casos escrever** e a tag de camada de cada um.
⛔ A camada **Integração** nunca é considerada.

> 🚫 **REGRA — SEM CABEÇALHO DE SUITE NO DOCUMENTO:** **Não** crie cabeçalhos de seção do tipo `## Suite: Web`, `## Suite: API` ou `## Suite: E2E` no `testing-case-manual.md`.
> Liste os casos **em sequência**, identificados apenas pela **tag de camada** no título (`[UI]`, `[API]`, `[E2E]`).
> Ordene os casos por camada (UI → API → E2E) e, dentro disso, pela prioridade de escrita. A numeração `CT<NN>` permanece sequencial e contínua entre as camadas.
> A única exceção de cabeçalho permitido é o bloco `### 🔵 Candidatos Futuros`, quando houver casos sem critério mapeado.

> 🔖 **REGRA DE ID — OBRIGATÓRIA:** O ID de cada caso de teste deve **derivar do ID do card de origem no Huly**.
> Formato: `<ID-DO-CARD>-CT<NN> [LAYER] [Action verb title in Portuguese]`
> - `<ID-DO-CARD>` = o identificador exato do card (ex: o card `ATD-504` gera `ATD-504-CT01`).
> - `CT` = marcador fixo de "Caso de Teste".
> - `<NN>` = número sequencial de 2 dígitos (01, 02, 03...), **sequencial entre todas as suites** do card.
> - ⛔ Nunca use numeração genérica tipo `ATD-001` que colida com IDs de outros cards do tracker.
> - Se o ID do card não for informado, pergunte ou registre `⚠️ [QA] Confirmar o ID do card de origem` e use o placeholder `<CARD>-CT01`.
> Exemplos para o card `ATD-504`: `ATD-504-CT01 [API] Deve salvar cadastro`, `ATD-504-CT02 [UI] Deve exibir erro`.

Layer tags:
- `[UI]` — browser/interface tests
- `[API]` — API-only tests
- `[E2E]` — end-to-end tests crossing multiple layers

> 🚫 **REGRA — NÃO DUPLICAR O TÍTULO:** Ao criar o caso no Huly Test Management, o título (`<ID-DO-CARD>-CT<NN> [LAYER] ...`) vai **somente** no campo de **nome** do caso.
> A **descrição NÃO pode conter** o título/nome do caso nem qualquer cabeçalho markdown (`#`, `##`, `###`) repetindo o nome do caso ou o título do card.
> A descrição deve **começar direto** pelo primeiro campo do conteúdo (`**Critério coberto:** ...`).
> O bloco ` ### <ID-DO-CARD>-CT<NN> [LAYER] [título] ` abaixo é o cabeçalho usado **apenas** no documento `testing-case-manual.md` — ao publicar no Huly, ele vira o nome do caso e **não** se repete dentro da descrição.

**Orientação para casos [UI]** (sem cabeçalho de suite no documento):

> Gere **um caso por critério de aceitação** que envolva interação com a interface.
> Mapeie explicitamente qual critério de aceitação cada caso cobre — ex: `**Critério coberto:** CA-01`.

Cada caso [UI] deve seguir esta ordem exata:

```
### <ID-DO-CARD>-CT01 [UI] [Action verb title in Portuguese]
- **Critério coberto:** [CA-XX — copy the acceptance criterion from the card]
- **Fluxo:** Feliz | Alternativo | Erro
- **Classificação:** Smoke | Regressão | Funcional
- **Pré-condições:** (reference the massa de dados checklist when needed)
- **Passos:**
  1. ...
  2. ...
- **Resultado esperado:** ...
- **Automatizar:** Sim | Não
- **Obs:** [instruction for junior]
```

**Orientação para casos [API]** (sem cabeçalho de suite no documento):

> 📄 **Fonte obrigatória para casos de API:** o card **e** o Swagger.
> - Do card: extraia os critérios de aceitação — gere **um caso por critério** que envolva chamada de API.
> - Do Swagger: extraia o método HTTP, endpoint, parâmetros, status codes e contrato de request/response.
> - Se o Swagger não estiver disponível ou não cobrir o endpoint: registre `⚠️ [Dev] Confirmar contrato do endpoint no Swagger antes de executar os testes de API.` e deixe os campos de endpoint/body/status como `⚠️ A confirmar`.
> - ⛔ Não invente endpoints, parâmetros ou comportamentos que não estão no card ou no Swagger.
> Gere **um caso por critério de aceitação** que envolva chamada de API.
> Mapeie explicitamente qual critério de aceitação cada caso cobre — ex: `**Critério coberto:** CA-01`.

Cada caso [API] deve seguir esta ordem exata:

```
### <ID-DO-CARD>-CT02 [API] [Action verb title in Portuguese]
- **Critério coberto:** [CA-XX — copy the acceptance criterion from the card]
- **Fluxo:** Feliz | Alternativo | Erro
- **Classificação:** Smoke | Regressão | Funcional
- **Pré-condições:** (reference the massa de dados checklist when needed)
- **Método + Endpoint:** POST /api/...
- **Corpo da Requisição:**
  ```json
  { ... }
  ```
- **Status Code esperado:** 200 | 400 | 422 | ...
- **Corpo da Resposta esperado:**
  ```json
  { ... }
  ```
- **Automatizar:** Sim | Não
- **Obs:** [instruction for junior]
```

**Orientação para casos [E2E]** (sem cabeçalho de suite no documento):

> Gere **um caso por critério de aceitação** que envolva fluxo completo entre camadas (UI → API).
> Mapeie explicitamente qual critério de aceitação cada caso cobre — ex: `**Critério coberto:** CA-01`.

Gere casos [E2E] APENAS se fluxos E2E foram identificados na estratégia.
Cada caso [E2E] deve seguir esta ordem exata:

```
### <ID-DO-CARD>-CT03 [E2E] [Action verb title in Portuguese]
- **Critério coberto:** [CA-XX — copy the acceptance criterion from the card]
- **Fluxo:** Feliz | Alternativo | Erro
- **Classificação:** Smoke | Regressão | Funcional
- **Camadas envolvidas:** UI → API → [outros sistemas]
- **Pré-condições:** (reference the massa de dados checklist when needed)
- **Passos:**
  1. ...
- **Resultado esperado:** ...
- **Automatizar:** Sim | Não
- **Obs:** [instruction for junior]
```

---

## Priority Rules — Business Criticality and Risk

Before writing test cases, evaluate and classify the card using the two dimensions below.
This classification must appear at the top of `testing-case-manual.md`, before the first suite.

### Step 1 — Classify Business Criticality

Ask: "If this breaks in production, what is the impact on the business or the user?"

| Level | Criteria | Examples |
|---|---|---|
| 🔴 Crítico | Blocks core business operation or revenue. Complete loss of function. | Login, checkout, payment, core data save |
| 🟡 Alto | Degrades important experience but has workaround. | Report generation, notifications, filters |
| 🟢 Médio | Affects secondary feature. Business continues normally. | UI tweaks, optional fields, cosmetic behavior |

### Step 2 — Classify Test Risk

Ask: "What is the probability this breaks, and how hard is it to detect if it does?"

| Level | Criteria |
|---|---|
| 🔴 Alto | Legacy code with no unit tests, recent changes in this area, complex business rules, integration with external systems |
| 🟡 Médio | Existing feature receiving new behavior, moderate complexity, partially covered by existing tests |
| 🟢 Baixo | Simple isolated change, stable area, well-covered by existing tests |

### Step 3 — Define Writing Priority

Cross criticality and risk to decide what to write first:

| Business Criticality | Risk | Writing Priority |
|---|---|---|
| 🔴 Crítico | 🔴 Alto | ⚡ Escrever primeiro — Fluxo Feliz + todos os casos de Erro |
| 🔴 Crítico | 🟡 Médio | ⚡ Escrever primeiro — Fluxo Feliz obrigatório + principais Erros |
| 🟡 Alto | 🔴 Alto | 🔼 Escrever na sequência — Fluxo Feliz + Erros críticos |
| 🟡 Alto | 🟡 Médio | 🔼 Escrever na sequência — Fluxo Feliz + principais Alternativos |
| 🟢 Médio | qualquer | 🔽 Escrever por último — Fluxo Feliz mínimo |

### Output format — add this block at the top of testing-case-manual.md

```
## Prioridade de Escrita — [Card Title]

- **Criticidade de negócio:** 🔴 Crítico | 🟡 Alto | 🟢 Médio
- **Risco de teste:** 🔴 Alto | 🟡 Médio | 🟢 Baixo
- **Prioridade:** ⚡ Escrever primeiro | 🔼 Escrever na sequência | 🔽 Escrever por último
- **Justificativa:** [one sentence explaining why this combination was chosen]
- **Foco dos casos:** [what flows to prioritize — e.g. "Priorizar Fluxo Feliz e casos de Erro de autenticação"]
```

> If the card has multiple features with different criticality levels, classify each separately and note which part drives the overall priority.

---



## Classification Rules — Flow

| Flow | When to use |
|---|---|
| Feliz | Everything correct, valid data, expected user path |
| Alternativo | Valid but different path from the main one |
| Erro | Invalid data, system unavailable, validation fails |

---

## Classification Rules — Smoke / Regressão / Funcional

| Classification | When to use |
|---|---|
| Smoke | Basic and fast test — verifies the feature opens and works minimally. Runs before anything else. |
| Regressão | Verifies that what already worked continues working after a system change. |
| Funcional | Covers a specific behavior, error or alternative case. Neither Smoke nor Regression. |

> A case may have more than one classification. Ex: `Smoke, Regressão`

---

## Classification Rules — Automatizar

| Criterion | Indication |
|---|---|
| Critical happy path repeated every release | Sim |
| Classified as Smoke or Regressão | Sim |
| Simple and stable field validation | Sim |
| Complex flow with many variables | Não |
| Integration between systems | Não |
| Exploratory or visual test | Não |
| Frequently changing flow | Não |

---

## Title Rules

Always start with an action verb in Portuguese:

| ✅ Correct | ❌ Wrong |
|---|---|
| Deve salvar cadastro com campos válidos | Teste do cadastro |
| Não deve aceitar CPF duplicado | Verificar CPF |
| Deve retornar erro 400 ao enviar data inválida | Erro de data |

---

## Open Questions Rules

Classify and list at the end of each document:

```
⚠️ [PO] — questions about business rule or expected behavior
⚠️ [Dev] — technical questions about endpoint, integration or system behavior
```

Always add automatically if not informed in the card:
- `⚠️ [Dev] Em qual ambiente o código está disponível para teste?`
- `⚠️ [Dev] Confirmar se a massa de dados necessária está disponível no ambiente.`

---

## Trigger Examples

```
Use $huly-test-docs para o seguinte card: [paste the text]
```
```
Gere a estratégia e os casos de teste para este card do Huly: [paste the text]
```
```
[paste the card text directly]
```
