"""
Gerador do documento .docx com os casos de teste.
Usa docx-js via Node.js conforme a SKILL.md.
"""

import json
import os
import re
import subprocess
import tempfile
from datetime import datetime
from urllib.parse import urlparse


def generate_docx(
    pages_analysis: list[dict],
    summary_text: str,
    site_url: str,
    perfil: str,
    output_path: str,
) -> str:
    """
    Gera o .docx completo com todos os casos de teste.
    Retorna o caminho do arquivo gerado.
    """
    # Serializa os dados para o script JS
    payload = {
        "site_url": site_url,
        "perfil": perfil,
        "generated_at": datetime.now().strftime("%d/%m/%Y %H:%M"),
        "summary": summary_text,
        "pages": [
            {
                "url": p["url"],
                "title": p["title"],
                "route": p["route"],
                "test_cases_md": p["test_cases_md"],
                "screenshot_path": p.get("screenshot_path", ""),
            }
            for p in pages_analysis
        ],
        "output_path": output_path,
    }

    # Escreve payload em arquivo temporário
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False, encoding="utf-8"
    ) as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
        payload_path = f.name

    # Escreve o script JS
    js_script = _build_js_script()
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".js", delete=False, encoding="utf-8"
    ) as f:
        f.write(js_script)
        js_path = f.name

    try:
        result = subprocess.run(
            ["node", js_path, payload_path],
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.returncode != 0:
            raise RuntimeError(f"Erro no script JS:\n{result.stderr}\n{result.stdout}")
    finally:
        os.unlink(payload_path)
        os.unlink(js_path)

    return output_path


def _build_js_script() -> str:
    return r"""
const fs = require('fs');
const path = require('path');

let docxModule;
try {
  docxModule = require('docx');
} catch(e) {
  console.error('Módulo docx não encontrado. Execute: npm install -g docx');
  process.exit(1);
}

const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  Header, AlignmentType, HeadingLevel, BorderStyle, WidthType, ShadingType,
  LevelFormat, PageBreak
} = docxModule;

const payloadPath = process.argv[2];
const data = JSON.parse(fs.readFileSync(payloadPath, 'utf8'));

// ── Helpers ──────────────────────────────────────────────────────────────────

const BORDER = { style: BorderStyle.SINGLE, size: 1, color: 'CCCCCC' };
const BORDERS = { top: BORDER, bottom: BORDER, left: BORDER, right: BORDER };
const HEADER_FILL = { fill: '1F4E79', type: ShadingType.CLEAR };
const ALT_FILL    = { fill: 'EBF3FB', type: ShadingType.CLEAR };

const cell = (text, opts = {}) => new TableCell({
  borders: BORDERS,
  width: { size: opts.width || 1000, type: WidthType.DXA },
  shading: opts.shading || {},
  margins: { top: 80, bottom: 80, left: 120, right: 120 },
  children: [new Paragraph({
    children: [new TextRun({
      text: String(text),
      bold: opts.bold || false,
      color: opts.color || '000000',
      size: opts.size || 18,
      font: 'Arial',
    })]
  })]
});

function priorityColor(text) {
  if (/alta/i.test(text)) return 'C00000';
  if (/média|media/i.test(text)) return 'C55A11';
  return '375623';
}

// ── Parse de Markdown simples para linhas de texto ───────────────────────────

function mdToRuns(text) {
  const runs = [];
  const parts = text.split(/(\*\*[^*]+\*\*|`[^`]+`)/g);
  for (const part of parts) {
    if (part.startsWith('**') && part.endsWith('**')) {
      runs.push(new TextRun({ text: part.slice(2, -2), bold: true, font: 'Arial', size: 18 }));
    } else if (part.startsWith('`') && part.endsWith('`')) {
      runs.push(new TextRun({ text: part.slice(1, -1), font: 'Courier New', size: 18 }));
    } else if (part) {
      runs.push(new TextRun({ text: part, font: 'Arial', size: 18 }));
    }
  }
  return runs.length ? runs : [new TextRun({ text, font: 'Arial', size: 18 })];
}

// ── Parse de tabela Markdown ─────────────────────────────────────────────────

function parseMdTable(lines) {
  const tableLines = lines.filter(l => l.trim().startsWith('|') && !l.match(/^\|[-:\s|]+\|$/));
  if (tableLines.length < 2) return null;

  const rows = tableLines.map(l =>
    l.trim().replace(/^\||\|$/g, '').split('|').map(c => c.trim())
  );

  const colCount = rows[0].length;
  // largura total: 9026 DXA (A4 com margens 1")
  const colWidth = Math.floor(9026 / colCount);

  const tableRows = rows.map((row, ri) =>
    new TableRow({
      children: row.map((cellText, ci) => {
        const isHeader = ri === 0;
        const isAlt = !isHeader && ri % 2 === 0;
        const isPriority = isHeader ? false : rows[0][ci] && /prioridade/i.test(rows[0][ci]);
        const color = isPriority ? priorityColor(cellText) : (isHeader ? 'FFFFFF' : '000000');

        return new TableCell({
          borders: BORDERS,
          width: { size: colWidth, type: WidthType.DXA },
          shading: isHeader ? HEADER_FILL : (isAlt ? ALT_FILL : {}),
          margins: { top: 80, bottom: 80, left: 120, right: 120 },
          children: [new Paragraph({
            children: [new TextRun({
              text: cellText,
              bold: isHeader,
              color: color,
              size: isHeader ? 18 : 16,
              font: 'Arial',
            })]
          })]
        });
      })
    })
  );

  return new Table({
    width: { size: 9026, type: WidthType.DXA },
    columnWidths: Array(colCount).fill(colWidth),
    rows: tableRows,
  });
}

// ── Converte bloco de Markdown de página em nós do docx ──────────────────────

function mdToDocxNodes(md) {
  const lines = md.split('\n');
  const nodes = [];
  let i = 0;

  while (i < lines.length) {
    const line = lines[i];

    // Heading
    const hMatch = line.match(/^(#{1,3})\s+(.+)/);
    if (hMatch) {
      const level = hMatch[1].length === 1 ? HeadingLevel.HEADING_2
                  : hMatch[1].length === 2 ? HeadingLevel.HEADING_3
                  : HeadingLevel.HEADING_4;
      nodes.push(new Paragraph({
        heading: level,
        children: [new TextRun({ text: hMatch[2], font: 'Arial', bold: true, size: hMatch[1].length === 1 ? 26 : 22 })]
      }));
      i++; continue;
    }

    // Tabela
    if (line.trim().startsWith('|')) {
      const tableLines = [];
      while (i < lines.length && lines[i].trim().startsWith('|')) {
        tableLines.push(lines[i]);
        i++;
      }
      const tbl = parseMdTable(tableLines);
      if (tbl) nodes.push(tbl);
      nodes.push(new Paragraph({ children: [] }));
      continue;
    }

    // Lista
    if (line.match(/^[-*] /)) {
      const text = line.replace(/^[-*] /, '');
      nodes.push(new Paragraph({
        numbering: { reference: 'bullets', level: 0 },
        children: mdToRuns(text),
      }));
      i++; continue;
    }

    // Linha em branco
    if (!line.trim()) {
      nodes.push(new Paragraph({ children: [] }));
      i++; continue;
    }

    // Parágrafo normal
    nodes.push(new Paragraph({ children: mdToRuns(line) }));
    i++;
  }

  return nodes;
}

// ── Capa ─────────────────────────────────────────────────────────────────────

function buildCover(siteUrl, perfil, date) {
  return [
    new Paragraph({ children: [] }),
    new Paragraph({ children: [] }),
    new Paragraph({ children: [] }),
    new Paragraph({
      alignment: AlignmentType.CENTER,
      children: [new TextRun({ text: 'Plano de Testes de Front-End', bold: true, size: 52, font: 'Arial', color: '1F4E79' })]
    }),
    new Paragraph({ children: [] }),
    new Paragraph({
      alignment: AlignmentType.CENTER,
      children: [new TextRun({ text: siteUrl, size: 26, font: 'Arial', color: '2E75B6' })]
    }),
    new Paragraph({ children: [] }),
    new Paragraph({
      alignment: AlignmentType.CENTER,
      children: [new TextRun({ text: `Perfil: ${perfil}  |  Gerado em: ${date}`, size: 20, font: 'Arial', color: '666666' })]
    }),
    new Paragraph({ children: [] }),
    new Paragraph({ children: [] }),
    new Paragraph({
      children: [new TextRun({ text: '', size: 20 }),
        new PageBreak()
      ]
    }),
  ];
}

// ── Resumo executivo ──────────────────────────────────────────────────────────

function buildSummary(summaryText) {
  const nodes = [
    new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun({ text: 'Resumo', font: 'Arial', bold: true, size: 32 })] }),
    new Paragraph({ children: [] }),
  ];
  for (const line of summaryText.split('\n')) {
    if (!line.trim()) { nodes.push(new Paragraph({ children: [] })); continue; }
    nodes.push(new Paragraph({ children: mdToRuns(line) }));
  }
  nodes.push(new Paragraph({ children: [new PageBreak()] }));
  return nodes;
}

// ── Índice de páginas ─────────────────────────────────────────────────────────

function buildIndex(pages) {
  const nodes = [
    new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun({ text: 'Paginas Analisadas', font: 'Arial', bold: true, size: 32 })] }),
    new Paragraph({ children: [] }),
    new Table({
      width: { size: 9026, type: WidthType.DXA },
      columnWidths: [500, 2500, 6026],
      rows: [
        new TableRow({ children: [
          cell('#', { width: 500, bold: true, color: 'FFFFFF', shading: HEADER_FILL }),
          cell('Rota', { width: 2500, bold: true, color: 'FFFFFF', shading: HEADER_FILL }),
          cell('Título', { width: 6026, bold: true, color: 'FFFFFF', shading: HEADER_FILL }),
        ]}),
        ...pages.map((p, i) => new TableRow({ children: [
          cell(String(i + 1), { width: 500, shading: i % 2 === 0 ? ALT_FILL : {} }),
          cell(p.route, { width: 2500, shading: i % 2 === 0 ? ALT_FILL : {} }),
          cell(p.title || p.url, { width: 6026, shading: i % 2 === 0 ? ALT_FILL : {} }),
        ]}))
      ]
    }),
    new Paragraph({ children: [] }),
    new Paragraph({ children: [new PageBreak()] }),
  ];
  return nodes;
}

// ── Seção de casos de teste por página ───────────────────────────────────────

function buildPageSection(page, idx) {
  const nodes = [
    new Paragraph({
      heading: HeadingLevel.HEADING_1,
      children: [new TextRun({ text: `${idx}. ${page.title || page.route}`, font: 'Arial', bold: true, size: 32, color: '1F4E79' })]
    }),
    new Paragraph({
      children: [new TextRun({ text: page.url, font: 'Arial', size: 16, color: '2E75B6', italics: true })]
    }),
    new Paragraph({ children: [] }),
    ...mdToDocxNodes(page.test_cases_md),
    new Paragraph({ children: [] }),
    new Paragraph({ children: [new PageBreak()] }),
  ];
  return nodes;
}

// ── Montagem do documento ─────────────────────────────────────────────────────

const allChildren = [
  ...buildCover(data.site_url, data.perfil, data.generated_at),
  ...buildSummary(data.summary),
  ...buildIndex(data.pages),
  ...data.pages.flatMap((p, i) => buildPageSection(p, i + 1)),
];

const doc = new Document({
  numbering: {
    config: [{
      reference: 'bullets',
      levels: [{ level: 0, format: LevelFormat.BULLET, text: '•', alignment: AlignmentType.LEFT,
        style: { paragraph: { indent: { left: 720, hanging: 360 } } } }]
    }]
  },
  styles: {
    default: { document: { run: { font: 'Arial', size: 20 } } },
    paragraphStyles: [
      { id: 'Heading1', name: 'Heading 1', basedOn: 'Normal', next: 'Normal', quickFormat: true,
        run: { size: 32, bold: true, font: 'Arial', color: '1F4E79' },
        paragraph: { spacing: { before: 320, after: 160 }, outlineLevel: 0 } },
      { id: 'Heading2', name: 'Heading 2', basedOn: 'Normal', next: 'Normal', quickFormat: true,
        run: { size: 26, bold: true, font: 'Arial', color: '2E75B6' },
        paragraph: { spacing: { before: 240, after: 120 }, outlineLevel: 1 } },
      { id: 'Heading3', name: 'Heading 3', basedOn: 'Normal', next: 'Normal', quickFormat: true,
        run: { size: 22, bold: true, font: 'Arial', color: '333333' },
        paragraph: { spacing: { before: 180, after: 80 }, outlineLevel: 2 } },
      { id: 'Heading4', name: 'Heading 4', basedOn: 'Normal', next: 'Normal', quickFormat: true,
        run: { size: 20, bold: true, font: 'Arial', color: '555555' },
        paragraph: { spacing: { before: 120, after: 60 }, outlineLevel: 3 } },
    ]
  },
  sections: [{
    properties: {
      page: {
        size: { width: 11906, height: 16838 },  // A4
        margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 }
      }
    },
    children: allChildren,
  }]
});

Packer.toBuffer(doc).then(buf => {
  fs.writeFileSync(data.output_path, buf);
  console.log('OK:' + data.output_path);
}).catch(err => {
  console.error('ERRO:', err.message);
  process.exit(1);
});
"""
