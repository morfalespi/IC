import html
import os
import re
import sys
import unittest

sys.path.insert(0, os.path.dirname(__file__))
from ficha_completa import rich_pages, basic_pages, markdown_document, markdown_files, RICH_BYTES


class TesteFichaCompleta(unittest.TestCase):
    def test_um_cartao_completo(self):
        paginas = rich_pages(
            [("Tipo", "usuário"), ("Nome", "Exemplo")],
            [("Perfil e atividade", [("Bio", "Descrição oficial")])],
            ["Referência verificada"], "")
        self.assertEqual(len(paginas), 1)
        self.assertIn("Identificação confirmada", paginas[0])
        self.assertIn("Descrição oficial", paginas[0])
        self.assertIn("Referência verificada", paginas[0])

    def test_muitos_campos_nao_se_perdem(self):
        registros = [(f"Campo {i}", "valor-" + str(i) + "-" + ("X" * 900))
                     for i in range(140)]
        paginas = rich_pages([("ID", "777000")], [("Dados", registros)],
                             [f"Nota {i}" for i in range(20)], "")
        self.assertGreater(len(paginas), 1)
        todo = "".join(paginas)
        for i in range(140):
            self.assertIn("valor-" + str(i) + "-", todo)
        for i in range(20):
            self.assertIn("Nota " + str(i), todo)
        self.assertTrue(all(len(pg.encode("utf-8")) <= RICH_BYTES for pg in paginas))

    def test_valor_longo_reconstituivel(self):
        original = "A" * 25000
        paginas = rich_pages([("ID", "42")], [("Extras", [("Bio", original)])], [], "")
        partes = re.findall(
            r"<th>Bio(?: \(parte [^<]+\))?</th><td>([^<]+)</td>", "".join(paginas)
        )
        self.assertEqual("".join(html.unescape(p) for p in partes), original)

    def test_markdown_preserva_campos_e_texto_original(self):
        dados = [
            ("Bio", "<teste> & conteúdo" + "🇧🇷" * 1200),
            ("Comandos", "/a — primeira linha\n/b — segunda linha"),
            ("Texto com markdown", "código de exemplo com " + chr(96) * 5),
        ]
        documento = markdown_document([("ID", "123")], [("Perfil", dados)],
                                      ["Origem verificada no Telegram"])
        for nome, valor in dados:
            self.assertIn(nome, documento)
            self.assertIn(valor, documento)
        self.assertIn("Origem verificada no Telegram", documento)
        self.assertNotIn("API_HASH", documento)

    def test_markdown_fatiado_sem_perder_utf8(self):
        bio = "📄✨漢字" * 2400
        secoes = [("Dados", [("Bio", bio)])]
        partes = markdown_files([("ID", "456")], secoes, [], max_bytes=2048)
        self.assertGreater(len(partes), 1)
        esperado = markdown_document([("ID", "456")], secoes, []).encode("utf-8")
        self.assertTrue(all(len(p) <= 2048 for p in partes))
        for p in partes:
            self.assertTrue(p.decode("utf-8").startswith("# Infocard"))
        textos = [
            trecho
            for pagina in partes
            for trecho in re.findall(
                r"### Bio(?: — trecho [0-9]+)?\n\n~{3,}text\n(.*?)\n~{3,}",
                pagina.decode("utf-8"), flags=re.DOTALL
            )
        ]
        self.assertEqual("".join(textos), bio)
        self.assertIn("Bio", "".join(p.decode("utf-8") for p in partes))

    def test_html_escapado_e_fallback_em_paginas(self):
        original = '<IMG> & "A"' * 1000
        grupos = [("Info", [("Bio", original)])]
        ricos = rich_pages([("ID", "42")], grupos, [], "")
        simples = basic_pages([("ID", "42")], grupos, [])
        self.assertGreater(len(simples), 1)
        self.assertTrue(all(len(s) < 4096 for s in simples))
        self.assertIn("&lt;IMG&gt;", "".join(ricos))
        self.assertNotIn("<IMG>", "".join(ricos))
        self.assertIn("Parte", simples[-1])
        conteudo = "\n".join(simples)
        trechos = re.findall(r"<b>Bio:</b> ([^\n]+)", conteudo)
        self.assertEqual("".join(html.unescape(t) for t in trechos), original)
        self.assertNotIn("&amp;lt;IMG", conteudo)


if __name__ == "__main__":
    unittest.main()
