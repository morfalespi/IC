# Cobertura MTProto do Infocard

## Decisão de objetivo

Aplicar Partners como método obrigatório de evolução. O resultado desejado é entregar a cobertura máxima e verificável dos dados de leitura que o Telegram MTProto disponibiliza à sessão de bot para a entidade consultada. Código e campos já exibidos servem como inventário do estado atual, não como limite normativo.

A cobertura deve incluir campos escalares e aninhados, listas, metadados e conteúdo retornado por métodos de leitura elegíveis para bots. Resultados paginados devem ser percorridos até o fim ou receber um estado explícito de incompletude. A entrega deve preservar dados vazios, zero e falso quando esses valores fizerem parte da resposta; ausência de campo não significa valor falso nem inexistência da entidade.

## Limites oficiais do modelo de bot

- `users.getFullUser`, `channels.getFullChannel`, `messages.getFullChat`, `photos.getUserPhotos` e `users.getSavedMusic` aceitam autorização de bot.
- `channels.getParticipants` aceita bots, mas o Telegram pode exigir administração e a lista pode estar oculta ou indisponível.
- `messages.getHistory` e `stories.getPeerStories` são métodos exclusivos de contas de usuário. Não prometer histórico de mensagens nem stories ativos enquanto o projeto usar `BOT_TOKEN`.
- Recursos privados, removidos, inacessíveis ao bot, bloqueados por privacidade ou limitados por flood wait devem ser reportados como indisponíveis ou parciais, com motivo observável; não inferir que não existem.
- Não converter método de leitura em método de alteração. O escopo é leitura da entidade solicitada e recursos associados necessários ao relatório.

## Estado observado antes desta evolução

- O resolver autentica Telethon com `bot_token`.
- Os métodos completos retornam conjuntos de campos de usuário, canal e grupo; o código apresenta apenas alguns campos mapeados.
- A resolução descarta os wrappers de resposta completos de `users.getFullUser`, `channels.getFullChannel` e `messages.getFullChat`.
- Fotos de perfil e músicas são consultadas com limite inicial de um item; a implementação registra contagens, não percorre os recursos completos.
- Não existe exportação estruturada de todas as respostas MTProto.

Estes itens descrevem o estado inspecionado e não justificam manter o recorte atual.

## Plano de evolução

1. Inventariar os métodos de leitura e todos os campos dos tipos TL usados, confrontando a versão instalada de Telethon com a layer oficial.
2. Preservar wrappers e objetos associados retornados pelo Telegram, além da entidade principal e do objeto `full_user`/`full_chat`.
3. Percorrer listas elegíveis por paginação, respeitando autorização, permissões, limites e FloodWait.
4. Gerar uma exportação estruturada que preserve os valores retornados e entregue itens em partes sem truncamento silencioso; manter uma apresentação legível para consulta.
5. Registrar a cobertura de cada método como concluída, parcial, recusada ou não suportada nesta autenticação.
6. Só declarar resultado completo após evidência da resposta MTProto, aceitação de cada página/anexo pela Bot API e inspeção do conteúdo recebido no Telegram.

## Critério de sucesso sustentado

Para cada consulta, os campos e recursos elegíveis retornados pela sessão de bot estão presentes na exportação; coleções pagináveis foram consumidas até o fim; cada parte obrigatória teve confirmação da Bot API; campos omitidos por acesso, privacidade, versão ou limite aparecem no relatório de cobertura com o motivo. O sucesso é limitado ao acesso que o Telegram realmente concedeu à sessão de bot.
