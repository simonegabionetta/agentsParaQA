"""
Crawler com Playwright.
Navega pelo site, detecta páginas, formulários, botões, inputs e captura screenshots.
"""

import re
import time
from dataclasses import dataclass, field
from typing import Optional
from urllib.parse import urljoin, urlparse

from playwright.sync_api import sync_playwright, Page, Browser, BrowserContext


@dataclass
class PageData:
    url: str
    title: str
    route: str                          # path normalizado (ex: /dashboard/users)
    forms: list[dict] = field(default_factory=list)
    buttons: list[str] = field(default_factory=list)
    inputs: list[dict] = field(default_factory=list)
    links_found: list[str] = field(default_factory=list)
    headings: list[str] = field(default_factory=list)
    alerts_modals: list[str] = field(default_factory=list)
    tables: list[dict] = field(default_factory=list)
    screenshot_path: Optional[str] = None
    page_text_summary: str = ""         # primeiros 800 chars de texto visível


class SiteCrawler:
    def __init__(self, headless: bool = True, capture_screenshots: bool = True):
        self.headless = headless
        self.capture_screenshots = capture_screenshots

    def crawl(
        self,
        start_url: str,
        email: str = "",
        senha: str = "",
        login_click_text: str = "",
        max_pages: int = 15,
        verbose: bool = False,
    ) -> list[PageData]:
        """
        Percorre o site a partir de start_url.
        Retorna lista de PageData com tudo que foi encontrado.
        """
        base_domain = _base_domain(start_url)
        visited: set[str] = set()
        queue: list[str] = [start_url]
        results: list[PageData] = []

        with sync_playwright() as pw:
            browser: Browser = pw.chromium.launch(headless=self.headless)
            context: BrowserContext = browser.new_context(
                viewport={"width": 1280, "height": 900},
                ignore_https_errors=True,
            )
            page: Page = context.new_page()

            # ── Login ────────────────────────────────────────────────
            if login_click_text:
                if verbose:
                    print(f"  🔐 Login por clique em '{login_click_text}'...")
                self._do_click_login(page, start_url, login_click_text, verbose)
            elif email and senha:
                if verbose:
                    print(f"  🔐 Tentando login em {start_url}...")
                self._do_login(page, start_url, email, senha, verbose)
            else:
                page.goto(start_url, wait_until="networkidle", timeout=30000)

            # Adiciona URL atual após login (pode ter redirecionado)
            queue = [page.url]

            # ── Crawl ────────────────────────────────────────────────
            while queue and len(results) < max_pages:
                url = queue.pop(0)
                norm = _normalize_url(url)

                if norm in visited:
                    continue
                if not _same_domain(url, base_domain):
                    continue

                visited.add(norm)

                if verbose:
                    print(f"  📄 [{len(results)+1}/{max_pages}] {url}")

                try:
                    page.goto(url, wait_until="networkidle", timeout=20000)
                    page.wait_for_timeout(800)  # JS dinâmico
                except Exception as e:
                    if verbose:
                        print(f"    ⚠️  Erro ao navegar: {e}")
                    continue

                pd = self._extract_page_data(page, url, len(results))
                results.append(pd)

                # Descobre novos links
                for link in pd.links_found:
                    norm_link = _normalize_url(link)
                    if norm_link not in visited and _same_domain(link, base_domain):
                        queue.append(link)

            browser.close()

        return results

    # ------------------------------------------------------------------
    # Login automático
    # ------------------------------------------------------------------

    def _do_login(self, page: Page, url: str, email: str, senha: str, verbose: bool):
        page.goto(url, wait_until="networkidle", timeout=30000)
        page.wait_for_timeout(1000)

        # Tenta detectar campos de login por heurísticas comuns
        email_selectors = [
            'input[type="email"]',
            'input[name*="email"]',
            'input[name*="user"]',
            'input[placeholder*="mail" i]',
            'input[placeholder*="usuário" i]',
            'input[id*="email"]',
            'input[id*="login"]',
        ]
        password_selectors = [
            'input[type="password"]',
            'input[name*="pass"]',
            'input[name*="senha"]',
        ]
        submit_selectors = [
            'button[type="submit"]',
            'input[type="submit"]',
            'button:has-text("Entrar")',
            'button:has-text("Login")',
            'button:has-text("Sign in")',
            'button:has-text("Acessar")',
        ]

        email_field = _find_first(page, email_selectors)
        pass_field = _find_first(page, password_selectors)

        if not email_field or not pass_field:
            if verbose:
                print("    ⚠️  Campos de login não encontrados automaticamente.")
            return

        page.fill(email_field, email)
        page.fill(pass_field, senha)

        submit = _find_first(page, submit_selectors)
        if submit:
            page.click(submit)
            page.wait_for_load_state("networkidle", timeout=15000)
            page.wait_for_timeout(1000)
        else:
            page.keyboard.press("Enter")
            page.wait_for_load_state("networkidle", timeout=15000)

        if verbose:
            print(f"    ✅ Login executado. URL atual: {page.url}")

    def _do_click_login(self, page: Page, url: str, click_text: str, verbose: bool):
        page.goto(url, wait_until="networkidle", timeout=30000)
        page.wait_for_timeout(1000)

        selectors = [
            f'button:has-text("{click_text}")',
            f'a:has-text("{click_text}")',
            f'[role="button"]:has-text("{click_text}")',
            f'div:has-text("{click_text}")',
            f'span:has-text("{click_text}")',
            f'li:has-text("{click_text}")',
        ]

        clicked = False
        for sel in selectors:
            try:
                el = page.query_selector(sel)
                if el and el.is_visible():
                    login_url = page.url
                    el.click()
                    # Aguarda sair da página de login (SPA pode demorar)
                    try:
                        page.wait_for_url(lambda u: u != login_url, timeout=10000)
                    except Exception:
                        pass
                    page.wait_for_load_state("networkidle", timeout=15000)
                    page.wait_for_timeout(1000)
                    clicked = True
                    break
            except Exception:
                continue

        if not clicked:
            if verbose:
                print(f"    ⚠️  Elemento '{click_text}' não encontrado para clique de login.")
        elif verbose:
            print(f"    ✅ Clique em '{click_text}' executado. URL atual: {page.url}")

    # ------------------------------------------------------------------
    # Extração de dados da página
    # ------------------------------------------------------------------

    def _extract_page_data(self, page: Page, url: str, idx: int) -> PageData:
        title = page.title() or ""
        route = urlparse(url).path or "/"

        # Headings
        headings = []
        for sel in ["h1", "h2", "h3"]:
            els = page.query_selector_all(sel)
            for el in els[:5]:
                txt = el.inner_text().strip()
                if txt:
                    headings.append(f"{sel.upper()}: {txt}")

        # Formulários
        forms = []
        for form_el in page.query_selector_all("form")[:5]:
            form_inputs = []
            for inp in form_el.query_selector_all("input, select, textarea"):
                inp_type = inp.get_attribute("type") or inp.evaluate("el => el.tagName.toLowerCase()")
                inp_name = inp.get_attribute("name") or inp.get_attribute("id") or inp.get_attribute("placeholder") or ""
                inp_required = inp.get_attribute("required") is not None
                form_inputs.append({
                    "type": inp_type,
                    "name": inp_name,
                    "required": inp_required,
                })
            action = form_el.get_attribute("action") or ""
            method = form_el.get_attribute("method") or "GET"
            if form_inputs:
                forms.append({"action": action, "method": method, "inputs": form_inputs})

        # Inputs soltos (fora de form)
        inputs = []
        for inp in page.query_selector_all("input:not(form input), select:not(form select), textarea:not(form textarea)")[:10]:
            inp_type = inp.get_attribute("type") or "text"
            inp_name = inp.get_attribute("name") or inp.get_attribute("id") or inp.get_attribute("placeholder") or ""
            if inp_name and inp_type not in ("hidden", "submit"):
                inputs.append({"type": inp_type, "name": inp_name})

        # Botões
        buttons = []
        for btn in page.query_selector_all("button, [role='button'], a.btn, .btn")[:15]:
            txt = btn.inner_text().strip()
            if txt and len(txt) < 60:
                buttons.append(txt)
        buttons = list(dict.fromkeys(buttons))  # deduplica mantendo ordem

        # Links internos
        links_found = []
        for a in page.query_selector_all("a[href]")[:50]:
            href = a.get_attribute("href") or ""
            full = urljoin(url, href)
            if full.startswith("http") and "#" not in full:
                links_found.append(full)

        # Tabelas
        tables = []
        for tbl in page.query_selector_all("table")[:3]:
            headers = []
            for th in tbl.query_selector_all("th"):
                txt = th.inner_text().strip()
                if txt:
                    headers.append(txt)
            row_count = len(tbl.query_selector_all("tr"))
            if headers or row_count > 1:
                tables.append({"headers": headers, "rows": row_count})

        # Modais / alertas (detecta elementos escondidos com role=dialog)
        alerts_modals = []
        for el in page.query_selector_all("[role='dialog'], [role='alert'], .modal, .alert")[:5]:
            txt = el.inner_text().strip()[:100]
            if txt:
                alerts_modals.append(txt)

        # Texto visível resumido
        try:
            body_text = page.inner_text("body")
            page_text_summary = " ".join(body_text.split())[:800]
        except Exception:
            page_text_summary = ""

        # Screenshot
        screenshot_path = None
        if self.capture_screenshots:
            import os
            os.makedirs("screenshots", exist_ok=True)
            screenshot_path = f"screenshots/page_{idx:02d}.png"
            try:
                page.screenshot(path=screenshot_path, full_page=False)
            except Exception:
                screenshot_path = None

        return PageData(
            url=url,
            title=title,
            route=route,
            forms=forms,
            buttons=buttons,
            inputs=inputs,
            links_found=links_found,
            headings=headings,
            alerts_modals=alerts_modals,
            tables=tables,
            screenshot_path=screenshot_path,
            page_text_summary=page_text_summary,
        )


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _base_domain(url: str) -> str:
    parsed = urlparse(url)
    return parsed.netloc


def _same_domain(url: str, base_domain: str) -> bool:
    return urlparse(url).netloc == base_domain


def _normalize_url(url: str) -> str:
    """Remove query string e fragment para deduplicação."""
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}{parsed.path}".rstrip("/")


def _find_first(page: Page, selectors: list[str]) -> Optional[str]:
    for sel in selectors:
        try:
            el = page.query_selector(sel)
            if el and el.is_visible():
                return sel
        except Exception:
            continue
    return None
