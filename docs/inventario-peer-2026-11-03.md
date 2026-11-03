# Inventário oficial de métodos com contexto de peer — 2026-11-03

Esta rodada cruzou o schema JSON oficial consultado em `https://core.telegram.org/schema/json` com as páginas oficiais de **109 candidatos** das famílias users, photos, channels, messages, contacts, payments, premium, stories, stats e bots. O recorte seleciona nomes contendo get/resolve/check/search e parâmetros InputPeer, InputUser ou InputChannel. O recorte textual também inclui ações, como `messages.editFactCheck` e `messages.deleteFactCheck`; ações são excluídas da execução de leitura. O prefixo get tampouco garante ausência de efeito, como nos getters de callback ou de URL de saque. Não é um inventário de todas as APIs Telegram: métodos sem esses parâmetros, vetores de peers e contextos empresariais exigem seus próprios recortes.

Foram encontrados 17 candidatos com suporte explícito a bots e 92 exclusivos de usuário. Todas as 109 páginas responderam e publicaram a classificação. Os 17 compatíveis com bots possuem construtor no Telethon 1.45.0 instalado (layer 229). O schema oficial consultado anuncia layer 225; assinatura e capacidade da página oficial foram confrontadas separadamente com o SDK, sem presumir equivalência integral entre as layers.

## Candidatos compatíveis com bots

