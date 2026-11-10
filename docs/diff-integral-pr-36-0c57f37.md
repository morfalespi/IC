# Diff integral do PR #36 — captura de 9 de novembro de 2026

Este documento guarda a **comparação integral do PR #36 no instante anterior à inclusão deste próprio arquivo**. É uma captura para leitura e auditoria; não certifica a conformidade operacional do IC.

- **PR:** https://github.com/morfalespi/IC/pull/36
- **Base:** `1609cad4117f0cacdb8e65a5b28862a9d1d18846`
- **Head capturado:** `0c57f37e3cd60ccc19e688ae5ba37c82eb7ab80a`
- **Escopo capturado:** 27 commits; 32 arquivos; 862 adições e 2.806 remoções.
- **Observação:** após o commit que adiciona este documento, o diff atual do PR passa a incluir também este próprio arquivo; por isso esta captura tem um head fixo.
- **Diff atual dinâmico:** https://github.com/morfalespi/IC/pull/36.diff
- **Comparação visual:** https://github.com/morfalespi/IC/pull/36/files

## Diff unificado completo, sem cortes

````diff
diff --git a/.github/workflows/official-api-conformance.yml b/.github/workflows/official-api-conformance.yml
new file mode 100644
index 0000000..ba37666
--- /dev/null
+++ b/.github/workflows/official-api-conformance.yml
@@ -0,0 +1,42 @@
+name: IC - Auditoria Bot API oficial (sem conclusao presumida)
+
+on:
+  push:
+    branches:
+      - fix/verified-core-2026-11-09
+    paths:
+      - ".github/workflows/official-api-conformance.yml"
+      - "scripts/**"
+      - "tgcloud/**"
+      - "tests/**"
+      - "docs/verificacao-api-oficial.md"
+  workflow_dispatch:
+
+permissions:
+  contents: read
+
+jobs:
+  conferencia:
+    runs-on: ubuntu-latest
+    timeout-minutes: 12
+    steps:
+      - uses: actions/checkout@v4
+      - uses: actions/setup-python@v5
+        with:
+          python-version: "3.12"
+          cache: pip
+          cache-dependency-path: scripts/requirements-lock.txt
+      - name: Preparar fixture local
+        run: python -m pip install -r scripts/requirements-lock.txt
+      - name: Ler documentacao atual e confrontar escopo observado
+        run: |
+          set -o pipefail
+          python tests/official_api_conformance.py | tee official-api-audit.log
+      - name: Preservar log inclusive em caso de nao comprovacao
+        if: always()
+        uses: actions/upload-artifact@v4
+        with:
+          name: ic-auditoria-api-oficial
+          path: official-api-audit.log
+          if-no-files-found: warn
+          retention-days: 30
diff --git a/.github/workflows/official-api-live.yml b/.github/workflows/official-api-live.yml
new file mode 100644
index 0000000..1b88afb
--- /dev/null
+++ b/.github/workflows/official-api-live.yml
@@ -0,0 +1,40 @@
+name: IC - Validacao REAL autorizada da Bot API
+
+on:
+  workflow_dispatch:
+    inputs:
+      autorizo_envios_sinteticos:
+        description: "Confirmo a entrega de texto, foto PNG e documento sintéticos no chat de teste configurado como secret"
+        type: boolean
+        required: true
+        default: false
+
+permissions:
+  contents: read
+
+jobs:
+  api-real:
+    runs-on: ubuntu-latest
+    timeout-minutes: 10
+    env:
+      BOT_TOKEN: ${{ secrets.BOT_TOKEN }}
+      IC_TEST_CHAT_ID: ${{ secrets.IC_TEST_CHAT_ID }}
+      IC_ALLOW_SYNTHETIC_DELIVERY: "yes"
+    steps:
+      - uses: actions/checkout@v4
+      - name: Exigir autorizacao e configuracao real
+        env:
+          CONFIRMACAO: ${{ inputs.autorizo_envios_sinteticos }}
+        run: |
+          if [ "$CONFIRMACAO" != "true" ] || [ -z "$BOT_TOKEN" ] || [ -z "$IC_TEST_CHAT_ID" ]; then
+            echo "::error::NAO EXECUTADO: autorizacao, BOT_TOKEN e IC_TEST_CHAT_ID sao obrigatorios."
+            exit 2
+          fi
+      - uses: actions/setup-python@v5
+        with:
+          python-version: "3.12"
+          cache: pip
+          cache-dependency-path: scripts/requirements-lock.txt
+      - run: python -m pip install -r scripts/requirements-lock.txt
+      - name: Executar chamadas reais, conferir identidade e comparar bytes
+        run: python tests/official_api_live.py
diff --git a/.github/workflows/resolver.yml b/.github/workflows/resolver.yml
index a57f38a..80fcb1e 100644
--- a/.github/workflows/resolver.yml
+++ b/.github/workflows/resolver.yml
@@ -9,48 +9,6 @@ on:
         default: ""
       healthcheck:
         description: "Somente verificar o dispatch; não acessa dados do Telegram"
-      alvo:
-        description: "Username público ou ID numérico. Informe expected_id separadamente, quando houver."
-        required: true
-      healthcheck:
-        description: "Somente validar o dispatch; não acessa Telegram"
-        type: boolean
-        required: false
-        default: false
-      validar_apis:
-        description: "Registrar getMe/getChat e MTProto sem exigir identidade, integridade ou redação"
-        type: boolean
-        required: false
-        default: false
-      expected_id:
-        description: "ID do peer esperado, informativo; não bloqueia peers divergentes"
-        required: false
-        default: ""
-      chat:
-        description: "ID do chat que recebe a resposta (vazio: coleta sem entrega; logs com os valores coletados)"
-        required: false
-        default: ""
-      message_id:
-        description: "ID da ficha rica já enviada ao chat para edição progressiva"
-        required: false
-        default: ""
-      modo:
-        description: "completo/resumo consultam; validar_entrega envia uma mensagem e três arquivos sintéticos ao chat indicado sem conferir os bytes"
-        required: false
-        default: "completo"
-        type: choice
-        options: [completo, resumo, validar_entrega]
-      formato:
-        description: "Formato inicial; falhas ricas tentam HTML automaticamente"
-        type: choice
-        options: [rich, html]
-        default: rich
-      origem_id:
-        description: "ID da mensagem original que solicitou o relatório completo"
-        required: false
-        default: ""
-      coletar_midia:
-        description: "Baixar mídia mesmo sem chat de destino para validar a coleta; não envia arquivos nem mensagens sem chat"
         type: boolean
         required: false
         default: false
@@ -74,9 +32,6 @@ jobs:
         run: echo "workflow_dispatch aceito"
       - uses: actions/checkout@v4
         if: ${{ !inputs.healthcheck }}
-      - name: Registrar entradas da consulta sem máscara local
-        if: ${{ !inputs.healthcheck }}
-        run: python3 scripts/mascarar_inputs.py
       - uses: actions/setup-python@v5
         if: ${{ !inputs.healthcheck }}
         with:
@@ -93,34 +48,3 @@ jobs:
       - name: Remover arquivos da solicitação
         if: ${{ always() && !inputs.healthcheck }}
         run: rm -rf .ic
-      - name: Registrar respostas Bot API e MTProto
-        if: ${{ !inputs.healthcheck && inputs.validar_apis }}
-        env:
-          MODO: resumo
-          CHAT_ID: ""
-          MESSAGE_ID: ""
-        run: python scripts/validar_apis.py
-      - name: Validar entrega sintética ao chat escolhido
-        if: ${{ !inputs.healthcheck && inputs.modo == 'validar_entrega' }}
-        env:
-          MODO: validar_entrega
-          CHAT_ID: ${{ inputs.chat }}
-        run: python scripts/validar_entrega.py
-      - if: ${{ !inputs.healthcheck && !inputs.validar_apis && inputs.modo != 'validar_entrega' }}
-        env:
-          ALVO: ${{ inputs.alvo }}
-          EXPECTED_ID: ${{ inputs.expected_id }}
-          CHAT_ID: ${{ inputs.chat }}
-          MESSAGE_ID: ${{ inputs.message_id }}
-          MODO: ${{ inputs.modo }}
-          FORMATO_MENSAGEM: ${{ inputs.formato || 'rich' }}
-          ORIGEM_ID: ${{ inputs.origem_id }}
-          COLETAR_MIDIA: ${{ inputs.coletar_midia }}
-        run: python scripts/resolver.py
-      - name: Avisar o chat ao encerrar, com repetição permitida
-        if: ${{ always() && !inputs.healthcheck && !inputs.validar_apis && inputs.modo != 'validar_entrega' }}
-        env:
-          CHAT_ID: ${{ inputs.chat }}
-          RUN_URL: ${{ github.server_url }}/${{ github.repository }}/actions/runs/${{ github.run_id }}
-        run: python scripts/notificar_falha.py
-
diff --git a/README.md b/README.md
index 927af1a..911c766 100644
--- a/README.md
+++ b/README.md
@@ -2,6 +2,16 @@
 
 An authorization-aware Telegram bot and local export runner. IC uses the official HTTPS Bot API and Telethon 1.45.0 (MTProto layer 229). Python 3.12+ is supported; Node is needed only for the optional TgCloud host and JavaScript checks.
 
+## Evidência, alcance e documentação normativa
+
+A fonte de referência para a Bot API é a [documentação oficial atual](https://core.telegram.org/bots/api), lida novamente em cada verificação. O código deste repositório é objeto de auditoria; commits anteriores não são a regra do comportamento esperado.
+
+- **Comparação local:** a [Action de conformidade](.github/workflows/official-api-conformance.yml) lê as regras oficiais, testa requisições locais e identifica explicitamente métodos e condições sem comprovação. A saída `INCOMPLETO` não é sucesso operacional.
+- **Execução real:** a [Action manual](.github/workflows/official-api-live.yml), após estar disponível no GitHub Actions e ter secrets configurados, pode executar um teste sintético autorizado diretamente nos servidores do Telegram. Nenhuma aprovação local substitui o resultado desse teste.
+- **Limites:** nenhuma dessas verificações isoladamente certifica coleta completa por MTProto, acesso a dados restritos ou leitura de relatórios pelo destinatário.
+
+Os critérios, fontes e códigos de saída estão em [verificacao-api-oficial.md](docs/verificacao-api-oficial.md). A documentação do Telegram orienta os protocolos, mas não garante autorização, visibilidade de dados ou resultados para um alvo específico.
+
 ## Proveniência da colaboração
 
 As correções desta recuperação funcional do IC foram desenvolvidas pelo **ChatGPT com Codex, em colaboração com morfalespi**, que definiu os objetivos e orientou as decisões do trabalho. Este registro se refere às alterações desta recuperação, não à autoria exclusiva de todo o histórico do projeto. A implementação técnica e os relatos de validação foram produzidos pelo agente; a solicitação e a autorização de publicação pelo usuário não equivalem à escrita ou à revisão técnica do código. Veja o [registro verificável de autoria operacional](docs/agent-provenance.md), com commits, escopo das alterações e limites das evidências. Os testes e seus limites estão documentados em [recovery-results.md](docs/recovery-results.md).
diff --git a/docs/contrato-operacional-verificavel.md b/docs/contrato-operacional-verificavel.md
new file mode 100644
index 0000000..2b6a6a2
--- /dev/null
+++ b/docs/contrato-operacional-verificavel.md
@@ -0,0 +1,27 @@
+# Contrato operacional verificável do IC
+
+## Premissa
+
+O IC consulta somente alvos acessíveis pelas APIs oficiais do Telegram a partir de uma sessão autorizada. A autorização para iniciar uma consulta não amplia os direitos da sessão no Telegram; falhas de acesso e resultados incompletos devem ser informados, jamais preenchidos artificialmente.
+
+## Escopo preservado
+
+- Identificar usuário, bot, grupo ou canal acessível por username público ou ID canônico conhecido pela sessão.
+- Conferir EXPECTED_ID antes da coleta e interromper em caso de divergência.
+- Reunir metadados e categorias solicitadas dentro da visibilidade permitida, de limites de paginação e das restrições da API.
+- Gerar arquivos locais Markdown/JSONL e pacotes de mídia verificados quando os dados realmente estiverem disponíveis.
+- Enviar relatórios somente para destinos explicitamente autorizados, com proteção contra repetição incerta de envios.
+- Validar sinteticamente formatos e integridade de anexos; testes controlados não são prova de acesso remoto.
+
+## O que não é prometido
+
+- Acesso universal por ID, histórico integral, membros não visíveis, dados privados ou privilégios administrativos.
+- Leitura pelo destinatário: resposta positiva da Bot API confirma aceitação pelo servidor, não leitura ou recebimento no aplicativo.
+- Bot funcionando em produção a partir de CI verde, healthcheck ou deploy sem teste no Telegram real.
+- Envio ou recuperação automáticos após falha ambígua. Um envio incerto exige reconciliação manual antes de repetir.
+
+## Revisão de integridade em 2026-11-09
+
+A versão de main resultante do merge de PR #35 continha funções duplicadas, blocos antigos inseridos no fluxo novo e saídas enganosas. Esta recuperação restaura **18 arquivos de execução** exatamente como estavam no commit `73ff763ca75dc62c3ad07a4cbbcc23ce833a764f`, antes daquele merge defeituoso, mantendo todo o restante da branch-base. Entre as eliminações estão o bypass de limite de consultas, o registro de entradas privadas em texto aberto, a validação de anexos que alegava sucesso sem conferir bytes e os exits de erro com código 0.
+
+A implementação é submetida novamente à CI em Pull Request. Não há credenciais reais neste commit nem contato vivo com Telegram/TgCloud; a confirmação de produção continua pendente até testes com credenciais seguras e alvos autorizados. Nenhuma execução atual deve alegar o que ainda não foi observado.
diff --git a/docs/execucao-api-real.md b/docs/execucao-api-real.md
new file mode 100644
index 0000000..c0819b2
--- /dev/null
+++ b/docs/execucao-api-real.md
@@ -0,0 +1,16 @@
+# Execução externa controlada da Bot API
+
+A auditoria estática e os fixtures locais não constituem comprovação de execução externa. Para produzir essa evidência, `.github/workflows/official-api-live.yml` disponibiliza execução **manual e voluntária** de `tests/official_api_live.py`.
+
+Pré-condições verificadas em tempo de execução:
+
+1. Confirmação manual `autorizo_envios_sinteticos=true`.
+2. Secret `BOT_TOKEN` configurado para o bot de teste próprio.
+3. Secret `IC_TEST_CHAT_ID` configurado para um chat numérico em que o bot tenha permissão de envio.
+4. Rede e autenticação reais aceitas pelo Telegram.
+
+Somente após as pré-condições, o teste envia texto, PNG e documento sintéticos ao destino configurado, consulta `getMe`, `getChat` e `getFile`, compara os parâmetros com a documentação atual e baixa o documento por `getFile` para confrontar SHA-256 e bytes. O script não pode certificar que uma pessoa leu a mensagem, nem provar operações MTProto ou coleta de dados de terceiros.
+
+Um resultado positivo **desta execução manual** (não da auditoria local) representa a comprovação limitada às chamadas reais exercitadas, ao destino de teste e à sessão configurada. Quaisquer operações que não participarem do teste continuam não verificadas. Não é necessário publicar ou divulgar tokens em código, chat ou logs.
+
+**Estado atual:** workflow adicionado à branch de recuperação em um Pull Request em rascunho. Isso por si só não executa a prova externa, nem confirma disponibilidade de secrets.
diff --git a/docs/verificacao-api-oficial.md b/docs/verificacao-api-oficial.md
new file mode 100644
index 0000000..9b2b49b
--- /dev/null
+++ b/docs/verificacao-api-oficial.md
@@ -0,0 +1,28 @@
+# Referência normativa e evidência operacional — IC
+
+## Fonte
+
+A referência deste projeto é a documentação **atual publicada pelo Telegram no momento de cada execução**, não uma versão anterior do código nem o próprio teste. O comparador em `scripts/official_bot_api_contract.py` (independente dos módulos de teste) baixa os índices oficiais e os arquivos Markdown individuais em `https://core.telegram.org/bots/api.md` e `https://core.telegram.org/bots/api/types.md`, registra URL e SHA-256 no log e lê os requisitos dos métodos observados. Uma mudança no texto pode exigir ajuste do interpretador; nunca deve ser convertida automaticamente em aprovação.
+
+A Bot API 10.4, publicada em 9 de novembro de 2026, tornou `chat_id` opcional **somente para certos envios efêmeros**. A operação normal do IC exige um destino explícito. O IC rejeita `ephemeral_message_parameters` porque não implementa esse modo; isso não é uma proibição da API.
+
+## O que a execução comprova
+
+`.github/workflows/official-api-conformance.yml` exercita métodos do cliente contra um servidor local simulado e confronta as requisições observadas com as tabelas oficiais. O inventário também indica referências a outros métodos no código que não foram executadas. Tipos desconhecidos, regras condicionais sem verificação, lacunas de cobertura e respostas sintéticas não autorizam uma declaração global de conformidade.
+
+Códigos de saída do comparador:
+- `1`: encontrou divergência dentro do que tentou verificar;
+- `2`: faltam evidências para declarar conformidade integral, ou a fonte não pôde ser interpretada;
+- `0`: não deve ocorrer na verificação local enquanto não houver provas de operação integral, pois ela usa respostas simuladas.
+
+A action **não testa** autenticação externa, controle de acesso remoto, MTProto real, entregabilidade final ou leitura de mensagens pelo destinatário. Nenhum comentário, resumo ou CI verde deve substituir essas evidências.
+
+## Execução real independente
+
+`.github/workflows/official-api-live.yml` é manual e exige confirmação explícita. Utiliza `BOT_TOKEN` e `IC_TEST_CHAT_ID` configurados como **secrets do GitHub Actions**. Envia somente conteúdo sintético para o chat de teste explicitamente indicado; consulta `getMe` e `getChat`, envia texto, foto e documento, solicita `getFile` e compara os bytes recuperados do documento. Os logs mostram nomes de métodos e resultados, não os IDs do chat nem credenciais.
+
+Esse teste real não executou automaticamente por ter sido criado na branch do PR. A existência do arquivo e uma CI de sintaxe bem-sucedida não comprovam funcionamento real. Após a integração controlada e configuração do chat de teste, o operador pode iniciá-lo manualmente; ele não garante a entrega ao aplicativo nem a leitura pelo usuário.
+
+## Interpretação
+
+A API determina as regras oficiais. O código implementa operações dentro da visibilidade e permissões concedidas pelo Telegram. O teste local importa regras do comparador, não das fixtures. A aprovação operacional depende de chamadas reais, e o comparador continua podendo deixar regras fora de cobertura; essas lacunas impedem uma conclusão integral. A documentação não executa o programa nem certifica automaticamente a aplicação.
\ No newline at end of file
diff --git a/scripts/bot_api.py b/scripts/bot_api.py
index a166254..d24c162 100644
--- a/scripts/bot_api.py
+++ b/scripts/bot_api.py
@@ -87,6 +87,9 @@ def validate_result_object(value, kind):
         'AcceptedGiftTypes': {'unlimited_gifts': bool, 'limited_gifts': bool, 'unique_gifts': bool, 'premium_subscription': bool, 'gifts_from_channels': bool},
         'Message': {'message_id': int, 'date': int, 'chat': dict},
         'File': {'file_id': str, 'file_unique_id': str},
+        'WebhookInfo': {'url': str, 'has_custom_certificate': bool, 'pending_update_count': int},
+        'UserProfilePhotos': {'total_count': int, 'photos': list},
+        'PhotoSize': {'file_id': str, 'file_unique_id': str, 'width': int, 'height': int},
     }
     if not isinstance(value, dict) or any(type(value.get(key)) is not expected for key, expected in required[kind].items()):
         raise APIProtocolError(kind, {'ok': False, 'description': f'Invalid required fields in {kind}'})
@@ -97,6 +100,12 @@ def validate_result_object(value, kind):
         raise APIProtocolError(kind, {'ok': False, 'description': 'Invalid chat type'})
     if kind == 'Message':
         validate_result_object(value['chat'], 'Chat')
+    if kind == 'UserProfilePhotos':
+        if any(not isinstance(photo, list) for photo in value['photos']):
+            raise APIProtocolError(kind, {'ok': False, 'description': 'Invalid UserProfilePhotos photos'})
+        for photo in value['photos']:
+            for size in photo:
+                validate_result_object(size, 'PhotoSize')
 
 
 @dataclass(frozen=True)
@@ -119,11 +128,20 @@ def decode(cls, method, raw):
             if method in {'getMe', 'getChat', 'getFile', 'sendMessage', 'sendPhoto', 'sendDocument', 'sendRichMessage'}:
                 if not isinstance(result, dict):
                     raise APIProtocolError(method, {'ok': False, 'description': 'Expected an object result'})
-            result_kind = {'getMe': 'User', 'getChat': 'ChatFullInfo', 'getFile': 'File'}.get(method)
+            result_kind = {'getMe': 'User', 'getChat': 'ChatFullInfo', 'getFile': 'File', 'getWebhookInfo': 'WebhookInfo', 'getUserProfilePhotos': 'UserProfilePhotos'}.get(method)
             if method in {'sendMessage', 'sendPhoto', 'sendDocument', 'sendRichMessage', 'editMessageText'}:
                 result_kind = 'Message'
             if result_kind:
                 validate_result_object(result, result_kind)
+            if method == 'getUpdates':
+                if not isinstance(result, list) or any(
+                    not isinstance(update, dict) or type(update.get('update_id')) is not int for update in result
+                ):
+                    raise APIProtocolError(method, {'ok': False, 'description': 'Invalid Update array'})
+            if method == 'getChatMemberCount' and type(result) is not int:
+                raise APIProtocolError(method, {'ok': False, 'description': 'Invalid member count'})
+            if method == 'getChatAdministrators' and not isinstance(result, list):
+                raise APIProtocolError(method, {'ok': False, 'description': 'Invalid administrators array'})
             if method == 'getMe' and (type(result.get('id')) is not int or result.get('is_bot') is not True):
                 raise APIProtocolError(method, {'ok': False, 'description': 'Invalid bot identity'})
             if method == 'getChat' and (type(result.get('id')) is not int or result.get('type') not in {'private', 'group', 'supergroup', 'channel'}):
@@ -159,38 +177,6 @@ def diagnostico_api(resposta, metodo):
             diagnostic[key] = resposta[key]
     # Telegram descriptions and parameters may contain personal identifiers.
     return diagnostic
-def recusar_autenticacao(metodo, resposta):
-    return resposta
-
-
-def chamar(metodo, corpo, cabecalhos):
-    retorno = {}
-    for tentativa in range(3):
-        pedido = urllib.request.Request(
-            f"https://api.telegram.org/bot{os.environ.get('BOT_TOKEN', '')}/{metodo}",
-            data=corpo, headers=cabecalhos,
-        )
-        try:
-            with urllib.request.urlopen(pedido) as resposta:
-                codigo, bruto = resposta.status, resposta.read()
-        except urllib.error.HTTPError as erro:
-            codigo, bruto = erro.code, erro.read()
-        except (urllib.error.URLError, OSError) as erro:
-            retorno = {"ok": False, "error_code": 0, "description": str(erro), "origin": "transport"}
-            continue
-        try:
-            retorno = json.loads(bruto)
-        except ValueError:
-            retorno = {"ok": True, "result": bruto.decode("utf-8", errors="replace")}
-        if not isinstance(retorno, dict):
-            retorno = {"ok": True, "result": retorno}
-        if retorno.get("ok", True):
-            return retorno
-    return retorno
-
-
-def diagnostico_api(resposta, metodo):
-    return {"method": metodo, **resposta}
 
 
 def diagnostico_excecao(erro):
@@ -284,6 +270,10 @@ def call(self, method: str, payload=None, *, body=None, headers=None) -> BotResu
         body = body if body is not None else json.dumps(payload or {}, ensure_ascii=False).encode()
         fields = _fields(body, headers)
         sending = method.startswith('send') or method.startswith('editMessage')
+        if sending and 'ephemeral_message_parameters' in fields:
+            raise ValueError('IC delivery does not implement ephemeral message semantics')
+        if sending and (fields.get('chat_id') is None or fields.get('chat_id') == ''):
+            raise PermissionError('IC delivery requires an explicit destination chat_id')
         journal = None
         key = None
         if sending:
@@ -408,17 +398,3 @@ def registrar_notificacao(resposta, chat_id):
     (path / 'notificado').touch()
     (path / 'notificacao_pendente').unlink(missing_ok=True)
     return state
-        return erro.diagnostic
-    return {"origin": "runtime", "type": type(erro).__name__,
-            "description": str(erro), "stack": traceback.format_exception(erro)}
-
-
-def estado_mensagem(resposta, chat_id=None):
-    return "confirmed"
-
-
-def registrar_notificacao(resposta, chat_id):
-    pasta = Path(os.environ.get("RUNNER_TEMP", "/tmp"))
-    (pasta / "notificado").touch()
-    (pasta / "notificacao_pendente").unlink(missing_ok=True)
-    return "confirmed"
diff --git a/scripts/ficha_completa.py b/scripts/ficha_completa.py
index 565bc0e..7dd3982 100644
--- a/scripts/ficha_completa.py
+++ b/scripts/ficha_completa.py
@@ -85,69 +85,3 @@ def markdown_files(identity, sections, observations, max_bytes=40 * 1024 * 1024)
     if current or not files:
         files.append(current.encode())
     return files
