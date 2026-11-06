# Evolução prática de execução — 12 commits (04–06/11/2026)

**Repositório:** morfalespi/IC · **referência analisada:** 6a4eb788069055c48f0829580c32d64367ca0455 (main) · **base da sequência:** b7e59b14148f3cd57352f44b7b2661155054fffc. 

## 1. Escopo e método de verificação

Foram analisados os 12 commits mais recentes retornados pelo histórico do GitHub, do commit aeef5957 ao merge 6a4eb788, em ordem cronológica; os estados completos de cada commit foram obtidos, além do estado-base b7e59b14 e do primeiro pai 1d3433a5 do merge c9195d12. Este último é essencial para explicar a incorporação real à main. O inventário, a prova de leitura por blob e as exclusões do escopo estão em **docs/leitura-integral-12-commits.md**. As partes não detalhadas nesta narrativa estão em **docs/complemento-omissoes-12-commits.md**.

**Classes de evidência:** (1) conteúdo do arquivo/versionamento; (2) consequência determinística da ramificação do código; (3) registro de job real no GitHub Actions; (4) verificação externa de entrega. As classes 1–3 foram consultadas; **não foi realizado um teste próprio de ponta a ponta, nem foi verificado o conteúdo que apareceu no chat Telegram do destinatário**. Um job verde não é sinônimo de coleta completa, envio confirmado ou arquivo íntegro.

**Resultado geral:** os commits intermediários evoluíram positivamente no diagnóstico de falhas, validação do protocolo, identidade e integridade. O commit 7d718b31 reverteu deliberadamente muitas dessas garantias; 6a4eb788 o incorporou. Assim, o resultado final oferece maior permissividade e menos barreiras locais, mas **piora substancialmente a confiabilidade do estado de sucesso, o controle de repetição, a proteção dos dados exportados e a integridade da entrega**. É uma avaliação da semântica implementada e da evidência disponível, não uma suposição de falha de toda consulta.

## 2. Os 12 commits — mudança e efeito prático

