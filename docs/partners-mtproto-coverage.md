# Cobertura das APIs do Telegram no Infocard

## Decisão de objetivo

Aplicar Partners como método obrigatório de evolução. O resultado desejado é entregar, para a referência consultada, todos os campos e conteúdos de leitura que MTProto e Bot API realmente disponibilizam à sessão de bot, sem reduzir o escopo aos campos já exibidos pelo projeto. Código anterior é inventário, não padrão normativo.

A cobertura deve preservar objetos TL completos, respostas JSON Bot API, wrappers, campos escalares e aninhados, listas, metadados e conteúdo de mídia devolvido pelos métodos elegíveis. Coleções pagináveis devem ser lidas até o fim ou identificadas como parciais. A exportação estruturada preserva também valores vazios, zero e falso quando retornados. No modo completo, essa representação é apresentada em Rich Messages paginadas: cada linha mostra o caminho do campo e o valor, inclusive valores vazios, zero e falso; os anexos mantêm a representação detalhada. O sucesso da apresentação completa exige confirmação de todas as páginas ricas. Se apenas o fallback HTML for aceito, o conteúdo permanece entregue em formato alternativo e o resultado é marcado incompleto.

## Métodos atualmente tentados

| API | Métodos | Tipo de entidade | Uso na exportação completa |
|---|---|---|---|
| Bot API | `getChat` | Usuário, grupo, supergrupo ou canal | Preserva `ChatFullInfo` completo e tenta obter também chats pessoais, pais ou vinculados indicados na resposta. |
| Bot API | `getUserProfilePhotos`, `getUserProfileAudios`, `getUserGifts` | Usuário | Pagina fotos, áudios e presentes recebidos/hosteados; tenta baixar os stickers dos presentes. |
| Bot API | `getUserPersonalChatMessages` | Usuário | Preserva até 20 mensagens do chat pessoal atualmente indicado no perfil e tenta baixar anexos compatíveis. |
| Bot API | `getChatAdministrators`, `getChatMemberCount`, `getChatGifts` | Grupo, supergrupo ou canal | Preserva administradores, contagem e presentes pertencentes ao chat; pagina presentes e tenta baixar seus stickers. |
| Bot API | `getChatMember`, `getUserChatBoosts` | Participantes de canais e supergrupos | Consulta estado/permissões e boosts de cada participante encontrado, mantendo índice entre usuário e resposta. |
| Bot API | `getFile` | Mídia retornada por métodos acima | Percorre recursivamente respostas Bot API em busca de `file_id`, escolhendo a maior resolução em vetores de `PhotoSize`; baixa até o limite da Bot API e registra falhas/limites. |
| Bot API | `getStickerSet`, `getCustomEmojiStickers`, `getForumTopicIconStickers` | Conjuntos e emojis referenciados por chats, perfis e mensagens | Consulta conjuntos de stickers e emojis personalizados citados pelas respostas; em fóruns consulta também stickers permitidos para ícones de tópico e tenta baixar os arquivos acessíveis. |
| MTProto | `getFullUser`, `getFullChannel`, `getFullChat`, `getUserPhotos`, `getSavedMusic`, `getParticipants`, `getMessages`, `channels.getMessages`, `payments.getSavedStarGifts` | Conforme tipo de peer | Preserva respostas disponíveis; pagina coleções no modo completo, tenta obter mensagens fixadas e presentes Star recebidos/guardados por usuário ou canal. |

## Limites oficiais da sessão de bot

