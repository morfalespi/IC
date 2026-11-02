# Cobertura MTProto do Infocard

## Decisão de objetivo

Aplicar Partners como método obrigatório de evolução. O resultado desejado é entregar, para a referência consultada, todos os campos e conteúdos de leitura que o Telegram MTProto realmente disponibiliza à sessão de bot, sem reduzir o escopo aos campos já exibidos pelo projeto. Código anterior é inventário, não padrão normativo.

A cobertura deve preservar objetos TL completos, wrappers de resposta, campos escalares e aninhados, listas, metadados e conteúdo de mídia devolvido pelos métodos elegíveis. Coleções pagináveis devem ser lidas até o fim ou identificadas como parciais. A exportação estruturada preserva também valores vazios, zero e falso quando retornados.

## Limites oficiais da sessão de bot

- As chamadas de leitura usadas nesta primeira entrega são `users.getFullUser`, `channels.getFullChannel`, `messages.getFullChat`, `photos.getUserPhotos`, `users.getSavedMusic` e, quando o Telegram indicar capacidade, `channels.getParticipants`.
- `channels.getParticipants`, `photos.getUserPhotos` e `users.getSavedMusic` aceitam bots. O worker agora tenta essas leituras no modo completo sem depender de flags parciais; a resposta do Telegram determina o que a sessão realmente pode ler. Participantes podem exigir administração.
- `messages.getHistory`, `stories.getPeerStories`, `messages.getCommonChats` e `messages.getPeerSettings` são exclusivos de sessões de usuário. Como a pessoa decidiu manter autenticação de bot, o Infocard registra esses limites e não promete histórico ou stories ativos.
- Permissões, privacidade, FloodWait, ausência de dados e diferenças de layer podem limitar a resposta. Campo ausente não significa que o dado não exista.
- Escopo é leitura da entidade e das coleções que os métodos acima retornam. Nenhuma chamada de alteração é incluída.

## Estado da implementação na branch

| Capacidade | Estado no código | Limite atual |
|---|---|---|
| Entidade resolvida e objeto de perfil completo | Implementado | As respostas completas são serializadas; isso ainda precisa de execução real após a alteração |
| Fotos de perfil | Consultada e paginada no modo completo para todo usuário resolvido | Paginação e download dependem do que Telegram disponibilizar |
| Música salva no perfil | Consultada e paginada no modo completo para todo usuário resolvido | A resposta do Telegram informa a coleção acessível, inclusive vazia |
| Participantes de canal | Tentativa paginada no modo completo | A chamada não é pulada por flags; Telegram ainda pode recusar por permissão |
| Dados estruturados | JSONL sem mapeamento manual, dividido em anexos | Confirmação da Bot API não prova que o arquivo recebido abre ou preserva todo conteúdo |
| Foto e arquivos de mídia baixáveis | ZIP com manifesto e hash | Itens indisponíveis ou acima do limite são explicitados; não contam como sucesso integral |
| Histórico de mensagens e stories ativos | Fora do acesso de bot | Métodos exigem sessão de usuário; não serão habilitados mantendo a decisão de autenticação atual |
| Inventário de todos os outros métodos MTProto elegíveis por tipo de peer | Ainda não concluído | A exportação atual preserva respostas dos métodos chamados, mas não cobre por si só todos os métodos relacionados possíveis |

## O que substitui

Antes desta evolução, o resolver mapeava uma seleção de campos, consultava no máximo uma foto e uma música, e não entregava uma exportação bruta completa. A implementação atual acrescenta preservação de respostas TL, paginação de fotos e músicas, tentativa de listar participantes, exportação JSONL e pacotes de mídia. Isso amplia materialmente a cobertura, mas não conclui a meta de inventariar e chamar todos os métodos de leitura relevantes.

## Próximos passos necessários

1. Inventariar, por tipo de peer, os métodos oficiais de leitura que podem ser chamados por bot e quais dados adicionais cada método fornece. Comparar com a layer realmente instalada do Telethon.
2. Implementar as chamadas relevantes que ainda não existem, registrar por método o estado `concluído`, `sem dados`, `sem permissão`, `não suportado para bot` ou `falha`, e paginar até o fim.
3. Confirmar que cada resposta chamada está presente no JSONL, que as mídias acessíveis foram empacotadas e que arquivos acima do limite aparecem como parciais.
4. Executar no Telegram com referência pública de teste; inspecionar os JSONL e os pacotes realmente recebidos. CI, sintaxe e `ok=true` de envio são verificações intermediárias.
5. Só declarar cobertura total dentro do escopo definido quando o inventário de métodos e a prova de ponta a ponta estiverem concluídos. Dados que a API não conceder devem aparecer como limite observado, nunca ser inferidos.

## Critério de sucesso sustentado

Para cada execução completa, todas as respostas dos métodos de leitura inventariados e elegíveis foram serializadas sem perda, as coleções acessíveis foram paginadas até o fim, os anexos obrigatórios foram aceitos e inspecionados no Telegram, e cada campo ou coleção indisponível tem um estado e motivo explícitos. O sucesso continua limitado ao acesso realmente concedido pelo Telegram à sessão de bot.