-def fragments(value, max_chars=None):
-    return [str(value)]
-
-
-def _groups(identity, sections, observations):
-    groups = [("Identificação", identity)] + list(sections)
-    if observations:
-        groups.append(("Origem e observações", [("Observação " + str(i), note)
-                                               for i, note in enumerate(observations, 1)]))
-    return groups
-
-
-def rich_pages(identity, sections, observations, controls):
-    parts = ["<h2>Infocard · dados coletados</h2>"]
-    for title, rows in _groups(identity, sections, observations):
-        parts.append("<h3>" + escape(title) + "</h3><table>")
-        parts.extend("<tr><th>" + escape(key) + "</th><td>" + escape(value) + "</td></tr>"
-                     for key, value in rows)
-        parts.append("</table>")
-    parts.append(controls or "")
-    return ["".join(parts)]
-
-
-def basic_pages(identity, sections, observations):
-    parts = ["<b>Infocard · dados coletados</b>"]
-    for title, rows in _groups(identity, sections, observations):
-        parts.append("<b>" + escape(title) + "</b>")
-        parts.extend("<b>" + escape(key) + ":</b> " + escape(value) for key, value in rows)
-    return ["\n".join(parts)]
-
-
-def markdown_document(identity, sections, observations):
-
-    linhas = [
-        "# Infocard — dados coletados nesta consulta", "",
-        "Fonte: campos mapeados das respostas MTProto e Bot API; campos de autenticação são preservados sem redação também no JSONL.",
-        "Campos ausentes podem não ter sido consultados ou retornados; ausência não comprova inexistência.", "",
-    ]
-    for titulo, campos in [("Identificação confirmada", identity)] + list(sections):
-        if not campos:
-            continue
-        linhas.extend(["## " + str(titulo), ""])
-        for nome, valor in campos:
-            rotulo = str(nome).replace("\r", " ").replace("\n", " ")
-            original = str(valor)
-            max_fence = max((len(m.group(0)) for m in re.finditer(r"\x60+", original)), default=0)
-            fence = chr(96) * max(3, max_fence + 1)
-            linhas.extend(["### " + rotulo, "", fence + "text", original, fence, ""])
-    if observations:
-        linhas.extend(["## Origem e observações", ""])
-        for i, nota in enumerate(observations, 1):
-            original = str(nota)
-            max_fence = max((len(m.group(0)) for m in re.finditer(r"\x60+", original)), default=0)
-            fence = chr(96) * max(3, max_fence + 1)
-            linhas.extend([f"### Observação {i}", "", fence + "text", original, fence, ""])
-    return "\n".join(linhas) + "\n"
-
-
-
-def jsonl_files(records, max_bytes=None):
-    return ["".join(json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n"
-                    for record in records).encode("utf-8")]
-
-
-def markdown_files(identity, sections, observations, max_bytes=None):
-    return [markdown_document(identity, sections, observations).encode("utf-8")]
diff --git a/scripts/mascarar_inputs.py b/scripts/mascarar_inputs.py
index 04fba02..5f48aaf 100644
--- a/scripts/mascarar_inputs.py
+++ b/scripts/mascarar_inputs.py
@@ -11,8 +11,6 @@ def principal():
             escaped = str(value).replace('%', '%25').replace('\r', '%0D').replace('\n', '%0A')
             print('::add-mask::' + escaped)
     print(json.dumps({'state': 'inputs_masked'}))
-    evento = json.loads(Path(os.environ["GITHUB_EVENT_PATH"]).read_text())
-    print(json.dumps(evento.get("inputs") or {}, ensure_ascii=False), flush=True)
     return 0
 
 