| Ordem | Commit e tipo | Evolução observada | Efeito de execução e julgamento |
|---:|---|---|---|
| 1 | [aeef5957](https://github.com/morfalespi/IC/commit/aeef5957d13d5c2893d23d066401750e21a59568) — alteração | Introduz camada Bot API, diagnósticos estruturados, proteção de mensagens e revisão de contratos Telegram/Telethon. Altera resolução MTProto, workflow e validação. | **Positivo:** resultado remoto e erro passam a ter rotas explícitas. **Limite:** ainda dependia da cobertura dos cenários e das permissões da API. |
| 2 | [e37cf3d0](https://github.com/morfalespi/IC/commit/e37cf3d076afd44bc07ed9ce8d01245abaae11e8) — alteração | Preserva diagnóstico do GitHub no caminho do dispatch e documenta resultados de validação. | **Positivo:** falhas HTTP passam a conservar origem e motivo em vez de se confundirem com resposta do Telegram. |
| 3 | [c7b1644a](https://github.com/morfalespi/IC/commit/c7b1644a706bdd359a7617a6475499255e0f4f5d) — alteração | Retira capturas silenciosas, reenvios não autorizados por fallback e parte dos caminhos que aparentavam sucesso sem execução. | **Positivo:** reduz falso positivo e duplicação de escritas. **Trade-off:** erros antes escondidos tornam-se visíveis, elevando a quantidade de jobs classificados como falha. |
| 4 | [8db7c084](https://github.com/morfalespi/IC/commit/8db7c084526a061246583e08b279269b48ea6634) — alteração | Elimina código inacessível ou baseado em peers presumidos e melhora a apresentação de erro; registra verificação. | **Positivo:** o resolvedor deixa de sugerir confiança em dados que não possui. Não garante resolução de ID sem acesso concedido pelo Telegram. |
| 5 | [9d3408c6](https://github.com/morfalespi/IC/commit/9d3408c6e85a7dc88bcdaf170f947d85c259c5e5) — alteração | Distingue resposta de erro GitHub não JSON de exceções inesperadas no dispatch. | **Positivo:** erro de parsing não substitui indevidamente a falha de HTTP; exceções não previstas deixam de ser mascaradas como resposta JSON inválida. |
| 6 | [4c1da31d](https://github.com/morfalespi/IC/commit/4c1da31da3f499be517a9cb2df1c078aba56526d) — alteração | Torna autenticação Bot API recusada fatal, impede confirmação com envelopes HTTP incoerentes e trata falhas MTProto de forma mais explícita. | **Positivo:** um 401 ou payload sem formato válido não deve ser contado como entrega ou coleta bem-sucedida. |
| 7 | [c7d45452](https://github.com/morfalespi/IC/commit/c7d454523d3c67efd8741db8ad449822c8423f8e) — alteração | Redação recursiva dos campos sigilosos, mensagens pendentes, sinais de notificação, tratamento de dry-run em deploy e correções da camada de transporte. | **Positivo:** reduz exposição em exportações, duplicatas e falsos sucessos. **Limite:** garantia de entrega ainda precisava de observação remota. |
| 8 | [03baeed9](https://github.com/morfalespi/IC/commit/03baeed97deb2adfd52dc0c3a37a1c8d6fef0af4) — alteração | Adiciona validação sintética com download e SHA-256 de arquivos, confere identidade de chat, prepara coleta/entrega e ajusta verificadores. | **Positivo:** estabelece critério verificável de bytes devolvidos; o recurso existe no código, mas não significa execução automática de todas as etapas em cada consulta. |
| 9 | [cb7c4807](https://github.com/morfalespi/IC/commit/cb7c48079b78af99076e8f50f42963266c1b52e7) — alteração | Corrige classificação de mensagens aceitas sem confirmação final e acrescenta prova documentada da sanitização de exportação. | **Positivo:** mensagens sem ID comprovado permanecem pendentes em vez de confirmadas. |
| 10 | [c9195d12](https://github.com/morfalespi/IC/commit/c9195d12547112745b8e091644b3586fccff9a2e) — merge PR #32 | Integra as alterações de validação na main. Comparado ao seu **primeiro pai** 1d3433a5, também remove README.md, AGENTS.md e SECURITY.md, altera workflows e agrega arquivos de Python. | **Misto:** o código de execução fica mais verificável, mas o repositório perde três documentos de orientação e segurança; o merge não é uma implementação independente de todos os commits internos. |
| 11 | [7d718b31](https://github.com/morfalespi/IC/commit/7d718b312249ea76bac4edc5ec07d8c3cdddf7e3) — alteração | Inverte políticas locais no resolver, bot, envio, exportação e workflow: elimina cotas, validações, limites, espera e controles de confirmação, autoriza repetição imediata, mantém mídia e valores sem redação. | **Negativo para verificabilidade e proteção:** mais tentativas são disparadas, mas operações inválidas também podem ser marcadas como concluídas. **Positivo restrito:** retira bloqueios locais para requisições que o provedor ainda poderá aceitar. |
| 12 | [6a4eb788](https://github.com/morfalespi/IC/commit/6a4eb788069055c48f0829580c32d64367ca0455) — merge PR #34 | Incorpora 7d718b31 na main; a árvore resultante é idêntica à árvore daquele commit de origem. | **Sem nova alteração semântica além do merge**; operacionalmente a política permissiva passa à main e é publicada no deploy que consta como sucesso. |

O commit 6a4eb788 e o commit 7d718b31 não devem ser somados como dois conjuntos independentes de linhas modificadas. O mesmo cuidado vale para c9195d12, cujo primeiro pai difere do histórico do branch incorporado.

## 3. Como o fluxo mudou na prática

### 3.1 Entrada, callback e início da consulta

**Antes da reversão:** a camada **tgcloud/lib/entrada.js** rejeitava IDs fora da faixa, formatos não canônicos e callbacks incompatíveis; **tgcloud/handlers/callback_query.js** exigia chat privado e vinculava o autor ao chat; **tgcloud/lib/limite.js** reservava no banco até duas consultas por chat e seis globais em 60 segundos. **tgcloud/lib/consulta.js** propagava falhas de reserva, status de cartão e despacho.

**Na revisão final:** entrada deixa de aplicar essas verificações, o callback não confirma o autor, a função de limite é uma aprovação incondicional, e **consulta.js** não faz reserva. Consultas em grupo e inline podem seguir para o dispatch, conforme o handler e contexto. **Consequência:** maior superfície operacional e concorrência; menor capacidade de impedir consulta involuntária ou callback não correspondente.

### 3.2 Dispatch GitHub e duplicação

**Antes:** **tgcloud/lib/despacho.js** conferia configuração do repositório e token, enviava um dispatch e, para respostas não 200/204, gerava erro com status e mensagem saneada. Em 9d3408c6, erros não JSON preservavam explicitamente o status.

**Depois:** até **três POSTs imediatos**, captura de falhas de transporte e status em log, e retorno da última resposta sem lançamento obrigatório de erro quando as tentativas terminam sem aceitação. **Consequência:** diante de resposta remota ambígua, um dispatch já aceito pode ser repetido; o chamador pode exibir estado de solicitação sem comprovar que o workflow foi disparado. HTTP de erro não se torna sucesso do GitHub: a **semântica local** é que deixa de diferenciá-lo.

### 3.3 Bot API, erro de protocolo e identidade

**Antes:** **scripts/bot_api.py** validava envelopes JSON, coerência HTTP, autenticação 401, campos de Message/chat e valores de retry; o resolver validava **EXPECTED_ID** e correspondência do peer resolvido.

**Depois:** **bot_api.chamar** converte corpo não JSON em objeto local com **ok=true**, aceita corpos sem formato oficial e pode retornar resultado otimista, e **estado_mensagem** responde **confirmed** sempre. A resolução deixa **EXPECTED_ID** informativo e pode aceitar entidade alternativa retornada por fallback. **Consequência:** o relatório pode conter dados de um peer diferente do esperado e exibir entrega confirmada sem comprovação remota.

### 3.4 MTProto, reintentos e espera

A função **com_espera** deixou de aguardar especificamente **FloodWaitError** e passou a tentar operação **três vezes, imediatamente, em qualquer Exception**. As proteções de autenticação e pausas da revisão anterior foram removidas; o Telethon foi configurado com **flood_sleep_threshold=0**. Remover esperas não elimina FloodWait, indisponibilidade, timeout ou regras do Telegram. **Efeito previsível:** menor latência inicial em alguns casos e maior repetição sob falhas transitórias, inclusive as que não melhoram sem espera.

### 3.5 Legibilidade, exportação e limites

**Antes:** **scripts/ficha_completa.py** fragmentava páginas e documentos, **scripts/mtproto_export.py** dividia pacotes ZIP e aplicava limites; **scripts/exportacao.py** redigia campos de autenticação. **Depois:** uma página longa/um Markdown/um JSONL/um ZIP podem reunir a coleção inteira, sem limiares locais; conteúdos de chaves como access_hash podem ser exportados sem máscara. Escape HTML permanece, mas **escape não é truncamento, paginação nem confirmação de legibilidade**. O provedor continua impondo os próprios limites.

### 3.6 Entrega, sinalização de sucesso e dry-run

**Antes:** havia estado de Message **confirmed/pending/rejected**, checagem de documento recebido, download e conferência SHA-256 no teste sintético; a CI podia observar falha de API. **Depois:** **scripts/validar_entrega.py** apenas declara a confirmação e registra respostas; não redownload nem compara bytes; seu bloco externo de exceção termina com código zero. Em **scripts/resolver.py**, a função **aceitacao_mensagem** retorna true sem examinar a resposta, e o bloco externo **except** também chama **sys.exit(0)**. **scripts/notificar_falha.py** pode emitir texto de processamento concluído de maneira repetida. No deploy, dry-run não equivale mais à separação estrita de não publicação implementada antes da reversão.

## 4. Evidência de execução real no GitHub Actions

| Evidência consultada | O que se pode afirmar | O que NÃO comprova |
|---|---|---|
| [CI de 6a4eb788](https://github.com/morfalespi/IC/actions/runs/42238080549) | Checks terminam verdes nas duas matrizes Python/Node. | Que cada ramo de erro e toda API Telegram funcionam; que o conteúdo enviado é íntegro. |
| [Deploy de 6a4eb788](https://github.com/morfalespi/IC/actions/runs/42238080624) | Etapas de instalação, verificação, sincronização, migração, push e webhook terminam verdes. | Que cada operação futura de coleta ou entrega remota terá êxito. |
| [Healthcheck de 6a4eb788](https://github.com/morfalespi/IC/actions/runs/42238133744) | O dispatch de healthcheck foi aceito pelo workflow; o resolver foi pulado. | Leitura MTProto ou entrega de arquivo. |
| [Resolver real de 6a4eb788](https://github.com/morfalespi/IC/actions/runs/42238240333) | O passo **resolver.py** foi executado e terminou verde; há autenticação Telethon, tentativas de coleta, planejamento de páginas e arquivos e classificação local de conclusão. | Confirmação independente de Message, integridade por download/SHA-256 ou ausência de falhas parciais. |
| [Validação de APIs de 03baeed9](https://github.com/morfalespi/IC/actions/runs/42023095036) | A etapa **validar_apis.py** terminou verde na revisão que ainda testava identidade e redação. | Entrega de três arquivos a um destinatário. |
| [Três execuções anteriores em c9195d12](https://github.com/morfalespi/IC/actions/runs/42106712608), [segunda](https://github.com/morfalespi/IC/actions/runs/42106692706), [terceira](https://github.com/morfalespi/IC/actions/runs/42106526642) | O passo **resolver.py** terminou com falha nas três execuções, em contraste com o verde final. | Que o código final resolveu a causa remota; o critério de código de saída também mudou. |

**Observações verificadas no log do resolver final** (sem reproduzir identidades, respostas pessoais ou anexos):

1. O log registra **StickersetInvalidError** em coleta de stickers e **TimeoutError** em **GetFileRequest**. Portanto, não houve ausência total de erros de leitura.
2. O programa anuncia **100.833 campos exibidos**, **uma Rich Message planejada**, uma Rich Message dita aceita, além de um Markdown, um JSONL e um pacote de mídia ditos aceitos. Esses números são emitidos pela lógica local; não correspondem a contagem independente de campos legíveis recebidos.
3. O empacotamento Python gerou avisos de **nomes duplicados** em entradas ZIP (UserWarning: Duplicate name), risco de ambiguidade ao extrair ou inspecionar o pacote.
4. A saída de logs continha uma linha serializada muito grande (aproximadamente 3,62 milhões de caracteres). Isso confirma **volume elevado de dados registrados**, mas não autoriza republicá-los. A revisão final não executa a máscara local desses valores.
5. O passo posterior de notificação também aparece como sucesso. Não foi inspecionada uma confirmação externa do destinatário.

A melhora do **indicador de job verde** entre execuções anteriores e posteriores é **observável**; a melhora de **correção da operação real** não é demonstrada apenas por essa cor. Alterações que fazem exceções sair como código zero permitem o mesmo sintoma de job verde em cenários que deveriam ser classificados como falha.

## 5. Avaliação por característica

| Critério de execução | Tendência até cb7c4807 / merge c9195d12 | Estado após 7d718b31 / merge 6a4eb788 |
|---|---|---|
| Transparência do motivo de falha | **Melhora**: exceções e status preservados | **Regressão**: exceções podem terminar em zero e erros são contados como sucesso |
| Fidelidade da entidade | **Melhora**: identidade e expected_id confrontados | **Regressão**: validação retirada e fallback permissivo |
| Envio realmente confirmado | **Melhora**: Message e pendências diferenciados | **Regressão**: confirmação incondicional |
| Integridade de exportação | **Melhora**: teste sintético de download e hash disponível | **Regressão**: teste afirma sucesso sem conferir bytes |
| Proteção de dados | **Melhora**: redação e mascaramento | **Regressão**: exportação e logs podem preservar campos sigilosos |
| Legibilidade de grandes resultados | **Melhora**: divisão por partes | **Regressão**: página única desproporcional e ZIP único |
| Rapidez sem bloqueios locais | **Restrições intencionais** | **Melhora restrita**: menos barreiras e esperas; risco de spam/repetição |
| Controle de cargas | **Melhora**: cotas e pausas | **Regressão**: cotas retiradas, três tentativas imediatas |
| Facilidade de diagnosticar regressões | **Melhora**: falha exposta à CI | **Regressão**: testes de integração deixam de ter a mesma força semântica |

## 6. Conclusão técnica

A sequência **não é uma melhora linear**. Há uma evolução positiva demonstrável nas revisões intermediárias, seguida de reversão que aumenta permissividade e produz **declarações de sucesso mais fracas**. O caso real final comprova que o pipeline rodou, coletou dados e **tentou** produzir as saídas; não comprova a legibilidade no destinatário nem a integridade efetiva dos arquivos. A recomendação técnica para comparar qualidade é medir separadamente: identidade resolvida, operações MTProto tentadas/concluídas, erros e ausências, respostas do Bot API com Message verificável, partes previstas/confirmadas, hash do download e informação efetivamente entregue. Um único booleano de sucesso não é métrica suficiente.

**Referências primárias:** [comparação da base com main](https://github.com/morfalespi/IC/compare/b7e59b14148f3cd57352f44b7b2661155054fffc...6a4eb788069055c48f0829580c32d64367ca0455); [PR #32](https://github.com/morfalespi/IC/pull/32); [PR #34](https://github.com/morfalespi/IC/pull/34); paths de código e execuções indicados acima. A comparação entre pais de merge é feita a partir das árvores reais de cada pai.

## Autoria e responsabilidade pela aplicação

- **Autor da análise, redação, seleção das evidências e conclusões deste relatório:** ChatGPT (GPT-6).
- **Responsável pelas decisões editoriais e pela execução integral da tarefa:** ChatGPT (GPT-6). A elaboração e aplicação do texto foram executadas sem solicitar decisões editoriais ao usuário.
- **Responsável pela criação e publicação dos arquivos no repositório:** ChatGPT (GPT-6), por meio da integração GitHub.
- **Metadados nativos do Git:** os campos `author` e `committer` dos commits feitos pela integração aparecem sob a conta autenticada (`morfalespi`); essa identificação técnica é distinta da atribuição da elaboração e aplicação acima.
