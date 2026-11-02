"""Paginação sem perda de campos do relatório, conforme limites da Bot API 10.3."""
import html
import re

# Margens conservadoras para tags, caracteres UTF-8 e blocos adicionais.
RICH_BYTES = 25000
RICH_ROWS = 180
BASIC_CHARS = 3800
FIELD_PART = 2600


def escape(value):
    return html.escape(str(value), quote=True)


def fragments(value, max_chars=FIELD_PART):
    text = str(value)
    if not text:
        return [""]
    return [text[i:i + max_chars] for i in range(0, len(text), max_chars)]


def _expand(rows):
    """Divide somente valores longos; não omite partes ou campos."""
    expanded = []
    for label, value in rows:
        pieces = fragments(value)
        for ix, part in enumerate(pieces):
            suffix = f" (parte {ix+1}/{len(pieces)})" if len(pieces) > 1 else ""
            expanded.append((str(label) + suffix, part))
    return expanded


def _rich_table(title, rows):
    body = "".join(
        "<tr><th>" + escape(k) + "</th><td>" + escape(v) + "</td></tr>"
        for k, v in rows
    )
    return "<h3>" + escape(title) + "</h3><table bordered striped compact>" + (
        "<tr><th>Campo</th><th>Resultado</th></tr>" + body + "</table>"
    )


def _basic_lines(title, rows):
    output = ["<b>" + escape(title) + "</b>"]
    output.extend("<b>" + escape(key) + ":</b> " + escape(val) for key, val in rows)
    return output


def rich_pages(identity, sections, observations, controls):
    """Gera tantas Rich Messages quanto necessário, mantendo o conteúdo integral.

    A primeira página é editada no cartão original. Excedentes são mensagens
    complementares ligadas pela numeração e pela identificação confirmada.
    """
    groups = [("👤 Identificação confirmada", _expand(identity))]
    groups.extend((title, _expand(rows)) for title, rows in sections if rows)
    if observations:
        groups.append(("🔎 Origem e observações", _expand(
            [("Observação " + str(i), note) for i, note in enumerate(observations, 1)]
        )))
    prefix = "<h2>📇 Infocard · Relatório oficial</h2>"
    controls = controls or ""
    # Reserva espaço para cabeçalho, rodapé, botões e numeração.
    safe_budget = RICH_BYTES - 1500 - len(controls.encode("utf-8"))
    if safe_budget < 7000:
        raise ValueError("Controles excedem o orçamento seguro da Rich Message")

    segments = []
    for title, rows in groups:
        if not rows:
            continue
        chunk = []
        for entry in rows:
            trial = _rich_table(title, chunk + [entry])
            if chunk and (len(trial.encode("utf-8")) > 10000 or len(chunk) >= 90):
                segments.append((_rich_table(title, chunk), len(chunk)))
                chunk = []
            if len(_rich_table(title, [entry]).encode("utf-8")) > safe_budget:
                raise ValueError("Um campo excedeu o limite seguro de tamanho")
            chunk.append(entry)
        if chunk:
            segments.append((_rich_table(title, chunk), len(chunk)))

    pages = []
    current = []
    n_rows = 0
    size = 0
    for segment, count in segments:
        segment_bytes = len(segment.encode("utf-8"))
        if current and (size + segment_bytes > safe_budget or n_rows + count > RICH_ROWS):
            pages.append(current)
            current = []
            size, n_rows = 0, 0
        current.append(segment)
        size += segment_bytes
        n_rows += count
    if current or not pages:
        pages.append(current)

    result = []
    total = len(pages)
    for ix, body in enumerate(pages, 1):
        foot = (
            "<hr/><footer>Telegram MTProto • somente dados retornados • "
            f"Parte {ix}/{total}</footer>"
        )
        html_result = (prefix + f"<p><b>✅ Resultado verificado · parte {ix}/{total}</b></p>"
                       + "".join(body) + foot + controls)
        if len(html_result.encode("utf-8")) > RICH_BYTES:
            raise ValueError("A paginação gerou uma Rich Message acima do tamanho seguro")
        result.append(html_result)
    return result


