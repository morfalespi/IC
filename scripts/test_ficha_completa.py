import html
import os
import re
import sys
import unittest

sys.path.insert(0, os.path.dirname(__file__))
from ficha_completa import rich_pages, basic_pages, RICH_BYTES


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


if __name__ == "__main__":
    unittest.main()
