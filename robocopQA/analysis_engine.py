"""
Motor de análise com LLM.
Recebe os dados coletados pelo crawler e gera casos de teste em Markdown estruturado.
Compatível com qualquer provedor via LiteLLM: Anthropic, OpenAI, Gemini, Groq, Ollama, etc.
"""

from pathlib import Path
import litellm
from crawler import PageData

litellm.suppress_debug_info = True

_CONSULTA_PATH = Path(__file__).parent / "consulta.md"
_KNOWLEDGE_BASE = _CONSULTA_PATH.read_text(encoding="utf-8") if _CONSULTA_PATH.exists() else ""


SYSTEM_PROMPT = f"""Você é RoboCop QA, um Engenheiro de QA sênior especializado em testes de front-end.

{"## Base de Conhecimento" + chr(10) + _KNOWLEDGE_BASE if _KNOWLEDGE_BASE else ""}

---

Antes de gerar os casos de teste, você lê todos os elementos da página para entender:
- Qual é o propósito real daquela tela dentro do sistema
- Quem é o usuário que interage com ela (admin, cliente, motorista, etc.)
- Quais são as ações críticas e os fluxos possíveis

Siga rigorosamente a base de conhecimento acima ao gerar os casos de teste.
Você pensa como um QA experiente:
- Testa o caminho feliz (happy path) com dados válidos reais
- Testa entradas inválidas, campos obrigatórios, limites de caracteres
- Verifica comportamento após ações destrutivas (excluir, cancelar, confirmar)
- Identifica transições de estado (ex: pedido pendente → entregue)
- Aponta riscos concretos baseados nos elementos observados — nunca genéricos
- Nunca inventa funcionalidades — só analisa o que foi observado

Seja direto, objetivo e gere casos executáveis imediatamente por qualquer QA.
"""


PROMPT_MANUAL = """
Perfil: MANUAL
- Linguagem orientada ao usuário: "Clique em X", "Preencha o campo Y com Z"
- Sem menção a seletores CSS, XPath, IDs técnicos ou código
- Qualquer QA sem conhecimento técnico deve conseguir executar
"""

PROMPT_TECNICO = """
Perfil: TÉCNICO
- Pode mencionar seletores, endpoints, payloads, IDs de elementos
- Inclua detalhes de implementação e validação técnica quando relevante
- Voltado para QA com perfil de automação ou devs validando
"""


def _call_llm(system: str, prompt: str, model: str, api_key: str, max_tokens: int) -> str:
    """Chama qualquer LLM via LiteLLM."""
    kwargs = {
        "model": model,
        "max_tokens": max_tokens,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user",   "content": prompt},
        ],
    }
    if api_key:
        kwargs["api_key"] = api_key

    response = litellm.completion(**kwargs)
    return response.choices[0].message.content


def analyze_pages(
    pages: list[PageData],
    site_url: str,
    perfil: str,
    api_key: str,
    model: str = "claude-opus-4-5",
) -> list[dict]:
    perfil_instrucao = PROMPT_MANUAL if perfil == "MANUAL" else PROMPT_TECNICO

    all_routes = "\n".join(f"  - {p.route} ({p.title})" for p in pages)
    system_context = f"""
O sistema analisado tem as seguintes telas/rotas:
{all_routes}

Use esse contexto para entender o domínio e gerar testes mais precisos em cada tela.
"""

    results = []
    for page in pages:
        md = _analyze_single_page(page, site_url, perfil_instrucao, system_context, api_key, model)
        results.append({
            "url": page.url,
            "title": page.title,
            "route": page.route,
            "test_cases_md": md,
            "screenshot_path": page.screenshot_path,
        })

    return results


