import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from report_reader import read_report, all_passed, CaseVerdict


RELATORIO_TUDO_PASSOU = """
Relatório de Testes
Funcionalidade: ATD-142  Importação de contatos via CSV

Card: ATD-142 · Tipo: Funcionalidade · Módulo: CRM · Status no Jira: Em QA · Ambiente: staging

2 passaram · 0 reprovaram · 0 bloqueados

## Veredito por caso

| ID | Caso (título e comportamento esperado) | Critério | Automatizar | Veredito |
|----|------------------------------------------|----------|--------------|----------|
| CT01 | **Importar CSV válido**<br>Esperado: toast de sucesso | CA-01 | Sim | PASSOU |
| CT02 | **Importar CSV vazio**<br>Esperado: mensagem de arquivo vazio | CA-02 | Não | PASSOU |
"""

RELATORIO_COM_FALHA = """
Relatório de Testes
Bug: ATD-200  Categoria não aparece no filtro

Card: ATD-200 · Tipo: Bug · Módulo: CRM · Status no Jira: Em QA · Ambiente: staging

1 passou · 1 reprovou · 0 bloqueados

## Veredito por caso

| ID | Caso (título e comportamento esperado) | Critério | Automatizar | Veredito |
|----|------------------------------------------|----------|--------------|----------|
| CT01 | **Filtro lista categoria ativa**<br>Esperado: aparece na lista | CA-01 | Sim | PASSOU |
| CT02 | **Filtro lista categoria criada agora**<br>Esperado: aparece na lista | CA-02 | Sim | **REPROVOU** |

## Bugs encontrados

| # | Caso | O que acontece (visão do usuário) | Causa | Responsável |
|---|------|-----------------------------------|-------|-------------|
| BUG-01 | CT02 | Categoria criada não aparece no filtro até recarregar a página | cache do filtro não invalida ao criar | tela (front-end) |
"""


def test_parse_veredicts_todos_passaram():
    report = read_report(RELATORIO_TUDO_PASSOU)
    assert [c.id for c in report.cases] == ["CT01", "CT02"]
    assert all(c.veredito == "PASSOU" for c in report.cases)
    assert all_passed(report.cases) is True


def test_parse_veredicts_com_reprovado():
    report = read_report(RELATORIO_COM_FALHA)
    assert [c.veredito for c in report.cases] == ["PASSOU", "REPROVOU"]
    assert all_passed(report.cases) is False


def test_veredito_com_negrito_normaliza():
    report = read_report(RELATORIO_COM_FALHA)
    ct02 = next(c for c in report.cases if c.id == "CT02")
    assert ct02.veredito == "REPROVOU"
    assert ct02.criterio == "CA-02"


def test_tabela_de_bugs_nao_vira_caso():
    report = read_report(RELATORIO_COM_FALHA)
    ids = [c.id for c in report.cases]
    assert "BUG-01" not in ids
    assert len(report.cases) == 2


def test_all_passed_com_lista_vazia_e_falso():
    assert all_passed([]) is False


def test_nao_executado_e_reconhecido():
    texto = """
| ID | Caso | Critério | Automatizar | Veredito |
|----|------|----------|--------------|----------|
| CT01 | **Limite de tamanho do arquivo**<br>Esperado: erro de tamanho | CA-05 | Não | NÃO EXECUTADO |
"""
    report = read_report(texto)
    assert report.cases[0].veredito == "NÃO EXECUTADO"
    assert all_passed(report.cases) is False


def test_table_markdown_preserva_cabecalho_e_linhas():
    report = read_report(RELATORIO_TUDO_PASSOU)
    assert report.table_markdown.splitlines()[0].strip().startswith("| ID |")
    assert "CT01" in report.table_markdown
    assert "CT02" in report.table_markdown
    assert "Bugs encontrados" not in report.table_markdown
