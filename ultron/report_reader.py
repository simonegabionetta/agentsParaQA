"""Le o RELATORIO.md gerado pelo agente ultron e extrai o veredito por caso."""

from __future__ import annotations

import re
from dataclasses import dataclass

NAO_EXECUTADO = "NÃO EXECUTADO"
VEREDITOS_VALIDOS = ("PASSOU", "REPROVOU", "BLOQUEADO", NAO_EXECUTADO)

_SEPARADOR_RE = re.compile(r"^:?-{2,}:?$")


@dataclass
class CaseVerdict:
    id: str
    criterio: str
    veredito: str


@dataclass
class Report:
    cases: list[CaseVerdict]
    table_markdown: str


def _split_row(line: str) -> list[str]:
    return [c.strip() for c in line.strip().strip("|").split("|")]


def _is_separator_row(cells: list[str]) -> bool:
    return all(_SEPARADOR_RE.match(c) for c in cells if c)


def _normalize_veredito(raw: str) -> str:
    text = raw.replace("**", "").replace("`", "").strip().upper()
    for veredito in VEREDITOS_VALIDOS:
        if veredito in text:
            return veredito
    return text


def read_report(markdown_text: str) -> Report:
    lines = markdown_text.splitlines()
    cases: list[CaseVerdict] = []
    table_lines: list[str] = []

    col_id = col_veredito = col_criterio = None
    in_table = False

    for line in lines:
        stripped = line.strip()
        if not stripped.startswith("|"):
            if in_table and col_id is not None:
                # Linha fora da tabela encerra o bloco de veredito por caso.
                break
            continue

        cells = _split_row(line)

        if col_id is None:
            lowered = [c.lower() for c in cells]
            if "id" in lowered and "veredito" in lowered:
                col_id = lowered.index("id")
                col_veredito = lowered.index("veredito")
                col_criterio = None
                for nome in ("critério", "criterio"):
                    if nome in lowered:
                        col_criterio = lowered.index(nome)
                        break
                in_table = True
                table_lines.append(line)
            continue

        if _is_separator_row(cells):
            table_lines.append(line)
            continue

        if len(cells) <= max(col_id, col_veredito):
            continue

        case_id = cells[col_id].strip()
        if not case_id:
            continue

        veredito = _normalize_veredito(cells[col_veredito])
        criterio = ""
        if col_criterio is not None and col_criterio < len(cells):
            criterio = cells[col_criterio].strip()

        cases.append(CaseVerdict(id=case_id, criterio=criterio, veredito=veredito))
        table_lines.append(line)

    return Report(cases=cases, table_markdown="\n".join(table_lines))


def all_passed(cases: list[CaseVerdict]) -> bool:
    return bool(cases) and all(c.veredito == "PASSOU" for c in cases)