def basic_pages(identity, sections, observations):
    groups = [("👤 Identificação confirmada", identity)]
    groups.extend((title, rows) for title, rows in sections if rows)
    if observations:
        groups.append(("🔎 Origem e observações", [
            ("Observação " + str(i), note) for i, note in enumerate(observations, 1)
        ]))
    limit = BASIC_CHARS - 140
    header = "<b>📇 Infocard · Telegram MTProto</b>"
    lines = [header]
    for title, rows in groups:
        lines.append("<b>" + escape(title) + "</b>")
        for key, value in rows:
            label = escape(str(key).replace("\n", " ").replace("\r", " "))
            value = str(value)
            prefix = "<b>" + label + ":</b> "
            pos = 0
            if not value:
                lines.append(prefix)
            while pos < len(value):
                low, high = 1, len(value) - pos
                while low < high:
                    mid = (low + high + 1) // 2
                    candidate = prefix + escape(value[pos:pos + mid])
                    if len(candidate) <= limit - 120:
                        low = mid
                    else:
                        high = mid - 1
                take = low
                line = prefix + escape(value[pos:pos + take])
                if len(line) > limit - 120:
                    raise ValueError("Rótulo muito longo para envio HTML")
                lines.append(line)
                pos += take

    pages = []
    current = []
    for line in lines:
        trial = "\n".join(current + [line])
        if current and len(trial) > limit:
            pages.append("\n".join(current))
            current = []
        current.append(line)
    if current:
        pages.append("\n".join(current))
    return [
        page + f"\n<i>Parte {ix}/{len(pages)}</i>"
        for ix, page in enumerate(pages, 1)
    ]



def markdown_document(identity, sections, observations):
    """Exporta os valores originais em Markdown UTF-8, sem resumir ou cortar."""
    linhas = [
        "# Infocard — relatório completo", "",
        "Fonte: respostas oficiais do Telegram MTProto acessíveis à sessão do bot.",
        "Campos ausentes não foram retornados; não implicam inexistência.", "",
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


def markdown_files(identity, sections, observations, max_bytes=40 * 1024 * 1024):
    if max_bytes < 1024:
        raise ValueError("max_bytes muito pequeno")
    whole = markdown_document(identity, sections, observations).encode("utf-8")
    if len(whole) <= max_bytes:
        return [whole]

    header = (
        "# Infocard — relatório completo (continuação)\n\n"
        "Fonte: dados oficialmente acessíveis à sessão MTProto do bot.\n\n"
    )
    groups = [("Identificação confirmada", identity)] + list(sections)
    if observations:
        groups.append(("Origem e observações", [
            ("Observação " + str(i), note) for i, note in enumerate(observations, 1)
        ]))

    def render(section, label, content, segment):
        longest = max((len(m.group(0)) for m in re.finditer(r"~+", content)), default=0)
        fence = "~" * max(3, longest + 1)
        suffix = f" — trecho {segment}" if segment > 1 else ""
        return (
            "## " + str(section) + "\n\n### " +
            str(label).replace("\r", " ").replace("\n", " ") + suffix +
            "\n\n" + fence + "text\n" + content + "\n" + fence + "\n\n"
        )

    pages = []
    current = header
    for section, rows in groups:
        for label, value in rows:
            value = str(value)
            position = 0
            part = 1
            while True:
                remaining = value[position:]
                block = render(section, label, remaining, part)
                if len((current + block).encode("utf-8")) <= max_bytes:
                    current += block
                    break
                if current != header:
                    pages.append(current.encode("utf-8"))
                    current = header
                    continue
                low, high = 0, len(remaining)
                while low < high:
                    middle = (low + high + 1) // 2
                    trial = render(section, label, remaining[:middle], part)
                    if len((header + trial).encode("utf-8")) <= max_bytes:
                        low = middle
                    else:
                        high = middle - 1
                if low == 0:
                    raise ValueError("Um rótulo excede o limite do documento")
                current += render(section, label, remaining[:low], part)
                pages.append(current.encode("utf-8"))
                current = header
                position += low
                part += 1
                if position == len(value):
                    break
    if current != header:
        pages.append(current.encode("utf-8"))
    return pages