- As leituras Bot API incluem `getStickerSet` para nomes de conjuntos retornados por chats e `getCustomEmojiStickers` para IDs em campos/entidades, em lotes de até 200 conforme o limite oficial. Em chats de fórum, `getForumTopicIconStickers` também é consultado. `getUserGifts` e `getChatGifts` percorrem `next_offset` até o fim e preservam todas as respostas e presentes; a disponibilidade depende do que a API permite ao bot para aquele alvo. `getChatMember` e `getUserChatBoosts` são consultados por participante obtido e exigem direitos de administrador para garantia de dados de terceiros; cada resposta e falha é associada ao ID consultado. `getBusinessAccountGifts` exige um `business_connection_id` ativo e direitos empresariais; esse contexto não faz parte de uma consulta por peer e não é presumido.
- As chamadas MTProto de leitura usadas incluem `users.getFullUser`, `channels.getFullChannel`, `messages.getFullChat`, `photos.getUserPhotos`, `users.getSavedMusic`, `channels.getParticipants` e `payments.getSavedStarGifts`. A chamada de presentes percorre o `next_offset`, registra respostas TL integrais e tenta baixar o sticker de cada presente regular retornado.
- `channels.getParticipants`, `photos.getUserPhotos` e `users.getSavedMusic` aceitam bots. O worker tenta no modo completo os filtros `recent`, `admins`, `bots`, `banned` (membros restritos) e `kicked` (membros banidos), cada um paginado e registrado separadamente. `channels.getParticipants` exige administração; o Telegram determina o que a sessão realmente pode ler. Filtros de contatos e menções dependem de contexto da conta/mensagem e não representam inventário geral do grupo.
- `messages.getHistory`, `stories.getPeerStories`, `messages.getCommonChats`, `messages.getPeerSettings`, `channels.getAdminLog`, `channels.getForumTopics`, `messages.getForumTopics` e `channels.getForumTopicsByID` são exclusivos de sessões de usuário. Como a pessoa decidiu manter autenticação de bot, o Infocard não consulta histórico, stories ativos, log administrativo ou listagem completa de tópicos de fórum por esses métodos. `channels.getAdminLog` ainda requer administração do canal mesmo em uma sessão de usuário.
- Permissões, privacidade, FloodWait, ausência de dados e diferenças de layer podem limitar a resposta. Campo ausente não significa que o dado não exista.
- Escopo é leitura da entidade e das coleções que os métodos acima retornam. Nenhuma chamada de alteração é incluída.

## Estado da implementação na branch

| Capacidade | Estado no código | Limite atual |
|---|---|---|
| Entidade resolvida e objeto de perfil completo | Implementado | As respostas completas são serializadas; isso ainda precisa de execução real após a alteração |
| Leituras Bot API adicionais | Implementadas no modo completo | Chamadas são tentadas e respostas ou falhas ficam no JSONL; o Telegram pode negar acesso |
| Arquivos da Bot API | Percorridos recursivamente em respostas de chat e mensagens pessoais; deduplicados por `file_unique_id` | `getFile` e download são limitados a 20 MiB; acima disso, ficam parciais |
| Stickers e emojis Bot API | Conjuntos referenciados, emojis personalizados e stickers dos presentes consultados; resultados percorridos para baixar mídia | Respostas e arquivos ainda dependem de disponibilidade e permissões do Telegram; o CI não confirma retorno ao vivo |
| Presentes Bot API | `getUserGifts` ou `getChatGifts` no modo completo, paginados pelo `next_offset`; respostas brutas e associação página/resposta preservadas | O Telegram pode recusar ou limitar a consulta; stickers podem estar indisponíveis para download |
| Presentes MTProto | `payments.getSavedStarGifts` no modo completo para usuários e canais, paginado por `next_offset`; respostas TL completas ficam no JSONL; grupos básicos são registrados como não aplicáveis | O servidor pode recusar peer, método ou acesso; respostas específicas precisam de verificação ao vivo; mídia de presentes únicos pode exigir arquivos referenciados por atributos |
| Fotos de perfil | Consultada e paginada no modo completo para todo usuário resolvido | Paginação e download dependem do que Telegram disponibilizar |
| Música salva no perfil | Consultada e paginada no modo completo para todo usuário resolvido | A resposta do Telegram informa a coleção acessível, inclusive vazia |
| Participantes de canal | Filtros recentes, administradores, bots, restritos e banidos paginados no modo completo | Telegram pode recusar por permissão; CI não comprova que cada filtro retorna dados em execução |
| Mensagem fixada | Obtida por ID no modo completo quando MTProto retorna `pinned_msg_id` | Métodos aceitam bots; Telegram pode não entregar a mensagem ou sua mídia |
| Dados estruturados | Cada campo das respostas coletadas também é exibido em tabelas Rich Message paginadas com caminho e valor; JSONL e Markdown são anexados | A confirmação da Bot API não prova que a pessoa inspecionou o conteúdo; campos que a API não retornou continuam fora do escopo observável |
| Foto e arquivos de mídia baixáveis | ZIP com manifesto e hash; coleta de presentes tenta baixar stickers regulares via Bot API e MTProto | Itens indisponíveis ou acima do limite são explicitados; presentes únicos podem expor mídia como atributos e exigem revisão adicional |
| Histórico de mensagens e stories ativos | Fora do acesso de bot | Métodos exigem sessão de usuário; não serão habilitados mantendo a decisão de autenticação atual |
| Inventário de todos os outros métodos MTProto elegíveis por tipo de peer | Ainda não concluído | A exportação atual preserva respostas dos métodos chamados, mas não cobre por si só todos os métodos relacionados possíveis |

