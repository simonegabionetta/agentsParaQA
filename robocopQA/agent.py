"""
Orquestrador principal do RoboCop QA.
Coordena: crawl → análise com LLM → geração do .docx
"""

import os
import sys
from datetime import datetime
from urllib.parse import urlparse

from config import Config
from crawler import SiteCrawler
from analysis_engine import analyze_pages, generate_summary
from docx_generator import generate_docx

REPORTS_DIR = "reports"


class RoboCop:
    def __init__(self, config: Config, verbose: bool = False):
        self.config = config
        self.verbose = verbose

    def run(
        self,
        url: str,
        email: str = "",
        senha: str = "",
        login_click_text: str = "",
        perfil: str = "MANUAL",
        max_pages: int = 15,
        output_file: str = "",
        dry_run: bool = False,
    ):
        self._header(url, perfil, dry_run)

        # 1. Crawl
        self._step("Iniciando crawler com Playwright...")
        crawler = SiteCrawler(
            headless=self.config.headless,
            capture_screenshots=self.config.screenshot,
        )

        try:
            pages = crawler.crawl(
                start_url=url,
                email=email,
                senha=senha,
                login_click_text=login_click_text,
                max_pages=max_pages,
                verbose=self.verbose,
            )
        except Exception as e:
            self._error(f"Erro no crawler: {e}")
            sys.exit(1)

        if not pages:
            self._error("Nenhuma pagina foi coletada. Verifique a URL e as credenciais.")
            sys.exit(1)

        self._ok(f"{len(pages)} pagina(s) coletada(s)")

        # 2. Analise com LLM
        self._step(f"Analisando paginas com {self.config.llm_provider} / {self.config.resolved_model} (perfil: {perfil})...")
        try:
            pages_analysis = analyze_pages(
                pages=pages,
                site_url=url,
                perfil=perfil,
                api_key=self.config.api_key,
                model=self.config.resolved_model,
            )
        except Exception as e:
            self._error(f"Erro na analise: {e}")
            sys.exit(1)

        self._ok("Analise concluida")

        # 3. Resumo
        self._step("Gerando resumo...")
        try:
            summary = generate_summary(pages_analysis, url, self.config.api_key, self.config.resolved_model)
        except Exception as e:
            summary = f"Resumo indisponivel: {e}"

        # 4. Dry-run
        if dry_run:
            print("\n" + "=" * 70)
            print(f"RESUMO\n{summary}")
            print("=" * 70)
            for p in pages_analysis:
                print(f"\n{'-'*60}\n{p['route']} -- {p['title']}\n{p['url']}\n")
                print(p["test_cases_md"])
            print("=" * 70)
            self._ok("Dry-run concluido. Nenhum arquivo gerado.")
            return

        # 5. Gera .docx em reports/
        os.makedirs(REPORTS_DIR, exist_ok=True)
        self._step("Gerando documento .docx...")

        if not output_file:
            domain = urlparse(url).netloc.replace(".", "_")
            ts = datetime.now().strftime("%Y%m%d_%H%M")
            output_file = os.path.join(REPORTS_DIR, f"casos_de_teste_{domain}_{ts}.docx")
        elif not os.path.dirname(output_file):
            output_file = os.path.join(REPORTS_DIR, output_file)

        try:
            path = generate_docx(
                pages_analysis=pages_analysis,
                summary_text=summary,
                site_url=url,
                perfil=perfil,
                output_path=output_file,
            )
        except Exception as e:
            self._error(f"Erro ao gerar .docx: {e}\nVerifique se o Node.js e o pacote 'docx' estao instalados.")
            md_path = output_file.replace(".docx", ".md")
            self._save_markdown_fallback(pages_analysis, summary, url, md_path)
            self._ok(f"Arquivo Markdown salvo em: {md_path}")
            return

        ct_count = sum(p["test_cases_md"].count("CT-") for p in pages_analysis)
        self._ok(f"Documento gerado: {path}  ({len(pages_analysis)} paginas | {ct_count} casos de teste)")

    # ------------------------------------------------------------------

    def _save_markdown_fallback(self, pages_analysis, summary, url, path):
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        lines = [
            f"# Plano de Testes -- {url}\n",
            f"## Resumo\n\n{summary}\n",
            "---\n",
        ]
        for p in pages_analysis:
            lines.append(f"## {p['route']} -- {p['title']}\n")
            lines.append(f"**URL:** {p['url']}\n")
            lines.append(p["test_cases_md"])
            lines.append("\n---\n")
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

    # ------------------------------------------------------------------

    def _header(self, url, perfil, dry_run):
        mode = " [DRY-RUN]" if dry_run else ""
        print(f"\n{'='*60}")
        print(f"  RoboCop QA{mode}")
        print(f"  URL: {url}")
        print(f"  Perfil: {perfil}")
        print(f"{'='*60}\n")

    def _step(self, msg):
        print(f">> {msg}")

    def _ok(self, msg):
        print(f"   {msg}")

    def _error(self, msg):
        print(f"\nERRO: {msg}\n")
