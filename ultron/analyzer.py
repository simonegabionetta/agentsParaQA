"""
Motor de análise do Ultron.
Recebe o card + diff do PR e gera casos de teste formatados para comentar no PM.
"""

import litellm
from github_client import PRData
from pm_client import CardData

litellm.suppress_debug_info = True

_SYSTEM = """Você é Ultron, um Engenheiro de QA sênior especializado em revisão de código e geração de testes.

Seu papel é analisar o contexto de um card (história/tarefa/bug) e as alterações de código de um Pull Request e sugerir casos de teste precisos e executáveis para o time de QA.

Regras:
- Gere apenas testes baseados nas alterações reais do diff — nunca invente
- Priorize fluxos críticos e casos de borda revelados pelo código modificado
- Se o diff não tiver lógica testável (só config, docs, etc.), diga isso claramente
- Seja direto e objetivo — o QA vai ler isso no gerenciador de tarefas
"""

_PERFIL_INSTRUCAO = {
    "MANUAL": """
Perfil: MANUAL
- Linguagem orientada ao usuário final: "Clique em X", "Preencha o campo Y com Z"
- Sem menção a seletores CSS, endpoints, IDs técnicos ou código
- Qualquer QA sem background de desenvolvimento deve conseguir executar
""",
    "TECNICO": """
Perfil: TÉCNICO
- Pode mencionar seletores, endpoints, payloads, variáveis e IDs de elementos
- Inclua detalhes de implementação e validação técnica quando relevante
- Voltado para QA com perfil de automação ou devs fazendo validação
""",
}

_TEMPLATE = """
{perfil_instrucao}

## Card
**ID:** {card_id}
**Título:** {card_title}
**Descrição:**
{card_description}

---

## Pull Request(s)
{prs_summary}

## Diff completo
```diff
{diff}
```

---

## Tarefa

Analise o card e o diff acima e produza EXATAMENTE no formato abaixo, sem adicionar seções extras:

---

### Resumo das Alterações
[2-4 frases descrevendo o que foi modificado tecnicamente e qual impacto funcional isso tem para o usuário]

---

### Casos de Teste Sugeridos

| # | Cenário | Pré-condição | Passos | Resultado Esperado | Prioridade |
|---|---------|-------------|--------|--------------------|-----------|
| CT-01 | [nome claro] | [estado necessário] | [passos numerados] | [comportamento esperado] | Alta/Média/Baixa |
[Continue com quantos casos forem necessários — mínimo 3, máximo 15]

---

### Checklist de Validação

- [ ] [item de validação obrigatório]
[Continue com todos os itens relevantes]

---

### Pontos de Atenção

- [risco ou detalhe técnico concreto baseado no diff]
[Continue com outros pontos se houver]

---
"""


def build_comment(
    card: CardData,
    prs: list[PRData],
    model: str,
    api_key: str,
    perfil: str = "MANUAL",
) -> str:
    prs_summary = _format_prs_summary(prs)
    combined_diff = _merge_diffs(prs)
    perfil_instrucao = _PERFIL_INSTRUCAO.get(perfil.upper(), _PERFIL_INSTRUCAO["MANUAL"])

    prompt = _TEMPLATE.format(
        perfil_instrucao=perfil_instrucao,
        card_id=card.id,
        card_title=card.title,
        card_description=card.description or "Sem descrição.",
        prs_summary=prs_summary,
        diff=combined_diff,
    )

    raw = _call_llm(_SYSTEM, prompt, model, api_key)
    return _wrap_comment(card, prs, raw, perfil)


def _call_llm(system: str, prompt: str, model: str, api_key: str) -> str:
    kwargs = {
        "model": model,
        "max_tokens": 3000,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user",   "content": prompt},
        ],
    }
    if api_key:
        kwargs["api_key"] = api_key
    response = litellm.completion(**kwargs)
    return response.choices[0].message.content


def _format_prs_summary(prs: list[PRData]) -> str:
    lines = []
    for pr in prs:
        files = len(pr.files_changed)
        additions = sum(f["additions"] for f in pr.files_changed)
        deletions = sum(f["deletions"] for f in pr.files_changed)
        lines.append(
            f"- **PR #{pr.number}** — {pr.title} | "
            f"Branch: `{pr.head_branch}` → `{pr.base_branch}` | "
            f"{files} arquivo(s) | +{additions} / -{deletions} linhas"
        )
        if pr.commits:
            lines.append("  Commits: " + " · ".join(pr.commits[:5]))
    return "\n".join(lines)


def _merge_diffs(prs: list[PRData]) -> str:
    if len(prs) == 1:
        return _trim_diff(prs[0].diff)
    parts = []
    for pr in prs:
        parts.append(f"# ── PR #{pr.number}: {pr.title} ──")
        parts.append(_trim_diff(pr.diff))
    return "\n\n".join(parts)


def _trim_diff(diff: str, max_chars: int = 18_000) -> str:
    """Trunca diffs muito grandes para não estourar o contexto do LLM."""
    if len(diff) <= max_chars:
        return diff
    return diff[:max_chars] + f"\n\n[... diff truncado — {len(diff) - max_chars} caracteres omitidos ...]"


def _wrap_comment(card: CardData, prs: list[PRData], analysis: str, perfil: str) -> str:
    pr_refs = ", ".join(f"#{pr.number}" for pr in prs)
    header = (
        f"## Ultron QA — Análise automática\n\n"
        f"> Card **{card.id}** · PR(s): {pr_refs} · Perfil: {perfil.upper()}\n\n"
        f"---\n\n"
    )
    footer = (
        "\n\n---\n"
        "_Gerado automaticamente pelo Ultron QA. "
        "Revise os casos antes de executar._"
    )
    return header + analysis + footer