## O que substitui

Antes desta evolução, o resolver mapeava uma seleção de campos, consultava no máximo uma foto e uma música, e não entregava uma exportação bruta completa. A implementação atual acrescenta preservação de respostas TL e Bot API, paginação de fotos, músicas, áudios e presentes via Bot API/MTProto, tentativas para campos de chat e mensagens pessoais, tentativa de listar participantes, exportação JSONL e pacotes de mídia. Isso amplia materialmente a cobertura, mas não conclui a meta de inventariar e chamar todos os métodos de leitura relevantes.

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
- [payments.getSavedStarGifts](https://core.telegram.org/method/payments.getSavedStarGifts): usuários e bots podem consultar presentes recebidos/guardados por um peer, com `next_offset` para paginação. [getUserGifts](https://core.telegram.org/bots/api#getusergifts) e [getChatGifts](https://core.telegram.org/bots/api#getchatgifts): listam presentes do usuário ou chat e paginam por `next_offset`; objetos `OwnedGift` incluem metadados e o objeto `Gift` com sticker. [getBusinessAccountGifts](https://core.telegram.org/bots/api#getbusinessaccountgifts) exige conexão e permissões de conta empresarial. [getChatMember](https://core.telegram.org/bots/api#getchatmember): retorna `ChatMember` e só garante o resultado para outros usuários quando o bot é administrador. [getUserChatBoosts](https://core.telegram.org/bots/api#getuserchatboosts): lista os boosts de um participante e exige que o bot seja administrador. [Bot API Message](https://core.telegram.org/bots/api#message), [PaidMedia](https://core.telegram.org/bots/api#paidmedia) e [getFile](https://core.telegram.org/bots/api#getfile): mensagens podem conter anexos em objetos aninhados; cada `file_id` acessível é elegível para download, sujeito ao limite oficial de arquivo. [getStickerSet](https://core.telegram.org/bots/api#getstickerset) retorna stickers do conjunto pelo nome; [getCustomEmojiStickers](https://core.telegram.org/bots/api#getcustomemojistickers) aceita até 200 IDs por chamada; [getForumTopicIconStickers](https://core.telegram.org/bots/api#getforumtopiciconstickers) lista stickers de emoji válidos para ícones de tópicos.
- [messages.getHistory](https://core.telegram.org/method/messages.getHistory), [stories.getPeerStories](https://core.telegram.org/method/stories.getPeerStories), [messages.getCommonChats](https://core.telegram.org/method/messages.getCommonChats), [messages.getPeerSettings](https://core.telegram.org/method/messages.getPeerSettings), [channels.getAdminLog](https://core.telegram.org/method/channels.getAdminLog), [channels.getForumTopics](https://core.telegram.org/method/channels.getForumTopics), [messages.getForumTopics](https://core.telegram.org/method/messages.getForumTopics) e [channels.getForumTopicsByID](https://core.telegram.org/method/channels.getForumTopicsByID): limitações de autenticação de bot.
