# Verificação complementar — cobertura lida e fidelidade da análise dos 12 commits

**Repositório:** `morfalespi/IC`  
**Corpus histórico fixado:** [`b7e59b14` (base)](https://github.com/morfalespi/IC/tree/b7e59b14148f3cd57352f44b7b2661155054fffc), 12 commits de [`aeef5957`](https://github.com/morfalespi/IC/commit/aeef5957d13d5c2893d23d066401750e21a59568) a [`6a4eb788`](https://github.com/morfalespi/IC/commit/6a4eb788069055c48f0829580c32d64367ca0455) e pai complementar [`1d3433a5`](https://github.com/morfalespi/IC/tree/1d3433a5c2cc7eb73fd6d9294b08eced23cb2fab).  
**Verificação complementar:** 2026-11-07.  
**Responsável pela consulta, conferência e redação deste relatório:** ChatGPT (GPT-6), utilizando as ferramentas da integração GitHub nesta conversa.

Este relatório é uma **segunda conferência material**, não uma declaração de certeza sem testes. Liga cada métrica a um conjunto verificável de objetos Git e separa o que foi efetivamente recuperado, o que foi examinado semanticamente e o que não foi comprovado por execução de ponta a ponta.

## 1. Conferência independente do inventário histórico

Foram consultadas novamente as **14 árvores Git completas** com `GET /repos/morfalespi/IC/git/trees/{commit}?recursive=1`, mediante a ferramenta GitHub. Em nenhuma resposta a propriedade `truncated` estava ativada. Cada árvore foi comparada com a tabela de estados e o manifesto do arquivo [leitura-integral-12-commits.md](leitura-integral-12-commits.md).

| Item conferido | Resultado desta verificação |
|---|---:|
| Commits solicitados no corpus | 12 de 12 |
| Estados adicionais B00 e P10 | 2 de 2 |
| Árvores completas obtidas | 14 de 14 |
| Referências a blobs nas árvores, incluindo repetidos | 585 |
| Blobs distintos por SHA | 129 |
| Caminhos distintos nas árvores | 48 |
| Bytes totais dos conteúdos distintos | 1.838.421 |
| Versões de código/configuração (py, js, sh, yaml/yml, json/jsonc, txt) | 103 |
| Bytes distintos de código/configuração | 1.422.687 |
| Divergências de caminho, tamanho, presença ou snapshots frente às 129 linhas do manifesto | **0** |
| Divergências de quantidade ou soma de bytes entre as 14 árvores e a tabela de estados | **0** |

**Segunda recuperação integral:** os **129 blobs foram recuperados novamente pelo conteúdo inteiro**, e o tamanho UTF-8 de cada resposta foi calculado e comparado ao campo `size` da árvore Git. Todas as **129 verificações** corresponderam; nenhuma consulta individual reportou erro ou truncamento.

A contagem por lotes de índices do manifesto documenta a segunda passagem, inclusive os bytes conferidos:

| Índices do manifesto | Blobs completos | Bytes conferidos | Divergências |
|---|---:|---:|---:|
| 001–016 | 16 | 42.689 | 0 |
| 017–032 | 16 | 296.174 | 0 |
| 033–048 | 16 | 162.980 | 0 |
| 049–064 | 16 | 38.991 | 0 |
| 065–080 | 16 | 1.199.293 | 0 |
| 081–096 | 16 | 29.727 | 0 |
| 097–112 | 16 | 40.190 | 0 |
| 113–129 | 17 | 28.377 | 0 |
| **Total** | **129** | **1.838.421** | **0** |

**O que esta cobertura significa:** recuperação de todos os bytes dos arquivos de texto identificados nos estados especificados, conferência de tamanho, organização por SHA e verificação de presença nas árvores. **O que ela não significa:** recálculo independente do SHA-1 Git, demonstração formal de compreensão de todas as linhas, cobertura de todos os ramos por teste ou acesso a dados externos não presentes no repositório.

## 2. Fidelidade da sequência de commits e merges

Os 14 objetos commit foram consultados para conferir SHA, `tree.sha` e `parents`. As 12 respostas do endpoint de commits também foram verificadas quanto aos arquivos alterados; nenhum resumo de arquivos retornou indicação de limite de 300.

- **C01–C09:** a sequência de pais corresponde à ordem cronológica descrita no relatório principal.
- **C10 — merge [`c9195d12`](https://github.com/morfalespi/IC/commit/c9195d12547112745b8e091644b3586fccff9a2e):** pais `1d3433a5` e `cb7c4807`. O comparativo com o **primeiro pai** confirma a remoção de `AGENTS.md`, `README.md` e `SECURITY.md`.
- **C11 — [`7d718b31`](https://github.com/morfalespi/IC/commit/7d718b312249ea76bac4edc5ec07d8c3cdddf7e3):** contém alterações funcionais nos módulos de consulta, resposta, exportação, limites, workflows e apresentação.
- **C12 — merge [`6a4eb788`](https://github.com/morfalespi/IC/commit/6a4eb788069055c48f0829580c32d64367ca0455):** pais `c9195d12` e `7d718b31`. Sua árvore é **idêntica** à de C11, com SHA `b3977e510ebf023115a472645992ba594b35000d`. O merge não constitui um segundo conjunto independente de alterações semânticas.

As comparações de arquivos confirmam que os commits posteriores ao corpus analisado, até o commit de documentação [`9753940f`](https://github.com/morfalespi/IC/commit/9753940ffdb545ca42bf6a838f37e42f4a27031f), alteraram **somente os quatro documentos então criados** na pasta `docs/`. A análise da execução continua fixada na árvore de C12; não mistura tais revisões documentais com mudanças de runtime.

## 3. Correspondência de conclusões com trechos de código

A tabela abaixo confirma os mecanismos de maior impacto usados na conclusão do [relatório principal](evolucao-pratica-12-commits.md), por comparação do código intermediário C09 com C11/C12.

| Alegação operacional verificada | Evidência direta no código | Resultado |
|---|---|---|
| Mensagem deixou de exigir `Message` válido | [`scripts/bot_api.py` C09, `estado_mensagem`](https://github.com/morfalespi/IC/blob/cb7c48079b78af99076e8f50f42963266c1b52e7/scripts/bot_api.py#L136-L164) valida ID, chat e data; [C11, mesma função](https://github.com/morfalespi/IC/blob/7d718b312249ea76bac4edc5ec07d8c3cdddf7e3/scripts/bot_api.py#L68-L69) devolve `confirmed` incondicionalmente | **Confirmada** |
| Resposta Bot API fora do protocolo pode ser aceita localmente | [`chamar` C11](https://github.com/morfalespi/IC/blob/7d718b312249ea76bac4edc5ec07d8c3cdddf7e3/scripts/bot_api.py#L31-L54) transforma resposta não JSON em `{"ok": true, ...}` | **Confirmada** |
| Aceitação de mensagem no resolver tornou-se incondicional | [`aceitacao_mensagem` C09](https://github.com/morfalespi/IC/blob/cb7c48079b78af99076e8f50f42963266c1b52e7/scripts/resolver.py#L107-L114) examina estado; [C11](https://github.com/morfalespi/IC/blob/7d718b312249ea76bac4edc5ec07d8c3cdddf7e3/scripts/resolver.py#L102-L103) devolve `True` | **Confirmada** |
| Espera por `FloodWaitError` substituída por até três tentativas imediatas | [`com_espera` C09](https://github.com/morfalespi/IC/blob/cb7c48079b78af99076e8f50f42963266c1b52e7/scripts/resolver.py#L1646-L1652) utiliza `asyncio.sleep`; [C11](https://github.com/morfalespi/IC/blob/7d718b312249ea76bac4edc5ec07d8c3cdddf7e3/scripts/resolver.py#L1584-L1590) tenta novamente sem espera | **Confirmada** |
| Verificação de identidade esperada deixou de ser obrigatória | [`resolver.py` C09](https://github.com/morfalespi/IC/blob/cb7c48079b78af99076e8f50f42963266c1b52e7/scripts/resolver.py#L1757-L1760) compara `EXPECTED_ID`; [`resolver.py` C11](https://github.com/morfalespi/IC/blob/7d718b312249ea76bac4edc5ec07d8c3cdddf7e3/scripts/resolver.py#L1433-L1434) escolhe primeiro elemento em `entidade_de`, sem a mesma correspondência | **Confirmada a retirada das verificações descritas** |
| Exportação deixou de redigir campos sensíveis | [`exportacao.py` C09](https://github.com/morfalespi/IC/blob/cb7c48079b78af99076e8f50f42963266c1b52e7/scripts/exportacao.py#L7-L30) contém lista de campos e redação; [C11](https://github.com/morfalespi/IC/blob/7d718b312249ea76bac4edc5ec07d8c3cdddf7e3/scripts/exportacao.py#L1-L25) mantém valores originais | **Confirmada** |
| Teste sintético perdeu o download e confronto de SHA-256 | [`validar_entrega.py` C09](https://github.com/morfalespi/IC/blob/cb7c48079b78af99076e8f50f42963266c1b52e7/scripts/validar_entrega.py#L17-L29) confere `downloaded` e hash; [C11](https://github.com/morfalespi/IC/blob/7d718b312249ea76bac4edc5ec07d8c3cdddf7e3/scripts/validar_entrega.py#L16-L17) apenas imprime o estado | **Confirmada** |
| Erro externo do resolver pode gerar código de saída zero | [`resolver.py` C11, bloco final](https://github.com/morfalespi/IC/blob/7d718b312249ea76bac4edc5ec07d8c3cdddf7e3/scripts/resolver.py#L2455-L2459) executa `sys.exit(0)` após `except Exception` | **Confirmada** |
| Retirado controle local de limite | [`tgcloud/lib/limite.js` C11](https://github.com/morfalespi/IC/blob/7d718b312249ea76bac4edc5ec07d8c3cdddf7e3/tgcloud/lib/limite.js) devolve `{permitido: true}`; [`consulta.js` C11](https://github.com/morfalespi/IC/blob/7d718b312249ea76bac4edc5ec07d8c3cdddf7e3/tgcloud/lib/consulta.js) não reserva limite | **Confirmada** |
| Dispatch pode ser repetido e ausência de HTTP 2xx não gera erro obrigatório | [`tgcloud/lib/despacho.js` C11](https://github.com/morfalespi/IC/blob/7d718b312249ea76bac4edc5ec07d8c3cdddf7e3/tgcloud/lib/despacho.js#L4-L30) efetua até três chamadas e retorna última resposta | **Confirmada** |
| ZIP deixa de ser repartido por tamanho | [`mtproto_export.py` C11](https://github.com/morfalespi/IC/blob/7d718b312249ea76bac4edc5ec07d8c3cdddf7e3/scripts/mtproto_export.py#L6-L17) escreve um ZIP, embora receba parâmetros de limite sem aplicá-los | **Confirmada** |

**Juízo de fidelidade:** as alegações centrais sobre a reversão C11/C12 são compatíveis com os trechos de código verificados. As avaliações “positiva”, “negativa” e “regressão” descrevem consequências operacionais dessas alterações sob critérios explícitos de verificabilidade, proteção de dados, integridade e legibilidade; **não são porcentagens empíricas de melhora ou piora**. Nenhuma divergência factual foi encontrada nessas correspondências, mas a revisão semântica acima não equivale a um teste exaustivo de todos os ramos.

## 4. Rechecagem da evidência de execução

Foram reconsultados jobs e etapas de **oito execuções do GitHub Actions** mencionadas nos documentos:

| Execução | Resultado confirmado | Limite |
|---|---|---|
| [CI `42238080549`](https://github.com/morfalespi/IC/actions/runs/42238080549) | Duas matrizes de checks com sucesso | Não exerce todos os caminhos Telegram |
| [Deploy `42238080624`](https://github.com/morfalespi/IC/actions/runs/42238080624) | Job `deploy` com sucesso | Não confirma entregas posteriores |
| [Healthcheck `42238133744`](https://github.com/morfalespi/IC/actions/runs/42238133744) | Healthcheck com sucesso; passo `resolver.py` pulado | Não executou a coleta |
| [Resolver `42238240333`](https://github.com/morfalespi/IC/actions/runs/42238240333) | `resolver.py` com sucesso de job; log completo consultado novamente | Não prova recebimento independente |
| [Validação `42023095036`](https://github.com/morfalespi/IC/actions/runs/42023095036) | `validar_apis.py` concluiu com sucesso | A rotina `resolver.py` foi pulada |
| [Falhas anteriores `42106712608`](https://github.com/morfalespi/IC/actions/runs/42106712608), [`42106692706`](https://github.com/morfalespi/IC/actions/runs/42106692706), [`42106526642`](https://github.com/morfalespi/IC/actions/runs/42106526642) | Três jobs `resolver` com falha no passo de execução | Comparação de verde/vermelho não isola a causa |

O log do job `127961424951` (execução `42238240333`) foi recuperado integralmente nesta segunda passagem. Metadados calculados sobre o texto retornado:

| Observação no log | Valor |
|---|---:|
| Comprimento total do log recuperado, em caracteres | 3.659.021 |
| Linhas | 301 |
| Maior linha serializada | 3.624.528 caracteres |
| Ocorrências textuais de `StickersetInvalidError` | 30 (ocorrências da string, **não** 30 RPCs distintas) |
| Ocorrências textuais de `TimeoutError` | 2 |
| Avisos `UserWarning: Duplicate name` | 11 |
| Campos **reportados localmente** | 100.833 |
| Rich Messages **ditas aceitas** | 1/1 |
| Documento Markdown **dito aceito** | 7.668.026 bytes |
| Documento JSONL **dito aceito** | 10.333.626 bytes |
| Pacote de mídia **dito aceito** | 59.613.692 bytes |

Os resultados “aceito” e “concluído” são **saídas do programa**, não confirmações externas de integridade, visualização, recebimento ou completude. A decisão de não transcrever o conteúdo da linha de milhões de caracteres impede a reprodução pública de dados brutos de terceiros.

## 5. Proveniência, identidade Git e ambiente

- **Autenticação e commits:** os objetos Git publicados nesta conversa contêm `author` e `committer` associados a `morfalespi`. O executor que acionou `create_commit` e `update_ref` aqui foi ChatGPT (GPT-6), por meio da integração GitHub. Os resultados de ferramenta, não os campos `author`/`committer` isolados, dão suporte à descrição das operações neste diálogo.
- **Evento de auditoria apresentado:** `integration_installation.repositories_added`, integração declarada `ChatGPT Codex Connector`, documento `l7TWPSi9NqpgEzjYrkiOBQ`, registra a instalação/autorização do repositório naquele evento; não é um log de criação de commit individual.
- **Linux comprovado nos jobs, não no cliente do commit:** [`.github/workflows/resolver.yml`, C12, linha 57](https://github.com/morfalespi/IC/blob/6a4eb788069055c48f0829580c32d64367ca0455/.github/workflows/resolver.yml#L57) declara `runs-on: ubuntu-latest`, e o log de execução mostra o Python sob `/opt/hostedtoolcache/Python/3.12.16/...`. Isso identifica o ambiente de execução **do workflow**, mas não nomeia a máquina ou o sistema operacional que enviou a solicitação REST de criação do commit.
- **Retificação vinculada:** [retificacao-proveniencia-dos-commits.md](retificacao-proveniencia-dos-commits.md) distingue os três conjuntos de dados e corrige associações declaradas sem sustentação direta.

## 6. Conclusão: três coberturas que não devem ser confundidas

| Dimensão | Resultado | Estado |
|---|---|---|
| Inventário e recuperação material do corpus histórico | 14 árvores, 585 referências, 129/129 blobs, 1.838.421 bytes, sem divergência de manifesto ou tamanho | **Cobertura material concluída** |
| Fidelidade das afirmações técnicas principais | Conferência de 12 commits, pais/árvores, arquivos alterados, trechos C09/C11 e oito jobs; sem contradição encontrada nas proposições verificadas | **Conferência factual concluída para o conjunto de afirmações explicitado** |
| Execução real de todos os ramos, integridade de cada anexo no destino, aferição do ambiente do cliente REST | Não foi realizada verificação de ponta a ponta nem existe dado nativo Git suficiente para todas essas afirmações | **Não comprovada; não declarada como realizada** |

O trabalho nesta etapa encerra a **rechecagem de cobertura recuperada e a correspondência factual das afirmações principais**. Não declara “100% de sucesso do código”, “100% de compreensão semântica” nem prova independente de entrega. O [relatório de evolução](evolucao-pratica-12-commits.md), o [complemento das omissões](complemento-omissoes-12-commits.md) e o [manifesto integral](leitura-integral-12-commits.md) permanecem disponíveis como documentos de base, com ressalvas rastreáveis pela evidência e sem substituição silenciosa do histórico.
