# AGENTS.md — normas operacionais do Infocard

Este arquivo orienta manutenção e revisão. Não é prova de execução ou disponibilidade de dados. As regras do proprietário, as especificações oficiais, o código de produção e as evidências de execução têm papéis diferentes.

## Prioridade das referências

1. Telegram Bot API: https://core.telegram.org/bots/api e histórico https://core.telegram.org/bots/api-changelog
2. Telegram MTProto: https://core.telegram.org/api/peers, https://core.telegram.org/method/contacts.resolveUsername e a documentação de cada método usado
3. Telegram Serverless: https://core.telegram.org/bots/serverless e cópia em docs/Serverless-OFFICIAL
4. SDK efetivamente instalado: docs/tgcloud-sdk.md e versão do projeto
5. GitHub Actions: https://docs.github.com/en/actions e documentação de workflow_dispatch

Repositórios de terceiros, exemplos, versões anteriores deste projeto e comentários históricos não substituem as fontes acima. Conferir versões e parâmetros antes de mudar integração.

## Regras do proprietário — preservar

- Sem comentários e docstrings no código de produção. Documentar decisões em Markdown fora dos arquivos executáveis.
- Não criar ou manter testes escritos pelo mesmo autor da implementação. A revisão deve confrontar as especificações oficiais e realizar verificações independentes e execução real. Checagem sintática não equivale a teste funcional.
- Não afirmar funcionamento sem evidência identificada. Usar IMPLEMENTADO, VERIFICADO, HIPÓTESE e DECISÃO em docs/registro.md.
- Falhas esperadas devem ser comunicadas ao usuário quando a Bot API estiver disponível. Não prometer comunicação quando a própria API ou a execução estiver indisponível.
- Publicar correções autorizadas na main. Mudanças no tgcloud/ acionam deploy automático; mudanças apenas em scripts/ acionam CI, mas o próximo workflow do resolver utiliza a main atual.
- Corrigir um problema identificado e avaliar suas regressões antes de afirmar sucesso.
- Não adicionar tokens, sessões MTProto ou dados privados em commits, arquivos de documentação ou logs deliberados.

## Fluxo implementado

- handlers/message.js recebe o objeto Message; handlers/callback_query.js recebe CallbackQuery; handlers/inline_query.js recebe InlineQuery. O Update completo pode ser acessado como ctx.update quando o segundo argumento do handler for declarado.
- Comandos de texto reconhecidos: /start e /help. Não há registro automático de menu por setMyCommands; o menu do BotFather não é inferido do código.
- Texto de consulta aceito: @username, ID ou ID @username. Este último é convenção da interface do Infocard, não sintaxe do Telegram.
- botões usam callback_data tipado (r ou f), validado em tgcloud/lib/entrada.js; não reutilizar conteúdo opaco de callback como texto digitado.
- O TGCloud envia alvo e expected_id como parâmetros separados a resolver.yml, que aciona scripts/resolver.py.
- MTProto tenta resolução por ID com as limitações de access_hash do Telegram; username passa por contacts.resolveUsername e, se houver expected_id, exige correspondência exata do peer.
- A busca comum exibe todos os campos mapeados que o MTProto efetivamente retornou, em páginas ricas, sem corte fixo de quantidade. O botão Obter Markdown completo faz outra consulta e entrega também o anexo .md; isso não significa coletar todas as propriedades possíveis do protocolo.
- Dados compartilhados por seletores e encaminhamentos podem aparecer no cartão inicial, mas o worker não possui armazenamento de contexto persistente para conservá-los se a ficha for sobrescrita.
- O modo inline orienta a conversa privada; não faz consulta MTProto dentro de outro chat.
- Sem Mini App nem endpoints próprios. Existe a tabela disparos para limitar requisições; limites atuais em tgcloud/lib/limite.js.

## Operações e limitações

- O runtime Serverless não tem sistema de arquivos Node nem pacotes arbitrários; importar o SDK de sdk e sdk/db e módulos locais por caminhos .js.
- Database: queries assíncronas, sem chaves estrangeiras. tgcloud push publica código e schema, mas não aplica migrações por si só.
- O workflow .github/workflows/deploy.yml executa tgcloud migrate antes de tgcloud push; portanto um deploy desse workflow **pode alterar o esquema do banco**.
- O GitHub injeta GH_DISPATCH_TOKEN no módulo publicado do TGCloud durante o deploy. O repositório mantém apenas placeholders em tgcloud/lib/segredos.js; o segredo existe no ambiente publicado e precisa de proteção e rotação.
- O repositório é PÚBLICO. workflow_dispatch recebe alvo, expected_id e identificadores de chat/mensagem; metadados e logs das execuções podem expor esse contexto. Não tratar o workflow atual como transporte privado. Não registrar IDs completos em respostas de suporte públicas.
- O status CI ou deploy só prova o que suas etapas verificaram. Healthcheck de dispatch ignora Telethon. Prova funcional exige workflow não-healthcheck, resultado da Bot API e inspeção do conteúdo entregue no Telegram.
- A Bot API 10.3 oferece Rich Messages, tabelas, mídia e botões, mas impõe limites por mensagem; paginação e envio de documentos são alternativas documentadas, não permissão para consultas ilimitadas.
- ID isolado de entidade desconhecida não possui resolução universal garantida. Não prometer acesso a dados ocultos ou inventar access_hash.

## Caminhos principais

| Arquivo | Responsabilidade |
|---|---|
| tgcloud/handlers/message.js | Mensagens, /start, /help, referências compartilhadas |
| tgcloud/handlers/callback_query.js | Ações dos botões r/f |
| tgcloud/handlers/inline_query.js | Pesquisa inline orientada ao privado |
| tgcloud/lib/entrada.js | Parser de entrada e codificação/decodificação de callback_data |
| tgcloud/lib/consulta.js | Cartão inicial, controle e disparo |
| tgcloud/lib/limite.js, tgcloud/schema.js | Limites por chat/global e tabela disparos |
| tgcloud/lib/despacho.js | workflow_dispatch |
| scripts/resolver.py | MTProto, enriquecimento e envio via Bot API |
| scripts/ficha_completa.py | Paginação rica, fallback HTML e arquivos Markdown |
| .github/workflows/ci.yml | Checagem de sintaxe e placeholders |
| .github/workflows/deploy.yml | Sincronização, migração, publicação e healthcheck |
| .github/workflows/resolver.yml | Consulta MTProto ou healthcheck sem consulta |
| docs/auditoria-operacional.md | Matriz atual de achados e provas |
| docs/registro.md | Histórico de decisões e evidências |

Não editar .tgcloud/ nem colocar segredos em documentação. Não afirmar que uma função foi verificada só porque está descrita neste arquivo.