| Método e fonte | Situação no contexto do Infocard |
|---|---|
| [users.getFullUser](https://core.telegram.org/method/users.getFullUser) | Implementado; resposta integral preservada e acesso sujeito à resposta real do Telegram. |
| [photos.getUserPhotos](https://core.telegram.org/method/photos.getUserPhotos) | Implementado; resposta integral preservada e acesso sujeito à resposta real do Telegram. |
| [channels.getMessages](https://core.telegram.org/method/channels.getMessages) | Implementado; resposta integral preservada e acesso sujeito à resposta real do Telegram. |
| [channels.getParticipants](https://core.telegram.org/method/channels.getParticipants) | Implementado; resposta integral preservada e acesso sujeito à resposta real do Telegram. |
| [channels.getParticipant](https://core.telegram.org/method/channels.getParticipant) | Implementado; resposta integral preservada e acesso sujeito à resposta real do Telegram. |
| [channels.getFullChannel](https://core.telegram.org/method/channels.getFullChannel) | Implementado; resposta integral preservada e acesso sujeito à resposta real do Telegram. |
| [messages.getGameHighScores](https://core.telegram.org/method/messages.getGameHighScores) | Contexto ausente: mensagem de jogo pertencente à aplicação; o Infocard não publica jogos. |
| [messages.getInlineGameHighScores](https://core.telegram.org/method/messages.getInlineGameHighScores) | Contexto ausente: identificador de mensagem inline de jogo; a consulta genérica não o fornece. |
| [bots.getBotMenuButton](https://core.telegram.org/method/bots.getBotMenuButton) | Configuração do menu do próprio bot para um usuário; não descreve o perfil pesquisado. Exige contexto da configuração do Infocard, fora da ficha de terceiros. |
| [bots.getBotInfo](https://core.telegram.org/method/bots.getBotInfo) | Só consulta a própria conta quando autenticado como bot; não consulta informações de outro bot por esse método. |
| [premium.getUserBoosts](https://core.telegram.org/method/premium.getUserBoosts) | Implementado; resposta integral preservada e acesso sujeito à resposta real do Telegram. |
| [payments.getStarsTransactions](https://core.telegram.org/method/payments.getStarsTransactions) | Somente conta própria ou bot pertencente à conta; falta contexto de titularidade e autorização do solicitante para exportar finanças. Não expor transações a qualquer usuário que consulte o bot. |
| [payments.getSavedStarGifts](https://core.telegram.org/method/payments.getSavedStarGifts) | Implementado; resposta integral preservada e acesso sujeito à resposta real do Telegram. |
| [users.getSavedMusic](https://core.telegram.org/method/users.getSavedMusic) | Implementado; resposta integral preservada e acesso sujeito à resposta real do Telegram. |
| [messages.getForumTopicsByID](https://core.telegram.org/method/messages.getForumTopicsByID) | Implementado para IDs de tópicos efetivamente retornados por mensagens; não enumera tópicos desconhecidos. |
| [bots.getAccessSettings](https://core.telegram.org/method/bots.getAccessSettings) | Contexto ausente: relação de manager bot com um managed bot. Não é inferida por um username. |
| [messages.getPersonalChannelHistory](https://core.telegram.org/method/messages.getPersonalChannelHistory) | Implementado; resposta integral preservada e acesso sujeito à resposta real do Telegram. |

A incompatibilidade das configurações/finanças próprias com uma ficha genérica é uma decisão de escopo e de contexto, não uma alegação de incompatibilidade desses métodos com autenticação de bot. Para habilitá-las, é necessário definir consulta administrativa autenticada e dados de contexto correspondentes.

## Candidatos exclusivos de usuário

As seguintes páginas oficiais declaram “Only users can use this method”. Os métodos não são executados com a sessão de bot; essa restrição não foi inferida do código antigo.

| Método e fonte | Decisão |
|---|---|
| [messages.getDialogs](https://core.telegram.org/method/messages.getDialogs) | Requer autenticação de usuário. |
| [messages.getHistory](https://core.telegram.org/method/messages.getHistory) | Requer autenticação de usuário. |
| [messages.search](https://core.telegram.org/method/messages.search) | Requer autenticação de usuário. |
| [messages.getPeerSettings](https://core.telegram.org/method/messages.getPeerSettings) | Requer autenticação de usuário. |
| [messages.getMessagesViews](https://core.telegram.org/method/messages.getMessagesViews) | Requer autenticação de usuário. |
| [channels.checkUsername](https://core.telegram.org/method/channels.checkUsername) | Requer autenticação de usuário. |
| [messages.searchGlobal](https://core.telegram.org/method/messages.searchGlobal) | Requer autenticação de usuário. |
| [messages.getInlineBotResults](https://core.telegram.org/method/messages.getInlineBotResults) | Requer autenticação de usuário. |
| [messages.getMessageEditData](https://core.telegram.org/method/messages.getMessageEditData) | Requer autenticação de usuário. |
| [messages.getBotCallbackAnswer](https://core.telegram.org/method/messages.getBotCallbackAnswer) | Ação mutável; excluída da coleta de leitura. |
| [messages.getCommonChats](https://core.telegram.org/method/messages.getCommonChats) | Requer autenticação de usuário. |
| [payments.getPaymentReceipt](https://core.telegram.org/method/payments.getPaymentReceipt) | Requer autenticação de usuário. |
| [channels.getAdminLog](https://core.telegram.org/method/channels.getAdminLog) | Requer autenticação de usuário. |
| [messages.getUnreadMentions](https://core.telegram.org/method/messages.getUnreadMentions) | Requer autenticação de usuário. |
| [messages.getRecentLocations](https://core.telegram.org/method/messages.getRecentLocations) | Requer autenticação de usuário. |
| [messages.getDialogUnreadMarks](https://core.telegram.org/method/messages.getDialogUnreadMarks) | Requer autenticação de usuário. |
| [messages.getPollResults](https://core.telegram.org/method/messages.getPollResults) | Requer autenticação de usuário. |
| [messages.getOnlines](https://core.telegram.org/method/messages.getOnlines) | Requer autenticação de usuário. |
| [messages.getSearchCounters](https://core.telegram.org/method/messages.getSearchCounters) | Requer autenticação de usuário. |
| [messages.getScheduledHistory](https://core.telegram.org/method/messages.getScheduledHistory) | Requer autenticação de usuário. |
| [messages.getScheduledMessages](https://core.telegram.org/method/messages.getScheduledMessages) | Requer autenticação de usuário. |
| [messages.getPollVotes](https://core.telegram.org/method/messages.getPollVotes) | Requer autenticação de usuário. |
| [stats.getBroadcastStats](https://core.telegram.org/method/stats.getBroadcastStats) | Requer autenticação de usuário. |
| [stats.getMegagroupStats](https://core.telegram.org/method/stats.getMegagroupStats) | Requer autenticação de usuário. |
| [messages.getReplies](https://core.telegram.org/method/messages.getReplies) | Requer autenticação de usuário. |
| [messages.getDiscussionMessage](https://core.telegram.org/method/messages.getDiscussionMessage) | Requer autenticação de usuário. |
| [stats.getMessagePublicForwards](https://core.telegram.org/method/stats.getMessagePublicForwards) | Requer autenticação de usuário. |
| [stats.getMessageStats](https://core.telegram.org/method/stats.getMessageStats) | Requer autenticação de usuário. |
| [messages.getExportedChatInvites](https://core.telegram.org/method/messages.getExportedChatInvites) | Requer autenticação de usuário. |
| [messages.getExportedChatInvite](https://core.telegram.org/method/messages.getExportedChatInvite) | Requer autenticação de usuário. |
| [messages.getAdminsWithInvites](https://core.telegram.org/method/messages.getAdminsWithInvites) | Requer autenticação de usuário. |
| [messages.getChatInviteImporters](https://core.telegram.org/method/messages.getChatInviteImporters) | Requer autenticação de usuário. |
| [messages.checkHistoryImportPeer](https://core.telegram.org/method/messages.checkHistoryImportPeer) | Requer autenticação de usuário. |
| [messages.getMessageReadParticipants](https://core.telegram.org/method/messages.getMessageReadParticipants) | Requer autenticação de usuário. |
| [messages.getSearchResultsCalendar](https://core.telegram.org/method/messages.getSearchResultsCalendar) | Requer autenticação de usuário. |
| [messages.getSearchResultsPositions](https://core.telegram.org/method/messages.getSearchResultsPositions) | Requer autenticação de usuário. |
| [channels.getSendAs](https://core.telegram.org/method/channels.getSendAs) | Requer autenticação de usuário. |
| [messages.getMessagesReactions](https://core.telegram.org/method/messages.getMessagesReactions) | Requer autenticação de usuário. |
| [messages.getMessageReactionsList](https://core.telegram.org/method/messages.getMessageReactionsList) | Requer autenticação de usuário. |
| [messages.getUnreadReactions](https://core.telegram.org/method/messages.getUnreadReactions) | Requer autenticação de usuário. |
| [messages.getAttachMenuBot](https://core.telegram.org/method/messages.getAttachMenuBot) | Requer autenticação de usuário. |
| [messages.getExtendedMedia](https://core.telegram.org/method/messages.getExtendedMedia) | Requer autenticação de usuário. |
| [stories.getPinnedStories](https://core.telegram.org/method/stories.getPinnedStories) | Requer autenticação de usuário. |
| [stories.getStoriesArchive](https://core.telegram.org/method/stories.getStoriesArchive) | Requer autenticação de usuário. |
| [stories.getStoriesByID](https://core.telegram.org/method/stories.getStoriesByID) | Requer autenticação de usuário. |
| [stories.getStoryViewsList](https://core.telegram.org/method/stories.getStoryViewsList) | Requer autenticação de usuário. |
| [stories.getStoriesViews](https://core.telegram.org/method/stories.getStoriesViews) | Requer autenticação de usuário. |
| [stories.getPeerStories](https://core.telegram.org/method/stories.getPeerStories) | Requer autenticação de usuário. |
| [payments.getPremiumGiftCodeOptions](https://core.telegram.org/method/payments.getPremiumGiftCodeOptions) | Requer autenticação de usuário. |
| [payments.getGiveawayInfo](https://core.telegram.org/method/payments.getGiveawayInfo) | Requer autenticação de usuário. |
| [premium.getBoostsList](https://core.telegram.org/method/premium.getBoostsList) | Requer autenticação de usuário. |
| [premium.getBoostsStatus](https://core.telegram.org/method/premium.getBoostsStatus) | Requer autenticação de usuário. |
| [channels.getChannelRecommendations](https://core.telegram.org/method/channels.getChannelRecommendations) | Requer autenticação de usuário. |
| [stats.getStoryStats](https://core.telegram.org/method/stats.getStoryStats) | Requer autenticação de usuário. |
| [stats.getStoryPublicForwards](https://core.telegram.org/method/stats.getStoryPublicForwards) | Requer autenticação de usuário. |
| [stories.getStoryReactionsList](https://core.telegram.org/method/stories.getStoryReactionsList) | Requer autenticação de usuário. |
| [messages.getSavedDialogs](https://core.telegram.org/method/messages.getSavedDialogs) | Requer autenticação de usuário. |
| [messages.getSavedHistory](https://core.telegram.org/method/messages.getSavedHistory) | Requer autenticação de usuário. |
| [messages.getSavedReactionTags](https://core.telegram.org/method/messages.getSavedReactionTags) | Requer autenticação de usuário. |
| [messages.getOutboxReadDate](https://core.telegram.org/method/messages.getOutboxReadDate) | Requer autenticação de usuário. |
| [channels.searchPosts](https://core.telegram.org/method/channels.searchPosts) | Requer autenticação de usuário. |
| [messages.editFactCheck](https://core.telegram.org/method/messages.editFactCheck) | Ação mutável; excluída da coleta de leitura. |
| [messages.deleteFactCheck](https://core.telegram.org/method/messages.deleteFactCheck) | Ação mutável; excluída da coleta de leitura. |
| [messages.getFactCheck](https://core.telegram.org/method/messages.getFactCheck) | Requer autenticação de usuário. |
| [payments.getStarsStatus](https://core.telegram.org/method/payments.getStarsStatus) | Requer autenticação de usuário. |
| [stories.searchPosts](https://core.telegram.org/method/stories.searchPosts) | Requer autenticação de usuário. |
| [payments.getStarsRevenueStats](https://core.telegram.org/method/payments.getStarsRevenueStats) | Requer autenticação de usuário. |
| [payments.getStarsRevenueWithdrawalUrl](https://core.telegram.org/method/payments.getStarsRevenueWithdrawalUrl) | Ação mutável; excluída da coleta de leitura. |
| [payments.getStarsRevenueAdsAccountUrl](https://core.telegram.org/method/payments.getStarsRevenueAdsAccountUrl) | Requer autenticação de usuário. |
| [payments.getStarsTransactionsByID](https://core.telegram.org/method/payments.getStarsTransactionsByID) | Requer autenticação de usuário. |
| [payments.getStarsGiftOptions](https://core.telegram.org/method/payments.getStarsGiftOptions) | Requer autenticação de usuário. |
| [bots.getPreviewInfo](https://core.telegram.org/method/bots.getPreviewInfo) | Requer autenticação de usuário. |
| [bots.getPreviewMedias](https://core.telegram.org/method/bots.getPreviewMedias) | Requer autenticação de usuário. |
| [payments.getStarsSubscriptions](https://core.telegram.org/method/payments.getStarsSubscriptions) | Requer autenticação de usuário. |
| [messages.getSponsoredMessages](https://core.telegram.org/method/messages.getSponsoredMessages) | Requer autenticação de usuário. |
| [messages.getPreparedInlineMessage](https://core.telegram.org/method/messages.getPreparedInlineMessage) | Requer autenticação de usuário. |
| [bots.checkDownloadFileParams](https://core.telegram.org/method/bots.checkDownloadFileParams) | Requer autenticação de usuário. |
| [payments.getConnectedStarRefBots](https://core.telegram.org/method/payments.getConnectedStarRefBots) | Requer autenticação de usuário. |
| [payments.getConnectedStarRefBot](https://core.telegram.org/method/payments.getConnectedStarRefBot) | Requer autenticação de usuário. |
| [payments.getSuggestedStarRefBots](https://core.telegram.org/method/payments.getSuggestedStarRefBots) | Requer autenticação de usuário. |
| [bots.getBotRecommendations](https://core.telegram.org/method/bots.getBotRecommendations) | Requer autenticação de usuário. |
| [messages.getSavedDialogsByID](https://core.telegram.org/method/messages.getSavedDialogsByID) | Requer autenticação de usuário. |
| [channels.getMessageAuthor](https://core.telegram.org/method/channels.getMessageAuthor) | Requer autenticação de usuário. |
| [payments.getStarGiftCollections](https://core.telegram.org/method/payments.getStarGiftCollections) | Requer autenticação de usuário. |
| [stories.getAlbums](https://core.telegram.org/method/stories.getAlbums) | Requer autenticação de usuário. |
| [stories.getAlbumStories](https://core.telegram.org/method/stories.getAlbumStories) | Requer autenticação de usuário. |
| [users.getSavedMusicByID](https://core.telegram.org/method/users.getSavedMusicByID) | Requer autenticação de usuário. |
| [messages.getForumTopics](https://core.telegram.org/method/messages.getForumTopics) | Requer autenticação de usuário. |
| [messages.getFutureChatCreatorAfterLeave](https://core.telegram.org/method/messages.getFutureChatCreatorAfterLeave) | Requer autenticação de usuário. |
| [messages.getUnreadPollVotes](https://core.telegram.org/method/messages.getUnreadPollVotes) | Requer autenticação de usuário. |
| [bots.getRequestedWebViewButton](https://core.telegram.org/method/bots.getRequestedWebViewButton) | Requer autenticação de usuário. |
| [stats.getPollStats](https://core.telegram.org/method/stats.getPollStats) | Requer autenticação de usuário. |

## Correção da matriz anterior

`messages.getForumTopicsByID` é oficialmente compatível com bots e está no schema executável. A exclusão ampla de consultas de tópicos era incorreta. O método exige IDs conhecidos: a listagem `messages.getForumTopics` continua exclusiva de usuário. Mensagens fixadas, mensagens do canal pessoal e respostas Bot API podem trazer referências de tópicos; quando trazem, o coletor consulta o peer exato e os IDs recebidos. Não inventa IDs nem usa o ID de uma mensagem comum como ID de tópico.

Verificação de suporte e assinatura não comprova execução real, entrega ou inspeção de conteúdo. Estados de execução e limites permanecem em [registro.md](registro.md).

## Recorte Bot API

A página oficial vigente contém 32 métodos cujo nome começa por get. Abaixo estão os métodos implementados no contexto de coleta e os contextos específicos ausentes; não se presume que um getter de configuração própria descreva um terceiro pesquisado. Métodos de alteração/envio não fazem parte deste recorte de leitura.

| Método e fonte | Contexto |
|---|---|
| [getUpdates](https://core.telegram.org/bots/api#getupdates) | Transporte de atualizações do próprio bot; a aplicação usa webhook Serverless, não consulta de perfil. |
| [getWebhookInfo](https://core.telegram.org/bots/api#getwebhookinfo) | Configuração operacional do webhook do próprio bot, fora da ficha do peer pesquisado. |
| [getMe](https://core.telegram.org/bots/api#getme) | Implementado quando aplicável ao tipo de alvo e à mídia/contexto retornado; preserva resposta ou erro real. |
| [getUserProfilePhotos](https://core.telegram.org/bots/api#getuserprofilephotos) | Implementado quando aplicável ao tipo de alvo e à mídia/contexto retornado; preserva resposta ou erro real. |
| [getUserProfileAudios](https://core.telegram.org/bots/api#getuserprofileaudios) | Implementado quando aplicável ao tipo de alvo e à mídia/contexto retornado; preserva resposta ou erro real. |
| [getFile](https://core.telegram.org/bots/api#getfile) | Implementado quando aplicável ao tipo de alvo e à mídia/contexto retornado; preserva resposta ou erro real. |
| [getChat](https://core.telegram.org/bots/api#getchat) | Implementado quando aplicável ao tipo de alvo e à mídia/contexto retornado; preserva resposta ou erro real. |
| [getChatAdministrators](https://core.telegram.org/bots/api#getchatadministrators) | Implementado quando aplicável ao tipo de alvo e à mídia/contexto retornado; preserva resposta ou erro real. |
| [getChatMemberCount](https://core.telegram.org/bots/api#getchatmembercount) | Implementado quando aplicável ao tipo de alvo e à mídia/contexto retornado; preserva resposta ou erro real. |
| [getChatMember](https://core.telegram.org/bots/api#getchatmember) | Implementado quando aplicável ao tipo de alvo e à mídia/contexto retornado; preserva resposta ou erro real. |
| [getUserPersonalChatMessages](https://core.telegram.org/bots/api#getuserpersonalchatmessages) | Implementado quando aplicável ao tipo de alvo e à mídia/contexto retornado; preserva resposta ou erro real. |
| [getForumTopicIconStickers](https://core.telegram.org/bots/api#getforumtopiciconstickers) | Implementado quando aplicável ao tipo de alvo e à mídia/contexto retornado; preserva resposta ou erro real. |
| [getUserChatBoosts](https://core.telegram.org/bots/api#getuserchatboosts) | Implementado quando aplicável ao tipo de alvo e à mídia/contexto retornado; preserva resposta ou erro real. |
| [getBusinessConnection](https://core.telegram.org/bots/api#getbusinessconnection) | Exige business_connection_id de uma conexão ativa, ausente da consulta por peer. |
| [getManagedBotToken](https://core.telegram.org/bots/api#getmanagedbottoken) | Retorna uma credencial de managed bot, exige contexto de manager; não pertence à exportação de perfil. |
| [getManagedBotAccessSettings](https://core.telegram.org/bots/api#getmanagedbotaccesssettings) | Exige relação de manager com um managed bot, ausente do contexto de consulta genérica. |
| [getMyCommands](https://core.telegram.org/bots/api#getmycommands) | Configuração do próprio Infocard, eventualmente por usuário/idioma/escopo; não é configuração do peer pesquisado. Exige contexto de consulta administrativa/configuração, fora da ficha de terceiros. |
| [getMyName](https://core.telegram.org/bots/api#getmyname) | Configuração do próprio Infocard, eventualmente por usuário/idioma/escopo; não é configuração do peer pesquisado. Exige contexto de consulta administrativa/configuração, fora da ficha de terceiros. |
| [getMyDescription](https://core.telegram.org/bots/api#getmydescription) | Configuração do próprio Infocard, eventualmente por usuário/idioma/escopo; não é configuração do peer pesquisado. Exige contexto de consulta administrativa/configuração, fora da ficha de terceiros. |
| [getMyShortDescription](https://core.telegram.org/bots/api#getmyshortdescription) | Configuração do próprio Infocard, eventualmente por usuário/idioma/escopo; não é configuração do peer pesquisado. Exige contexto de consulta administrativa/configuração, fora da ficha de terceiros. |
| [getChatMenuButton](https://core.telegram.org/bots/api#getchatmenubutton) | Configuração do próprio Infocard, eventualmente por usuário/idioma/escopo; não é configuração do peer pesquisado. Exige contexto de consulta administrativa/configuração, fora da ficha de terceiros. |
| [getMyDefaultAdministratorRights](https://core.telegram.org/bots/api#getmydefaultadministratorrights) | Configuração do próprio Infocard, eventualmente por usuário/idioma/escopo; não é configuração do peer pesquisado. Exige contexto de consulta administrativa/configuração, fora da ficha de terceiros. |
| [getAvailableGifts](https://core.telegram.org/bots/api#getavailablegifts) | Implementado quando aplicável ao tipo de alvo e à mídia/contexto retornado; preserva resposta ou erro real. |
| [getBusinessAccountStarBalance](https://core.telegram.org/bots/api#getbusinessaccountstarbalance) | Exige conexão empresarial ativa e direitos; falta business_connection_id e contexto autorizado. |
| [getBusinessAccountGifts](https://core.telegram.org/bots/api#getbusinessaccountgifts) | Exige conexão empresarial ativa e direitos; falta business_connection_id e contexto autorizado. |
| [getUserGifts](https://core.telegram.org/bots/api#getusergifts) | Implementado quando aplicável ao tipo de alvo e à mídia/contexto retornado; preserva resposta ou erro real. |
| [getChatGifts](https://core.telegram.org/bots/api#getchatgifts) | Implementado quando aplicável ao tipo de alvo e à mídia/contexto retornado; preserva resposta ou erro real. |
| [getStickerSet](https://core.telegram.org/bots/api#getstickerset) | Implementado quando aplicável ao tipo de alvo e à mídia/contexto retornado; preserva resposta ou erro real. |
| [getCustomEmojiStickers](https://core.telegram.org/bots/api#getcustomemojistickers) | Implementado quando aplicável ao tipo de alvo e à mídia/contexto retornado; preserva resposta ou erro real. |
| [getMyStarBalance](https://core.telegram.org/bots/api#getmystarbalance) | Saldo do próprio bot; requer consulta administrativa autorizada, ausente da ficha genérica. |
| [getStarTransactions](https://core.telegram.org/bots/api#getstartransactions) | Transações do próprio bot; requer consulta administrativa autorizada, ausente da ficha genérica. |
| [getGameHighScores](https://core.telegram.org/bots/api#getgamehighscores) | Exige mensagem de jogo da aplicação ou inline_message_id; o Infocard não publica jogos. |

`getChatAdministrators` utiliza `return_bots=true`. Respostas de métodos implementados podem ser recusadas pelo Telegram para um alvo concreto; o estado de execução não é inferido desta tabela.
