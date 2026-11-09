"""Destination-specific encoders; source values remain unchanged."""
import html
import json
import re


def escape(value):
    return html.escape(str(value), quote=True)


def fragments(value, max_chars=3000):
    text = str(value)
    if max_chars < 1:
        raise ValueError('max_chars must be positive')
    return [text[i:i + max_chars] for i in range(0, len(text), max_chars)] or ['']


def _groups(identity, sections, observations):
    return [('Identification', identity)] + list(sections) + ([('Observations', [(str(i), v) for i, v in enumerate(observations, 1)])] if observations else [])


def basic_pages(identity, sections, observations):
    # Escape after splitting, so no entity or UTF-16 surrogate is cut in half.
    pages, current = [], '<b>IC report</b>\n'
    for title, rows in _groups(identity, sections, observations):
        for key, value in [('Section', title)] + list(rows):
            for fragment in fragments(str(key) + ': ' + str(value), 700):
                line = escape(fragment) + '\n'
                if len((current + line).encode('utf-16-le')) // 2 > 3900:
                    pages.append(current)
                    current = ''
                current += line
    if current:
        pages.append(current)
    return pages


def rich_pages(identity, sections, observations, controls=''):
    # A compatibility adapter; the application uses supported Telegram HTML.
    return basic_pages(identity, sections, observations)


def md_escape(value):
    return re.sub(r'([\\`*_{}\[\]()#+.!|>~\-])', r'\\\1', str(value).replace('\r', ' ').replace('\n', ' '))


def markdown_document(identity, sections, observations):
    lines = ['# IC report', '', 'Source values are preserved; credentials and private capabilities are redacted for disclosure.', '']
    for title, rows in _groups(identity, sections, observations):
        lines.extend(['## ' + md_escape(title), ''])
        for key, value in rows:
            text = str(value)
            fence = '`' * max(3, max((len(m.group()) + 1 for m in re.finditer(r'`+', text)), default=3))
            lines.extend(['### ' + md_escape(key), '', fence + 'text', text, fence, ''])
    return '\n'.join(lines) + '\n'


def jsonl_files(records, max_bytes=40 * 1024 * 1024):
    files, current = [], bytearray()
    for record in records:
        line = (json.dumps(record, ensure_ascii=False, separators=(',', ':'), allow_nan=False) + '\n').encode()
        if len(line) > max_bytes:
            raise ValueError('One JSONL record exceeds export size limit')
        if current and len(current) + len(line) > max_bytes:
            files.append(bytes(current))
            current.clear()
        current.extend(line)
    if current or not files:
        files.append(bytes(current))
    return files


def markdown_files(identity, sections, observations, max_bytes=40 * 1024 * 1024):
    # Split only between complete fenced blocks; every part is valid Markdown.
    files, current = [], ''
    for title, rows in _groups(identity, sections, observations):
        for row in rows:
            block = markdown_document([], [(title, [row])], [])
            if len(block.encode()) > max_bytes:
                raise ValueError('One Markdown field exceeds export size limit')
            if current and len((current + block).encode()) > max_bytes:
                files.append(current.encode())
                current = ''
            current += block
    if current or not files:
        files.append(current.encode())
    return files