diff --git a/scripts/mtproto_export.py b/scripts/mtproto_export.py
index 717416d..4ca20fd 100644
--- a/scripts/mtproto_export.py
+++ b/scripts/mtproto_export.py
@@ -47,15 +47,3 @@ def build_media_archives(items, output_dir, max_batch_bytes=40 * 1024 * 1024, ma
                     raise ValueError('Archived media verification failed')
         paths.append(str(path))
     return paths
-def build_media_archives(items, output_dir, max_batch_bytes=None, max_archive_bytes=None):
-    batch = [item for item in items if item.get("path")]
-    if not batch:
-        return []
-    archive_path = os.path.join(output_dir, "midias_parte_1.zip")
-    manifest = [{key: item[key] for key in ("name", "category", "bytes", "sha256")} for item in batch]
-    with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
-        archive.writestr("manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2))
-        for item in batch:
-            archive.write(item["path"], arcname=item["name"])
-            item["status"] = "packaged"
-    return [archive_path]
diff --git a/scripts/notificar_falha.py b/scripts/notificar_falha.py
index 2c589f3..ecf68ac 100644
--- a/scripts/notificar_falha.py
+++ b/scripts/notificar_falha.py
@@ -17,18 +17,4 @@ def principal():
 
 
 if __name__ == '__main__':
-
-from bot_api import chamar, diagnostico_api, registrar_notificacao
-
-
-def principal():
-    chat = os.environ.get("CHAT_ID", "")
-    carga = {"chat_id": chat, "text": "Processamento concluído. Execução: " + os.environ.get("RUN_URL", "")}
-    resposta = chamar("sendMessage", json.dumps(carga).encode(), {"Content-Type": "application/json"})
-    print(json.dumps(diagnostico_api(resposta, "sendMessage"), ensure_ascii=False))
-    registrar_notificacao(resposta, chat)
-    return 0
-
-
-if __name__ == "__main__":
     raise SystemExit(principal())
diff --git a/scripts/official_bot_api_contract.py b/scripts/official_bot_api_contract.py
new file mode 100644
index 0000000..136a5c4
--- /dev/null
+++ b/scripts/official_bot_api_contract.py
@@ -0,0 +1,237 @@
+"""Read Telegram-published Bot API documents and compare observed request/response data.
+
+Parsing is deliberately narrow: an unsupported structure must not count as proof.
+This module does not assert live Telegram execution or complete API conformance.
+"""
+import ast
+from email.parser import BytesParser
+from email.policy import default
+import hashlib
+import json
+from pathlib import Path
+import re
+from urllib.request import Request, urlopen
+
+SOURCE = "https://core.telegram.org/bots/api.md"
+UNKNOWN_TYPES = set()
+RETURNS = {"getMe": "User", "getChat": "ChatFullInfo", "sendMessage": "Message",
+           "sendPhoto": "Message", "sendDocument": "Message", "getFile": "File",
+           "getWebhookInfo": "WebhookInfo", "getUpdates": "Array of Update",
+           "getUserProfilePhotos": "UserProfilePhotos", "getChatMemberCount": "Integer"}
+
+def parse_sections(document):
+    matches = list(re.finditer(r"(?m)^#{2,6}[ \t]+([A-Za-z][A-Za-z0-9]*)[ \t]*$", document))
+    return {m.group(1): document[m.end(): matches[i + 1].start() if i + 1 < len(matches) else len(document)]
+            for i, m in enumerate(matches)}
+
+
+def parse_table(section, columns):
+    lines = section.splitlines()
+    for i, line in enumerate(lines):
+        cells = [x.strip() for x in line.strip().strip("|").split("|")]
+        if cells[:len(columns)] == columns:
+            rows = []
+            for line in lines[i + 1:]:
+                if re.fullmatch(r"[-:\s|]+", line):
+                    continue
+                if not line.strip() or "|" not in line:
+                    break
+                values = [v.strip() for v in line.strip().strip("|").split("|")]
+                if len(values) < len(columns):
+                    break
+                rows.append(dict(zip(columns, values)))
+            if not rows:
+                raise ValueError("Empty official table: " + columns[0])
+            return rows
+    return None
+
+
+def official():
+    def read_page(url):
+        with urlopen(Request(url, headers={"User-Agent": "IC-Conformance-Check/1.0"}), timeout=35) as response:
+            if response.status != 200:
+                raise RuntimeError("Official page failed: " + url)
+            raw = response.read(2_000_001)
+        if not raw or len(raw) > 2_000_000:
+            raise RuntimeError("Official page empty/oversized: " + url)
+        print("FONTE OFICIAL:", url, "SHA256:", hashlib.sha256(raw).hexdigest())
+        return raw.decode("utf-8")
+
+    from urllib.parse import urljoin
+    root = read_page(SOURCE)
+    type_index = read_page("https://core.telegram.org/bots/api/types.md")
+    documents = {"_official_index": root}
+    references = active_bot_api_references()
+    required_types = {kind.removeprefix("Array of ") for kind in RETURNS.values()
+                      if kind != "Integer"} | {"Chat", "AcceptedGiftTypes", "Document", "PhotoSize"}
+    for name in sorted(set(RETURNS) | required_types | set(references)):
+        index = root if name in RETURNS or name in references else type_index
+        match = re.search(r"\[" + re.escape(name) + r"\]\((/bots/api/(?:methods|types)/[^)\s]+\.md)\)", index)
+        if not match:
+            if name in RETURNS or name in required_types:
+                raise RuntimeError("Official document not indexed for required method/type: " + name)
+            continue
+        documents[name] = read_page(urljoin(SOURCE, match.group(1)))
+    print("DOCUMENTOS ATUAIS LIDOS:", len(documents) - 1,
+          "| REFERENCIAS DE METODOS NO CODIGO:", len(references))
+    return documents
+
+
+def ok_type(value, typ):
+    normalized = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", typ).strip().strip("*")
+    if normalized == "Integer or String":
+        return type(value) in (int, str)
+    if normalized == "Integer":
+        return type(value) is int or (type(value) is str and value.lstrip("-").isdigit())
+    if normalized == "String":
+        return isinstance(value, str)
+    if normalized == "Boolean":
+        return type(value) is bool
+    if normalized == "True":
+        return value is True
+    if normalized == "Float":
+        return type(value) in (float, int)
+    if normalized == "InputFile or String":
+        return isinstance(value, (bytes, str))
+    if normalized in {"Chat", "ChatFullInfo", "Message", "User", "File", "AcceptedGiftTypes",
+                      "Document", "PhotoSize", "WebhookInfo", "Update", "UserProfilePhotos"}:
+        return isinstance(value, dict)
+    if normalized.startswith("Array of "):
+        return isinstance(value, list) and all(
+            ok_type(item, normalized[len("Array of "):]) for item in value
+        )
+    raise ValueError("Tipo oficial ainda sem validador: " + normalized)
+
+
+def request_violations(method, params, doc):
+    spec = parse_table(doc, ["Parameter", "Type", "Required", "Description"])
+    if spec is None:
+        return [] if not params and "Requires no parameters" in doc else ["Tabela oficial indisponivel ou argumentos inesperados"]
+    allowed = {row["Parameter"]: row for row in spec}
+    errors = ["Parametro nao encontrado na API: " + name for name in sorted(params.keys() - allowed.keys())]
+    for name, row in allowed.items():
+        required = row["Required"].strip().lower()
+        description = row["Description"].lower()
+        if required not in {"yes", "optional"}:
+            errors.append("Marcador oficial nao interpretado: " + name + "=" + row["Required"])
+        if required == "yes" and name not in params:
+            errors.append("Falta parametro obrigatorio: " + name)
+        if name == "chat_id" and "required unless" in description and "ephemeral reply" in description:
+            if name not in params and "ephemeral_message_parameters" not in params:
+                errors.append("chat_id necessario para envio comum segundo API")
+            if "ephemeral_message_parameters" in params:
+                errors.append("Modo efemero ainda nao verificado no IC")
+        if name in params:
+            try:
+                valid = ok_type(params[name], row["Type"])
+            except ValueError as exc:
+                errors.append(str(exc) + " [" + name + "]")
+            else:
+                if not valid:
+                    errors.append("Tipo de parametro incompativel: " + name + " (" + row["Type"] + ")")
+    return errors
+
+
+def response_violations(obj, kind, docs, stack=()):
+    if kind == "Integer":
+        return [] if type(obj) is int else ["Resposta oficial Integer invalida"]
+    if kind.startswith("Array of "):
+        if not isinstance(obj, list):
+            return ["Resposta oficial nao e array: " + kind]
+        nested = kind[len("Array of "):]
+        return [issue for item in obj
+                for issue in response_violations(item, nested, docs, stack)]
+    if kind in stack:
+        return ["Referencia circular de tipo: " + kind]
+    rows = parse_table(docs[kind], ["Field", "Type", "Description"])
+    if rows is None or not isinstance(obj, dict):
+        return ["Tabela oficial nao interpretada ou resposta nao estruturada: " + kind]
+    errors = []
+    for row in rows:
+        key = row["Field"]
+        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", key):
+            errors.append("Nome de campo nao interpretado: " + kind)
+            continue
+        optional = row["Description"].lstrip(" *_").lower().startswith("optional")
+        if key not in obj:
+            if not optional:
+                errors.append("Falta campo obrigatorio da API em " + kind + ": " + key)
+            continue
+        try:
+            valid = ok_type(obj[key], row["Type"])
+        except ValueError as exc:
+            errors.append(str(exc) + " [" + kind + "." + key + "]")
+            continue
+        if not valid:
+            errors.append("Tipo de campo incompativel: " + kind + "." + key)
+        normalized = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", row["Type"]).strip()
+        if valid and normalized in docs and normalized != "_official_index":
+            errors += response_violations(obj[key], normalized, docs, stack + (kind,))
+        if valid and normalized.startswith("Array of "):
+            errors += response_violations(obj[key], normalized, docs, stack + (kind,))
+    return errors
+
+
+def capture(req, calls):
+    if not req.full_url.startswith("https://api.telegram.org/bot") or req.get_method() != "POST":
+        raise ValueError("Unexpected HTTP endpoint or verb")
+    content_type = req.get_header("Content-type", "")
+    if content_type.startswith("application/json"):
+        params = json.loads(req.data)
+        transport = "JSON"
+    elif content_type.startswith("multipart/form-data"):
+        msg = BytesParser(policy=default).parsebytes(
+            b"Content-Type: " + content_type.encode() + b"\r\nMIME-Version: 1.0\r\n\r\n" + req.data
+        )
+        if not msg.is_multipart():
+            raise ValueError("Invalid multipart body")
+        params = {}
+        for part in msg.iter_parts():
+            key = part.get_param("name", header="content-disposition")
+            if not key or key in params:
+                raise ValueError("Missing or repeated multipart part")
+            params[key] = part.get_payload(decode=True) if part.get_filename() else part.get_payload(decode=True).decode("utf-8")
+        transport = "multipart"
+    else:
+        raise ValueError("Unknown request content type")
+    calls.append((req.full_url.rsplit("/", 1)[-1], params, transport))
+
+
+def active_bot_api_references():
+    """Inventory method references in active source; references are not verified calls."""
+    root = Path(__file__).resolve().parents[1]
+    words = set()
+    pattern = re.compile(r"^(?:get|send|edit|answer|set|delete|copy|forward|ban|unban|restrict|pin|unpin|approve|decline|refund|stop)[A-Z][A-Za-z0-9]*$")
+    paths = sorted((root / "scripts").rglob("*.py")) + sorted((root / "tgcloud").rglob("*.js"))
+    for path in paths:
+        text = path.read_text(encoding="utf-8")
+        if path.suffix == ".py":
+            tree = ast.parse(text, filename=str(path))
+            for node in ast.walk(tree):
+                if isinstance(node, ast.Constant) and isinstance(node.value, str) and pattern.fullmatch(node.value):
+                    words.add(node.value)
+        else:
+            for match in re.finditer(r"\bapi\.([A-Za-z][A-Za-z0-9]*)\s*\(", text):
+                if pattern.fullmatch(match.group(1)):
+                    words.add(match.group(1))
+    return sorted(words)
+
+
+def coverage_inventory(docs, observed):
+    methods = active_bot_api_references()
+    official_index = docs["_official_index"]
+    uncovered = []
+    print("ESCOPO INVENTARIADO: referencias de metodos no codigo ativo =", len(methods))
+    for method in methods:
+        match = re.search(r"\[" + re.escape(method) + r"\]\(/bots/api/methods/[^\s)]+\.md\)", official_index)
+        if not match:
+            uncovered.append(method + " — nenhuma entrada encontrada no índice atual da Bot API; revisar referência")
+            print("NAO VERIFICADO:", method, "| sem correspondência no índice oficial")
+        elif method not in observed:
+            uncovered.append(method + " — documentado, mas fluxo não executado pelo comparador")
+            print("NAO VERIFICADO:", method, "| documentado, sem execução")
+        else:
+            print("EXECUCAO LOCAL OBSERVADA:", method)
+    if len(observed - set(methods)) > 0:
+        uncovered.append("métodos exercitados não catalogados no código ativo: " + repr(sorted(observed - set(methods))))
+    return uncovered
diff --git a/scripts/resolver.py b/scripts/resolver.py
index e764755..a4d3135 100644
--- a/scripts/resolver.py
+++ b/scripts/resolver.py
@@ -7,7 +7,6 @@
 import os
 from pathlib import Path
 import re
-import tempfile
 import sys
 import uuid
 
@@ -134,837 +133,6 @@ async def open_client(bot):
         session.close()
         raise
 
-from telethon.sessions import SQLiteSession
-from telegram_ids import tipo_dialogo
-from exportacao import valor_exportavel
-from bot_api import chamar, diagnostico_api, diagnostico_excecao, BotAPIRequestError, BotAPIAuthenticationError, APIProtocolError, estado_mensagem, registrar_notificacao
-from telethon.tl.functions.channels import GetFullChannelRequest, GetChannelsRequest, GetParticipantsRequest, GetMessagesRequest as GetChannelMessagesRequest
-from telethon.tl.functions.contacts import ResolveUsernameRequest
-from telethon.tl.functions.messages import GetChatsRequest, GetFullChatRequest, GetMessagesRequest
-from telethon.tl.functions.users import GetFullUserRequest, GetUsersRequest
-from telethon.tl.types import Channel, Chat, ChannelParticipantsRecent, ChannelParticipantsAdmins, ChannelParticipantsBots, ChannelParticipantsBanned, ChannelParticipantsKicked, InputChannel, InputPeerChannel, InputPeerChat, InputPeerUser, InputUser, PeerChannel, PeerChat, PeerUser, User, InputMessageID
-
-USERNAME_VALIDO = re.compile(r".*", re.DOTALL)
-MENSAGEM_ID = os.environ.get("MESSAGE_ID", "").strip()
-CHAT_DESTINO = os.environ.get("CHAT_ID", "").strip()
-ID_MENSAGEM = MENSAGEM_ID or None
-MODO = "resumo" if os.environ.get("MODO") == "resumo" else "completo"
-FORMATO_MENSAGEM = os.environ.get("FORMATO_MENSAGEM", "rich")
-EXPECTED_ID = os.environ.get("EXPECTED_ID", "").strip()
-REFERENCIA = os.environ.get("ORIGEM_ID", "")
-ORIGEM_ID = REFERENCIA or None
-
-
-class BotAPIEntity:
-    def __init__(self, chat):
-        self.data = chat
-        self.id = chat.get("id")
-        self.type = chat.get("type")
-        self.title = chat.get("title")
-        self.first_name = chat.get("first_name")
-        self.last_name = chat.get("last_name")
-        self.username = chat.get("username")
-        self.photo = chat.get("photo")
-
-    def to_dict(self):
-        return self.data
-
-
-def id_peer(entidade):
-    return entidade.id if isinstance(entidade, BotAPIEntity) else utils.get_peer_id(entidade)
-
-
-def input_usuario_bot(entidade):
-    if isinstance(entidade, BotAPIEntity) and entidade.type == "private":
-        return InputUser(entidade.id, 0)
-    if isinstance(entidade, User):
-        try:
-            return utils.get_input_user(utils.get_input_peer(entidade))
-        except TypeError:
-            return InputUser(entidade.id, 0)
-    return None
-
-
-def input_canal_bot(entidade):
-    if isinstance(entidade, Channel):
-        try:
-            return utils.get_input_channel(utils.get_input_peer(entidade))
-        except TypeError:
-            return InputChannel(entidade.id, 0)
-    if isinstance(entidade, BotAPIEntity) and entidade.type in ("supergroup", "channel"):
-        id_real, tipo = utils.resolve_id(entidade.id)
-        if tipo is PeerChannel:
-            return InputChannel(id_real, 0)
-    return None
-
-
-def input_peer_canal_bot(entidade):
-    canal = input_canal_bot(entidade)
-    if isinstance(canal, InputChannel):
-        return InputPeerChannel(canal.channel_id, canal.access_hash)
-    return None
-
-
-
-def esc(valor):
-    return html.escape(str(valor), quote=False)
-
-
-def corte(valor, limite=400):
-    texto = " ".join(str(valor).split())
-    return texto
-
-
-
-
-def aceitacao_mensagem(resposta):
-    return True
-
-
-def postar(chat_id, texto, formatado, teclado=None):
-    carga = {"chat_id": chat_id, "text": texto}
-    if formatado:
-        carga["parse_mode"] = "HTML"
-    if teclado:
-        carga["reply_markup"] = teclado
-    return chamar("sendMessage", json.dumps(carga).encode(), {"Content-Type": "application/json"})
-
-
-def enviar(chat_id, texto):
-    retorno = postar(chat_id, texto, True)
-    registrar_notificacao(retorno, chat_id)
-
-
-def enviar_foto(chat_id, conteudo):
-    limite = uuid.uuid4().hex
-    corpo = b"".join([
-        f'--{limite}\r\nContent-Disposition: form-data; name="chat_id"\r\n\r\n{chat_id}\r\n'.encode(),
-        f'--{limite}\r\nContent-Disposition: form-data; name="photo"; filename="perfil.jpg"\r\nContent-Type: image/jpeg\r\n\r\n'.encode(),
-        conteudo,
-        f"\r\n--{limite}--\r\n".encode(),
-    ])
-    retorno = chamar("sendPhoto", corpo, {"Content-Type": f"multipart/form-data; boundary={limite}"})
-
-
-def solicitar_bot_api(metodo, dados, foto=None):
-    corpo = dict(dados)
-    if foto:
-        rich = dict(corpo["rich_message"])
-        rich["html"] = rich["html"].replace("</h2>", '</h2><img src="tg://photo?id=perfil"/>', 1)
-        rich["media"] = [{"id": "perfil", "media": {"type": "photo", "media": "attach://perfil_file"}}]
-        corpo["rich_message"] = rich
-        limite = uuid.uuid4().hex
-        partes = []
-        for chave, valor in corpo.items():
-            texto = json.dumps(valor, ensure_ascii=False) if isinstance(valor, (dict, list)) else str(valor)
-            partes.append(f'--{limite}\r\nContent-Disposition: form-data; name="{chave}"\r\n\r\n{texto}\r\n'.encode("utf-8"))
-        partes.extend([
-            f'--{limite}\r\nContent-Disposition: form-data; name="perfil_file"; filename="perfil.jpg"\r\nContent-Type: image/jpeg\r\n\r\n'.encode(),
-            foto,
-            f'\r\n--{limite}--\r\n'.encode(),
-        ])
-        return chamar(metodo, b"".join(partes), {"Content-Type": f"multipart/form-data; boundary={limite}"})
-    return chamar(metodo, json.dumps(corpo, ensure_ascii=False).encode("utf-8"), {"Content-Type": "application/json"})
-
-
-def marcar_notificado():
-    open(os.path.join(os.environ.get("RUNNER_TEMP", "/tmp"), "notificado"), "w").close()
-
-
-def mensagem_inalterada(resposta):
-    return (resposta.get("error_code") == 400
-            and "message is not modified" in str(resposta.get("description", "")).lower())
-
-
-def editar_ficha_rica(conteudo, foto=None, definitiva=False):
-    if not CHAT_DESTINO:
-        return False, False, ID_MENSAGEM
-    metodo = "editMessageText" if ID_MENSAGEM else "sendRichMessage"
-    dados = {"chat_id": CHAT_DESTINO, "rich_message": {"html": conteudo}}
-    if ID_MENSAGEM:
-        dados["message_id"] = ID_MENSAGEM
-    incorporar = bool(foto)
-    resposta = solicitar_bot_api(metodo, dados, foto if incorporar else None)
-    if metodo == "editMessageText" and mensagem_inalterada(resposta):
-        print("editMessageText: mensagem já está no estado solicitado")
-        if definitiva:
-            marcar_notificado()
-        return True, incorporar, ID_MENSAGEM
-    if definitiva and estado_mensagem(resposta, CHAT_DESTINO) == "confirmed":
-        marcar_notificado()
-    return True, incorporar, (resposta.get("result") or {}).get("message_id")
-
-
-def callback_data(acao, alvo):
-    if re.fullmatch(r"[+-]?\d+", alvo):
-        valor = f"{acao}:i:{alvo}"
-    elif USERNAME_VALIDO.fullmatch(alvo):
-        valor = f"{acao}:u:{EXPECTED_ID}:{alvo}" if EXPECTED_ID else f"{acao}:n:{alvo}"
-    else:
-        return ""
-    return valor
-
-
-def botao_completo(alvo):
-    dados = callback_data("f", alvo)
-    return ('<tg-button type="callback_data" style="primary" data="' +
-            esc(dados) + '">📥 Exportação completa</tg-button>') if dados else ""
-
-def enviar_documento_md(chat, conteudo, id_entidade, indice, total):
-    limite = uuid.uuid4().hex
-    filename = "infocard_" + str(id_entidade).replace("-", "n") + "_dados_coletados"
-    if total > 1:
-        filename += f"_parte_{indice}_de_{total}"
-    filename += ".md"
-    resumo_hash = hashlib.sha256(conteudo).hexdigest()
-    campos = {"chat_id": str(chat), "caption": "📄 Dados coletados nesta consulta" +
-              (f" · parte {indice}/{total}" if total > 1 else "") +
-              "\nSHA-256: " + resumo_hash}
-    if ORIGEM_ID:
-        campos["reply_parameters"] = json.dumps({"message_id": ORIGEM_ID})
-    partes = []
-    for chave, valor in campos.items():
-        partes.append((f'--{limite}\r\nContent-Disposition: form-data; name="{chave}"'
-                       f'\r\n\r\n{valor}\r\n').encode("utf-8"))
-    partes.extend([
-        (f'--{limite}\r\nContent-Disposition: form-data; name="document"; '
-         f'filename="{filename}"\r\nContent-Type: text/markdown; charset=utf-8'
-         f'\r\n\r\n').encode("utf-8"),
-        conteudo,
-        f'\r\n--{limite}--\r\n'.encode("utf-8"),
-    ])
-    resposta = chamar("sendDocument", b"".join(partes),
-                     {"Content-Type": f"multipart/form-data; boundary={limite}"})
-    print(f"documento Markdown {indice}/{total} aceito: {len(conteudo)} bytes")
-    return resposta
-
-
-
-
-
-
-def registrar_midia(dados, categoria, nome, caminho=None, status="downloaded", erro=None):
-    item = {"category": categoria, "name": nome, "status": status}
-    if erro:
-        item["error"] = erro
-    if caminho and os.path.isfile(caminho):
-        resumo = hashlib.sha256()
-        tamanho = 0
-        with open(caminho, "rb") as arquivo:
-            while True:
-                bloco = arquivo.read(1024 * 1024)
-                if not bloco:
-                    break
-                tamanho += len(bloco)
-                resumo.update(bloco)
-        item["path"] = caminho
-        item["bytes"] = tamanho
-        item["sha256"] = resumo.hexdigest()
-    dados.setdefault("midias", []).append(item)
-    return item
-
-
-def registrar_paginacao_incompleta(dados, metodo, esperado, recebido):
-    if isinstance(esperado, int) and recebido < esperado:
-        entrada = {"method": metodo, "expected": esperado, "received": recebido}
-        dados.setdefault("coletas_incompletas", []).append(entrada)
-        dados.setdefault("notas", []).append(
-            f"{metodo}: paginação incompleta ({recebido}/{esperado})."
-        )
-
-
-async def bot_api_leitura(dados, metodo, parametros):
-    resposta = await asyncio.to_thread(
-        chamar, metodo, json.dumps(parametros, ensure_ascii=False).encode("utf-8"),
-        {"Content-Type": "application/json"}
-    )
-    dados.setdefault("respostas_bot_api", {}).setdefault(metodo, []).append(resposta)
-    if not resposta.get("ok"):
-        dados.setdefault("falhas_bot_api", []).append({
-            "method": metodo,
-            "error_code": resposta.get("error_code"),
-            "description": corte(resposta.get("description", "Resposta sem sucesso"), 300),
-        })
-    return resposta
-
-
-async def baixar_arquivo_bot_api(dados, file_id, categoria, file_unique_id=None):
-    if not dados.get("midias_dir") or not file_id:
-        return None
-    hash_nome = hashlib.sha256(str(file_unique_id or file_id).encode("utf-8")).hexdigest()[:20]
-    processados = dados.setdefault("_arquivos_bot_api_processados", set())
-    processados.add(hash_nome)
-    try:
-        retorno = await bot_api_leitura(dados, "getFile", {"file_id": file_id})
-        if not retorno.get("ok"):
-            return registrar_midia(
-                dados, categoria, hash_nome, status="unavailable",
-                erro=f"getFile: {retorno.get('error_code')} {corte(retorno.get('description', ''), 160)}"
-            )
-        arquivo = retorno.get("result") or {}
-        caminho_remoto = arquivo.get("file_path")
-        if not caminho_remoto:
-            return registrar_midia(dados, categoria, hash_nome, status="unavailable",
-                                   erro="getFile não retornou file_path")
-        url = "https://api.telegram.org/file/bot" + os.environ["BOT_TOKEN"] + "/" + caminho_remoto
-        try:
-            with urllib.request.urlopen(urllib.request.Request(url)) as resposta:
-                conteudo = resposta.read()
-        except (errors.RPCError, OSError, BotAPIRequestError) as erro:
-            print(json.dumps(diagnostico_excecao(erro), ensure_ascii=False))
-            return registrar_midia(dados, categoria, hash_nome, status="failed",
-                                   erro=f"download: {type(erro).__name__}")
-        extensao = os.path.splitext(caminho_remoto)[1][:12] or ".bin"
-        nome = hash_nome + extensao
-        caminho_local = os.path.join(dados["midias_dir"], nome)
-        with open(caminho_local, "wb") as saida:
-            saida.write(conteudo)
-        item = registrar_midia(dados, categoria, nome, caminho_local)
-        item["source"] = "Bot API"
-        return item
-    except (errors.RPCError, OSError, BotAPIRequestError) as erro:
-        print(json.dumps(diagnostico_excecao(erro), ensure_ascii=False))
-        return registrar_midia(dados, categoria, hash_nome, status="failed",
-                               erro=type(erro).__name__)
-
-
-async def baixar_arquivos_bot_api(dados, objeto, categoria):
-    anexos = []
-
-    def visitar(valor, caminho=()):
-        if isinstance(valor, dict):
-            if isinstance(valor.get("file_id"), str):
-                anexos.append((valor, caminho))
-            for chave, item in valor.items():
-                if chave in ("file_id", "file_unique_id"):
-                    continue
-                if isinstance(item, list) and item and all(
-                    isinstance(tamanho, dict) and isinstance(tamanho.get("file_id"), str)
-                    and isinstance(tamanho.get("width"), int)
-                    and isinstance(tamanho.get("height"), int)
-                    for tamanho in item
-                ):
-                    maior = max(item, key=lambda tamanho: (
-                        tamanho["width"] * tamanho["height"],
-                        tamanho.get("file_size", 0)
-                    ))
-                    visitar(maior, caminho + (str(chave),))
-                else:
-                    visitar(item, caminho + (str(chave),))
-        elif isinstance(valor, list):
-            for indice, item in enumerate(valor):
-                visitar(item, caminho + (str(indice),))
-
-    visitar(objeto)
-    for item, caminho in anexos:
-        rotulo = re.sub(r"[^A-Za-z0-9_-]+", "_", "_".join(caminho))[:80] or "arquivo"
-        await baixar_arquivo_bot_api(
-            dados, item["file_id"], categoria + "_" + rotulo,
-            item.get("file_unique_id")
-        )
-
-
-def ids_participantes_conhecidos(dados):
-    ids = set()
-    ids_bot = set()
-    id_bot = (dados.get("estado_bot_no_chat") or {}).get("bot_id")
-    if isinstance(id_bot, int):
-        ids_bot.add(id_bot)
-    fontes = [dados.get("participantes_mtproto", [])]
-    fontes.extend((dados.get("participantes_filtrados_mtproto", {}) or {}).values())
-    for paginas in fontes:
-        for pagina in paginas or []:
-            for usuario in getattr(pagina, "users", []) or []:
-                if getattr(usuario, "bot", False):
-                    ids_bot.add(getattr(usuario, "id", None))
-            for participante in getattr(pagina, "participants", []) or []:
-                id_usuario = getattr(participante, "user_id", None)
-                if isinstance(id_usuario, int):
-                    ids.add(id_usuario)
-    resposta_completa = dados.get("resposta_completa")
-    for usuario in getattr(resposta_completa, "users", []) or []:
-        id_usuario = getattr(usuario, "id", None)
-        if getattr(usuario, "bot", False) and isinstance(id_usuario, int):
-            ids_bot.add(id_usuario)
-    participantes_chat = getattr(dados.get("completo"), "participants", None)
-    for participante in getattr(participantes_chat, "participants", []) or []:
-        id_usuario = getattr(participante, "user_id", None)
-        if isinstance(id_usuario, int):
-            ids.add(id_usuario)
-    for resposta in (dados.get("respostas_bot_api", {}).get("getChatAdministrators", []) or []):
-        if not resposta.get("ok"):
-            continue
-        for administrador in resposta.get("result") or []:
-            usuario = (administrador or {}).get("user") or {}
-            id_usuario = usuario.get("id")
-            if usuario.get("is_bot"):
-                ids_bot.add(id_usuario)
-            elif isinstance(id_usuario, int):
-                ids.add(id_usuario)
-    return sorted(id_usuario for id_usuario in ids if id_usuario not in ids_bot)
-
-
-def chave_participante_mtproto(participante):
-    id_usuario = getattr(participante, "user_id", None)
-    if isinstance(id_usuario, int):
-        return ("user", id_usuario)
-    peer = getattr(participante, "peer", None)
-    if peer is not None:
-        return ("peer", utils.get_peer_id(peer))
-    raise TypeError("Construtor de participante sem user_id ou peer reconhecido.")
-
-
-def ids_participantes_com_boosts_bot_api(dados):
-    ids = set()
-    respostas = dados.get("respostas_bot_api", {}).get("getUserChatBoosts", [])
-    for entrada in dados.get("boosts_por_participante_bot_api", []) or []:
-        id_usuario = entrada.get("user_id")
-        indice = entrada.get("response_index")
-        if not entrada.get("ok") or not isinstance(id_usuario, int):
-            continue
-        if not isinstance(indice, int) or indice < 0 or indice >= len(respostas):
-            continue
-        resposta = respostas[indice]
-        if not resposta.get("ok"):
-            continue
-        resultado = resposta.get("result") or {}
-        if isinstance(resultado, dict) and resultado.get("boosts"):
-            ids.add(id_usuario)
-    return sorted(ids)
-
-
-def registrar_coleta_participantes_incompleta(dados, metodo, esperado, recebido):
-    dados.setdefault("coletas_incompletas", []).append({
-        "method": metodo, "expected": esperado, "received": recebido,
-    })
-    dados.setdefault("notas", []).append(
-        f"{metodo}: consulta interrompida após {recebido} respostas bem-sucedidas de {esperado} participantes."
-    )
-
-
-async def coletar_dados_participante_bot_api(dados, entidade, chat_id):
-    entidade_bot_api_chat = isinstance(entidade, BotAPIEntity) and entidade.type in (
-        "group", "supergroup", "channel"
-    )
-    if not isinstance(entidade, (Channel, Chat)) and not entidade_bot_api_chat:
-        return
-    ids_usuarios = ids_participantes_conhecidos(dados)
-    if not ids_usuarios:
-        return
-    consulta_boosts = isinstance(entidade, Channel) or (
-        isinstance(entidade, BotAPIEntity) and entidade.type in ("supergroup", "channel")
-    )
-    estados = dados.setdefault("membros_bot_api_por_participante", [])
-    boosts = dados.setdefault("boosts_por_participante_bot_api", []) if consulta_boosts else []
-    membros_ok = 0
-    boosts_ok = 0
-    for indice, id_usuario in enumerate(ids_usuarios):
-        respostas_membros = dados.get("respostas_bot_api", {}).get("getChatMember", [])
-        indice_membro = len(respostas_membros)
-        membro = await bot_api_leitura(
-            dados, "getChatMember",
-            {"chat_id": chat_id, "user_id": id_usuario}
-        )
-        estados.append({
-            "user_id": id_usuario,
-            "response_index": indice_membro,
-            "ok": bool(membro.get("ok")),
-        })
-        if membro.get("ok"):
-            membros_ok += 1
-        else:
-            descricao = str(membro.get("description", "")).upper()
-            estado = membro.get("error_code")
-            if estado == 429 or (isinstance(estado, int) and estado >= 500) or "CHAT_ADMIN_REQUIRED" in descricao:
-                registrar_coleta_participantes_incompleta(
-                    dados, "getChatMember", len(ids_usuarios), membros_ok
-                )
-                if consulta_boosts:
-                    registrar_coleta_participantes_incompleta(
-                        dados, "getUserChatBoosts", len(ids_usuarios), boosts_ok
-                    )
-                break
-
-        if not consulta_boosts:
-            continue
-
-        respostas_boosts = dados.get("respostas_bot_api", {}).get("getUserChatBoosts", [])
-        indice_boost = len(respostas_boosts)
-        resposta_boost = await bot_api_leitura(
-            dados, "getUserChatBoosts",
-            {"chat_id": chat_id, "user_id": id_usuario}
-        )
-        boosts.append({
-            "user_id": id_usuario,
-            "response_index": indice_boost,
-            "ok": bool(resposta_boost.get("ok")),
-        })
-        if resposta_boost.get("ok"):
-            boosts_ok += 1
-            continue
-        descricao = str(resposta_boost.get("description", "")).upper()
-        estado = resposta_boost.get("error_code")
-        if estado == 429 or (isinstance(estado, int) and estado >= 500) or "CHAT_ADMIN_REQUIRED" in descricao:
-            registrar_coleta_participantes_incompleta(
-                dados, "getUserChatBoosts", len(ids_usuarios), boosts_ok
-            )
-            break
-
-
-async def coletar_estado_bot_no_chat(dados, chat_id):
-    me = await bot_api_leitura(dados, "getMe", {})
-    if not me.get("ok"):
-        return
-    bot_id = (me.get("result") or {}).get("id")
-    if not isinstance(bot_id, int):
-        dados.setdefault("notas", []).append(
-            "getMe não retornou um ID numérico; status do bot no chat não foi consultado."
-        )
-        return
-    respostas = dados.get("respostas_bot_api", {}).get("getChatMember", [])
-    indice = len(respostas)
-    membro = await bot_api_leitura(
-        dados, "getChatMember", {"chat_id": chat_id, "user_id": bot_id}
-    )
-    dados["estado_bot_no_chat"] = {
-        "bot_id": bot_id,
-        "response_index": indice,
-        "ok": bool(membro.get("ok")),
-    }
-
-
-async def coletar_stickers_bot_api(dados, objeto):
-    nomes_conjuntos = set()
-    ids_emojis = set()
-
-    def visitar(valor):
-        if isinstance(valor, dict):
-            for chave, item in valor.items():
-                if chave in ("sticker_set_name", "custom_emoji_sticker_set_name") and isinstance(item, str) and item:
-                    nomes_conjuntos.add(item)
-                elif chave in ("custom_emoji_id", "emoji_status_custom_emoji_id") and isinstance(item, str) and item:
-                    ids_emojis.add(item)
-                visitar(item)
-        elif isinstance(valor, list):
-            for item in valor:
-                visitar(item)
-
-    visitar(objeto)
-    for nome in sorted(nomes_conjuntos):
-        resposta = await bot_api_leitura(dados, "getStickerSet", {"name": nome})
-        if resposta.get("ok"):
-            await baixar_arquivos_bot_api(dados, resposta.get("result"), "conjunto_stickers_bot_api")
-    emojis = sorted(ids_emojis)
-    for inicio in range(0, len(emojis), 200):
-        resposta = await bot_api_leitura(
-            dados, "getCustomEmojiStickers",
-            {"custom_emoji_ids": emojis[inicio:inicio + 200]}
-        )
-        if resposta.get("ok"):
-            await baixar_arquivos_bot_api(dados, resposta.get("result"), "emoji_personalizado_bot_api")
-
-
-async def coletar_catalogo_presentes_bot_api(dados):
-    metodo = "getAvailableGifts"
-    indice_resposta = len(dados.get("respostas_bot_api", {}).get(metodo, []))
-    resposta = await bot_api_leitura(dados, metodo, {})
-    resultado = resposta.get("result") or {}
-    presentes = resultado.get("gifts") or []
-    dados["catalogo_presentes_bot_api"] = {
-        "method": metodo,
-        "response_index": indice_resposta,
-        "ok": bool(resposta.get("ok")),
-        "gift_count": len(presentes),
-    }
-    if resposta.get("ok"):
-        await baixar_arquivos_bot_api(dados, resultado, "catalogo_presentes_bot_api")
-
-
-async def coletar_presentes_bot_api(dados, entidade, chat_id):
-    entidade_usuario = isinstance(entidade, User) or (
-        isinstance(entidade, BotAPIEntity) and entidade.type == "private"
-    )
-    metodo = "getUserGifts" if entidade_usuario else "getChatGifts"
-    parametros_base = (
-        {"user_id": entidade.id}
-        if entidade_usuario
-        else {"chat_id": chat_id}
-    )
-    offset = ""
-    offsets_vistos = set()
-    total = None
-    recebidos = 0
-    paginas = dados.setdefault("presentes_bot_api", [])
-    while True:
-        parametros = dict(parametros_base, offset=offset, limit=100)
-        indice_resposta = len(dados.get("respostas_bot_api", {}).get(metodo, []))
-        resposta = await bot_api_leitura(dados, metodo, parametros)
-        if not resposta.get("ok"):
-            if isinstance(total, int):
-                registrar_paginacao_incompleta(dados, metodo, total, recebidos)
-            break
-        resultado = resposta.get("result") or {}
-        contagem = resultado.get("total_count")
-        if isinstance(contagem, int):
-            total = contagem if total is None else max(total, contagem)
-        presentes = resultado.get("gifts") or []
-        paginas.append({
-            "method": metodo,
-            "response_index": indice_resposta,
-            "offset": offset,
-            "next_offset": resultado.get("next_offset", ""),
-            "total_count": contagem,
-            "received": len(presentes),
-        })
-        recebidos += len(presentes)
-        await baixar_arquivos_bot_api(dados, resultado, "presente_" + metodo)
-        proximo = resultado.get("next_offset") or ""
-        if not proximo:
-            break
-        if proximo == offset or proximo in offsets_vistos:
-            dados.setdefault("coletas_incompletas", []).append({
-                "method": metodo,
-                "expected": total,
-                "received": recebidos,
-                "reason": "next_offset repetido; paginação interrompida para evitar ciclo",
-            })
-            dados.setdefault("notas", []).append(
-                f"{metodo}: paginação interrompida porque next_offset repetiu."
-            )
-            break
-        offsets_vistos.add(offset)
-        offset = proximo
-    registrar_paginacao_incompleta(dados, metodo, total, recebidos)
-
-
-def objetos_mtproto(valor, visitados=None):
-    if visitados is None:
-        visitados = set()
-    if valor is None or isinstance(valor, (str, bytes, int, float, bool)):
-        return
-    identidade = id(valor)
-    if identidade in visitados:
-        return
-    visitados.add(identidade)
-    yield valor
-    if isinstance(valor, dict):
-        filhos = valor.values()
-    elif isinstance(valor, (list, tuple, set)):
-        filhos = valor
-    else:
-        atributos = dict(vars(valor)) if hasattr(valor, "__dict__") else {}
-        for classe in type(valor).__mro__:
-            slots = getattr(classe, "__slots__", ())
-            if isinstance(slots, str):
-                slots = (slots,)
-            for nome in slots:
-                if not nome.startswith("_") and hasattr(valor, nome):
-                    atributos[nome] = getattr(valor, nome)
-        filhos = (item for nome, item in atributos.items() if not nome.startswith("_"))
-    for filho in filhos:
-        yield from objetos_mtproto(filho, visitados)
-
-
-def documentos_mtproto(valor):
-    from telethon.tl.types import Document
-    for objeto in objetos_mtproto(valor):
-        if isinstance(objeto, Document):
-            yield objeto
-
-
-async def baixar_documentos_presente_mtproto(cliente, presente, dados, categoria, nome):
-    if not dados.get("midias_dir"):
-        return
-    processados = dados.setdefault("_documentos_mtproto_processados", set())
-    for indice, documento in enumerate(documentos_mtproto(presente), 1):
-        if documento.id in processados:
-            continue
-        processados.add(documento.id)
-        await baixar_midia(
-            cliente, documento, dados, categoria,
-            f"{nome}_documento_{indice:02d}"
-        )
-
-
-async def coletar_stickers_mtproto(cliente, dados):
-    from telethon.tl.functions.messages import GetCustomEmojiDocumentsRequest, GetStickerSetRequest
-    from telethon.tl.types import (
-        DocumentAttributeCustomEmoji, DocumentAttributeSticker, EmojiStatus,
-        EmojiStatusCollectible, InputStickerSetEmpty, InputStickerSetID,
-        ForumTopic, MessageActionTopicCreate, MessageActionTopicEdit,
-        MessageEntityCustomEmoji, PeerColor, PeerColorCollectible, StickerSet,
-    )
-    fontes = list(objetos_mtproto(dados))
-    ids_emoji = set()
-    for objeto in fontes:
-        if isinstance(objeto, (MessageEntityCustomEmoji, EmojiStatus, EmojiStatusCollectible)):
-            ids_emoji.add(objeto.document_id)
-        if isinstance(objeto, EmojiStatusCollectible):
-            ids_emoji.add(objeto.pattern_document_id)
-        if isinstance(objeto, (PeerColor, PeerColorCollectible)) and objeto.background_emoji_id:
-            ids_emoji.add(objeto.background_emoji_id)
-        if isinstance(objeto, PeerColorCollectible):
-            ids_emoji.add(objeto.gift_emoji_id)
-        if isinstance(objeto, (ForumTopic, MessageActionTopicCreate, MessageActionTopicEdit)) and objeto.icon_emoji_id:
-            ids_emoji.add(objeto.icon_emoji_id)
-    ids_emoji = sorted(ids_emoji)
-    respostas_emoji = dados.setdefault("emojis_personalizados_mtproto", [])
-    for inicio in range(0, len(ids_emoji), 100):
-        lote = ids_emoji[inicio:inicio + 100]
-        try:
-            resposta = await com_espera(lambda: cliente(GetCustomEmojiDocumentsRequest(document_id=lote)))
-            respostas_emoji.append({"request_ids": lote, "response": resposta})
-        except (errors.RPCError, OSError, BotAPIRequestError) as erro:
-            print(json.dumps(diagnostico_excecao(erro), ensure_ascii=False))
-            dados.setdefault("falhas_coleta", []).append({
-                "method": "messages.getCustomEmojiDocuments", "error": type(erro).__name__, "diagnostic": diagnostico_excecao(erro),
-                "document_ids": lote,
-            })
-    fontes.extend(objetos_mtproto(respostas_emoji))
-    conjuntos = {}
-    for objeto in fontes:
-        referencia = None
-        if isinstance(objeto, StickerSet):
-            referencia = InputStickerSetID(objeto.id, objeto.access_hash)
-        elif isinstance(objeto, (DocumentAttributeSticker, DocumentAttributeCustomEmoji)):
-            referencia = objeto.stickerset
-        if referencia is not None and not isinstance(referencia, InputStickerSetEmpty):
-            conjuntos.setdefault(bytes(referencia), referencia)
-    respostas_conjuntos = dados.setdefault("conjuntos_stickers_mtproto", [])
-    for referencia in conjuntos.values():
-        try:
-            resposta = await com_espera(lambda: cliente(GetStickerSetRequest(stickerset=referencia, hash=0)))
-            respostas_conjuntos.append({"request": referencia, "response": resposta})
-        except (errors.RPCError, OSError, BotAPIRequestError) as erro:
-            print(json.dumps(diagnostico_excecao(erro), ensure_ascii=False))
-            dados.setdefault("falhas_coleta", []).append({
-                "method": "messages.getStickerSet", "error": type(erro).__name__, "diagnostic": diagnostico_excecao(erro),
-                "request": referencia,
-            })
-    await baixar_documentos_presente_mtproto(
-        cliente, respostas_emoji, dados, "emoji_personalizado_mtproto", "emoji_personalizado_mtproto"
-    )
-    await baixar_documentos_presente_mtproto(
-        cliente, respostas_conjuntos, dados, "conjunto_stickers_mtproto", "conjunto_stickers_mtproto"
-    )
-    documentos_referenciados = list(documentos_mtproto(dados))
-    await baixar_documentos_presente_mtproto(
-        cliente, documentos_referenciados, dados, "documento_referenciado_mtproto", "documento_referenciado_mtproto"
-    )
-
-
-async def coletar_topicos_conhecidos_mtproto(cliente, dados):
-    from telethon.tl.functions.messages import GetForumTopicsByIDRequest
-    from telethon.tl.types import Message, MessageService, MessageActionTopicCreate
-    topicos = {}
-    for objeto in objetos_mtproto(dados):
-        peer_id = None
-        id_topico = None
-        if isinstance(objeto, (Message, MessageService)):
-            resposta = getattr(objeto, "reply_to", None)
-            if getattr(resposta, "forum_topic", False):
-                id_topico = getattr(resposta, "reply_to_top_id", None) or getattr(resposta, "reply_to_msg_id", None)
-            if isinstance(getattr(objeto, "action", None), MessageActionTopicCreate):
-                id_topico = objeto.id
-            peer = getattr(objeto, "peer_id", None)
-            if not isinstance(getattr(objeto, "action", None), MessageActionTopicCreate):
-                peer = getattr(resposta, "reply_to_peer_id", None) or peer
-            if peer is not None:
-                peer_id = utils.get_peer_id(peer)
-        elif isinstance(objeto, dict) and objeto.get("is_topic_message") is True:
-            id_topico = objeto.get("message_thread_id")
-            peer_id = (objeto.get("chat") or {}).get("id")
-        if isinstance(peer_id, int) and isinstance(id_topico, int) and id_topico > 0:
-            topicos.setdefault(peer_id, set()).add(id_topico)
-    respostas = dados.setdefault("topicos_forum_mtproto", [])
-    for peer_id, ids in topicos.items():
-        id_real, tipo = utils.resolve_id(peer_id)
-        if tipo is PeerChannel:
-            peer = InputPeerChannel(id_real, 0)
-        elif tipo is PeerChat:
-            peer = InputPeerChat(id_real)
-        else:
-            peer = InputPeerUser(id_real, 0)
-        ids = sorted(ids)
-        for inicio in range(0, len(ids), 100):
-            lote = ids[inicio:inicio + 100]
-            try:
-                resultado = await com_espera(lambda: cliente(GetForumTopicsByIDRequest(peer=peer, topics=lote)))
-                respostas.append({"peer": peer, "topic_ids": lote, "response": resultado})
-            except (errors.RPCError, OSError, BotAPIRequestError) as erro:
-                print(json.dumps(diagnostico_excecao(erro), ensure_ascii=False))
-                dados.setdefault("falhas_coleta", []).append({
-                    "method": "messages.getForumTopicsByID", "error": type(erro).__name__, "diagnostic": diagnostico_excecao(erro),
-                    "peer": peer, "topic_ids": lote,
-                })
-
-
-async def coletar_catalogo_presentes_mtproto(cliente, dados):
-    metodo = "payments.getStarGifts"
-    try:
-        from telethon.tl.functions.payments import GetStarGiftsRequest
-        resposta = await com_espera(lambda: cliente(GetStarGiftsRequest(hash=0)))
-        dados.setdefault("catalogo_presentes_star_gifts_mtproto", []).append(resposta)
-        presentes = getattr(resposta, "gifts", []) or []
-        if dados.get("midias_dir"):
-            for indice, presente in enumerate(presentes, 1):
-                await baixar_documentos_presente_mtproto(
-                    cliente, presente, dados, "catalogo_presente_mtproto",
-                    f"catalogo_presente_mtproto_{indice:04d}"
-                )
-    except (errors.RPCError, OSError, BotAPIRequestError) as erro:
-        print(json.dumps(diagnostico_excecao(erro), ensure_ascii=False))
-        dados.setdefault("falhas_coleta", []).append({
-            "method": metodo,
-            "error": type(erro).__name__, "diagnostic": diagnostico_excecao(erro),
-        })
-        dados.setdefault("notas", []).append(
-            f"{metodo} indisponível nesta sessão: {type(erro).__name__}."
-        )
-
-
-async def coletar_boosts_mtproto(cliente, dados, entidade):
-    canal = input_peer_canal_bot(entidade)
-    if canal is None:
-        return
-    metodo = "premium.getUserBoosts"
-    try:
-        from telethon.tl.functions.premium import GetUserBoostsRequest
-    except ImportError as erro:
-        dados.setdefault("falhas_coleta", []).append({
-            "method": metodo,
-            "error": type(erro).__name__, "diagnostic": diagnostico_excecao(erro),
-        })
-        return
-    resultados = dados.setdefault("boosts_por_usuario_mtproto", [])
-    ids_com_boosts = ids_participantes_com_boosts_bot_api(dados)
-    if not ids_com_boosts:
-        dados.setdefault("notas", []).append(
-            f"{metodo}: sem chamada individual; a Bot API não retornou boosters."
-        )
-        return
-    for id_usuario in ids_com_boosts:
-        try:
-            try:
-                peer_usuario = utils.get_input_user(
-                    cliente.session.get_input_entity(PeerUser(id_usuario))
-                )
-            except ValueError:
-                peer_usuario = InputUser(id_usuario, 0)
-            resposta = await com_espera(lambda: cliente(
-                GetUserBoostsRequest(peer=canal, user_id=peer_usuario)
-            ))
-            resultados.append({
-                "user_id": id_usuario,
-                "response": resposta,
-            })
-        except (errors.RPCError, OSError, BotAPIRequestError) as erro:
-            print(json.dumps(diagnostico_excecao(erro), ensure_ascii=False))
-            dados.setdefault("falhas_coleta", []).append({
-                "method": metodo,
-                "user_id": id_usuario,
-                "error": type(erro).__name__, "diagnostic": diagnostico_excecao(erro),
-            })
 
 def interrupted(collection, error):
     if isinstance(error, (BotAPIAuthenticationError, errors.UnauthorizedError)):
@@ -975,28 +143,6 @@ def interrupted(collection, error):
     if isinstance(error, errors.FloodWaitError):
         collection.reason += f': retry_after={error.seconds}'
 
-async def coletar_participacao_bot_mtproto(cliente, dados, entidade):
-    canal = input_canal_bot(entidade)
-    if canal is None:
-        return
-    metodo = "channels.getParticipant"
-    try:
-        from telethon.tl.functions.channels import GetParticipantRequest
-        from telethon.tl.types import InputPeerSelf
-        resposta = await com_espera(lambda: cliente(
-            GetParticipantRequest(channel=canal, participant=InputPeerSelf())
-        ))
-        dados["participacao_bot_mtproto"] = resposta
-    except (errors.RPCError, OSError, BotAPIRequestError) as erro:
-        print(json.dumps(diagnostico_excecao(erro), ensure_ascii=False))
-        dados.setdefault("falhas_coleta", []).append({
-            "method": metodo,
-            "participant": "self",
-            "error": type(erro).__name__, "diagnostic": diagnostico_excecao(erro),
-        })
-        dados.setdefault("notas", []).append(
-            f"{metodo} para o próprio bot indisponível: {type(erro).__name__}."
-        )
 
 async def paginated(collection, fetch, items, identity, *, max_pages=1000, expected=None):
     """Offset pagination counts server rows; unique records detect repeated pages."""
@@ -1036,22 +182,6 @@ async def paginated(collection, fetch, items, identity, *, max_pages=1000, expec
     except (errors.RPCError, OSError, asyncio.TimeoutError, ValueError) as error:
         interrupted(collection, error)
     return rows
-            offsets_vistos.add(offset)
-            offset = proximo
-    except (errors.RPCError, OSError, BotAPIRequestError) as erro:
-        print(json.dumps(diagnostico_excecao(erro), ensure_ascii=False))
-        dados.setdefault("falhas_coleta", []).append({
-            "method": metodo,
-            "error": type(erro).__name__, "diagnostic": diagnostico_excecao(erro),
-        })
-        dados.setdefault("notas", []).append(
-            f"{metodo}: coleta interrompida por {type(erro).__name__}."
-        )
-    registrar_paginacao_incompleta(
-        dados, metodo, total if "total" in locals() else None,
-        recebidos if "recebidos" in locals() else 0
-    )
-
 
 
 async def collect_messages(client, peer, data, ids=None, max_pages=1000):
@@ -1211,525 +341,6 @@ def identity(participant):
                 if name == 'recent':
                     data.participants = rows
         elif isinstance(entity, Chat):
-            if not total_inexato and total is not None and recebidos >= total:
-                if recebidos == total:
-                    break
-                total_inexato = True
-                dados.setdefault("notas", []).append(
-                    f"{metodo}: count ({total}) menor que mensagens distintas ({recebidos}); a paginação segue pelo cursor."
-                )
-            cursor = proximo_cursor
-    except (errors.RPCError, OSError, BotAPIRequestError) as erro:
-        print(json.dumps(diagnostico_excecao(erro), ensure_ascii=False))
-        dados.setdefault("falhas_coleta", []).append({
-            "method": metodo,
-            "error": type(erro).__name__, "diagnostic": diagnostico_excecao(erro),
-        })
-        dados.setdefault("notas", []).append(
-            f"{metodo}: coleta interrompida por {type(erro).__name__}."
-        )
-    registrar_paginacao_incompleta(
-        dados, metodo, None if total_inexato else total, recebidos
-    )
-
-
-async def coletar_bot_api(dados, entidade, info):
-    chat_id = info.get("id")
-    if not chat_id:
-        return
-    respostas_chat = dados.get("respostas_bot_api", {}).get("getChat", [])
-    chat = None
-    if str(dados.get("getChat_alvo_id")) == str(info.get("id")) and dados.get("getChat_alvo_attempted"):
-        chat = respostas_chat[-1] if respostas_chat else None
-    else:
-        chat = next((resposta for resposta in reversed(respostas_chat)
-            if resposta.get("ok") and str((resposta.get("result") or {}).get("id")) == str(info.get("id"))), None)
-    if chat is None:
-        chat = await bot_api_leitura(dados, "getChat", {"chat_id": chat_id})
-    if chat.get("ok"):
-        dados["chat_bot_api"] = chat.get("result")
-        resultado_chat = chat.get("result") or {}
-        foto = resultado_chat.get("photo") or {}
-        if foto.get("big_file_id"):
-            await baixar_arquivo_bot_api(
-                dados, foto["big_file_id"], "foto_perfil_bot_api",
-                foto.get("big_file_unique_id")
-            )
-        audio = resultado_chat.get("first_profile_audio") or {}
-        if audio.get("file_id"):
-            await baixar_arquivo_bot_api(
-                dados, audio["file_id"], "audio_perfil_bot_api",
-                audio.get("file_unique_id")
-            )
-        await baixar_arquivos_bot_api(dados, resultado_chat, "chat_bot_api")
-        if resultado_chat.get("is_forum"):
-            icones_forum = await bot_api_leitura(dados, "getForumTopicIconStickers", {})
-            if icones_forum.get("ok"):
-                await baixar_arquivos_bot_api(
-                    dados, icones_forum.get("result"), "icones_topico_forum_bot_api"
-                )
-        ids_relacionados = []
-        for chave in ("personal_chat", "parent_chat"):
-            relacionado = resultado_chat.get(chave)
-            id_relacionado = relacionado.get("id") if isinstance(relacionado, dict) else None
-            if isinstance(id_relacionado, int):
-                ids_relacionados.append(id_relacionado)
-        id_vinculado = resultado_chat.get("linked_chat_id")
-        if isinstance(id_vinculado, int):
-            ids_relacionados.append(id_vinculado)
-        id_atual = info.get("id")
-        ids_relacionados = list(dict.fromkeys(
-            identificador for identificador in ids_relacionados
-            if identificador != id_atual
-        ))
-        for id_relacionado in ids_relacionados:
-            resposta_relacionada = await bot_api_leitura(
-                dados, "getChat", {"chat_id": id_relacionado}
-            )
-            if not resposta_relacionada.get("ok"):
-                continue
-            chat_relacionado = resposta_relacionada.get("result") or {}
-            dados.setdefault("chats_relacionados_bot_api", []).append(chat_relacionado)
-            foto_relacionada = chat_relacionado.get("photo") or {}
-            if foto_relacionada.get("big_file_id"):
-                await baixar_arquivo_bot_api(
-                    dados, foto_relacionada["big_file_id"], "foto_chat_relacionado_bot_api",
-                    foto_relacionada.get("big_file_unique_id")
-                )
-            audio_relacionado = chat_relacionado.get("first_profile_audio") or {}
-            if audio_relacionado.get("file_id"):
-                await baixar_arquivo_bot_api(
-                    dados, audio_relacionado["file_id"], "audio_chat_relacionado_bot_api",
-                    audio_relacionado.get("file_unique_id")
-                )
-            await baixar_arquivos_bot_api(dados, chat_relacionado, "chat_relacionado_bot_api")
-
-    entidade_usuario = isinstance(entidade, User) or (
-        isinstance(entidade, BotAPIEntity) and entidade.type == "private"
-    )
-    if entidade_usuario:
-        id_usuario = entidade.id
-        for metodo, lista_chave, categoria in (
-            ("getUserProfilePhotos", "photos", "foto_perfil_bot_api"),
-            ("getUserProfileAudios", "audios", "audio_perfil_bot_api"),
-        ):
-            offset = 0
-            total = None
-            while True:
-                resposta = await bot_api_leitura(
-                    dados, metodo, {"user_id": id_usuario, "offset": offset, "limit": 100}
-                )
-                if not resposta.get("ok"):
-                    break
-                resultado = resposta.get("result") or {}
-                contagem = resultado.get("total_count")
-                if isinstance(contagem, int):
-                    total = contagem if total is None else max(total, contagem)
-                itens = resultado.get(lista_chave) or []
-                if not itens:
-                    break
-                for item in itens:
-                    if metodo == "getUserProfilePhotos":
-                        if not item:
-                            continue
-                        item = max(item, key=lambda foto: (
-                            foto.get("width", 0) * foto.get("height", 0),
-                            foto.get("file_size", 0)
-                        ))
-                    await baixar_arquivo_bot_api(
-                        dados, item.get("file_id"), categoria, item.get("file_unique_id")
-                    )
-                offset += len(itens)
-                if total is not None and offset >= total:
-                    break
-            registrar_paginacao_incompleta(dados, metodo, total, offset)
-        mensagens = await bot_api_leitura(
-            dados, "getUserPersonalChatMessages", {"user_id": id_usuario, "limit": 20}
-        )
-        if mensagens.get("ok"):
-            for mensagem in mensagens.get("result") or []:
-                for categoria, valor in (mensagem or {}).items():
-                    if categoria == "photo" and isinstance(valor, list):
-                        if valor:
-                            foto = max(valor, key=lambda item: (
-                                item.get("width", 0) * item.get("height", 0),
-                                item.get("file_size", 0)
-                            ))
-                            await baixar_arquivo_bot_api(
-                                dados, foto.get("file_id"), "mensagem_foto_bot_api",
-                                foto.get("file_unique_id")
-                            )
-                    elif categoria in ("audio", "document", "animation", "video", "video_note", "voice", "sticker", "live_photo") and isinstance(valor, dict):
-                        await baixar_arquivo_bot_api(
-                            dados, valor.get("file_id"), "mensagem_" + categoria + "_bot_api",
-                            valor.get("file_unique_id")
-                        )
-                await baixar_arquivos_bot_api(dados, mensagem, "mensagem_pessoal_bot_api")
-    else:
-        await coletar_estado_bot_no_chat(dados, chat_id)
-        await bot_api_leitura(
-            dados, "getChatAdministrators", {"chat_id": chat_id, "return_bots": True}
-        )
-        await bot_api_leitura(dados, "getChatMemberCount", {"chat_id": chat_id})
-        if MODO == "completo":
-            await coletar_dados_participante_bot_api(dados, entidade, chat_id)
-
-    await coletar_stickers_bot_api(dados, dados.get("respostas_bot_api", {}))
-    if MODO == "completo":
-        await coletar_presentes_bot_api(dados, entidade, chat_id)
-
-
-async def baixar_midia(cliente, objeto, dados, categoria, nome):
-    caminho = os.path.join(dados["midias_dir"], nome)
-    try:
-        retorno = await com_espera(lambda: cliente.download_media(objeto, file=caminho))
-        if isinstance(retorno, str) and os.path.isfile(retorno):
-            item = registrar_midia(dados, categoria, os.path.basename(retorno), retorno)
-            from telethon.tl.types import Document
-            if isinstance(objeto, Document):
-                dados.setdefault("_documentos_mtproto_processados", set()).add(objeto.id)
-            return item
-        return registrar_midia(dados, categoria, nome, status="unavailable", erro="Telegram não retornou o arquivo")
-    except (errors.RPCError, OSError, BotAPIRequestError) as erro:
-        print(json.dumps(diagnostico_excecao(erro), ensure_ascii=False))
-        return registrar_midia(dados, categoria, nome, status="failed", erro=type(erro).__name__)
-
-
-def enviar_documento_arquivo(chat, caminho, id_entidade, indice, total):
-    with open(caminho, "rb") as arquivo:
-        conteudo = arquivo.read()
-    limite = uuid.uuid4().hex
-    filename = "infocard_" + str(id_entidade).replace("-", "n") + "_midias"
-    if total > 1:
-        filename += f"_parte_{indice}_de_{total}"
-    filename += ".zip"
-    resumo_hash = hashlib.sha256(conteudo).hexdigest()
-    campos = {"chat_id": str(chat), "caption": "🖼️ Mídia Telegram exportada" +
-              (f" · parte {indice}/{total}" if total > 1 else "") +
-              "\nSHA-256: " + resumo_hash}
-    if ORIGEM_ID:
-        campos["reply_parameters"] = json.dumps({"message_id": ORIGEM_ID})
-    partes = []
-    for chave, valor in campos.items():
-        partes.append((f'--{limite}\r\nContent-Disposition: form-data; name="{chave}"'
-                       f'\r\n\r\n{valor}\r\n').encode("utf-8"))
-    partes.extend([
-        (f'--{limite}\r\nContent-Disposition: form-data; name="document"; '
-         f'filename="{filename}"\r\nContent-Type: application/zip'
-         f'\r\n\r\n').encode("utf-8"),
-        conteudo,
-        f'\r\n--{limite}--\r\n'.encode("utf-8"),
-    ])
-    resposta = chamar("sendDocument", b"".join(partes),
-                     {"Content-Type": f"multipart/form-data; boundary={limite}"})
-    print(f"pacote de mídia {indice}/{total} aceito: {len(conteudo)} bytes")
-    return resposta
-
-def enviar_documento_jsonl(chat, conteudo, id_entidade, indice, total):
-    limite = uuid.uuid4().hex
-    filename = "infocard_" + str(id_entidade).replace("-", "n") + "_telegram"
-    if total > 1:
-        filename += f"_parte_{indice}_de_{total}"
-    filename += ".jsonl"
-    resumo_hash = hashlib.sha256(conteudo).hexdigest()
-    campos = {"chat_id": str(chat), "caption": "🧾 Respostas Telegram coletadas (JSONL)" +
-              (f" · parte {indice}/{total}" if total > 1 else "") +
-              "\nSHA-256: " + resumo_hash}
-    if ORIGEM_ID:
-        campos["reply_parameters"] = json.dumps({"message_id": ORIGEM_ID})
-    partes = []
-    for chave, valor in campos.items():
-        partes.append((f'--{limite}\r\nContent-Disposition: form-data; name="{chave}"'
-                       f'\r\n\r\n{valor}\r\n').encode("utf-8"))
-    partes.extend([
-        (f'--{limite}\r\nContent-Disposition: form-data; name="document"; '
-         f'filename="{filename}"\r\nContent-Type: application/x-ndjson'
-         f'\r\n\r\n').encode("utf-8"),
-        conteudo,
-        f'\r\n--{limite}--\r\n'.encode("utf-8"),
-    ])
-    resposta = chamar("sendDocument", b"".join(partes),
-                     {"Content-Type": f"multipart/form-data; boundary={limite}"})
-    print(f"documento JSONL {indice}/{total} aceito: {len(conteudo)} bytes")
-    return resposta
-
-def botao_atualizar(alvo):
-    dados = callback_data("r", alvo)
-    return ('<tg-button type="callback_data" style="primary" data="' +
-            esc(dados) + '">🔄 Atualizar</tg-button>') if dados else ""
-
-
-def status_ficha(etapa, nome=None, id_entidade=None):
-    linhas = ['<tr><th>Etapa</th><td>' + esc(etapa) + '</td></tr>']
-    if nome:
-        linhas.append('<tr><th>Nome</th><td>' + esc(corte(nome, 100)) + '</td></tr>')
-    if id_entidade is not None:
-        linhas.append('<tr><th>ID</th><td><code>' + esc(id_entidade) + '</code></td></tr>')
-    return ('<h2>🔎 Infocard</h2><p><b>⏳ Consulta MTProto em andamento</b></p>'
-            '<table compact bordered><tr><th>Campo</th><th>Valor</th></tr>'
-            + ''.join(linhas) + '</table><footer>Fonte: Telegram Bot API + MTProto</footer>')
-
-
-def atualizar_status(etapa, entidade=None):
-    if not ID_MENSAGEM or not CHAT_DESTINO:
-        return
-    nome = None
-    id_entidade = None
-    if entidade is not None:
-        nome = getattr(entidade, "title", None) or " ".join(
-            parte for parte in [getattr(entidade, "first_name", None), getattr(entidade, "last_name", None)] if parte
-        )
-        id_entidade = id_peer(entidade)
-    if FORMATO_MENSAGEM == "html":
-        resposta = solicitar_bot_api("editMessageText", {
-            "chat_id": CHAT_DESTINO, "message_id": ID_MENSAGEM,
-            "text": "<b>Consulta em andamento</b>\n" + esc(etapa), "parse_mode": "HTML",
-        })
-        if mensagem_inalterada(resposta):
-            print("editMessageText: estado HTML já está atualizado")
-    else:
-        editar_ficha_rica(status_ficha(etapa, nome, id_entidade))
-
-
-CATEGORIAS = (
-    ("👤 Perfil e atividade", (
-        "Bio", "Bio (Bot API)", "Aniversário", "Aniversário (Bot API)", "Idioma", "Premium", "Restrições", "Chats em comum",
-        "Canal pessoal", "Nome nos encaminhamentos", "Mensagens de voz",
-        "Emoji de status", "Fotos de perfil no MTProto",
-    )),
-    ("🎵 Recursos e presença", (
-        "Música destacada no perfil", "Músicas de perfil no MTProto", "Fotos de perfil na Bot API",
-        "Áudios de perfil na Bot API", "Mensagens no chat pessoal via Bot API",
-        "Administradores via Bot API", "Membros via Bot API", "Presentes recebidos",
-        "Nível Telegram Stars", "Placeholder inline", "Usuários ativos do bot",
-        "Mini App principal do bot", "Descrição do bot", "Comandos",
-        "Política de privacidade",
-    )),
-    ("🏢 Informações comerciais", (
-        "Intro comercial", "Endereço comercial", "Fuso dos horários comerciais",
-        "Intervalos de atendimento registrados",
-    )),
-    ("📢 Canal ou grupo", (
-        "Descrição", "Descrição (Bot API)", "Intro comercial (Bot API)",
-        "Local comercial (Bot API)", "Horários comerciais (Bot API)",
-        "Avaliação do chat (Bot API)", "Membros", "Administradores", "Online agora",
-        "Chat vinculado", "Modo lento", "Boosts aplicados",
-        "Nível de boosts do canal", "Presentes recebidos pelo canal",
-        "Limite de reações distintas", "Localização",
-    )),
-)
-
-
-def agrupar_campos(info):
-    restantes = list(info["campos"])
-    grupos = []
-    for nome_grupo, rotulos in CATEGORIAS:
-        encontrados = [campo for campo in restantes if campo[0] in rotulos]
-        if encontrados:
-            grupos.append((nome_grupo, encontrados))
-            restantes = [campo for campo in restantes if campo[0] not in rotulos]
-    if restantes:
-        grupos.append(("➕ Outros dados retornados", restantes))
-    return grupos
-
-
-def dados_basicos(info):
-    linhas = [
-        ("Tipo", info["tipo"]),
-        ("ID", str(info["id"])),
-        ("Nome", info["nome"] or "Não informado"),
-    ]
-    if info["username"]:
-        linhas.append(("Username", "@" + info["username"]))
-    if info["usernames"]:
-        linhas.append(("Outros usernames ativos", ", ".join("@" + u for u in info["usernames"])))
-    if info["marcas"]:
-        linhas.append(("Indicadores públicos", ", ".join(info["marcas"])))
-    linhas.append(("Foto de perfil", "Disponível" if info["foto"] else "Não informada"))
-    return linhas
-
-
-def ficha_falha(alvo, motivo):
-    linhas = '<tr><th>Consulta</th><td>' + esc(f"{EXPECTED_ID} @{alvo}" if EXPECTED_ID else (alvo if re.fullmatch(r"-?\d{1,16}", alvo) else f"@{alvo}")) + '</td></tr>'
-    linhas += '<tr><th>Resultado</th><td>' + esc(corte(motivo, 600)) + '</td></tr>'
-    return ('<h2>📇 Infocard</h2><p><b>Processamento concluído</b></p>'
-            '<table bordered compact><tr><th>Campo</th><th>Valor</th></tr>' + linhas +
-            '</table><p><i>Uma referência não encontrada não prova inexistência da conta.</i></p>'
-            '<tg-button-row>' + botao_atualizar(alvo) + '</tg-button-row>')
-
-
-def entidade_de(resultado):
-    return next(iter([*resultado.users, *resultado.chats]), None)
-
-
-async def completo(cliente, entidade):
-    if isinstance(entidade, User):
-        return await cliente(GetFullUserRequest(input_usuario_bot(entidade)))
-    if isinstance(entidade, Channel):
-        return await cliente(GetFullChannelRequest(input_canal_bot(entidade)))
-    if isinstance(entidade, Chat):
-        return await cliente(GetFullChatRequest(entidade.id))
-    if isinstance(entidade, BotAPIEntity):
-        usuario = input_usuario_bot(entidade)
-        if usuario is not None:
-            return await cliente(GetFullUserRequest(usuario))
-        canal = input_canal_bot(entidade)
-        if canal is not None:
-            return await cliente(GetFullChannelRequest(canal))
-        if entidade.type == "group":
-            id_real, tipo = utils.resolve_id(entidade.id)
-            if tipo is PeerChat:
-                return await cliente(GetFullChatRequest(id_real))
-    return None
-
-
-def objeto_completo(resposta):
-    if resposta is None:
-        return None
-    return getattr(resposta, "full_user", None) or getattr(resposta, "full_chat", None)
-
-
-def valor_mtproto(valor):
-    return valor_exportavel(valor)
-
-
-def registros_telegram(dados, alvo, info):
-    metadados = {
-        "formato": "infocard-telegram-jsonl-v4",
-        "redaction": {"enabled": False, "fields": []},
-        "escopo": "respostas de leitura obtidas pelas APIs do Telegram nesta execução",
-        "apis": ["Bot API", "MTProto"],
-        "telethon": telethon.__version__,
-        "referencia": alvo,
-        "tipo": info.get("tipo"),
-        "capturado_unix": int(time.time()),
-    }
-    objetos = {
-        "metadados": metadados,
-        "respostas_bot_api": dados.get("respostas_bot_api", {}),
-        "coletas_incompletas": dados.get("coletas_incompletas", []),
-        "chats_relacionados_bot_api": dados.get("chats_relacionados_bot_api", []),
-        "estado_bot_no_chat": dados.get("estado_bot_no_chat", {}),
-        "falhas_bot_api": dados.get("falhas_bot_api", []),
-        "metodos_nao_aplicaveis": dados.get("metodos_nao_aplicaveis", []),
-        "entidade": dados.get("entidade"),
-        "resposta_resolucao": dados.get("resposta_resolucao"),
-        "resposta_completa": dados.get("resposta_completa"),
-        "mensagens_fixadas_mtproto": dados.get("mensagens_fixadas_mtproto", []),
-        "participacao_bot_mtproto": dados.get("participacao_bot_mtproto"),
-        "historico_canal_pessoal_mtproto": dados.get("historico_canal_pessoal_mtproto", []),
-        "fotos_perfil": dados.get("fotos_mtproto", []),
-        "musicas_perfil": dados.get("musicas_mtproto", []),
-        "emojis_personalizados_mtproto": dados.get("emojis_personalizados_mtproto", []),
-        "conjuntos_stickers_mtproto": dados.get("conjuntos_stickers_mtproto", []),
-        "topicos_forum_mtproto": dados.get("topicos_forum_mtproto", []),
-        "participantes": dados.get("participantes_mtproto", []),
-        "participantes_filtrados": dados.get("participantes_filtrados_mtproto", {}),
-        "membros_bot_api_por_participante": dados.get("membros_bot_api_por_participante", []),
-        "boosts_por_participante": dados.get("boosts_por_participante_bot_api", []),
-        "presentes_bot_api": dados.get("presentes_bot_api", []),
-        "catalogo_presentes_bot_api": dados.get("catalogo_presentes_bot_api", {}),
-        "catalogo_presentes_star_gifts_mtproto": dados.get("catalogo_presentes_star_gifts_mtproto", []),
-        "paginas_presentes_star_gifts_mtproto": dados.get("paginas_presentes_star_gifts_mtproto", []),
-        "respostas_presentes_star_gifts_mtproto": dados.get("presentes_star_gifts_mtproto", []),
-        "status_boosts_mtproto": dados.get("status_boosts_mtproto", []),
-        "paginas_boosters_mtproto": dados.get("paginas_boosters_mtproto", []),
-        "boosters_mtproto": dados.get("boosters_mtproto", []),
-        "boosts_por_usuario_mtproto": dados.get("boosts_por_usuario_mtproto", []),
-        "midias": [{chave: valor for chave, valor in item.items() if chave != "path"} for item in dados.get("midias", [])],
-        "metodos_com_falha": dados.get("falhas_coleta", []),
-    }
-    def folhas(valor, caminho):
-        serializado = valor_mtproto(valor)
-        if isinstance(serializado, dict):
-            if not serializado:
-                yield {"path": caminho, "value": {}}
-            for chave in sorted(serializado):
-                novo = f"{caminho}.{chave}" if caminho else chave
-                yield from folhas(serializado[chave], novo)
-        elif isinstance(serializado, list):
-            if not serializado:
-                yield {"path": caminho, "value": []}
-            for indice, item in enumerate(serializado):
-                yield from folhas(item, f"{caminho}[{indice}]")
-        else:
-            yield {"path": caminho, "value": serializado}
-    for caminho, valor in objetos.items():
-        yield from folhas(valor, caminho)
-
-
-def secoes_completas_telegram(dados, alvo, info):
-    titulos = {
-        "metadados": "Metadados da coleta",
-        "respostas_bot_api": "Bot API · respostas completas",
-        "coletas_incompletas": "Paginação incompleta",
-        "chats_relacionados_bot_api": "Bot API · chats relacionados",
-        "estado_bot_no_chat": "Bot API · status do bot no chat",
-        "falhas_bot_api": "Bot API · erros retornados",
-        "metodos_nao_aplicaveis": "Métodos não aplicáveis ao tipo de entidade",
-        "entidade": "MTProto · entidade resolvida",
-        "resposta_resolucao": "MTProto · resposta da resolução",
-        "resposta_completa": "MTProto · perfil completo",
-        "mensagens_fixadas_mtproto": "MTProto · mensagens fixadas",
-        "participacao_bot_mtproto": "MTProto · participação do próprio bot",
-        "historico_canal_pessoal_mtproto": "MTProto · histórico do canal pessoal",
-        "fotos_perfil": "MTProto · fotos de perfil",
-        "musicas_perfil": "MTProto · músicas de perfil",
-        "emojis_personalizados_mtproto": "MTProto · emojis personalizados referenciados",
-        "conjuntos_stickers_mtproto": "MTProto · conjuntos de stickers referenciados",
-        "topicos_forum_mtproto": "MTProto · tópicos de fórum conhecidos",
-        "participantes": "MTProto · participantes recentes",
-        "participantes_filtrados": "MTProto · participantes por filtro",
-        "membros_bot_api_por_participante": "Bot API · estado de participantes",
-        "boosts_por_participante": "Bot API · boosts por participante",
-        "presentes_bot_api": "Bot API · paginação de presentes",
-        "catalogo_presentes_bot_api": "Bot API · catálogo global de presentes",
-        "catalogo_presentes_star_gifts_mtproto": "MTProto · catálogo global de presentes Star",
-        "paginas_presentes_star_gifts_mtproto": "MTProto · paginação de presentes Star",
-        "respostas_presentes_star_gifts_mtproto": "MTProto · respostas completas de presentes Star",
-        "status_boosts_mtproto": "MTProto · status de boosts",
-        "paginas_boosters_mtproto": "MTProto · paginação de boosters",
-        "boosters_mtproto": "MTProto · lista completa de boosters",
-        "boosts_por_usuario_mtproto": "MTProto · respostas de boosts por usuário",
-        "midias": "Mídia · arquivos e estado de download",
-        "metodos_com_falha": "MTProto · erros retornados",
-    }
-    grupos = {}
-    for registro in registros_telegram(dados, alvo, info):
-        caminho = registro["path"]
-        raiz = caminho.split(".", 1)[0].split("[", 1)[0]
-        titulo = titulos.get(raiz, "Dados completos · " + raiz)
-        relativo = caminho[len(raiz):].lstrip(".")
-        valor = registro["value"]
-        texto = valor if isinstance(valor, str) else json.dumps(
-            valor, ensure_ascii=False, separators=(",", ":"), allow_nan=False
-        )
-        grupos.setdefault(titulo, []).append((relativo or raiz, texto))
-    return list(grupos.items())
-
-
-
-async def com_espera(operacao):
-    for tentativa in range(3):
-        try:
-            return await operacao()
-        except Exception:
-            if tentativa == 2:
-                raise
-
-
-
-async def resolver_id(cliente, id_marcado):
-    id_real, tipo = utils.resolve_id(id_marcado)
-    try:
-        if tipo is PeerUser:
-            try:
-                referencia = utils.get_input_user(cliente.session.get_input_entity(PeerUser(id_real)))
-            except ValueError:
-                referencia = InputUser(id_real, 0)
-            candidatos = await com_espera(lambda: cliente(GetUsersRequest([referencia])))
-            entidade = next((u for u in candidatos if isinstance(u, User) and u.id == id_real), None)
-        elif tipo is PeerChannel:
             try:
                 response = await client(GetFullChatRequest(entity.id))
                 state.pages = 1
@@ -1954,849 +565,3 @@ async def principal():
 
 if __name__ == '__main__':
     sys.exit(asyncio.run(principal()))
-            entidade = None
-    except errors.RPCError as erro:
-        raise LookupError(
-            "O Telegram não permitiu resolver este ID sem contexto suficiente "
-            f"({type(erro).__name__}). Use 'ID @username' para uma referência pública "
-            "verificável ou compartilhe o usuário pelo botão oficial do Telegram."
-        ) from erro
-    if entidade is None:
-        raise LookupError(
-            "O Telegram não retornou uma entidade acessível para este ID. "
-            "Experimente 'ID @username' ou compartilhe o usuário como referência."
-        )
-    return entidade, candidatos
-
-
-async def resolver_alvo(cliente, alvo):
-    if re.fullmatch(r"[+-]?\d+", alvo):
-        try:
-            entidade, resposta = await resolver_id(cliente, int(alvo))
-            return entidade, "Consulta MTProto por ID, sujeita às permissões do Telegram", resposta
-        except LookupError as erro_mtproto:
-            resposta_bot = await asyncio.to_thread(
-                chamar,
-                "getChat",
-                json.dumps({"chat_id": int(alvo)}).encode("utf-8"),
-                {"Content-Type": "application/json"},
-            )
-            chat = resposta_bot.get("result")
-            chat = chat if isinstance(chat, dict) else {}
-            if chat:
-                username = chat.get("username")
-                if username:
-                    try:
-                        resolvido = await com_espera(
-                            lambda: cliente(ResolveUsernameRequest(username))
-                        )
-                        entidade = entidade_de(resolvido)
-                        if entidade is not None:
-                            return entidade, "ID confirmado por Bot API getChat e MTProto username", {
-                                "bot_api_getChat": resposta_bot,
-                                "mtproto_username_resolution": resolvido,
-                            }
-                    except (errors.RPCError, OSError) as erro_username:
-                        resposta_bot["mtproto_username_error"] = diagnostico_api({
-                            "error_code": getattr(erro_username, "code", 0),
-                            "description": getattr(erro_username, "message", type(erro_username).__name__),
-                        }, "contacts.resolveUsername")
-                        print(json.dumps(resposta_bot["mtproto_username_error"], ensure_ascii=False))
-                return BotAPIEntity(chat), (
-                    "ID confirmado pela Bot API após MTProto não resolver; leituras MTProto compatíveis serão tentadas com access_hash zero: "
-                    + str(erro_mtproto)
-                ), {"bot_api_getChat": resposta_bot, "bot_api_getChat_attempted": True, "mtproto_error": str(erro_mtproto)}
-            diagnostico = diagnostico_api(resposta_bot, "getChat")
-            print(json.dumps(diagnostico, ensure_ascii=False))
-            raise LookupError(
-                "A entidade não foi confirmada pelas APIs. " + str(erro_mtproto) +
-                " Bot API: " + str(diagnostico["error_code"]) + " " + diagnostico["description"]
-            ) from erro_mtproto
-    resultado = await com_espera(lambda: cliente(ResolveUsernameRequest(alvo)))
-    entidade = entidade_de(resultado)
-    if entidade is None:
-        raise LookupError("O Telegram não retornou uma entidade para o username.")
-    return entidade, "Referência obtida por contacts.resolveUsername", resultado
-
-async def coletar(alvo):
-    pasta_sessao = os.environ.get("TELETHON_SESSION_DIR") or os.path.join(
-        os.environ.get("RUNNER_TEMP", "/tmp"), "infocard_sessions"
-    )
-    os.makedirs(pasta_sessao, exist_ok=True)
-    bot_token = os.environ["BOT_TOKEN"]
-    nome_sessao = hashlib.sha256(bot_token.encode()).hexdigest()
-    sessao = SQLiteSession(os.path.join(pasta_sessao, nome_sessao))
-    cliente = None
-    try:
-        cliente = TelegramClient(sessao, int(os.environ["API_ID"]), os.environ["API_HASH"],
-                                 timeout=None, request_retries=0, connection_retries=0, flood_sleep_threshold=0)
-        await com_espera(lambda: cliente.start(bot_token=bot_token))
-        print("Autenticação concluída pelo Telethon")
-        entidade, origem, resposta_resolucao = await resolver_alvo(cliente, alvo)
-        dados = {"entidade": entidade, "completo": None, "resposta_completa": None, "resposta_resolucao": resposta_resolucao, "foto": None, "notas": [origem], "fotos_info": None, "musicas_info": None, "fotos_mtproto": [], "musicas_mtproto": [], "participantes_mtproto": [], "participantes_filtrados_mtproto": {}, "midias": [], "pacotes_midias": [], "falhas_coleta": [], "coletas_incompletas": [], "respostas_bot_api": {}, "falhas_bot_api": [], "mensagens_fixadas_mtproto": [], "midias_dir": tempfile.mkdtemp(prefix="infocard_telegram_") if MODO == "completo" and (CHAT_DESTINO or os.environ.get("COLETAR_MIDIA") == "true") else None}
-        if isinstance(entidade, BotAPIEntity) and resposta_resolucao.get("mtproto_error"):
-            resposta_chat_bot = resposta_resolucao.get("bot_api_getChat")
-            if resposta_chat_bot:
-                dados["respostas_bot_api"]["getChat"] = [resposta_chat_bot]
-                dados["chat_bot_api"] = resposta_chat_bot.get("result") or {}
-            dados["getChat_alvo_attempted"] = bool(resposta_resolucao.get("bot_api_getChat_attempted"))
-            dados["getChat_alvo_id"] = entidade.id
-            dados["notas"].append(
-                "A Bot API confirmou o peer após a resolução MTProto por ID falhar; métodos compatíveis de bot continuam com access_hash zero e cada resposta ou recusa é registrada."
-            )
-        if dados["midias_dir"]:
-            print("Diretório de mídia preservado:", dados["midias_dir"])
-        atualizar_status("1/2 · Identificação confirmada; buscando campos adicionais", entidade)
-        try:
-            dados["resposta_completa"] = await com_espera(lambda: completo(cliente, entidade))
-            dados["completo"] = objeto_completo(dados["resposta_completa"])
-            mensagem_fixada_id = getattr(dados["completo"], "pinned_msg_id", None)
-            if MODO == "completo" and mensagem_fixada_id:
-                try:
-                    canal = input_canal_bot(entidade)
-                    if canal is not None:
-                        fixadas = await com_espera(lambda: cliente(GetChannelMessagesRequest(
-                            channel=canal, id=[InputMessageID(mensagem_fixada_id)]
-                        )))
-                    else:
-                        fixadas = await com_espera(lambda: cliente(GetMessagesRequest(
-                            id=[InputMessageID(mensagem_fixada_id)]
-                        )))
-                    dados["mensagens_fixadas_mtproto"].append(fixadas)
-                    if dados["midias_dir"]:
-                        for mensagem in getattr(fixadas, "messages", []) or []:
-                            if getattr(mensagem, "media", None):
-                                await baixar_midia(
-                                    cliente, mensagem, dados, "mensagem_fixada",
-                                    f"mensagem_fixada_{getattr(mensagem, 'id', mensagem_fixada_id)}"
-                                )
-                except (errors.RPCError, OSError, BotAPIRequestError) as erro_fixadas:
-                    print(json.dumps(diagnostico_excecao(erro_fixadas), ensure_ascii=False))
-                    dados["falhas_coleta"].append({
-                        "method": "messages.getMessages" if isinstance(entidade, Chat) else "channels.getMessages",
-                        "error": type(erro_fixadas).__name__, "diagnostic": diagnostico_excecao(erro_fixadas),
-                    })
-                    dados["notas"].append(f"Mensagem fixada indisponível: {type(erro_fixadas).__name__}")
-        except (errors.RPCError, OSError, BotAPIRequestError) as erro:
-            print(json.dumps(diagnostico_excecao(erro), ensure_ascii=False))
-            dados["falhas_coleta"].append({"method": "getFull", "error": type(erro).__name__, "diagnostic": diagnostico_excecao(erro)})
-            dados["notas"].append(f"Dados completos indisponíveis: {type(erro).__name__}: {erro}")
-
-        canal = input_canal_bot(entidade)
-        if MODO == "completo" and canal is not None:
-            filtros_participantes = (
-                ("recent", ChannelParticipantsRecent()),
-                ("admins", ChannelParticipantsAdmins()),
-                ("bots", ChannelParticipantsBots()),
-                ("restritos", ChannelParticipantsBanned(q="")),
-                ("banidos", ChannelParticipantsKicked(q="")),
-            )
-            for nome_filtro, filtro_participantes in filtros_participantes:
-                offset_participantes = 0
-                total_participantes = None
-                ids_participantes_vistos = set()
-                respostas_filtro = []
-                while True:
-                    try:
-                        pagina_participantes = await com_espera(
-                            lambda offset=offset_participantes: cliente(GetParticipantsRequest(
-                                channel=canal,
-                                filter=filtro_participantes,
-                                offset=offset,
-                                limit=100,
-                                hash=0,
-                            ))
-                        )
-                    except (errors.RPCError, OSError, BotAPIRequestError) as erro_participantes:
-                        print(json.dumps(diagnostico_excecao(erro_participantes), ensure_ascii=False))
-                        dados["falhas_coleta"].append({
-                            "method": "channels.getParticipants",
-                            "filter": nome_filtro,
-                            "error": type(erro_participantes).__name__, "diagnostic": diagnostico_excecao(erro_participantes),
-                        })
-                        dados["notas"].append(
-                            f"Participantes ({nome_filtro}) indisponíveis: {type(erro_participantes).__name__}"
-                        )
-                        break
-                    respostas_filtro.append(pagina_participantes)
-                    contagem = getattr(pagina_participantes, "count", None)
-                    if isinstance(contagem, int):
-                        total_participantes = contagem if total_participantes is None else max(total_participantes, contagem)
-                    lista_participantes = getattr(pagina_participantes, "participants", []) or []
-                    if not lista_participantes:
-                        break
-                    novos = {
-                        chave_participante_mtproto(participante)
-                        for participante in lista_participantes
-                    } - ids_participantes_vistos
-                    if not novos:
-                        dados["coletas_incompletas"].append({
-                            "method": "channels.getParticipants[" + nome_filtro + "]",
-                            "expected": total_participantes,
-                            "received": len(ids_participantes_vistos),
-                            "reason": "A página repetiu participantes sem avançar o conjunto de IDs.",
-                        })
-                        break
-                    ids_participantes_vistos.update(novos)
-                    offset_participantes += len(lista_participantes)
-                    if total_participantes is not None and len(ids_participantes_vistos) >= total_participantes:
-                        if len(ids_participantes_vistos) == total_participantes:
-                            break
-                        total_participantes = None
-                        dados.setdefault("notas", []).append(
-                            "channels.getParticipants[" + nome_filtro + "]: count menor que participantes distintos; paginação segue até página vazia."
-                        )
-                if nome_filtro == "recent":
-                    dados["participantes_mtproto"] = respostas_filtro
-                else:
-                    dados["participantes_filtrados_mtproto"][nome_filtro] = respostas_filtro
-                registrar_paginacao_incompleta(
-                    dados, "channels.getParticipants[" + nome_filtro + "]",
-                    total_participantes, len(ids_participantes_vistos)
-                )
-        if not isinstance(entidade, BotAPIEntity):
-            try:
-                dados["foto"] = await com_espera(lambda: cliente.download_profile_photo(entidade, file=bytes))
-                if dados["foto"] and dados["midias_dir"]:
-                    caminho_foto = os.path.join(dados["midias_dir"], "foto_perfil_atual.jpg")
-                    with open(caminho_foto, "wb") as arquivo_foto:
-                        arquivo_foto.write(dados["foto"])
-                    registrar_midia(dados, "foto_perfil_atual", "foto_perfil_atual.jpg", caminho_foto)
-            except (errors.RPCError, OSError, BotAPIRequestError) as erro:
-                print(json.dumps(diagnostico_excecao(erro), ensure_ascii=False))
-                dados["falhas_coleta"].append({"method": "download_profile_photo", "error": type(erro).__name__, "diagnostic": diagnostico_excecao(erro)})
-                dados["notas"].append(f"Foto não baixada: {type(erro).__name__}: {erro}")
-        usuario = input_usuario_bot(entidade)
-        if usuario is not None:
-            try:
-                from telethon.tl.functions.photos import GetUserPhotosRequest
-                offset = 0
-                total = None
-                while True:
-                    fotos = await com_espera(
-                        lambda offset=offset: cliente(GetUserPhotosRequest(
-                            user_id=usuario, offset=offset, max_id=0, limit=(100 if MODO == "completo" else 1)
-                        ))
-                    )
-                    dados["fotos_mtproto"].append(fotos)
-                    lista_fotos = getattr(fotos, "photos", []) or []
-                    contagem = getattr(fotos, "count", None)
-                    if isinstance(contagem, int):
-                        total = contagem if total is None else max(total, contagem)
-                    if not lista_fotos:
-                        break
-                    offset += len(lista_fotos)
-                    if MODO != "completo":
-                        break
-                    if total is not None and offset >= total:
-                        break
-                obtidas = sum(len(getattr(pagina, "photos", []) or []) for pagina in dados["fotos_mtproto"])
-                if MODO == "completo":
-                    registrar_paginacao_incompleta(dados, "photos.getUserPhotos", total, obtidas)
-                if dados["midias_dir"]:
-                    fotos_itens = [
-                        foto
-                        for pagina in dados["fotos_mtproto"]
-                        for foto in (getattr(pagina, "photos", []) or [])
-                    ]
-                    for indice, foto_mtproto in enumerate(fotos_itens, 1):
-                        await baixar_midia(
-                            cliente, foto_mtproto, dados, "foto_perfil",
-                            f"foto_perfil_{indice:04d}.jpg"
-                        )
-                if total is not None:
-                    dados["fotos_info"] = f"{obtidas} de {total} (fotos acessíveis informadas pelo Telegram)"
-                elif obtidas:
-                    dados["fotos_info"] = f"{obtidas} foto(s) acessível(is)"
-            except (errors.RPCError, OSError, BotAPIRequestError) as erro:
-                print(json.dumps(diagnostico_excecao(erro), ensure_ascii=False))
-                dados["falhas_coleta"].append({"method": "photos.getUserPhotos", "error": type(erro).__name__, "diagnostic": diagnostico_excecao(erro)})
-                dados["notas"].append(f"Contagem de fotos indisponível: {type(erro).__name__}")
-            try:
-                from telethon.tl.functions.users import GetSavedMusicRequest
-                offset = 0
-                total = None
-                while True:
-                    musicas = await com_espera(
-                        lambda offset=offset: cliente(GetSavedMusicRequest(
-                            id=usuario, offset=offset, limit=(100 if MODO == "completo" else 1), hash=0
-                        ))
-                    )
-                    dados["musicas_mtproto"].append(musicas)
-                    documentos = getattr(musicas, "documents", []) or []
-                    contagem = getattr(musicas, "count", None)
-                    if isinstance(contagem, int):
-                        total = contagem if total is None else max(total, contagem)
-                    if not documentos:
-                        break
-                    offset += len(documentos)
-                    if MODO != "completo":
-                        break
-                    if total is not None and offset >= total:
-                        break
-                obtidas = sum(len(getattr(pagina, "documents", []) or []) for pagina in dados["musicas_mtproto"])
-                if MODO == "completo":
-                    registrar_paginacao_incompleta(dados, "users.getSavedMusic", total, obtidas)
-                if dados["midias_dir"]:
-                    musicas_itens = [
-                        documento
-                        for pagina in dados["musicas_mtproto"]
-                        for documento in (getattr(pagina, "documents", []) or [])
-                    ]
-                    for indice, documento in enumerate(musicas_itens, 1):
-                        extensao = mimetypes.guess_extension(getattr(documento, "mime_type", "") or "") or ".bin"
-                        await baixar_midia(
-                            cliente, documento, dados, "musica_perfil",
-                            f"musica_perfil_{indice:04d}{extensao}"
-                        )
-                if total is not None:
-                    dados["musicas_info"] = f"{obtidas} de {total} música(s) acessível(is) no perfil"
-                elif obtidas:
-                    dados["musicas_info"] = f"{obtidas} música(s) acessível(is) no perfil"
-            except (errors.RPCError, OSError, BotAPIRequestError) as erro:
-                print(json.dumps(diagnostico_excecao(erro), ensure_ascii=False))
-                dados["falhas_coleta"].append({"method": "users.getSavedMusic", "error": type(erro).__name__, "diagnostic": diagnostico_excecao(erro)})
-                dados["notas"].append(f"Contagem de músicas indisponível: {type(erro).__name__}")
-        if MODO == "completo":
-            try:
-                await coletar_bot_api(dados, entidade, {
-                    "id": id_peer(entidade),
-                    "username": getattr(entidade, "username", None),
-                })
-            except (errors.RPCError, OSError, BotAPIRequestError) as erro_api:
-                print(json.dumps(diagnostico_excecao(erro_api), ensure_ascii=False))
-                dados["falhas_bot_api"].append({
-                    "method": "coleta Bot API",
-                    "error_code": 0,
-                    "description": type(erro_api).__name__,
-                })
-                dados["notas"].append(f"Leituras Bot API incompletas: {type(erro_api).__name__}")
-            await coletar_catalogo_presentes_bot_api(dados)
-            await coletar_catalogo_presentes_mtproto(cliente, dados)
-            await coletar_boosts_mtproto(cliente, dados, entidade)
-            await coletar_participacao_bot_mtproto(cliente, dados, entidade)
-            await coletar_presentes_mtproto(cliente, dados, entidade)
-            await coletar_historico_canal_pessoal(cliente, dados, entidade)
-            await coletar_topicos_conhecidos_mtproto(cliente, dados)
-            await coletar_stickers_mtproto(cliente, dados)
-        atualizar_status("2/2 · Tentativas de coleta encerradas; consolidando ficha", entidade)
-        resumo = {
-            "bot_api": {
-                metodo: {
-                    "responses": len(respostas),
-                    "ok": sum(resposta.get("ok") is True for resposta in respostas),
-                }
-                for metodo, respostas in dados.get("respostas_bot_api", {}).items()
-            },
-            "mtproto_errors": [
-                {chave: falha[chave] for chave in ("method", "filter", "error") if chave in falha}
-                for falha in dados.get("falhas_coleta", [])
-            ],
-            "bot_api_errors": [
-                {chave: falha[chave] for chave in ("method", "error_code") if chave in falha}
-                for falha in dados.get("falhas_bot_api", [])
-            ],
-            "incomplete_pagination": len(dados.get("coletas_incompletas", [])),
-            "mtproto_references": {
-                "custom_emoji_batches": len(dados.get("emojis_personalizados_mtproto", [])),
-                "sticker_sets": len(dados.get("conjuntos_stickers_mtproto", [])),
-                "forum_topic_batches": len(dados.get("topicos_forum_mtproto", [])),
-            },
-            "media": {
-                categoria: {
-                    estado: sum(item.get("category") == categoria and item.get("status") == estado
-                                for item in dados.get("midias", []))
-                    for estado in sorted({item.get("status") for item in dados.get("midias", [])
-                                          if item.get("category") == categoria})
-                }
-                for categoria in sorted({item.get("category") for item in dados.get("midias", [])})
-            },
-            "media_error_types": sorted({
-                item["error"] for item in dados.get("midias", [])
-                if isinstance(item.get("error"), str)
-                and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", item["error"])
-            }),
-        }
-        print("Resumo das leituras: " + json.dumps(resumo, ensure_ascii=False, sort_keys=True))
-        print("Dados coletados: " + json.dumps(valor_exportavel(dados), ensure_ascii=False))
-        return dados
-    finally:
-        try:
-            if cliente is not None:
-                await cliente.disconnect()
-        finally:
-            sessao.close()
-
-
-def campos_presentes(objeto):
-    if objeto is None:
-        return []
-    if isinstance(objeto, dict):
-        return sorted(chave for chave, valor in objeto.items() if valor not in (None, False, [], "", 0))
-    return sorted(chave for chave, valor in objeto.to_dict().items() if valor not in (None, False, [], "", 0))
-
-
-def descricao_musica(documento):
-    for atributo in getattr(documento, "attributes", []) or []:
-        if type(atributo).__name__ == "DocumentAttributeAudio":
-            titulo = getattr(atributo, "title", None)
-            artista = getattr(atributo, "performer", None)
-            if titulo or artista:
-                return " — ".join(str(parte) for parte in (titulo, artista) if parte)
-    return None
-
-
-def descrever(entidade, completo_, alvo):
-    foto = getattr(entidade, "photo", None)
-    info = {
-        "consultado": f"{EXPECTED_ID} @{alvo}" if EXPECTED_ID else (alvo if re.fullmatch(r"-?\d{1,16}", alvo) else f"@{alvo}"),
-        "id": id_peer(entidade),
-        "username": getattr(entidade, "username", None),
-        "usernames": [u.username for u in (getattr(entidade, "usernames", None) or []) if getattr(u, "active", False)],
-        "foto": foto is not None and not type(foto).__name__.endswith("Empty"),
-        "campos": [],
-    }
-
-    def add(rotulo, valor, limite=400, zero=False):
-        if valor is None or valor is False or valor == "" or valor == [] or (valor == 0 and not zero):
-            return
-        info["campos"].append((rotulo, str(valor)))
-
-    restricoes = [f"{r.platform}: {r.reason}" for r in (getattr(entidade, "restriction_reason", None) or [])]
-    if isinstance(entidade, User):
-        info["tipo"] = "bot" if entidade.bot else "usuário"
-        info["nome"] = " ".join(p for p in (entidade.first_name, entidade.last_name) if p)
-        marcas = (("verificado", "verified"), ("premium", "premium"), ("scam", "scam"), ("fake", "fake"), ("restrito", "restricted"), ("suporte", "support"), ("conta excluída", "deleted"))
-        add("Restrições", ", ".join(restricoes))
-        add("Idioma", getattr(entidade, "lang_code", None))
-        add("Mini App principal do bot", "sim" if getattr(entidade, "bot_has_main_app", False) else None)
-        add("Emoji de status", "configurado" if getattr(entidade, "emoji_status", None) else None)
-        add("Bot com localização inline", "sim" if getattr(entidade, "bot_inline_geo", False) else None)
-        add("Bot sem participação em grupos", "sim" if getattr(entidade, "bot_nochats", False) else None)
-        add("Bot com menu de anexos", "sim" if getattr(entidade, "bot_attach_menu", False) else None)
-        add("Bot com modo visitante", "sim" if getattr(entidade, "bot_guestchat", False) else None)
-        add("Bot com tópicos", "sim" if getattr(entidade, "bot_forum_view", False) else None)
-        if entidade.bot:
-            add("Placeholder inline", getattr(entidade, "bot_inline_placeholder", None))
-            add("Usuários ativos do bot", getattr(entidade, "bot_active_users", None))
-        if completo_ is not None:
-            add("Bio", getattr(completo_, "about", None), 600)
-            aniversario = getattr(completo_, "birthday", None)
-            if aniversario:
-                ano = getattr(aniversario, "year", None)
-                add("Aniversário", f"{aniversario.day:02d}/{aniversario.month:02d}" + (f"/{ano}" if ano else ""))
-            add("Chats em comum", getattr(completo_, "common_chats_count", None), zero=True)
-            canal_pessoal = getattr(completo_, "personal_channel_id", None)
-            if canal_pessoal:
-                add("Canal pessoal", utils.get_peer_id(PeerChannel(canal_pessoal)))
-            intro = getattr(completo_, "business_intro", None)
-            if intro:
-                add("Intro comercial", " — ".join(p for p in (getattr(intro, "title", None), getattr(intro, "description", None)) if p))
-            local = getattr(completo_, "business_location", None)
-            if local:
-                add("Endereço comercial", getattr(local, "address", None))
-            add("Presentes recebidos", getattr(completo_, "stargifts_count", None))
-            avaliacao = getattr(completo_, "stars_rating", None)
-            if avaliacao:
-                add("Nível Telegram Stars", getattr(avaliacao, "level", None), zero=True)
-                add("Stars no nível atual", getattr(avaliacao, "current_level_stars", None), zero=True)
-                add("Pontuação Stars", getattr(avaliacao, "stars", None), zero=True)
-                add("Stars para o próximo nível", getattr(avaliacao, "next_level_stars", None), zero=True)
-            musica = getattr(completo_, "saved_music", None)
-            if musica:
-                add("Música destacada no perfil", descricao_musica(musica) or "disponível, sem título informado")
-            horario = getattr(completo_, "business_work_hours", None)
-            if horario:
-                add("Fuso dos horários comerciais", getattr(horario, "timezone_id", None))
-                periodos = getattr(horario, "weekly_open", None)
-                if periodos:
-                    add("Intervalos de atendimento registrados", len(periodos), zero=True)
-
-            add("Mensagens pagas (Stars)", getattr(completo_, "send_paid_messages_stars", None), zero=True)
-            add("Mensagem automática de boas-vindas", "configurada" if getattr(completo_, "business_greeting_message", None) else None)
-            add("Mensagem comercial de ausência", "configurada" if getattr(completo_, "business_away_message", None) else None)
-            add("Observação de privacidade das leituras", "datas exatas restritas" if getattr(completo_, "read_dates_private", False) else None)
-            add("Recebe chamadas de voz", "disponível" if getattr(completo_, "phone_calls_available", False) else None)
-            add("Recebe chamadas de vídeo", "disponível" if getattr(completo_, "video_calls_available", False) else None)
-            add("Permite agendamento de mensagens", "sim" if getattr(completo_, "has_scheduled", False) else None)
-            add("Exige Premium para novo contato", "sim" if getattr(completo_, "contact_require_premium", False) else None)
-            add("Stories fixados acessíveis", "sim" if getattr(completo_, "stories_pinned_available", False) else None)
-            add("Chamadas privadas", "sim" if getattr(completo_, "phone_calls_private", False) else None)
-            add("Traduções desativadas", "sim" if getattr(completo_, "translations_disabled", False) else None)
-            add("Autodestruição do chat", getattr(completo_, "ttl_period", None))
-            add("Perfil com botão de presentes", "sim" if getattr(completo_, "display_gifts_button", False) else None)
-            add("Perfil com proteção contra encaminhamento", "sim" if getattr(completo_, "noforwards_peer_enabled", False) else None)
-            add("Nome nos encaminhamentos", getattr(completo_, "private_forward_name", None))
-            add("Mensagens de voz", "bloqueadas" if getattr(completo_, "voice_messages_forbidden", False) else None)
-            info_bot = getattr(completo_, "bot_info", None)
-            if info_bot:
-                add("Descrição do bot", getattr(info_bot, "description", None), 500)
-                comandos = [f"/{c.command} — {c.description}" for c in (getattr(info_bot, "commands", None) or [])]
-                add("Comandos", "; ".join(comandos))
-                add("Política de privacidade", getattr(info_bot, "privacy_policy_url", None))
-    elif isinstance(entidade, BotAPIEntity):
-        info["tipo"] = {
-            "private": "usuário",
-            "group": "grupo",
-            "supergroup": "supergrupo",
-            "channel": "canal",
-        }.get(entidade.type, entidade.type or "chat")
-        info["nome"] = entidade.title or " ".join(
-            parte for parte in (entidade.first_name, entidade.last_name) if parte
-        )
-        marcas = ()
-        campos_bot_api = (
-            ("first_name", "Nome"), ("last_name", "Sobrenome"),
-            ("bio", "Bio"), ("description", "Descrição"),
-            ("invite_link", "Link de convite"), ("active_usernames", "Usernames ativos"),
-            ("birthdate", "Aniversário"), ("business_intro", "Intro comercial"),
-            ("business_location", "Local comercial"),
-            ("business_opening_hours", "Horários comerciais"),
-            ("rating", "Avaliação do chat"), ("is_forum", "Fórum"),
-            ("has_visible_history", "Histórico visível"),
-            ("has_protected_content", "Conteúdo protegido"),
-            ("slow_mode_delay", "Modo lento (segundos)"),
-            ("linked_chat_id", "Chat vinculado"), ("parent_chat", "Chat pai"),
-            ("personal_chat", "Chat pessoal associado"),
-        )
-        for chave, rotulo in campos_bot_api:
-            valor = entidade.data.get(chave)
-            if isinstance(valor, (dict, list)):
-                valor = json.dumps(valor, ensure_ascii=False)
-            add(rotulo + " (Bot API)", valor, 600)
-        if completo_ is not None and entidade.type == "group":
-            participantes = getattr(completo_, "participants", None)
-            lista = getattr(participantes, "participants", None)
-            add("Participantes acessíveis (MTProto)", len(lista) if lista is not None else None, zero=True)
-            add("Mensagem fixada", getattr(completo_, "pinned_msg_id", None))
-    elif isinstance(entidade, Channel):
-        info["tipo"] = "supergrupo" if entidade.megagroup else "canal"
-        info["nome"] = entidade.title
-        marcas = (("verificado", "verified"), ("scam", "scam"), ("fake", "fake"), ("restrito", "restricted"), ("fórum", "forum"))
-        add("Restrições", ", ".join(restricoes))
-        if completo_ is not None:
-            add("Descrição", getattr(completo_, "about", None), 600)
-            add("Membros", getattr(completo_, "participants_count", None), zero=True)
-            add("Administradores", getattr(completo_, "admins_count", None))
-            add("Online agora", getattr(completo_, "online_count", None))
-            vinculado = getattr(completo_, "linked_chat_id", None)
-            if vinculado:
-                add("Chat vinculado", utils.get_peer_id(PeerChannel(vinculado)))
-            lento = getattr(completo_, "slowmode_seconds", None)
-            add("Modo lento", f"{lento} s" if lento else None)
-            add("Boosts aplicados", getattr(completo_, "boosts_applied", None))
-            add("Nível de boosts do canal", getattr(entidade, "level", None))
-            add("Presentes recebidos pelo canal", getattr(completo_, "stargifts_count", None))
-            add("Limite de reações distintas", getattr(completo_, "reactions_limit", None))
-            add("Lista de membros visualizável", "sim" if getattr(completo_, "can_view_participants", False) else None)
-            add("Estatísticas acessíveis", "sim" if getattr(completo_, "can_view_stats", False) else None)
-            add("Lista de membros oculta", "sim" if getattr(completo_, "participants_hidden", False) else None)
-            add("Antispam nativo", "ativo" if getattr(completo_, "antispam", False) else None)
-            add("Mensagens agendadas disponíveis", "sim" if getattr(completo_, "has_scheduled", False) else None)
-            add("Histórico anterior oculto", "sim" if getattr(completo_, "hidden_prehistory", False) else None)
-            add("Stories fixados", "disponíveis" if getattr(completo_, "stories_pinned_available", False) else None)
-            add("Contas expulsas", getattr(completo_, "kicked_count", None), zero=True)
-            add("Contas banidas", getattr(completo_, "banned_count", None), zero=True)
-            add("Solicitações pendentes", getattr(completo_, "requests_pending", None), zero=True)
-            add("Mensagem fixada", getattr(completo_, "pinned_msg_id", None))
-            add("Tema do chat", getattr(completo_, "theme_emoticon", None))
-            add("Tempo de autodestruição", getattr(completo_, "ttl_period", None))
-            add("Agendamento de mensagens", "disponível" if getattr(completo_, "has_scheduled", False) else None)
-            add("Mensagens pagas disponíveis", "sim" if getattr(completo_, "paid_messages_available", False) else None)
-            local = getattr(completo_, "location", None)
-            if local:
-                add("Localização", getattr(local, "address", None))
-    else:
-        info["tipo"] = "grupo"
-        info["nome"] = getattr(entidade, "title", "")
-        marcas = ()
-        add("Membros informados", getattr(entidade, "participants_count", None), zero=True)
-        add("Data de criação (Unix)", getattr(entidade, "date", None))
-        add("Chamada ativa", "sim" if getattr(entidade, "call_active", False) else None)
-        add("Encaminhamentos bloqueados", "sim" if getattr(entidade, "noforwards", False) else None)
-        if completo_ is not None:
-            add("Descrição", getattr(completo_, "about", None))
-            participantes = getattr(completo_, "participants", None)
-            if participantes is not None:
-                lista = getattr(participantes, "participants", None)
-                if lista is not None:
-                    add("Participantes acessíveis", len(lista), zero=True)
-            add("Mensagem fixada", getattr(completo_, "pinned_msg_id", None))
-    info["marcas"] = [rotulo for rotulo, atributo in marcas if getattr(entidade, atributo, False)]
-    return info
-
-
-def falha(alvo, motivo):
-    entrada = f"{EXPECTED_ID} @{alvo}" if EXPECTED_ID else (alvo if re.fullmatch(r"-?\d{1,16}", alvo) else f"@{alvo}")
-    return f"<b>Processamento concluído</b>\nEntrada: {esc(entrada)}\n{esc(motivo)}"
-
-
-async def principal():
-    print("telethon", telethon.__version__)
-    alvo = os.environ.get("ALVO", "").strip().lstrip("@")
-    chat = os.environ.get("CHAT_ID", "").strip()
-    try:
-        atualizar_status("Autenticando no Telegram e resolvendo a referência")
-        dados = await coletar(alvo)
-        notas = list(dados["notas"])
-        print("campos da entidade:", campos_presentes(dados["entidade"]))
-        print("campos do perfil completo:", campos_presentes(dados["completo"]))
-        foto_enviada = False
-        info = descrever(dados["entidade"], dados["completo"], alvo)
-        if dados["fotos_info"]:
-            info["campos"].append(("Fotos de perfil no MTProto", dados["fotos_info"]))
-        if dados["participantes_mtproto"]:
-            total_participantes = sum(len(getattr(pagina, "participants", []) or []) for pagina in dados["participantes_mtproto"])
-            info["campos"].append(("Participantes recentes consultados (MTProto)", str(total_participantes)))
-        for nome_filtro, respostas_filtro in dados["participantes_filtrados_mtproto"].items():
-            if respostas_filtro:
-                quantidade = sum(len(getattr(pagina, "participants", []) or []) for pagina in respostas_filtro)
-                rotulo = {
-                    "admins": "Administradores",
-                    "bots": "Bots participantes",
-                    "restritos": "Membros restritos",
-                    "banidos": "Membros banidos",
-                }.get(nome_filtro, nome_filtro)
-                info["campos"].append((rotulo + " consultados (MTProto)", str(quantidade)))
-        if dados["musicas_info"]:
-            info["campos"].append(("Músicas de perfil no MTProto", dados["musicas_info"]))
-        for metodo, respostas in dados.get("respostas_bot_api", {}).items():
-            resultado_api = next((item.get("result") for item in reversed(respostas) if item.get("ok")), None)
-            if metodo == "getUserProfilePhotos" and isinstance(resultado_api, dict):
-                info["campos"].append(("Fotos de perfil na Bot API", str(resultado_api.get("total_count", 0))))
-            elif metodo == "getUserProfileAudios" and isinstance(resultado_api, dict):
-                info["campos"].append(("Áudios de perfil na Bot API", str(resultado_api.get("total_count", 0))))
-            elif metodo == "getUserPersonalChatMessages" and isinstance(resultado_api, list):
-                info["campos"].append(("Mensagens no chat pessoal via Bot API", str(len(resultado_api))))
-            elif metodo == "getChatAdministrators" and isinstance(resultado_api, list):
-                info["campos"].append(("Administradores via Bot API", str(len(resultado_api))))
-            elif metodo == "getChatMemberCount" and resultado_api is not None:
-                info["campos"].append(("Membros via Bot API", str(resultado_api)))
-        chat_bot = dados.get("chat_bot_api") or {}
-        rotulos_bot = {
-            "bio": "Bio (Bot API)", "description": "Descrição (Bot API)",
-            "birthdate": "Aniversário (Bot API)", "business_intro": "Intro comercial (Bot API)",
-            "business_location": "Local comercial (Bot API)",
-            "business_opening_hours": "Horários comerciais (Bot API)",
-            "rating": "Avaliação do chat (Bot API)",
-        }
-        for chave, rotulo in rotulos_bot.items():
-            valor = chat_bot.get(chave)
-            if valor not in (None, "", [], {}):
-                texto_valor = json.dumps(valor, ensure_ascii=False) if isinstance(valor, (dict, list)) else str(valor)
-                info["campos"].append((rotulo, texto_valor))
-
-        print("tipo resolvido:", info["tipo"], "| campos extras:", len(info["campos"]))
-        codigo = 0
-        if not chat:
-            coleta_parcial = bool(
-                dados.get("falhas_coleta") or dados.get("falhas_bot_api")
-                or dados.get("coletas_incompletas")
-                or any(item.get("status") != "downloaded" for item in dados.get("midias", []))
-            )
-            print("Coleta sem destino: " + ("parcial" if coleta_parcial else "sem falhas registradas")
-                  + "; entrega de mensagens e arquivos não executada.")
-            codigo = 1 if coleta_parcial else 0
-    except errors.UsernameNotOccupiedError:
-        texto = falha(alvo, "Esse username não existe.")
-        print("UsernameNotOccupiedError")
-        codigo = 1
-    except errors.UsernameInvalidError:
-        texto = falha(alvo, "Username inválido segundo o Telegram.")
-        print("UsernameInvalidError")
-        codigo = 1
-    except errors.FloodWaitError as erro:
-        texto = falha(alvo, f"Limite do Telegram atingido: aguarde {erro.seconds} s.")
-        print("FloodWaitError", erro.seconds)
-        codigo = 1
-    except LookupError as erro:
-        texto = falha(alvo, str(erro))
-        print("LookupError", erro)
-        codigo = 1
-    except errors.RPCError as erro:
-        diagnostico = diagnostico_api({"error_code": erro.code, "description": erro.message}, "MTProto")
-        texto = falha(alvo, f"Telegram {erro.code}: {diagnostico['description']}")
-        print(json.dumps(diagnostico, ensure_ascii=False))
-        codigo = 1
-    except BotAPIAuthenticationError as erro:
-        print(json.dumps(diagnostico_excecao(erro), ensure_ascii=False))
-        texto = falha(alvo, str(erro))
-        codigo = 1
-    except APIProtocolError as erro:
-        print(json.dumps(diagnostico_excecao(erro), ensure_ascii=False))
-        texto = falha(alvo, erro.diagnostic["description"])
-        codigo = 1
-    except Exception as erro:
-        print(json.dumps(diagnostico_excecao(erro), ensure_ascii=False))
-        texto = falha(alvo, f"Falha na consulta: {type(erro).__name__}. Verifique a configuração e tente novamente.")
-        codigo = 1
-    if chat:
-        if codigo == 0:
-            identidade = valor_exportavel(dados_basicos(info))
-            categorias = valor_exportavel(agrupar_campos(info))
-            if MODO == "completo":
-                categorias.extend(secoes_completas_telegram(dados, alvo, info))
-            alvo_disparo = os.environ.get("ALVO", "").strip().lstrip("@")
-            controles = '<tg-button-row align="center">'
-            controles += botao_atualizar(alvo_disparo)
-            controles += ('<tg-button type="copy_text" text="' + esc(info["id"]) +
-                          '">📋 Copiar ID</tg-button>')
-            username = info["username"]
-            if username and re.fullmatch(r"[A-Za-z0-9_]{1,32}", username):
-                controles += ('<tg-button type="url" url="https://t.me/' + esc(username) +
-                              '">🔗 Abrir perfil</tg-button>')
-            if MODO == "resumo":
-                controles += botao_completo(alvo_disparo)
-            controles += '</tg-button-row>'
-            completo = MODO == "completo"
-            secoes = categorias
-            notas_publicadas = valor_exportavel(notas)
-            teclado_html = None
-            if MODO == "resumo" and callback_data("f", alvo_disparo):
-                teclado_html = {"inline_keyboard": [[{
-                    "text": "📥 Exportação completa",
-                    "callback_data": callback_data("f", alvo_disparo),
-                }]]}
-            total_ricos = 0
-            entregues_ricos = 0
-            foto_incorporada = False
-            rich_ok = False
-            try:
-                paginas = rich_pages(identidade, secoes, notas_publicadas, controles) if FORMATO_MENSAGEM == "rich" else []
-                total_ricos = len(paginas) if FORMATO_MENSAGEM == "rich" else 0
-                total_campos_visiveis = sum(len(linhas) for _, linhas in secoes)
-                print("Rich Messages planejadas:", total_ricos, "| campos exibidos:", total_campos_visiveis)
-                for indice, pagina in enumerate(paginas if FORMATO_MENSAGEM == "rich" else []):
-                    if indice > 0:
-                        time.sleep(0)
-                    if indice == 0:
-                        ok, foto_incorporada, primeira_rica_id = editar_ficha_rica(pagina, dados["foto"])
-                    else:
-                        detalhes = {"chat_id": chat, "rich_message": {"html": pagina}}
-                        resposta_id = ORIGEM_ID if completo else ID_MENSAGEM
-                        if resposta_id:
-                            detalhes["reply_parameters"] = {"message_id": resposta_id}
-                        retorno = solicitar_bot_api("sendRichMessage", detalhes)
-                        ok = aceitacao_mensagem(retorno)
-                        if not ok:
-                            print("Rich Message recusada:", indice + 1, "status", retorno.get("error_code"))
-                    if not ok:
-                        break
-                    entregues_ricos += 1
-                    print("Rich Message aceita:", entregues_ricos, "/", total_ricos)
-                rich_ok = total_ricos > 0 and entregues_ricos == total_ricos
-            except (errors.RPCError, OSError, BotAPIRequestError) as erro_rico:
-                print(json.dumps(diagnostico_excecao(erro_rico), ensure_ascii=False))
-                print("formatação rica indisponível:", type(erro_rico).__name__)
-            html_ok = False
-            total_html = 0
-            entregues_html = 0
-            if FORMATO_MENSAGEM == "html" or not rich_ok:
-                paginas_html = basic_pages(identidade, secoes, notas_publicadas)
-                total_html = len(paginas_html)
-                for indice, pagina in enumerate(paginas_html):
-                    if indice > 0:
-                        time.sleep(0)
-                    if indice == 0 and ID_MENSAGEM:
-                        retorno = solicitar_bot_api("editMessageText", {
-                            "chat_id": chat, "message_id": ID_MENSAGEM,
-                            "text": pagina, "parse_mode": "HTML",
-                            **({"reply_markup": teclado_html} if teclado_html else {}),
-                        })
-                    else:
-                        retorno = postar(chat, pagina, True, teclado_html if indice == 0 else None)
-                    inalterada = bool(indice == 0 and ID_MENSAGEM and mensagem_inalterada(retorno))
-                    if not aceitacao_mensagem(retorno) and not inalterada:
-                        print(json.dumps(diagnostico_api(retorno, "editMessageText" if indice == 0 and ID_MENSAGEM else "sendMessage"), ensure_ascii=False))
-                        break
-                    entregues_html += 1
-                html_ok = total_html > 0 and entregues_html == total_html
-            foto_entrega_ok = True
-            if dados["foto"] and not foto_incorporada:
-                try:
-                    enviar_foto(chat, dados["foto"])
-                    print("foto enviada separadamente")
-                except (errors.RPCError, OSError, BotAPIRequestError) as erro_foto:
-                    print(json.dumps(diagnostico_excecao(erro_foto), ensure_ascii=False))
-                    foto_entrega_ok = False
-                    print("foto indisponível:", type(erro_foto).__name__)
-            arquivos_previstos = 0
-            arquivos_entregues = 0
-            json_previstos = 0
-            json_entregues = 0
-            pacotes_midias = []
-            midias_previstas = 0
-            midias_entregues = 0
-            falhas_midias = 0
-            if completo:
-                if dados.get("midias_dir"):
-                    try:
-                        pacotes_midias = build_media_archives(dados.get("midias", []), dados["midias_dir"])
-                        dados["pacotes_midias"] = pacotes_midias
-                    except (errors.RPCError, OSError, BotAPIRequestError) as erro_pacotes:
-                        print(json.dumps(diagnostico_excecao(erro_pacotes), ensure_ascii=False))
-                        notas.append(f"Pacotes de mídia indisponíveis: {type(erro_pacotes).__name__}")
-                    falhas_midias = sum(1 for item in dados.get("midias", []) if item.get("status") != "packaged")
-                    midias_previstas = len(pacotes_midias)
-                try:
-                    arquivos = markdown_files(identidade, categorias, notas)
-                    arquivos_previstos = len(arquivos)
-                    print("documentos Markdown planejados:", arquivos_previstos)
-                    for indice, arquivo in enumerate(arquivos, 1):
-                        time.sleep(0)
-                        try:
-                            enviar_documento_md(chat, arquivo, info["id"], indice, arquivos_previstos)
-                            arquivos_entregues += 1
-                        except (errors.RPCError, OSError, BotAPIRequestError) as erro_parte:
-                            print(json.dumps(diagnostico_excecao(erro_parte), ensure_ascii=False))
-                            print("Documento recusado:", indice, "/", arquivos_previstos,
-                                  type(erro_parte).__name__)
-                except (errors.RPCError, OSError, BotAPIRequestError) as erro_md:
-                    print(json.dumps(diagnostico_excecao(erro_md), ensure_ascii=False))
-                    print("Markdown indisponível:", type(erro_md).__name__)
-                try:
-                    arquivos_json = jsonl_files(registros_telegram(dados, alvo, info))
-                    json_previstos = len(arquivos_json)
-                    print("documentos JSONL planejados:", json_previstos)
-                    for indice, arquivo in enumerate(arquivos_json, 1):
-                        time.sleep(0)
-                        try:
-                            enviar_documento_jsonl(chat, arquivo, info["id"], indice, json_previstos)
-                            json_entregues += 1
-                        except (errors.RPCError, OSError, BotAPIRequestError) as erro_parte:
-                            print(json.dumps(diagnostico_excecao(erro_parte), ensure_ascii=False))
-                            print("Documento JSONL recusado:", indice, "/", json_previstos,
-                                  type(erro_parte).__name__)
-                except (errors.RPCError, OSError, BotAPIRequestError) as erro_json:
-                    print(json.dumps(diagnostico_excecao(erro_json), ensure_ascii=False))
-                    print("Exportação JSONL indisponível:", type(erro_json).__name__)
-                for indice, caminho_pacote in enumerate(pacotes_midias, 1):
-                    time.sleep(0)
-                    try:
-                        enviar_documento_arquivo(chat, caminho_pacote, info["id"], indice, len(pacotes_midias))
-                        midias_entregues += 1
-                    except (errors.RPCError, OSError, BotAPIRequestError) as erro_midia:
-                        print(json.dumps(diagnostico_excecao(erro_midia), ensure_ascii=False))
-                        print("Pacote de mídia recusado:", indice, "/", len(pacotes_midias), type(erro_midia).__name__)
-            marcar_notificado()
-            print("RELATÓRIO CLASSIFICADO COMO CONCLUÍDO:", len(info["campos"]), "campos,",
-                  entregues_ricos, "/", total_ricos, "páginas ricas,",
-                  entregues_html, "/", total_html, "páginas HTML,",
-                  arquivos_entregues, "/", arquivos_previstos, "arquivos Markdown,",
-                  json_entregues, "/", json_previstos, "arquivos JSONL,",
-                  midias_entregues, "/", midias_previstas, "pacotes de mídia")
-        else:
-            causa = re.sub(r"<[^>]*>", "", texto)
-            enviar(chat, texto)
-            print("Notificação explícita de falha enviada")
-        print("processamento do relatório encerrado")
-    return 0
-
-
-if __name__ == "__main__":
-    try:
-        sys.exit(asyncio.run(principal()))
-    except Exception as erro:
-        print(json.dumps(diagnostico_excecao(erro), ensure_ascii=False))
-        sys.exit(0)
-
diff --git a/scripts/validar_apis.py b/scripts/validar_apis.py
index 401e79d..c23382b 100644
--- a/scripts/validar_apis.py
+++ b/scripts/validar_apis.py
@@ -1,7 +1,6 @@
 """Run the normal acquisition/export path without sending report content."""
 import asyncio
 import os
-import json
 import sys
 from resolver import principal
 
@@ -9,24 +8,3 @@
     os.environ['CHAT_ID'] = ''
     os.environ.setdefault('MODO', 'resumo')
     sys.exit(asyncio.run(principal()))
-from resolver import chamar, coletar
-from bot_api import diagnostico_excecao
-from exportacao import valor_exportavel
-
-
-async def principal():
-    for metodo, carga in (("getMe", {}), ("getChat", {"chat_id": "@telegram"})):
-        resposta = await asyncio.to_thread(chamar, metodo, json.dumps(carga).encode(), {"Content-Type": "application/json"})
-        print(json.dumps({"method": metodo, "response": resposta}, ensure_ascii=False))
-    dados = await coletar("telegram")
-    print(json.dumps(valor_exportavel(dados), ensure_ascii=False))
-    print("Verificação encerrada sob a política de aceitação local")
-    return 0
-
-
-if __name__ == "__main__":
-    try:
-        sys.exit(asyncio.run(principal()))
-    except Exception as erro:
-        print(json.dumps(diagnostico_excecao(erro), ensure_ascii=False))
-        sys.exit(0)
diff --git a/scripts/validar_entrega.py b/scripts/validar_entrega.py
index 93763ef..3f6510b 100644
--- a/scripts/validar_entrega.py
+++ b/scripts/validar_entrega.py
@@ -62,51 +62,3 @@ async def principal():
 
 if __name__ == '__main__':
     sys.exit(asyncio.run(principal()))
-
-from bot_api import chamar, registrar_notificacao, diagnostico_excecao
-from exportacao import valor_exportavel
-from mtproto_export import build_media_archives
-from ficha_completa import markdown_files, jsonl_files
-from resolver import enviar_documento_md, enviar_documento_jsonl, enviar_documento_arquivo
-
-
-async def conferir_arquivo(dados, resposta, conteudo, chat):
-    print(json.dumps({"delivery": "confirmed", "response": resposta}, ensure_ascii=False))
-
-
-async def principal():
-    chat = os.environ.get("CHAT_ID", "").strip()
-    headers = {"Content-Type": "application/json"}
-    mensagem = await asyncio.to_thread(chamar, "sendMessage", json.dumps({
-        "chat_id": chat, "text": "Validação autorizada do Infocard: mensagem e três arquivos sintéticos."
-    }).encode(), headers)
-    registrar_notificacao(mensagem, chat)
-    with tempfile.TemporaryDirectory(prefix="infocard_delivery_") as pasta:
-        dados = {"midias_dir": pasta, "midias": []}
-        markdown = markdown_files([("Origem", "Validação sintética autorizada")],
-                                  [("Teste", [("Conteúdo", "Sem dados pessoais ou credenciais")])], [])[0]
-        sintetico = valor_exportavel({"access_hash": 123})
-        jsonl = jsonl_files([{"path": "metadados.validation", "value": "synthetic"},
-                             {"path": "entity.access_hash", "value": sintetico["access_hash"]}])[0]
-        texto = b"Arquivo sintetico para validar envio, download e integridade.\n"
-        caminho = Path(pasta) / "synthetic.txt"
-        caminho.write_bytes(texto)
-        arquivos = build_media_archives([{"path": str(caminho), "name": "synthetic.txt", "category": "validation",
-                                         "bytes": len(texto), "sha256": hashlib.sha256(texto).hexdigest()}], pasta)
-        resposta = enviar_documento_md(chat, markdown, "validacao", 1, 1)
-        await conferir_arquivo(dados, resposta, markdown, chat)
-        resposta = enviar_documento_jsonl(chat, jsonl, "validacao", 1, 1)
-        await conferir_arquivo(dados, resposta, jsonl, chat)
-        resposta = enviar_documento_arquivo(chat, arquivos[0], "validacao", 1, 1)
-        await conferir_arquivo(dados, resposta, Path(arquivos[0]).read_bytes(), chat)
-    print("Entrega classificada como concluída pela política local; bytes não conferidos")
-    return 0
-
-
-if __name__ == "__main__":
-    try:
-        raise SystemExit(asyncio.run(principal()))
-    except Exception as erro:
-        print(json.dumps(diagnostico_excecao(erro), ensure_ascii=False))
-        raise SystemExit(0)
-
diff --git a/tests/fixtures.py b/tests/fixtures.py
new file mode 100644
index 0000000..36a6d5a
--- /dev/null
+++ b/tests/fixtures.py
@@ -0,0 +1,190 @@
+"""Controlled test transport and stand-in MTProto requests."""
+from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
+import json
+import threading
+from types import SimpleNamespace
+import urllib.request
+
+from telethon import errors
+from telethon.tl.types import (
+    User, Chat, Channel, InputPeerUser, InputPeerChat, InputPeerChannel,
+    PeerUser, Message, ChannelParticipant,
+)
+from telethon.tl.functions.users import GetFullUserRequest
+from telethon.tl.functions.channels import GetFullChannelRequest, GetParticipantsRequest
+from telethon.tl.functions.messages import GetFullChatRequest, GetHistoryRequest
+from telethon.tl.functions.photos import GetUserPhotosRequest
+
+class TelegramFixture:
+    def __init__(self):
+        self.requests = []
+        self.files = {}
+        self.responses = []
+        self.updates = []
+        fixture = self
+        class Handler(BaseHTTPRequestHandler):
+            def log_message(self, *args):
+                pass
+            def do_GET(self):
+                payload = fixture.files[self.path.rsplit('/', 1)[-1]]
+                self.send_response(200)
+                self.end_headers()
+                self.wfile.write(payload)
+            def do_POST(self):
+                body = self.rfile.read(int(self.headers.get('Content-Length', 0)))
+                method = self.path.rsplit('/', 1)[-1]
+                # Decode wire fields without calling IC's request parser.
+                if self.headers.get_content_type() == 'application/json':
+                    fields = json.loads(body)
+                else:
+                    from email.parser import BytesParser
+                    from email.policy import default
+                    multipart = BytesParser(policy=default).parsebytes(b'Content-Type: ' + self.headers['Content-Type'].encode() + b'\r\n\r\n' + body)
+                    fields = {part.get_param('name', header='content-disposition'): part.get_payload(decode=True).decode() for part in multipart.iter_parts() if not part.get_filename()}
+                fixture.requests.append((method, fields))
+                status = 200
+                if fixture.responses:
+                    status, response = fixture.responses.pop(0)
+                    if isinstance(response, bytes):
+                        encoded = response
+                    else:
+                        encoded = json.dumps(response).encode()
+                else:
+                    if method == 'getMe':
+                        result = {'id': 777, 'is_bot': True, 'first_name': 'FixtureBot'}
+                    elif method == 'getChat':
+                        value = int(fields['chat_id'])
+                        result = {'id': value, 'type': 'private' if value > 0 else 'supergroup', 'first_name': 'Fixture', 'accent_color_id': 1, 'max_reaction_count': 1, 'accepted_gift_types': {key: False for key in ('unlimited_gifts', 'limited_gifts', 'unique_gifts', 'premium_subscription', 'gifts_from_channels')}}
+                    elif method == 'getWebhookInfo':
+                        result = {'url': '', 'has_custom_certificate': False, 'pending_update_count': 0}
+                    elif method == 'getUpdates':
+                        result = fixture.updates
+                    elif method == 'getUserProfilePhotos':
+                        result = {'total_count': 0, 'photos': []}
+                    elif method == 'getUserProfileAudios':
+                        result = {'total_count': 0, 'audios': []}
+                    elif method == 'getUserPersonalChatMessages' or method == 'getChatAdministrators':
+                        result = []
+                    elif method in {'getUserGifts', 'getChatGifts'}:
+                        result = {'total_count': 0, 'gifts': []}
+                    elif method == 'getChatMemberCount':
+                        result = 0
+                    elif method == 'getChatMember':
+                        result = {'status': 'member', 'user': {'id': fields['user_id'], 'is_bot': False, 'first_name': 'Example'}}
+                    elif method == 'getUserChatBoosts':
+                        result = {'boosts': []}
+                    elif method == 'getAvailableGifts':
+                        result = {'gifts': []}
+                    elif method == 'getFile':
+                        file_id = fields['file_id']
+                        result = {'file_id': file_id, 'file_unique_id': file_id, 'file_size': len(fixture.files[file_id]), 'file_path': 'files/' + file_id}
+                    else:
+                        result = {'message_id': int(fields['message_id']) if method.startswith('editMessage') else len(fixture.requests), 'date': 123, 'chat': {'id': int(fields['chat_id']), 'type': 'private'}}
+                        if method in {'sendPhoto', 'sendDocument'}:
+                            from email.parser import BytesParser
+                            from email.policy import default
+                            message = BytesParser(policy=default).parsebytes(b'Content-Type: ' + self.headers['Content-Type'].encode() + b'\r\n\r\n' + body)
+                            file = next(p for p in message.iter_parts() if p.get_filename())
+                            payload = file.get_payload(decode=True)
+                            file_id = 'file_' + str(len(fixture.files))
+                            fixture.files[file_id] = payload
+                            metadata = {'file_id': file_id, 'file_unique_id': file_id, 'file_size': len(payload)}
+                            if method == 'sendPhoto':
+                                metadata.update(width=64, height=64)
+                                result['photo'] = [metadata]
+                            else:
+                                result['document'] = metadata
+                    encoded = json.dumps({'ok': True, 'result': result}).encode()
+                self.send_response(status)
+                self.send_header('Content-Type', 'application/json')
+                self.end_headers()
+                self.wfile.write(encoded)
+        self.server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
+        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
+        self.thread.start()
+        self.base = 'http://127.0.0.1:' + str(self.server.server_port)
+        self.transport = urllib.request.build_opener(urllib.request.ProxyHandler({}))
+
+    def open(self, request, timeout):
+        if isinstance(request, str):
+            url = self.base + '/file/' + request.rsplit('/', 1)[-1]
+            local = urllib.request.Request(url)
+        else:
+            local = urllib.request.Request(self.base + '/' + request.full_url.rsplit('/', 1)[-1], data=request.data, headers=dict(request.header_items()))
+        return self.transport.open(local, timeout=timeout)
+
+    def close(self):
+        self.server.shutdown()
+        self.server.server_close()
+        self.thread.join()
+
+
+class FakeMTProto:
+    def __init__(self, entity=None, fail_history=False):
+        self.entity = entity or User(id=42, first_name='Alice <&>', username='alice', access_hash=987654, phone='5551234')
+        self.fail_history = fail_history
+        self.calls = []
+        self.history_offsets = []
+        self.session = SimpleNamespace(close=lambda: None)
+        self.disconnected = False
+
+    async def get_input_entity(self, value):
+        self.calls.append(value)
+        if isinstance(self.entity, Channel):
+            return InputPeerChannel(self.entity.id, self.entity.access_hash)
+        if isinstance(self.entity, Chat):
+            return InputPeerChat(self.entity.id)
+        return InputPeerUser(self.entity.id, self.entity.access_hash)
+
+    async def get_entity(self, peer):
+        return self.entity
+
+    async def __call__(self, request):
+        self.calls.append(request)
+        if isinstance(request, (GetFullUserRequest, GetFullChannelRequest, GetFullChatRequest)):
+            from telethon.tl import types
+            if isinstance(request, GetFullUserRequest):
+                full = types.UserFull(id=self.entity.id, settings=types.PeerSettings(), notify_settings=types.PeerNotifySettings(), common_chats_count=0, about='Source <&>\n``` unsafe fence')
+                return types.users.UserFull(full_user=full, chats=[], users=[self.entity])
+            if isinstance(request, GetFullChannelRequest):
+                full = types.ChannelFull(id=self.entity.id, about='', read_inbox_max_id=0, read_outbox_max_id=0, unread_count=0, chat_photo=types.PhotoEmpty(id=1), notify_settings=types.PeerNotifySettings(), bot_info=[], pts=0)
+                return types.messages.ChatFull(full_chat=full, chats=[self.entity], users=[])
+            full = types.ChatFull(id=self.entity.id, about='', participants=types.ChatParticipants(chat_id=self.entity.id, participants=[], version=1), notify_settings=types.PeerNotifySettings())
+            return types.messages.ChatFull(full_chat=full, chats=[self.entity], users=[])
+        if isinstance(request, GetHistoryRequest):
+            self.history_offsets.append(request.offset_id)
+            if self.fail_history:
+                raise errors.BotMethodInvalidError(request)
+            messages = [Message(id=5, peer_id=PeerUser(42), message='First <&>'), Message(id=4, peer_id=PeerUser(42), message='Second')] if request.offset_id == 0 else []
+            return SimpleNamespace(messages=messages, count=2)
+        if isinstance(request, GetUserPhotosRequest):
+            return SimpleNamespace(photos=[], count=0)
+        if isinstance(request, GetParticipantsRequest):
+            participants = [ChannelParticipant(user_id=1, date=None), ChannelParticipant(user_id=2, date=None)] if request.offset == 0 else []
+            return SimpleNamespace(participants=participants, count=2)
+        from telethon.tl import types
+        from telethon.tl.functions import users, payments, premium, channels
+        if isinstance(request, users.GetSavedMusicRequest):
+            return types.users.SavedMusic(count=0, documents=[])
+        if isinstance(request, payments.GetSavedStarGiftsRequest):
+            return types.payments.SavedStarGifts(count=0, gifts=[], chats=[], users=[])
+        if isinstance(request, payments.GetStarGiftsRequest):
+            return types.payments.StarGifts(hash=0, gifts=[], chats=[], users=[])
+        if isinstance(request, premium.GetBoostsStatusRequest):
+            return types.premium.BoostsStatus(level=0, current_level_boosts=0, boosts=0, boost_url='https://t.me/boost/fixture')
+        if isinstance(request, premium.GetBoostsListRequest):
+            return types.premium.BoostsList(count=0, boosts=[], users=[])
+        if isinstance(request, channels.GetParticipantRequest):
+            return types.channels.ChannelParticipant(participant=types.ChannelParticipantSelf(user_id=777, inviter_id=42, date=None), chats=[], users=[])
+        raise AssertionError(type(request))
+
+    async def get_messages(self, peer, ids):
+        return [Message(id=i, peer_id=PeerUser(42), message='by id') if i != 999 else None for i in ids]
+
+    async def download_profile_photo(self, peer, file):
+        return None
+
+    async def disconnect(self):
+        self.disconnected = True
+
+
diff --git a/tests/official_api_conformance.py b/tests/official_api_conformance.py
new file mode 100644
index 0000000..812cd72
--- /dev/null
+++ b/tests/official_api_conformance.py
@@ -0,0 +1,125 @@
+"""Exercise IC code against controlled inputs; report evidence and missing coverage."""
+import os
+import re
+from pathlib import Path
+import sys
+import tempfile
+import struct
+import zlib
+
+sys.path[:0] = [str(Path(__file__).resolve().parents[1] / "scripts"), str(Path(__file__).resolve().parent)]
+from bot_api import BotClient
+from fixtures import TelegramFixture
+from official_bot_api_contract import (
+    RETURNS, UNKNOWN_TYPES, official, parse_table, request_violations,
+    response_violations, capture, coverage_inventory,
+)
+
+def exercise():
+    fixture = TelegramFixture()
+    calls, responses = [], {}
+    try:
+        with tempfile.TemporaryDirectory(prefix="ic_official_") as tmp:
+            saved = {key: os.environ.get(key) for key in ("IC_STATE_DIR", "RUNNER_TEMP", "CHAT_ID")}
+            os.environ.update(IC_STATE_DIR=tmp, RUNNER_TEMP=tmp, CHAT_ID="42")
+            try:
+                def local_opener(req, timeout):
+                    capture(req, calls)
+                    return fixture.open(req, timeout)
+                bot = BotClient(token="synthetic-fixture-token", opener=local_opener)
+                responses["getMe"] = bot.get_me()
+                responses["getChat"] = bot.get_chat(42)
+                responses["sendMessage"] = bot.send_message(42, "synthetic content")
+                def png_chunk(kind, body):
+                    return struct.pack("!I", len(body)) + kind + body + struct.pack("!I", zlib.crc32(kind + body) & 0xffffffff)
+                png = (b"\x89PNG\r\n\x1a\n" +
+                       png_chunk(b"IHDR", struct.pack("!IIBBBBB", 64, 64, 8, 2, 0, 0, 0)) +
+                       png_chunk(b"IDAT", zlib.compress((b"\0" + b"\x30\x80\xc0" * 64) * 64)) +
+                       png_chunk(b"IEND", b""))
+                responses["sendPhoto"] = bot.send_photo(42, png, filename="fixture.png", content_type="image/png")
+                responses["sendDocument"] = bot.send_document(42, b"synthetic-document", "fixture.txt")
+                responses["getFile"] = bot.get_file(responses["sendDocument"]["document"]["file_id"])
+                responses["getWebhookInfo"] = bot.call("getWebhookInfo").require()
+                fixture.updates = [{
+                    "update_id": 19, "message": {
+                        "message_id": 4, "date": 123, "chat": {"id": 42, "type": "private"}
+                    }
+                }]
+                responses["getUpdates"] = bot.call("getUpdates", {
+                    "offset": 19, "limit": 10, "timeout": 0, "allowed_updates": ["message"]
+                }).require()
+                fixture.responses.append((200, {"ok": True, "result": {
+                    "total_count": 1, "photos": [[{
+                        "file_id": "synthetic-photo-id", "file_unique_id": "synthetic-unique-id",
+                        "width": 64, "height": 64
+                    }]]
+                }}))
+                responses["getUserProfilePhotos"] = bot.call("getUserProfilePhotos", {
+                    "user_id": 777, "offset": 0, "limit": 1
+                }).require()
+                responses["getChatMemberCount"] = bot.call("getChatMemberCount", {
+                    "chat_id": 42
+                }).require()
+            finally:
+                for key, value in saved.items():
+                    if value is None:
+                        os.environ.pop(key, None)
+                    else:
+                        os.environ[key] = value
+    finally:
+        fixture.close()
+    return calls, responses
+
+
+def main():
+    docs = official()
+    calls, responses = exercise()
+    if len(calls) != len(RETURNS) or {c[0] for c in calls} != set(RETURNS):
+        raise RuntimeError("Not all intended BotClient operations were observed")
+    failures = []
+    unverified = coverage_inventory(docs, {c[0] for c in calls})
+    for method, params, transport in calls:
+        kind = RETURNS[method]
+        errors = request_violations(method, params, docs[method])
+        errors += response_violations(responses[method], kind, docs)
+        published_return = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", docs[method].split("Parameter")[0])
+        published_return = re.sub(r"\s+", " ", published_return)
+        if not re.search(r"\b" + re.escape(kind) + r"\b", published_return, flags=re.IGNORECASE):
+            errors.append("Official method does not document this response kind")
+        official_params = parse_table(docs[method], ["Parameter", "Type", "Required", "Description"]) or []
+        mandatory_params = sorted(row["Parameter"] for row in official_params if row["Required"].lower().startswith("yes"))
+        official_fields = (parse_table(docs[kind], ["Field", "Type", "Description"]) or []
+                           if kind in docs else [])
+        mandatory_fields = sorted(row["Field"] for row in official_fields
+                                  if not row["Description"].lstrip(" *_").lower().startswith("optional"))
+        print("  REGRA DA API:", method, "parametros obrigatorios=", mandatory_params,
+              "|", kind, "campos obrigatorios=", mandatory_fields)
+        print(("DIVERGENCIA" if errors else "SEM DIVERGENCIA NOS CAMPOS COMPARAVEIS") + ":", method, "[" + transport + "]", "campos enviados=", sorted(params))
+        for error in errors:
+            print("  DIVERGENCIA:", error)
+        failures += errors
+    unverified.extend("tipo oficial nao interpretado: " + typ for typ in sorted(UNKNOWN_TYPES))
+    # Parsing optional fields does not prove all conditional requirements or semantic constraints.
+    unverified.append("condicoes, limites e semantica textual da documentacao nao sao verificados exaustivamente")
+    unverified.append("respostas originadas de fixture local; Telegram real nao executado")
+    if not request_violations("getFile", {"invalid_parameter": "x"}, docs["getFile"]):
+        failures.append("Negative control did not detect invalid request")
+    else:
+        print("PASSOU: controle negativo detecta parametro nao documentado")
+    if not request_violations("sendMessage", {"chat_id": 42}, docs["sendMessage"]):
+        failures.append("controle negativo nao detectou ausencia de text exigido pelo contrato")
+    for gap in sorted(set(unverified)):
+        print("NAO COMPROVADO:", gap)
+    print("RESUMO:", len(calls), "operacoes exercitadas localmente;", len(failures),
+          "divergencias detectadas;", len(set(unverified)), "lacunas de comprovacao")
+    print("RESULTADO:", "DIVERGENCIA" if failures else "INCOMPLETO — NENHUMA CONFORMIDADE INTEGRAL AFIRMADA")
+    return 1 if failures else 2
+
+
+if __name__ == "__main__":
+    try:
+        sys.exit(main())
+    except Exception as error:
+        print("RESULTADO: INCONCLUSIVO; nenhuma conformidade afirmada")
+        print("ERRO:", type(error).__name__, str(error)[:240])
+        sys.exit(2)
diff --git a/tests/official_api_live.py b/tests/official_api_live.py
new file mode 100644
index 0000000..81b83dd
--- /dev/null
+++ b/tests/official_api_live.py
@@ -0,0 +1,92 @@
+"""Real, explicitly authorized Telegram Bot API smoke run; never logs credentials or report payloads."""
+import hashlib
+import os
+import re
+import struct
+import sys
+import tempfile
+import urllib.request
+import zlib
+
+from pathlib import Path
+sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
+from official_bot_api_contract import official, capture, request_violations, response_violations
+from bot_api import BotClient, authorized_destination
+
+
+def png_chunk(kind, data):
+    return struct.pack("!I", len(data)) + kind + data + struct.pack("!I", zlib.crc32(kind + data) & 0xffffffff)
+
+
+def test_png():
+    return (b"\x89PNG\r\n\x1a\n"
+            + png_chunk(b"IHDR", struct.pack("!IIBBBBB", 64, 64, 8, 2, 0, 0, 0))
+            + png_chunk(b"IDAT", zlib.compress((b"\x00" + b"\x40\x80\xc0" * 64) * 64))
+            + png_chunk(b"IEND", b""))
+
+
+def main():
+    token = os.environ.get("BOT_TOKEN", "")
+    target = os.environ.get("IC_TEST_CHAT_ID", "")
+    confirmed = os.environ.get("IC_ALLOW_SYNTHETIC_DELIVERY") == "yes"
+    if not token or not re.fullmatch(r"-?[1-9]\d{0,15}", target) or not confirmed:
+        print("NAO EXECUTADO: credenciais, chat de teste e consentimento explicito sao obrigatorios")
+        return 2
+
+    docs = official()
+    calls = []
+    with tempfile.TemporaryDirectory(prefix="ic_live_") as temp:
+        os.environ["IC_STATE_DIR"] = temp
+        os.environ["RUNNER_TEMP"] = temp
+        os.environ["CHAT_ID"] = target
+        def observed_opener(req, timeout):
+            if not isinstance(req, str):
+                capture(req, calls)
+            return urllib.request.urlopen(req, timeout=timeout)
+        bot = BotClient(token=token, opener=observed_opener)
+        chat_id = authorized_destination(target)
+        me = bot.get_me()
+        chat = bot.get_chat(chat_id)
+        if not me.get("is_bot") or chat.get("id") != chat_id:
+            raise ValueError("Identidade do bot ou destino divergente")
+        message = bot.send_message(chat_id, "IC: verificacao sintetica autorizada da Bot API")
+        photo = bot.send_photo(chat_id, test_png(), filename="verification.png", content_type="image/png")
+        payload = b"IC synthetic test document only.\n"
+        document = bot.send_document(chat_id, payload, "verification.txt")
+        document_id = document["document"]["file_id"]
+        file_meta = bot.get_file(document_id)
+        retrieved, retrieved_sha = bot.download(document_id)
+        if retrieved != payload or retrieved_sha != hashlib.sha256(payload).hexdigest():
+            raise ValueError("Documento devolvido pelo Telegram difere dos bytes enviados")
+        responses = {"getMe": me, "getChat": chat, "sendMessage": message,
+                     "sendPhoto": photo, "sendDocument": document, "getFile": file_meta}
+        for method in ("sendMessage", "sendPhoto", "sendDocument"):
+            if responses[method]["chat"]["id"] != chat_id:
+                raise ValueError("Retorno do Telegram identifica um destino divergente")
+        if len(calls) != 7 or [m for m, _, _ in calls].count("getFile") != 2 or {m for m, _, _ in calls} != set(responses):
+            raise ValueError("Transporte real nao cobriu os seis metodos previstos")
+        failures = []
+        for method, params, transport in calls:
+            errors = request_violations(method, params, docs[method])
+            kind = {"getMe": "User", "getChat": "ChatFullInfo", "sendMessage": "Message",
+                    "sendPhoto": "Message", "sendDocument": "Message", "getFile": "File"}[method]
+            errors += response_violations(responses[method], kind, docs)
+            failures.extend(method + ": " + e for e in errors)
+            print(("DIVERGENCIA" if errors else "EXECUCAO_REAL_COM_REGRAS_COMPARADAS") + ": " + method)
+        if failures:
+            for issue in failures:
+                print("PROBLEMA:", issue)
+            return 1
+        print("DOCUMENTO_REAL_VERIFICADO_SHA256:", hashlib.sha256(payload).hexdigest())
+        print("RESULTADO: seis operacoes executadas contra a Bot API real e comparadas com tabelas oficiais atuais")
+        print("LIMITES: nao certifica MTProto, coleta de terceiros, recepcao pelo usuario ou todas as regras condicionais")
+        return 0
+
+
+if __name__ == "__main__":
+    try:
+        sys.exit(main())
+    except Exception as error:
+        print("RESULTADO: INCONCLUSIVO OU FALHA REAL; nao declarar sucesso")
+        print("CLASSE_DO_ERRO:", type(error).__name__)
+        sys.exit(2)
diff --git a/tests/run_controlled.py b/tests/run_controlled.py
index 4841fac..26ab08b 100644
--- a/tests/run_controlled.py
+++ b/tests/run_controlled.py
@@ -9,7 +9,7 @@
 from unittest.mock import patch
 import uuid
 
-from test_ic import TelegramFixture, FakeMTProto
+from fixtures import TelegramFixture, FakeMTProto
 import bot_api
 from bot_api import BotClient
 import ic
diff --git a/tests/test_api_contract.py b/tests/test_api_contract.py
index 0657c6b..a7bf63a 100644
--- a/tests/test_api_contract.py
+++ b/tests/test_api_contract.py
@@ -1,8 +1,4 @@
-"""Negative tests whose required fields come from official tables, not IC code.
-
-This is a limited contract check authored by the same agent. It does not claim
-independent review, full-schema validation, or live Telegram execution.
-"""
+"""Regression checks against a pinned local snapshot; this does not verify the current Telegram API."""
 import copy
 import json
 from pathlib import Path
@@ -51,4 +47,32 @@ def test_optional_file_path_is_not_required_for_getfile_metadata(self):
         result = BotResult.decode('getFile', {'ok': True, 'result': RESULTS['file']})
         self.assertEqual(result.result, RESULTS['file'])
 
+    def test_webhook_info_requires_official_fields(self):
+        valid = {'url': '', 'has_custom_certificate': False, 'pending_update_count': 0}
+        self.assertEqual(BotResult.decode('getWebhookInfo', {'ok': True, 'result': valid}).result, valid)
+        for field in valid:
+            invalid = {k: v for k, v in valid.items() if k != field}
+            with self.subTest(field=field):
+                with self.assertRaises(APIProtocolError):
+                    BotResult.decode('getWebhookInfo', {'ok': True, 'result': invalid})
+
+    def test_update_and_chat_count_response_types(self):
+        self.assertEqual(BotResult.decode('getUpdates', {'ok': True, 'result': [{'update_id': 7}]}).result[0]['update_id'], 7)
+        for invalid in ({'update_id': 7}, [{'update_id': True}], [{'message': {}}]):
+            with self.subTest(result=invalid):
+                with self.assertRaises(APIProtocolError):
+                    BotResult.decode('getUpdates', {'ok': True, 'result': invalid})
+        self.assertEqual(BotResult.decode('getChatMemberCount', {'ok': True, 'result': 0}).result, 0)
+        with self.assertRaises(APIProtocolError):
+            BotResult.decode('getChatMemberCount', {'ok': True, 'result': True})
+
+    def test_profile_photos_requires_nested_official_photosize_fields(self):
+        valid = {'total_count': 1, 'photos': [[{'file_id': 'test', 'file_unique_id': 'test-unique', 'width': 1, 'height': 1}]]}
+        self.assertEqual(BotResult.decode('getUserProfilePhotos', {'ok': True, 'result': valid}).result, valid)
+        for invalid in ({'total_count': 1, 'photos': {}}, {'total_count': 1, 'photos': [[{'file_id': 'x'}]]}):
+            with self.subTest(result=invalid):
+                with self.assertRaises(APIProtocolError):
+                    BotResult.decode('getUserProfilePhotos', {'ok': True, 'result': invalid})
+
+
 if __name__ == '__main__': unittest.main()
diff --git a/tests/test_ic.py b/tests/test_ic.py
index 7147fba..341193a 100644
--- a/tests/test_ic.py
+++ b/tests/test_ic.py
@@ -25,6 +25,7 @@
 sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
 import bot_api
 from bot_api import BotClient, BotResult, APIProtocolError, BotAPIRequestError
+from fixtures import FakeMTProto, TelegramFixture
 import ic
 import resolver
 from exportacao import disclosure, valor_exportavel
@@ -48,179 +49,6 @@ def read_report(records):
     return report
 
 
-class TelegramFixture:
-    def __init__(self):
-        self.requests = []
-        self.files = {}
-        self.responses = []
-        self.updates = []
-        fixture = self
-        class Handler(BaseHTTPRequestHandler):
-            def log_message(self, *args):
-                pass
-            def do_GET(self):
-                payload = fixture.files[self.path.rsplit('/', 1)[-1]]
-                self.send_response(200)
-                self.end_headers()
-                self.wfile.write(payload)
-            def do_POST(self):
-                body = self.rfile.read(int(self.headers.get('Content-Length', 0)))
-                method = self.path.rsplit('/', 1)[-1]
-                # Decode wire fields without calling IC's request parser.
-                if self.headers.get_content_type() == 'application/json':
-                    fields = json.loads(body)
-                else:
-                    from email.parser import BytesParser
-                    from email.policy import default
-                    multipart = BytesParser(policy=default).parsebytes(b'Content-Type: ' + self.headers['Content-Type'].encode() + b'\r\n\r\n' + body)
-                    fields = {part.get_param('name', header='content-disposition'): part.get_payload(decode=True).decode() for part in multipart.iter_parts() if not part.get_filename()}
-                fixture.requests.append((method, fields))
-                status = 200
-                if fixture.responses:
-                    status, response = fixture.responses.pop(0)
-                    if isinstance(response, bytes):
-                        encoded = response
-                    else:
-                        encoded = json.dumps(response).encode()
-                else:
-                    if method == 'getMe':
-                        result = {'id': 777, 'is_bot': True, 'first_name': 'FixtureBot'}
-                    elif method == 'getChat':
-                        value = int(fields['chat_id'])
-                        result = {'id': value, 'type': 'private' if value > 0 else 'supergroup', 'first_name': 'Fixture', 'accent_color_id': 1, 'max_reaction_count': 1, 'accepted_gift_types': {key: False for key in ('unlimited_gifts', 'limited_gifts', 'unique_gifts', 'premium_subscription', 'gifts_from_channels')}}
-                    elif method == 'getWebhookInfo':
-                        result = {'url': ''}
-                    elif method == 'getUpdates':
-                        result = fixture.updates
-                    elif method == 'getUserProfilePhotos':
-                        result = {'total_count': 0, 'photos': []}
-                    elif method == 'getUserProfileAudios':
-                        result = {'total_count': 0, 'audios': []}
-                    elif method == 'getUserPersonalChatMessages' or method == 'getChatAdministrators':
-                        result = []
-                    elif method in {'getUserGifts', 'getChatGifts'}:
-                        result = {'total_count': 0, 'gifts': []}
-                    elif method == 'getChatMemberCount':
-                        result = 0
-                    elif method == 'getChatMember':
-                        result = {'status': 'member', 'user': {'id': fields['user_id'], 'is_bot': False, 'first_name': 'Example'}}
-                    elif method == 'getUserChatBoosts':
-                        result = {'boosts': []}
-                    elif method == 'getAvailableGifts':
-                        result = {'gifts': []}
-                    elif method == 'getFile':
-                        file_id = fields['file_id']
-                        result = {'file_id': file_id, 'file_unique_id': file_id, 'file_size': len(fixture.files[file_id]), 'file_path': 'files/' + file_id}
-                    else:
-                        result = {'message_id': int(fields['message_id']) if method.startswith('editMessage') else len(fixture.requests), 'date': 123, 'chat': {'id': int(fields['chat_id']), 'type': 'private'}}
-                        if method in {'sendPhoto', 'sendDocument'}:
-                            from email.parser import BytesParser
-                            from email.policy import default
-                            message = BytesParser(policy=default).parsebytes(b'Content-Type: ' + self.headers['Content-Type'].encode() + b'\r\n\r\n' + body)
-                            file = next(p for p in message.iter_parts() if p.get_filename())
-                            payload = file.get_payload(decode=True)
-                            file_id = 'file_' + str(len(fixture.files))
-                            fixture.files[file_id] = payload
-                            metadata = {'file_id': file_id, 'file_unique_id': file_id, 'file_size': len(payload)}
-                            if method == 'sendPhoto':
-                                metadata.update(width=64, height=64)
-                                result['photo'] = [metadata]
-                            else:
-                                result['document'] = metadata
-                    encoded = json.dumps({'ok': True, 'result': result}).encode()
-                self.send_response(status)
-                self.send_header('Content-Type', 'application/json')
-                self.end_headers()
-                self.wfile.write(encoded)
-        self.server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
-        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
-        self.thread.start()
-        self.base = 'http://127.0.0.1:' + str(self.server.server_port)
-        self.transport = urllib.request.build_opener(urllib.request.ProxyHandler({}))
-
-    def open(self, request, timeout):
-        if isinstance(request, str):
-            url = self.base + '/file/' + request.rsplit('/', 1)[-1]
-            local = urllib.request.Request(url)
-        else:
-            local = urllib.request.Request(self.base + '/' + request.full_url.rsplit('/', 1)[-1], data=request.data, headers=dict(request.header_items()))
-        return self.transport.open(local, timeout=timeout)
-
-    def close(self):
-        self.server.shutdown()
-        self.server.server_close()
-        self.thread.join()
-
-
-class FakeMTProto:
-    def __init__(self, entity=None, fail_history=False):
-        self.entity = entity or User(id=42, first_name='Alice <&>', username='alice', access_hash=987654, phone='5551234')
-        self.fail_history = fail_history
-        self.calls = []
-        self.history_offsets = []
-        self.session = SimpleNamespace(close=lambda: None)
-        self.disconnected = False
-
-    async def get_input_entity(self, value):
-        self.calls.append(value)
-        if isinstance(self.entity, Channel):
-            return InputPeerChannel(self.entity.id, self.entity.access_hash)
-        if isinstance(self.entity, Chat):
-            return InputPeerChat(self.entity.id)
-        return InputPeerUser(self.entity.id, self.entity.access_hash)
-
-    async def get_entity(self, peer):
-        return self.entity
-
-    async def __call__(self, request):
-        self.calls.append(request)
-        if isinstance(request, (GetFullUserRequest, GetFullChannelRequest, GetFullChatRequest)):
-            from telethon.tl import types
-            if isinstance(request, GetFullUserRequest):
-                full = types.UserFull(id=self.entity.id, settings=types.PeerSettings(), notify_settings=types.PeerNotifySettings(), common_chats_count=0, about='Source <&>\n``` unsafe fence')
-                return types.users.UserFull(full_user=full, chats=[], users=[self.entity])
-            if isinstance(request, GetFullChannelRequest):
-                full = types.ChannelFull(id=self.entity.id, about='', read_inbox_max_id=0, read_outbox_max_id=0, unread_count=0, chat_photo=types.PhotoEmpty(id=1), notify_settings=types.PeerNotifySettings(), bot_info=[], pts=0)
-                return types.messages.ChatFull(full_chat=full, chats=[self.entity], users=[])
-            full = types.ChatFull(id=self.entity.id, about='', participants=types.ChatParticipants(chat_id=self.entity.id, participants=[], version=1), notify_settings=types.PeerNotifySettings())
-            return types.messages.ChatFull(full_chat=full, chats=[self.entity], users=[])
-        if isinstance(request, GetHistoryRequest):
-            self.history_offsets.append(request.offset_id)
-            if self.fail_history:
-                raise errors.BotMethodInvalidError(request)
-            messages = [Message(id=5, peer_id=PeerUser(42), message='First <&>'), Message(id=4, peer_id=PeerUser(42), message='Second')] if request.offset_id == 0 else []
-            return SimpleNamespace(messages=messages, count=2)
-        if isinstance(request, GetUserPhotosRequest):
-            return SimpleNamespace(photos=[], count=0)
-        if isinstance(request, GetParticipantsRequest):
-            participants = [ChannelParticipant(user_id=1, date=None), ChannelParticipant(user_id=2, date=None)] if request.offset == 0 else []
-            return SimpleNamespace(participants=participants, count=2)
-        from telethon.tl import types
-        from telethon.tl.functions import users, payments, premium, channels
-        if isinstance(request, users.GetSavedMusicRequest):
-            return types.users.SavedMusic(count=0, documents=[])
-        if isinstance(request, payments.GetSavedStarGiftsRequest):
-            return types.payments.SavedStarGifts(count=0, gifts=[], chats=[], users=[])
-        if isinstance(request, payments.GetStarGiftsRequest):
-            return types.payments.StarGifts(hash=0, gifts=[], chats=[], users=[])
-        if isinstance(request, premium.GetBoostsStatusRequest):
-            return types.premium.BoostsStatus(level=0, current_level_boosts=0, boosts=0, boost_url='https://t.me/boost/fixture')
-        if isinstance(request, premium.GetBoostsListRequest):
-            return types.premium.BoostsList(count=0, boosts=[], users=[])
-        if isinstance(request, channels.GetParticipantRequest):
-            return types.channels.ChannelParticipant(participant=types.ChannelParticipantSelf(user_id=777, inviter_id=42, date=None), chats=[], users=[])
-        raise AssertionError(type(request))
-
-    async def get_messages(self, peer, ids):
-        return [Message(id=i, peer_id=PeerUser(42), message='by id') if i != 999 else None for i in ids]
-
-    async def download_profile_photo(self, peer, file):
-        return None
-
-    async def disconnect(self):
-        self.disconnected = True
-
-
 class SimpleTL:
     def __init__(self, value):
         self.value = value
diff --git a/tests/test_workflow_privacy.py b/tests/test_workflow_privacy.py
index ef3c721..92ad0d2 100644
--- a/tests/test_workflow_privacy.py
+++ b/tests/test_workflow_privacy.py
@@ -15,7 +15,7 @@
 from cryptography.hazmat.primitives import serialization
 from cryptography.hazmat.primitives.asymmetric import rsa
 
-from test_ic import FakeMTProto, TelegramFixture
+from fixtures import FakeMTProto, TelegramFixture
 from bot_api import BotClient, diagnostico_excecao
 from workflow import decrypt_request, main
 
diff --git a/tgcloud/handlers/callback_query.js b/tgcloud/handlers/callback_query.js
index 08574c2..b0f0c8f 100644
--- a/tgcloud/handlers/callback_query.js
+++ b/tgcloud/handlers/callback_query.js
@@ -13,8 +13,6 @@ export default async function (callback, ctx) {
     return;
   }
   if (!await reservarAtualizacao(ctx?.update?.update_id)) return;
-export default async function (callback) {
-  const chat = callback.message?.chat ?? callback.from;
   const messageId = callback.message?.message_id;
   const pedido = lerCallback(callback.data);
   const completo = pedido.acao === 'f';
@@ -31,7 +29,6 @@ export default async function (callback) {
   } catch (erro) {
     console.error('falha ao processar callback:', diagnosticoErro(erro));
     await enviarMensagem(chat.id, '<b>Falha no processamento.</b>');
-    await enviarMensagem(chat.id, '<b>Processamento concluído.</b>');
   }
 }
 
diff --git a/tgcloud/handlers/inline_query.js b/tgcloud/handlers/inline_query.js
index 2539c91..256614c 100644
--- a/tgcloud/handlers/inline_query.js
+++ b/tgcloud/handlers/inline_query.js
@@ -1,14 +1,4 @@
 import { api } from 'sdk';
 export default async function (query) {
   await api.answerInlineQuery({ inline_query_id: query.id, results: [], cache_time: 0, is_personal: true, button: { text: 'Consultar no privado', start_parameter: 'help' } });
-  const texto = (query.query || '').trim();
-  let resposta;
-  try {
-    resposta = await consultar(texto, { canal: 'inline', chatId: query.from?.id });
-  } catch (e) {
-    console.error('falha ao montar a resposta inline:', diagnosticoErro(e));
-    resposta = relatorioErro(e);
-  }
-  await responderInline(query.id, resposta.titulo, resposta.html, resposta.botaoPrivado);
 }
-
diff --git a/tgcloud/handlers/message.js b/tgcloud/handlers/message.js
index 9b86d9c..7f67250 100644
--- a/tgcloud/handlers/message.js
+++ b/tgcloud/handlers/message.js
@@ -11,7 +11,6 @@ function esc(valor) {
 
 function reduzir(valor, limite = 160) {
   return String(valor).slice(0, limite);
-  return String(valor);
 }
 
 function referencia(objeto, origem, tipo = 'usuario') {
@@ -70,7 +69,6 @@ function adicionarDadosCompartilhados(resposta, dados) {
 export default async function (message, ctx) {
   if (!autorizado(message.from?.id, message.chat?.id)) return;
   if (!await reservarAtualizacao(ctx?.update?.update_id)) return;
-export default async function (message) {
   let resposta;
   try {
     const compartilhamento = referenciaCompartilhada(message);
diff --git a/tgcloud/lib/despacho.js b/tgcloud/lib/despacho.js
index 4a3797e..1b1697e 100644
--- a/tgcloud/lib/despacho.js
+++ b/tgcloud/lib/despacho.js
@@ -15,32 +15,6 @@ export async function dispararBusca(entrada, chatId, mensagemId, modo = 'complet
     const erro = new Error('O GitHub não aceitou a execução.');
     erro.origin = 'github'; erro.status = resposta.status; erro.publicMessage = erro.message;
     throw erro;
-import { GH_DISPATCH_TOKEN, GH_REPOSITORY } from './segredos.js';
-
-export async function dispararBusca(entrada, chatId, mensagemId, modo = "completo", origemId = "") {
-  let resposta;
-  for (let tentativa = 0; tentativa < 3; tentativa++) {
-    try {
-      resposta = await fetch(`https://api.github.com/repos/${GH_REPOSITORY}/actions/workflows/resolver.yml/dispatches`, {
-        method: 'POST',
-        headers: {
-          Authorization: `Bearer ${GH_DISPATCH_TOKEN}`,
-          Accept: 'application/vnd.github+json',
-          'X-GitHub-Api-Version': '2026-03-10',
-          'User-Agent': 'infocard-bot',
-        },
-        body: fetch.body.json({ ref: 'main', inputs: {
-          alvo: String(entrada.username ?? entrada.id ?? ''),
-          expected_id: entrada.tipo === 'referencia' ? entrada.id : '',
-          chat: String(chatId ?? ''), message_id: String(mensagemId ?? ''),
-          modo, origem_id: String(origemId ?? ''),
-        } }),
-      });
-      if (resposta.status >= 200 && resposta.status < 300) return resposta;
-      console.error('GitHub dispatch:', resposta.status, await resposta.text());
-    } catch (erro) {
-      console.error('GitHub dispatch:', erro);
-    }
   }
   return resposta;
 }
diff --git a/tgcloud/lib/entrada.js b/tgcloud/lib/entrada.js
index 8433a17..00e7003 100644
--- a/tgcloud/lib/entrada.js
+++ b/tgcloud/lib/entrada.js
@@ -8,8 +8,6 @@ function validarUsername(value) {
 }
 function referencia(id, username) {
   return { tipo: 'referencia', id: validarId(id), username: validarUsername(username), rotulo: id + ' @' + username };
-function referencia(id, username) {
-  return { tipo: 'referencia', id, username, rotulo: id + ' @' + username };
 }
 function usuario(username) {
   return { tipo: 'username', username: validarUsername(username), rotulo: '@' + username };
@@ -22,9 +20,6 @@ export function lerEntrada(texto) {
   const par = /^(-?[1-9]\d{0,15})\s+@([A-Za-z][A-Za-z0-9_]{3,31})$/.exec(valor);
   if (par) return referencia(par[1], par[2]);
   if (/^-?\d+$/.test(valor)) return numerico(valor);
-  const par = /^(\S+)\s+@(.*)$/.exec(valor);
-  if (par) return referencia(par[1], par[2]);
-  if (/^[+-]?\d+$/.test(valor)) return numerico(valor);
   return usuario(valor.replace(/^@/, ''));
 }
 export function codigoCallback(acao, entrada) {
@@ -33,9 +28,6 @@ export function codigoCallback(acao, entrada) {
   // All permitted characters are ASCII, so length equals UTF-8 bytes.
   if (value.length > 64) throw new Error('Callback excede 64 bytes.');
   return value;
-  if (entrada?.tipo === 'referencia') return acao + ':u:' + entrada.id + ':' + entrada.username;
-  if (entrada?.tipo === 'id') return acao + ':i:' + entrada.id;
-  return acao + ':n:' + String(entrada?.username ?? '');
 }
 export function lerCallback(dados) {
   const match = /^([rf]):([uin]):(.*)$/.exec(String(dados ?? ''));
@@ -47,8 +39,4 @@ export function lerCallback(dados) {
     return { acao, entrada: referencia(...parts) };
   }
   return { acao, entrada: tipo === 'i' ? numerico(value) : usuario(value) };
-  const [acao = 'r', tipo, ...partes] = String(dados ?? '').split(':');
-  if (tipo === 'u') return { acao, entrada: referencia(partes.shift() ?? '', partes.join(':')) };
-  if (tipo === 'i') return { acao, entrada: numerico(partes.join(':')) };
-  return { acao, entrada: usuario(tipo === 'n' ? partes.join(':') : String(dados ?? '')) };
 }
diff --git a/tgcloud/lib/envio.js b/tgcloud/lib/envio.js
index a8c9054..359cb07 100644
--- a/tgcloud/lib/envio.js
+++ b/tgcloud/lib/envio.js
@@ -38,21 +38,4 @@ export function enviarCartao(chatId, richHtml) {
 }
 export function editarCartao(chatId, messageId, richHtml) {
   return api.editMessageText({ chat_id: chatId, message_id: messageId, text: plainCard(richHtml) });
-export async function enviarCartao(chatId, richHtml) {
-  try {
-    return await api.sendRichMessage({ chat_id: chatId, rich_message: { html: richHtml } });
-  } catch (erro) {
-    console.error('sendRichMessage:', diagnosticoErro(erro));
-    return api.sendMessage({ chat_id: chatId, text: richHtml.replace(/<[^>]*>/g, '') });
-  }
 }
-
-export async function editarCartao(chatId, messageId, richHtml) {
-  try {
-    return await api.editMessageText({ chat_id: chatId, message_id: messageId, rich_message: { html: richHtml } });
-  } catch (erro) {
-    console.error('editMessageText:', diagnosticoErro(erro));
-    return api.sendMessage({ chat_id: chatId, text: richHtml.replace(/<[^>]*>/g, '') });
-  }
-}
-
diff --git a/tgcloud/lib/erros.js b/tgcloud/lib/erros.js
index f372444..8c6231e 100644
--- a/tgcloud/lib/erros.js
+++ b/tgcloud/lib/erros.js
@@ -4,28 +4,6 @@ export function diagnosticoErro(erro) {
   if (erro instanceof BotApiError) return { origin: 'telegram', error_code: erro.code };
   if (erro?.origin === 'github') return { origin: 'github', status: erro.status };
   return { origin: 'runtime', type: 'OperationError' };
-
-export function textoSeguro(valor) {
-  return String(valor ?? '');
-}
-
-export function diagnosticoErro(erro) {
-  if (erro instanceof BotApiError) {
-    const parametros = erro.parameters ?? {};
-    return {
-      origin: 'telegram', method: erro.method, error_code: erro.code,
-      description: textoSeguro(erro.description),
-      parameters: parametros,
-    };
-  }
-  if (erro?.origin === 'github') {
-    return { origin: 'github', status: erro.status, description: textoSeguro(erro.publicMessage),
-      message: textoSeguro(erro.githubMessage) };
-  }
-  const linhas = typeof erro?.stack === 'string' ? erro.stack.split('\n') : [];
-  const locais = linhas.filter(linha => /^\s*at\s/.test(linha) || /^[^\s@]+@.+:\d+/.test(linha))
-    .map(textoSeguro);
-  return { origin: 'runtime', type: erro?.name ?? 'Error', message: textoSeguro(erro?.message ?? erro), stack: locais };
 }
 
 export function mensagemErro(erro) {
@@ -33,10 +11,4 @@ export function mensagemErro(erro) {
   if (dados.origin === 'telegram') return `O Telegram recusou a operação (código ${dados.error_code}).`;
   if (dados.origin === 'github') return `A execução não foi aceita (HTTP ${dados.status}).`;
   return 'Não foi possível concluir a solicitação.';
-  if (dados.origin === 'telegram') {
-    return `Telegram ${dados.error_code}: ${dados.description}`;
-  }
-  if (dados.origin === 'github') return [dados.description, dados.message].filter(Boolean).join(' ');
-  return textoSeguro(erro?.stack ?? erro?.message ?? erro);
 }
-
diff --git a/tgcloud/lib/limite.js b/tgcloud/lib/limite.js
index bb1c60c..5cf41cc 100644
--- a/tgcloud/lib/limite.js
+++ b/tgcloud/lib/limite.js
@@ -16,8 +16,3 @@ export async function reservarDisparo(chatId) {
     { ':chat': Number(chatId), ':now': now, ':cutoff': now - 30000 });
   return { permitido: rows.length === 1, id: rows[0]?.id ?? null };
 }
-export async function reservarDisparo() {
-  return { permitido: true, id: null };
-}
-
-export async function liberarDisparo() {}
diff --git a/tgcloud/lib/relatorio.js b/tgcloud/lib/relatorio.js
index a4a4c6f..69be883 100644
--- a/tgcloud/lib/relatorio.js
+++ b/tgcloud/lib/relatorio.js
@@ -75,7 +75,6 @@ export function relatorioErro() {
   return {
     titulo: 'Concluído',
     html: '<b>Falha no processamento.</b>',
-    html: '<b>Processamento concluído.</b>',
   };
 }
````
