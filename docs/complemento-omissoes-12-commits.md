# Complemento: conteúdo não exposto em detalhe no primeiro relatório

**Documento principal ao qual este complemento se refere:** [evolucao-pratica-12-commits.md](evolucao-pratica-12-commits.md). **Estado examinado:** main em 6a4eb788069055c48f0829580c32d64367ca0455. **Relação de todos os arquivos e versões lidas:** [leitura-integral-12-commits.md](leitura-integral-12-commits.md).

## 1. O que “omitido” significa neste contexto

O primeiro texto apresenta as mudanças com efeito operacional, seus ganhos, regressões e provas de execução. Não é uma transcrição de cada linha dos arquivos. Este segundo texto identifica **elementos efetivamente presentes no material lido que não foram individualizados no primeiro**, dá contexto aos caminhos adicionais e registra o que a evidência **não permite concluir**. Não se deve confundir (a) conteúdo recuperado e analisado mas não reproduzido, (b) comportamento observado nos logs, (c) teste não executado e (d) conteúdo não acessível. Também não se deve considerar a eliminação de um limite local como autorização ou superação de um limite remoto.

## 2. Inventário de componentes e detalhes que o primeiro texto resumiu ou não enumerou

| Código ou grupo | Detalhamento adicional que ficou fora da narrativa principal | Relevância para execução |
|---|---|---|
| **scripts/resolver.py** — identificação e resolução | **id_peer**, **input_usuario_bot**, **input_canal_bot**, **input_peer_canal_bot**, **resolver_id**, **resolver_alvo**, **entidade_de** e **completo** lidam com distinções User/Channel/Chat, referências de sessão e respostas distintas de Bot API e MTProto. A reversão retira a conferência do ID esperado e facilita fallback. | Um ID isolado pode não ser resolvido quando o servidor não dá acesso ao peer; aceitar um substituto sem comparar ID afeta a fidelidade. |
| **scripts/resolver.py** — leitura Bot API | **bot_api_leitura**, **coletar_bot_api**, **coletar_dados_participante_bot_api**, **coletar_estado_bot_no_chat**, **coletar_stickers_bot_api**, **coletar_catalogo_presentes_bot_api**, **coletar_presentes_bot_api**, **baixar_arquivo_bot_api** e **baixar_arquivos_bot_api** representam métodos e downloads distintos. | Um resultado positivo de um método não implica sucesso dos demais; autorização, retorno vazio, falha remota e falha de download precisam ser separados. |
| **scripts/resolver.py** — leitura MTProto | **coletar_stickers_mtproto**, **coletar_topicos_conhecidos_mtproto**, **coletar_catalogo_presentes_mtproto**, **coletar_boosts_mtproto**, **coletar_participacao_bot_mtproto**, **coletar_presentes_mtproto** e **coletar_historico_canal_pessoal** têm recursos e pré-condições distintos. | A presença desses caminhos no código não comprova disponibilidade universal; há erros concretos de stickers no job final. |
| **scripts/resolver.py** — mídia | **baixar_midia**, **registrar_midia**, **baixar_documentos_presente_mtproto**, **documentos_mtproto**, **objetos_mtproto** e funções de envio de documento controlam baixas, estados e apresentação de arquivos. | Há timeout concreto de GetFileRequest; tratar mídia planejada como integralmente entregue exige verificar cada download e cada arquivo remoto. |
| **scripts/resolver.py** — inventário e apresentação | **registros_telegram**, **secoes_completas_telegram**, **dados_basicos**, **agrupar_campos**, **valor_mtproto**, **campos_presentes**, **descricao_musica**, **descrever** e **status_ficha** convertem respostas em campos e páginas. | Número de propriedades mapeadas, tamanho serializado e quantidade realmente legível são grandezas diferentes. |
| **scripts/ficha_completa.py** | Além de **rich_pages** e **basic_pages**, contém **markdown_document**, **jsonl_files** e **markdown_files**. O código anterior usava fragmentação, expansão de células e páginas; o atual agrega sem teto local. | Uma saída gerada e marcada como aceita não significa que os limites do provedor comportaram toda a saída. |
| **scripts/mtproto_export.py** | O código antigo separava pacotes por bytes e registrava exceção quando lote excedia teto seguro; o atual cria um único ZIP de mídias com manifesto, sem limites locais. | O ZIP pode ser muito grande; nomes de entrada não únicos podem persistir, como os avisos vistos no job final. |
| **scripts/exportacao.py** | Mantém conversão de objetos, listas, bytes para base64 e datas para ISO, mas o último estado devolve strings originais e não filtra nomes de campos como access_hash. | Preserva fidelidade bruta de dados, incluindo valores que a versão anterior deliberadamente redigia; demanda proteção de logs e destino. |
| **scripts/telegram_ids.py** | Passou de checagens de intervalos e forma canônica para divisão entre IDs não negativos e negativos, sem a mesma validação anterior. | Facilita tentar peer não canônico; não muda as regras de resolução MTProto do servidor. |
| **scripts/mascarar_inputs.py** | A variante anterior imprimia comandos de máscara para entradas do workflow; a atual imprime o JSON de inputs do evento. | Potencial de divulgação nos logs, dependendo dos dados recebidos; o relatório principal não reproduz esses valores. |
| **scripts/notificar_falha.py** | Antes havia checagem de chat, ausência de BOT_TOKEN, marcador de autenticação recusada, notificação pendente e Message confirmado; hoje envia notificação de processamento concluído e devolve sucesso local. | Passar a notificar sempre pode criar alertas redundantes e não prova entrega da notificação. |
| **scripts/compatibility.py** e **scripts/validar_apis.py** | Verificações de compatibilidade de imports/assinaturas e, antes da reversão, comparação Bot API/MTProto, identidade do bot e redação de campos. | CI verde representa essas verificações no escopo daquele commit; o verificador final já não exige o mesmo conjunto de invariantes. |
| **scripts/validar_entrega.py** | A implementação intermediária validava chat, Message, download e SHA-256 de mensagem e três documentos sintéticos; a final imprime um status de sucesso sem recuperar os arquivos. | Trocar o critério faz o teste “passar” mais facilmente sem aumentar confirmação de bytes. |
| **tgcloud/handlers/message.js** | Interpreta mensagens e referências fornecidas via interface Telegram, inclusive formatos compartilhados; os callbacks e inline usam outros handlers. | Entrada compartilhada não equivale automaticamente à autorização para ler novos dados via outra API. |
| **tgcloud/handlers/inline_query.js** e **callback_query.js** | Inline pode iniciar consulta e o callback final ignora vinculação usuário–mensagem que era obrigatória. | Amplia locais em que a pesquisa se inicia e aumenta dependência das regras do Telegram e da aplicação. |
| **tgcloud/lib/cartao.js** e **relatorio.js** | Texto explicativo, estrutura visual, botões, mensagem de erro e recorte de rótulos afetam o que é comunicado ao solicitante. | A versão final de relatorio.js retira limites locais de recorte, podendo gerar texto excessivo ou induzir interpretação de conclusão. |
| **tgcloud/lib/envio.js** | Fallback para mensagem simples ou HTML após erro de rich message foi reintroduzido; no caminho final uma falha rica pode iniciar outra escrita. | O resultado visual pode ter formato distinto do solicitado e produzir duplicação em respostas ambíguas. |
| **tgcloud/lib/erros.js** | O diagnóstico final pode incluir descrição integral, stack e parâmetros, sem a mesma redação aplicada nas revisões intermediárias. | Melhora volume do diagnóstico bruto, mas amplia superfície de exposição em logs. |
| **tgcloud/lib/segredos.js**, **tgcloud/schema.js**, **tgcloud.jsonc**, **package.json**, **package-lock.json** e **scripts/resolver-requirements.txt** | São dependências/configurações presentes nas árvores. O arquivo de segredos versionado é módulo mínimo; o workflow injeta conteúdo privado durante o deploy. | O caminho de injeção e a separação entre fonte pública e secret devem ser mantidos na interpretação da execução; não foram extraídos segredos de Actions. |
| **.github/workflows/ci.yml**, **deploy.yml**, **resolver.yml** e **scripts/check.sh** | CI, publicação, healthcheck, validação, invocação real e notificação são fluxos diferentes. A mudança do dry-run e do tratamento de falha afeta o que o status de cada job significa. | Um verde na CI pode coexistir com erro remoto; a UI de Actions apresenta conclusão por etapas, não prova semântica de arquivos recebidos. |

