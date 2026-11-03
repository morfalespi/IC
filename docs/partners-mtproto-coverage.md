# Cobertura das APIs do Telegram no Infocard

## Decisão de objetivo

Aplicar Partners como método obrigatório de evolução. O resultado desejado é entregar, para a referência consultada, todos os campos e conteúdos de leitura que MTProto e Bot API realmente disponibilizam à sessão de bot, sem reduzir o escopo aos campos já exibidos pelo projeto. Código anterior é inventário, não padrão normativo.

A cobertura deve preservar objetos TL completos, respostas JSON Bot API, wrappers, campos escalares e aninhados, listas, metadados e conteúdo de mídia devolvido pelos métodos elegíveis. Coleções pagináveis devem ser lidas até o fim ou identificadas como parciais. A exportação estruturada preserva também valores vazios, zero e falso quando retornados.

## Métodos atualmente tentados

| API | Métodos | Tipo de entidade | Uso na exportação completa |
|---|---|---|---|
| Bot API | `getChat` | Usuário, grupo, supergrupo ou canal | Preserva `ChatFullInfo` completo e tenta obter também chats pessoais, pais ou vinculados indicados na resposta. |
| Bot API | `getUserProfilePhotos`, `getUserProfileAudios` | Usuário | Pagina as coleções e tenta baixar a maior foto de cada perfil e cada áudio. |
| Bot API | `getUserPersonalChatMessages` | Usuário | Preserva até 20 mensagens do chat pessoal atualmente indicado no perfil e tenta baixar anexos compatíveis. |
| Bot API | `getChatAdministrators`, `getChatMemberCount` | Grupo, supergrupo ou canal | Preserva a lista de administradores e a contagem informada. |
| Bot API | `getFile` | Mídia retornada por métodos acima | Baixa arquivos permitidos pelo limite da Bot API; a resposta e o estado do arquivo são registrados. |
| MTProto | `getFullUser`, `getFullChannel`, `getFullChat`, `getUserPhotos`, `getSavedMusic`, `getParticipants`, `getMessages`, `channels.getMessages` | Conforme tipo de peer | Preserva respostas disponíveis; pagina coleções no modo completo e tenta obter conteúdo das mensagens fixadas por seus IDs. |

## Limites oficiais da sessão de bot

- As chamadas MTProto de leitura usadas incluem `users.getFullUser`, `channels.getFullChannel`, `messages.getFullChat`, `photos.getUserPhotos`, `users.getSavedMusic` e `channels.getParticipants`.
- `channels.getParticipants`, `photos.getUserPhotos` e `users.getSavedMusic` aceitam bots. O worker tenta no modo completo os filtros `recent`, `admins`, `bots`, `banned` (membros restritos) e `kicked` (membros banidos), cada um paginado e registrado separadamente. `channels.getParticipants` exige administração; o Telegram determina o que a sessão realmente pode ler. Filtros de contatos e menções dependem de contexto da conta/mensagem e não representam inventário geral do grupo.
- `messages.getHistory`, `stories.getPeerStories`, `messages.getCommonChats`, `messages.getPeerSettings`, `channels.getAdminLog`, `channels.getForumTopics`, `messages.getForumTopics` e `channels.getForumTopicsByID` são exclusivos de sessões de usuário. Como a pessoa decidiu manter autenticação de bot, o Infocard não consulta histórico, stories ativos, log administrativo ou listagem completa de tópicos de fórum por esses métodos. `channels.getAdminLog` ainda requer administração do canal mesmo em uma sessão de usuário.
- Permissões, privacidade, FloodWait, ausência de dados e diferenças de layer podem limitar a resposta. Campo ausente não significa que o dado não exista.
- Escopo é leitura da entidade e das coleções que os métodos acima retornam. Nenhuma chamada de alteração é incluída.

## Estado da implementação na branch