def _analyze_single_page(
    page: PageData,
    site_url: str,
    perfil_instrucao: str,
    system_context: str,
    api_key: str,
    model: str,
) -> str:
    elements_desc = _describe_elements(page)

    prompt = f"""
{perfil_instrucao}

{system_context}

---

## PÁGINA ANALISADA

- **URL:** {page.url}
- **Título:** {page.title}
- **Rota:** {page.route}

## ELEMENTOS ENCONTRADOS

{elements_desc}

## TEXTO VISÍVEL NA PÁGINA

{page.page_text_summary or "Não disponível"}

---

## TAREFA

Analise esta página no contexto do sistema e gere casos de teste QA.

**Resumo da Página:** Explique em 2-3 frases o propósito desta tela, quem a utiliza e qual ação principal ela habilita.

Gere apenas casos de teste para o que foi realmente observado:
- Se a página tem formulário complexo: cubra validações, campos obrigatórios, limites, estados de erro
- Se tem tabela/lista: cubra filtros, ordenação, ações por linha (editar, excluir), estado vazio
- Se é uma tela de detalhe: cubra exibição de dados, transições de status, ações disponíveis
- Se é tela simples de leitura: gere CTs básicos de visualização e navegação

## FORMATO DE SAÍDA OBRIGATÓRIO

### Resumo da Página
[2-3 frases: propósito, quem usa, ação principal]

### Casos de Teste

| # | Cenário | Pré-condição | Passos | Resultado Esperado | Prioridade |
|---|---------|-------------|--------|--------------------|-----------|
| CT-01 | [nome claro do cenário] | [estado necessário] | [passos numerados] | [o que deve acontecer] | Alta/Média/Baixa |

[Mínimo 3, máximo 12 casos — proporcional à complexidade real da página]

### Riscos e Pontos de Atenção
- [riscos concretos baseados nos elementos desta página — sem generalidades]

---
"""

    return _call_llm(SYSTEM_PROMPT, prompt, model, api_key, max_tokens=2500)


def _describe_elements(page: PageData) -> str:
    parts = []

    if page.headings:
        parts.append("**Headings:**\n" + "\n".join(f"  - {h}" for h in page.headings))

    if page.forms:
        form_desc = []
        for i, f in enumerate(page.forms, 1):
            inp_list = ", ".join(
                f"{inp['name']} ({inp['type']}{'*' if inp['required'] else ''})"
                for inp in f["inputs"]
            )
            form_desc.append(
                f"  - Formulário {i}: {f['method'].upper()} {f['action'] or '(sem action)'} | Campos: {inp_list}"
            )
        parts.append("**Formulários:**\n" + "\n".join(form_desc))

    if page.inputs:
        inp_list = ", ".join(f"{i['name']} ({i['type']})" for i in page.inputs)
        parts.append(f"**Inputs soltos:** {inp_list}")

    if page.buttons:
        parts.append("**Botões:** " + " | ".join(page.buttons[:12]))

    if page.tables:
        tbl_desc = []
        for t in page.tables:
            headers = ", ".join(t["headers"]) if t["headers"] else "sem cabeçalho"
            tbl_desc.append(f"  - Tabela com {t['rows']} linhas | Colunas: {headers}")
        parts.append("**Tabelas:**\n" + "\n".join(tbl_desc))

    if page.alerts_modals:
        parts.append("**Modais/Alertas detectados:** " + " | ".join(page.alerts_modals[:3]))

    if not parts:
        parts.append("Nenhum elemento interativo detectado — página possivelmente estática ou de leitura.")

    return "\n\n".join(parts)


def generate_summary(
    pages_analysis: list[dict],
    site_url: str,
    api_key: str,
    model: str = "claude-opus-4-5",
) -> str:
    rotas = "\n".join(f"- {p['route']} — {p['title']}" for p in pages_analysis)

    resumos = []
    for p in pages_analysis:
        lines = p["test_cases_md"].splitlines()
        for j, line in enumerate(lines):
            if "### Resumo da Página" in line and j + 1 < len(lines):
                resumo = lines[j + 1].strip()
                if resumo:
                    resumos.append(f"- **{p['route']}**: {resumo}")
                break

    contexto_resumos = "\n".join(resumos) if resumos else ""

    prompt = f"""
Você analisou o front-end do sistema em: {site_url}

Telas exploradas:
{rotas}

Contexto das telas (resumos individuais):
{contexto_resumos}

Gere um **resumo executivo** objetivo com:

1. **Tipo e propósito do sistema** — o que é, para quem, qual problema resolve
2. **Perfis de usuário identificados** — quem acessa e o que cada perfil pode fazer
3. **Fluxos críticos** — os 3-5 fluxos mais importantes para cobrir com testes (baseados nas telas reais)
4. **Top 3 riscos de qualidade** — riscos concretos observados, não genéricos
5. **Recomendação de priorização** — por onde começar os testes e por quê

Máximo 250 palavras. Este texto será o preâmbulo do documento de casos de teste.
"""

    return _call_llm("", prompt, model, api_key, max_tokens=800)