## 3. Omissões específicas por compromisso de síntese

1. **Erros de toda coleta MTProto:** o primeiro texto não reproduz a mensagem de cada RPC individual, todo parâmetro e cada stack; limita-se a famílias de falha com impacto real observado. O inventário integral está no código versionado.
2. **Caminhos de paginação e estatísticas por peer:** diferenças entre método indisponível, paginação incompleta, total não oferecido e nenhum registro encontrado não foram listadas uma a uma. São condições distintas e não devem ser inferidas pela ausência de um campo.
3. **Armazenamento de mídia:** o histórico inclui tanto mídia temporária com exclusão final quanto conservação do diretório; os avisos de ZIP duplicado e os timeouts concretos foram incorporados ao principal, mas não se repetiu cada nome de mídia.
4. **Instruções e textos de segurança removidos pelo merge c9195d12:** **README.md**, **AGENTS.md** e **SECURITY.md** existiam no primeiro pai **1d3433a5**, foram eliminados no estado pós-merge e não aparecem no branch final. A consequência principal é de documentação, método e governança; os detalhes textuais dos documentos não foram transcritos.
5. **Histórico documental anterior:** docs/auditoria-operacional.md, docs/registro.md, docs/partners-mtproto-coverage.md, docs/inventario-peer-2026-11-03.md, docs/fontes-oficiais.md, docs/revisao-integracoes-2026-11-04.md, docs/launch-checklist.md, docs/tgcloud-sdk.md e docs/Serverless-OFFICIAL contêm especificações, decisões e evidências anteriores. São contexto histórico, não substitutos de comprovação do executável em cada commit.
6. **Métodos de configuração:** ações setup-node, setup-python, npm ci, pip install, migração e push foram observadas por status, mas não houve uma segunda execução com credenciais em ambiente controlado, pois os registros do próprio GitHub são a prova efetivamente disponível.
7. **Estatística de arquivos idênticos entre commits:** o primeiro relatório não repete versões byte-a-byte idênticas em cada revisão; elas são identificadas por SHA Git e pelas siglas de snapshot no terceiro arquivo.
8. **Atribuição e datas individuais de autores:** o primeiro relatório trata dos efeitos do código, não faz inferência de autoria intelectual ou intenção de pessoas a partir de mensagens de commit.
9. **Comparações de latência/throughput:** três tentativas imediatas e ausência de cotas podem mudar tempo e volume, mas nenhum benchmark comparável com carga idêntica foi executado. Não há ganho percentual comprovado.
10. **Diferenças de visibilidade nos canais:** o código novo aceita mais contextos; nenhum teste independente de privacidade de chats, permissões de bots e callbacks foi executado aqui.

