import html
import json
import re


def escape(value):
    return html.escape(str(value), quote=True)


def fragments(value, max_chars=None):
    return [str(value)]


def _groups(identity, sections, observations):
    groups = [("Identificação", identity)] + list(sections)
    if observations:
        groups.append(("Origem e observações", [("Observação " + str(i), note)
                                               for i, note in enumerate(observations, 1)]))
    return groups


def rich_pages(identity, sections, observations, controls):
    parts = ["<h2>Infocard · dados coletados</h2>"]
    for title, rows in _groups(identity, sections, observations):
        parts.append("<h3>" + escape(title) + "</h3><table>")
        parts.extend("<tr><th>" + escape(key) + "</th><td>" + escape(value) + "</td></tr>"
                     for key, value in rows)
        parts.append("</table>")
    parts.append(controls or "")
    return ["".join(parts)]


def basic_pages(identity, sections, observations):
    parts = ["<b>Infocard · dados coletados</b>"]
    for title, rows in _groups(identity, sections, observations):
        parts.append("<b>" + escape(title) + "</b>")
        parts.extend("<b>" + escape(key) + ":</b> " + escape(value) for key, value in rows)
    return ["\n".join(parts)]


def markdown_document(identity, sections, observations):

    linhas = [
        "# Infocard — dados coletados nesta consulta", "",
        "Fonte: campos mapeados das respostas MTProto e Bot API; campos de autenticação são preservados sem redação também no JSONL.",
        "Campos ausentes podem não ter sido consultados ou retornados; ausência não comprova inexistência.", "",
    ]
    for titulo, campos in [("Identificação confirmada", identity)] + list(sections):
        if not campos:
            continue
        linhas.extend(["## " + str(titulo), ""])
        for nome, valor in campos:
            rotulo = str(nome).replace("\r", " ").replace("\n", " ")
            original = str(valor)
            max_fence = max((len(m.group(0)) for m in re.finditer(r"\x60+", original)), default=0)
            fence = chr(96) * max(3, max_fence + 1)
            linhas.extend(["### " + rotulo, "", fence + "text", original, fence, ""])
    if observations:
        linhas.extend(["## Origem e observações", ""])
        for i, nota in enumerate(observations, 1):
            original = str(nota)
            max_fence = max((len(m.group(0)) for m in re.finditer(r"\x60+", original)), default=0)
            fence = chr(96) * max(3, max_fence + 1)
            linhas.extend([f"### Observação {i}", "", fence + "text", original, fence, ""])
    return "\n".join(linhas) + "\n"



def jsonl_files(records, max_bytes=None):
    return ["".join(json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n"
                    for record in records).encode("utf-8")]


def markdown_files(identity, sections, observations, max_bytes=None):
    return [markdown_document(identity, sections, observations).encode("utf-8")]
