# Infocard — consulta MTProto com referências oficiais

A consulta de entidades do Telegram usa **MTProto por Telethon**, sem chamada a `getChat` para busca de perfis. A Bot API é usada somente para receber mensagens, receber referências compartilhadas oficialmente e entregar resultados.

## Pesquisas suportadas

- `@username`: usa `contacts.resolveUsername` e consulta os dados autorizados pelo Telegram.
- `ID`: **tenta** o método oficial adequado ao tipo de entidade com `access_hash=0` quando permitido a bots. Esse valor não é um token, não é um segredo e não garante acesso; o servidor pode recusar IDs desconhecidos.
- `ID @username`: resolve o username pelo método oficial e **verifica se o ID corresponde ao peer retornado**. Em caso de divergência, não entrega dados de outra entidade.
- **Escolher usuário como referência**: usa `KeyboardButtonRequestUsers` e o `users_shared` oficial do Telegram para receber ID e, quando disponível, username. O bot utiliza essa referência no resolver MTProto, sem pesquisa por `getChat`.
- **Encaminhar uma mensagem com remetente identificado** ou compartilhar contato/menção: extrai exclusivamente o ID e eventual username fornecidos pelo Telegram e aciona a mesma pesquisa MTProto. Remetente oculto não pode ser identificado por esse fluxo.

IDs numéricos são aceitos como solicitações de pesquisa, mas **não existe consulta universal e garantida por ID**, pois o Telegram controla a disponibilidade de `access_hash` e referências por conta/sessão. Se um ID não for reconhecido, tente `ID @username` ou o seletor oficial de usuário.

## Resultados úteis quando o MTProto não consegue enriquecer o ID

O bot não descarta mais os campos recebidos em `users_shared`, `chat_shared`, contato, encaminhamento ou menção. Ele mostra imediatamente os valores efetivamente fornecidos pelo Telegram (ID, nome/título, username e indicação de foto quando presentes), identificando **a origem do compartilhamento**, além de tentar o enriquecimento por MTProto. Dados compartilhados e resposta da pesquisa são apresentados separadamente: um não prova o outro.

O seletor oficial oferece **Escolher usuário**, **Escolher canal** e **Escolher grupo**. Isso aumenta a chance de produzir informação útil sem criar um serviço de coleta de perfis ou inventar `access_hash`. Mesmo assim, a documentação do Telegram adverte que o bot pode não conseguir consultar o chat ou o usuário apenas pelo ID compartilhado.

Para **ID digitado isoladamente**, somente o número está disponível; nenhuma API oficial garante descobrir nome, foto ou username de uma conta desconhecida. A solução estrutural para recuperar entidades já conhecidas em consultas futuras é um worker MTProto de longa duração com base de peers e sessão autenticada persistente, protegida fora do Git e de artefatos públicos. Não armazene sessões ou access hashes em GitHub Actions logs, código ou secrets genéricos sem um projeto específico de proteção e rotação.

## Arquitetura

- `tgcloud/handlers/message.js`: entrada privada, referências compartilhadas e comandos.
- `tgcloud/handlers/inline_query.js`: oferece a continuação no privado.
- `tgcloud/lib/entrada.js`: parsing de username, ID e referência composta.
- `tgcloud/lib/consulta.js`: limite de disparos e criação do workflow; não usa `getChat`.
- `tgcloud/lib/despacho.js`: dispara o workflow pelo `github.repository` injetado no deploy.
- `scripts/resolver.py`: `contacts.resolveUsername`, `users.getUsers`, `channels.getChannels` e `messages.getChats` via Telethon; consulta informações adicionais quando possível e devolve o resultado ao chat.
- `.github/workflows/resolver.yml`: execução sob demanda, com verificação de secrets e entrega do resultado.
- `.github/workflows/deploy.yml`: publicação no Telegram Serverless.

O bot só processa pesquisas em conversas privadas. Inline exibe uma opção para continuar no privado. O limite operacional é 1 disparo por chat e 6 no total a cada 60 segundos.

## Segredos e segurança

**Nunca** versione tokens ou sessões. `tgcloud/lib/segredos.js` contém apenas placeholders vazios no Git; o deploy injeta `GH_DISPATCH_TOKEN` de Actions Secrets e o nome do repositório a partir de `github.repository`.

| Secret | Uso |
|---|---|
| `API_ID` | Aplicação MTProto |
| `API_HASH` | Aplicação MTProto |
| `BOT_TOKEN` | Autenticação do bot no Telethon e envio dos resultados |
| `GH_DISPATCH_TOKEN` | Disparar o resolver do GitHub Actions |
| `TGCLOUD_TOKEN` | Deploy no Telegram Serverless |

`API_HASH` não é `access_hash`. Não informe `access_hash` manualmente nem copie valores de outra conta/sessão.

## Testes do primeiro deploy

1. Rode `npm ci` e `npm run check` ou confira CI.
2. Confira o deploy TGCloud e o healthcheck do dispatch.
3. Envie `/start`, `@BotFather`, um ID numérico conhecido e `ID @username` correspondente em conversa privada.
4. Use o botão **Escolher usuário como referência**.
5. Verifique o run **Resolver entidade (MTProto)** realmente executando o Telethon; o healthcheck não exercita a consulta.
6. Em casos de falha, examine os logs e a mensagem devolvida ao chat.

## Documentação oficial

- Referências MTProto e `access_hash`: https://core.telegram.org/api/peers
- `users.getUsers`: https://core.telegram.org/method/users.getUsers
- `contacts.resolveUsername`: https://core.telegram.org/method/contacts.resolveUsername
- `KeyboardButtonRequestUsers` e `users_shared`: https://core.telegram.org/bots/api#keyboardbuttonrequestusers

O registro em `docs/registro.md` documenta versões anteriores e deve ser lido como histórico, não como uma instrução para retornar à pesquisa de perfis por Bot API.