## 4. Evidência real relevante não reproduzida integralmente

O job [42238240333](https://github.com/morfalespi/IC/actions/runs/42238240333) contém respostas e objetos serializados volumosos. Não foram copiados esses objetos para os relatórios, pois a publicação de dados de usuários, de tokens ou de metadados de sessão não é necessária para demonstrar o comportamento da rotina. No trecho operacional são identificáveis: **autenticação Telethon concluída**, **StickersetInvalidError**, **TimeoutError em GetFileRequest**, **100.833 campos reportados**, uma página rica planejada, Markdown e JSONL gerados, ZIP com **Duplicate name** e texto de **relatório classificado como concluído**. Tais afirmações não significam que 100.833 campos tenham sido de fato mostrados ao destinatário.

As três falhas de resolver na revisão c9195d12 foram verificadas por jobs: [42106712608](https://github.com/morfalespi/IC/actions/runs/42106712608), [42106692706](https://github.com/morfalespi/IC/actions/runs/42106692706) e [42106526642](https://github.com/morfalespi/IC/actions/runs/42106526642). O código então classificava erros como falha com exit 1. Já o caminho final de exceção pode sair 0: **comparar apenas a cor entre essas versões seria comparação não equivalente**.

## 5. Pontos incertos que não podem ser preenchidos por suposição

| Informação ausente | Por que permanece não confirmada |
|---|---|
| Arquivo Markdown/JSONL/ZIP recebido sem truncamento | Não se verificou download independente, hash e leitura no chat de destino. |
| Exibição efetivamente legível da Rich Message | A indicação local de “aceita” deriva de função sem validação de Message; uma página gigante foi planejada. |
| Zero exposição real de campos confidenciais | A versão final desativa a redação; o conteúdo bruto dos logs não foi republicado, mas não houve auditoria de todas as superfícies externas. |
| Comparação quantitativa de tempo e uso de API | Não há bateria de benchmark sob condições idênticas em ambos os commits. |
| Funcionamento de cada recurso Telegram em cada tipo de peer | A API limita dados conforme permissões e contexto; ausência não demonstra que o campo não exista. |
| “100% dos caminhos executados com sucesso” | Leitura de 100% dos arquivos não é cobertura de testes de 100% dos ramos, chamadas remotas e condições de corrida. |

## 6. Fechamento da lista de omissões

A lista é um **complemento de conteúdo**, não retificação silenciosa do primeiro relatório. As omissões assumidas foram: detalhes de funções não decisivas à narrativa, documentos históricos longos, strings e objetos retornados com dados potencialmente sensíveis, todas as linhas inalteradas de cada arquivo, parâmetros de métodos Telegram não exercitados e métricas sem observação. **Fatos adversos relevantes não devem ser omitidos do juízo final**: falso sucesso, perda de redação, mudança de identidade, reenvios, ausência de hash, duplicação no ZIP e erros registrados durante execução verde constam no primeiro texto.

Para comprovar quais bytes foram efetivamente recuperados em cada snapshot e para abrir o código completo por SHA, consulte o terceiro arquivo. Nenhuma linha de código foi deliberadamente removida da recuperação; a **síntese textual** é que não transcreve tudo.

## Atribuição desta aplicação

- **Autoria da redação e análise destes relatórios:** ChatGPT (GPT-6), mediante solicitação do usuário.
- **Aplicação e publicação dos arquivos no repositório:** ChatGPT (GPT-6), utilizando a integração GitHub autorizada.
- **Author e committer nativos do commit Git:** registrados pela integração sob a identidade da conta autenticada (`morfalespi`). Esta indicação textual não substitui os metadados nativos de autoria ou committer do objeto Git.
- **Escopo:** a atribuição é apenas desta documentação e da sua publicação, não da autoria do código do repositório nem de obras anteriores.
