import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import main as ultron_main


RELATORIO_OK = """
| ID | Caso | Critério | Automatizar | Veredito |
|----|------|----------|--------------|----------|
| CT01 | **Importar CSV válido**<br>Esperado: toast de sucesso | CA-01 | Sim | PASSOU |
"""

RELATORIO_COM_FALHA = """
| ID | Caso | Critério | Automatizar | Veredito |
|----|------|----------|--------------|----------|
| CT01 | **Importar CSV válido**<br>Esperado: toast de sucesso | CA-01 | Sim | PASSOU |
| CT02 | **Importar CSV inválido**<br>Esperado: erro | CA-02 | Sim | REPROVOU |
"""


def _write(tmp_path, texto):
    caminho = tmp_path / "RELATORIO.md"
    caminho.write_text(texto, encoding="utf-8")
    return caminho


def test_recusa_quando_ha_caso_nao_passou(tmp_path, capsys, monkeypatch):
    caminho = _write(tmp_path, RELATORIO_COM_FALHA)
    chamou_post = {"valor": False}

    def fake_build_pm_client(env):
        chamou_post["valor"] = True
        raise AssertionError("nao deveria construir cliente de PM quando ha reprovado")

    monkeypatch.setattr(ultron_main, "build_pm_client", fake_build_pm_client)

    codigo = ultron_main.run_publicar("ATD-200", caminho, dry_run=False)

    saida = capsys.readouterr().out
    assert codigo == 1
    assert "CT02" in saida
    assert "REPROVOU" in saida
    assert chamou_post["valor"] is False


def test_dry_run_nao_publica(tmp_path, capsys, monkeypatch):
    caminho = _write(tmp_path, RELATORIO_OK)

    def fake_build_pm_client(env):
        raise AssertionError("dry-run nao deveria construir cliente de PM")

    monkeypatch.setattr(ultron_main, "build_pm_client", fake_build_pm_client)

    codigo = ultron_main.run_publicar("ATD-142", caminho, dry_run=True)

    saida = capsys.readouterr().out
    assert codigo == 0
    assert "CT01" in saida
    assert "DRY-RUN" in saida.upper()


def test_publica_apos_confirmacao(tmp_path, capsys, monkeypatch):
    caminho = _write(tmp_path, RELATORIO_OK)
    postado = {}

    class FakePMClient:
        def post_comment(self, card_id, body):
            postado["card_id"] = card_id
            postado["body"] = body
            return "https://jira.exemplo/ATD-142?focusedCommentId=1"

    monkeypatch.setattr(ultron_main, "build_pm_client", lambda env: FakePMClient())
    monkeypatch.setattr("builtins.input", lambda _: "sim")

    codigo = ultron_main.run_publicar("ATD-142", caminho, dry_run=False)

    assert codigo == 0
    assert postado["card_id"] == "ATD-142"
    assert "CT01" in postado["body"]


def test_cancela_quando_resposta_nao_e_sim(tmp_path, capsys, monkeypatch):
    caminho = _write(tmp_path, RELATORIO_OK)

    def fake_build_pm_client(env):
        raise AssertionError("nao deveria publicar quando a resposta nao foi sim")

    monkeypatch.setattr(ultron_main, "build_pm_client", fake_build_pm_client)
    monkeypatch.setattr("builtins.input", lambda _: "nao")

    codigo = ultron_main.run_publicar("ATD-142", caminho, dry_run=False)

    assert codigo == 1


def test_relatorio_inexistente_recusa(tmp_path, capsys):
    caminho = tmp_path / "nao-existe.md"

    codigo = ultron_main.run_publicar("ATD-999", caminho, dry_run=False)

    saida = capsys.readouterr().out
    assert codigo == 1
    assert "nao encontrado" in saida.lower() or "não encontrado" in saida.lower()