| Capacidade | Estado no código | Limite atual |
|---|---|---|
| Entidade resolvida e objeto de perfil completo | Implementado | As respostas completas são serializadas; isso ainda precisa de execução real após a alteração |
| Leituras Bot API adicionais | Implementadas no modo completo | Chamadas são tentadas e respostas ou falhas ficam no JSONL; o Telegram pode negar acesso |
| Arquivos da Bot API | Implementados com deduplicação | `getFile` e download são limitados a 20 MiB; acima disso, ficam parciais |
| Fotos de perfil | Consultada e paginada no modo completo para todo usuário resolvido | Paginação e download dependem do que Telegram disponibilizar |
| Música salva no perfil | Consultada e paginada no modo completo para todo usuário resolvido | A resposta do Telegram informa a coleção acessível, inclusive vazia |
| Participantes de canal | Filtros recentes, administradores, bots, restritos e banidos paginados no modo completo | Telegram pode recusar por permissão; CI não comprova que cada filtro retorna dados em execução |
| Mensagem fixada | Obtida por ID no modo completo quando MTProto retorna `pinned_msg_id` | Métodos aceitam bots; Telegram pode não entregar a mensagem ou sua mídia |
| Dados estruturados | JSONL sem mapeamento manual, dividido em anexos | Confirmação da Bot API não prova que o arquivo recebido abre ou preserva todo conteúdo |
| Foto e arquivos de mídia baixáveis | ZIP com manifesto e hash | Itens indisponíveis ou acima do limite são explicitados; não contam como sucesso integral |
| Histórico de mensagens e stories ativos | Fora do acesso de bot | Métodos exigem sessão de usuário; não serão habilitados mantendo a decisão de autenticação atual |
| Inventário de todos os outros métodos MTProto elegíveis por tipo de peer | Ainda não concluído | A exportação atual preserva respostas dos métodos chamados, mas não cobre por si só todos os métodos relacionados possíveis |

## O que substitui

Antes desta evolução, o resolver mapeava uma seleção de campos, consultava no máximo uma foto e uma música, e não entregava uma exportação bruta completa. A implementação atual acrescenta preservação de respostas TL e Bot API, paginação de fotos, músicas e áudios, tentativas para campos de chat e mensagens pessoais, tentativa de listar participantes, exportação JSONL e pacotes de mídia. Isso amplia materialmente a cobertura, mas não conclui a meta de inventariar e chamar todos os métodos de leitura relevantes.

## Próximos passos necessários

1. Inventariar, por tipo de peer, os métodos oficiais de leitura Bot API e MTProto que podem ser chamados por bot e quais dados adicionais cada método fornece. Comparar MTProto com a layer realmente instalada do Telethon.
2. Implementar as chamadas relevantes que ainda não existem, registrar por método o estado `concluído`, `sem dados`, `sem permissão`, `não suportado para bot` ou `falha`, e paginar até o fim.
3. Confirmar que cada resposta chamada está presente no JSONL, que as mídias acessíveis foram empacotadas e que arquivos acima do limite aparecem como parciais.
4. Executar no Telegram com referência pública de teste; inspecionar os JSONL e os pacotes realmente recebidos. CI, sintaxe e `ok=true` de envio são verificações intermediárias.
5. Só declarar cobertura total dentro do escopo definido quando o inventário de métodos e a prova de ponta a ponta estiverem concluídos. Dados que a API não conceder devem aparecer como limite observado, nunca ser inferidos.

## Critério de sucesso sustentado

Para cada execução completa, todas as respostas dos métodos de leitura inventariados e elegíveis foram serializadas sem perda, as coleções acessíveis foram paginadas até o fim, os anexos obrigatórios foram aceitos e inspecionados no Telegram, e cada campo ou coleção indisponível tem um estado e motivo explícitos. O sucesso continua limitado ao acesso realmente concedido pelo Telegram à sessão de bot.


## Referências oficiais consultadas

- [users.getFullUser](https://core.telegram.org/method/users.getFullUser) e [channels.getFullChannel](https://core.telegram.org/method/channels.getFullChannel): respostas completas e disponibilidade para bots.
- [messages.getFullChat](https://core.telegram.org/method/messages.getFullChat): grupos básicos.
- [photos.getUserPhotos](https://core.telegram.org/method/photos.getUserPhotos) e [users.getSavedMusic](https://core.telegram.org/method/users.getSavedMusic): fotos e músicas de perfil, com paginação e autorização de bot.
- [channels.getParticipants](https://core.telegram.org/method/channels.getParticipants) e [ChannelParticipantsFilter](https://core.telegram.org/type/ChannelParticipantsFilter): filtros e paginação; o método pode retornar CHAT_ADMIN_REQUIRED. A documentação [Telethon iter_participants](https://docs.telethon.dev/en/stable/modules/client.html) distingue membros restritos (`banned`) de banidos (`kicked`).
- [messages.getHistory](https://core.telegram.org/method/messages.getHistory), [stories.getPeerStories](https://core.telegram.org/method/stories.getPeerStories), [messages.getCommonChats](https://core.telegram.org/method/messages.getCommonChats), [messages.getPeerSettings](https://core.telegram.org/method/messages.getPeerSettings), [channels.getAdminLog](https://core.telegram.org/method/channels.getAdminLog), [channels.getForumTopics](https://core.telegram.org/method/channels.getForumTopics), [messages.getForumTopics](https://core.telegram.org/method/messages.getForumTopics) e [channels.getForumTopicsByID](https://core.telegram.org/method/channels.getForumTopicsByID): limitações de autenticação de bot.
