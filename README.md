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

## Enriquecimento verificável (2026-11-02)

Para perfis de usuário e bot resolvidos por MTProto, o relatório tenta aproveitar **todos os valores úteis efetivamente fornecidos**, sem criar campos por inferência:

- `users.getFullUser`: mantém nome, bio, aniversário, canal pessoal, presentes e informações do bot quando presentes. Acrescenta o nível `stars_rating.level`, música de destaque (`saved_music`) e indicadores de horários comerciais quando o Telegram os entregar.
- `photos.getUserPhotos`: consulta opcional da contagem de fotos acessíveis. Se a resposta só contiver uma amostra, informa **pelo menos uma**, nunca apresenta a amostra como quantidade total.
- `users.getSavedMusic`: consulta opcional do total de músicas visíveis, executada somente se a ficha completa indicar música no perfil. A ausência desse campo não prova que a pessoa não possua músicas.
- `channels.getFullChannel`: mantém informação de membros, descrição, administradores e reforços, e acrescenta outros campos opcionais de canais, quando retornados.

Falhas nas consultas adicionais não invalidam a ficha principal. Um campo só aparece quando há valor observado; valores omitidos não significam que o dado inexiste. Os logs e resultados são referentes à conta autenticada como bot, não a uma visão irrestrita de todos os perfis.

Fontes: https://core.telegram.org/method/users.getFullUser , https://core.telegram.org/method/photos.getUserPhotos , https://core.telegram.org/method/users.getSavedMusic e https://core.telegram.org/method/channels.getFullChannel .

**Limite:** o ID isolado de uma entidade desconhecida ainda pode ser recusado pelo Telegram. Nem `access_hash=0` nem pesquisa externa permitem garantir a identificação. O cache persistente de peers exigiria uma sessão MTProto protegida e uma arquitetura distinta; **não está implementado**.

## Ficha única: dados consolidados e aprofundados

A pesquisa atualiza **a mesma mensagem rica** do Telegram Serverless / Bot API 10.3. O cartão final reúne:

1. **Identificação confirmada:** tipo de entidade, ID, nome, username, usernames adicionais, indicadores públicos e presença de foto. Esses campos vêm da entidade resolvida por MTProto.
2. **Dados aprofundados:** todos os campos observados no perfil completo e nas consultas opcionais, agrupados em **Perfil e atividade**, **Recursos e presença**, **Informações comerciais**, **Canal ou grupo** e **Outros dados retornados**. Blocos suplementares podem ser expandidos; o resultado não é mais cortado arbitrariamente após 13 linhas.
3. **Origem e observações:** qual referência oficial foi resolvida e quais consultas opcionais não foram autorizadas ou não retornaram dados.
4. **Controles e mídia:** Atualizar, Copiar ID e Abrir perfil quando permitido, mais tentativa de foto no próprio Rich Message; há alternativa com texto HTML válido e envio separado de foto.

Os estados temporários mudam de **pesquisando** para **identificação confirmada**, depois **dados aprofundados** e, por fim, **ficha consolidada** no mesmo `message_id` quando as edições são aceitas. A consulta MTProto não usa o Bot API `getChat` como fonte de perfis.

**Distinção importante:** quando a entrada veio do seletor oficial, a mensagem inicial também pode mostrar os dados compartilhados pelo Telegram; a ficha final apresenta os campos confirmados por MTProto. Não se deve atribuir a MTProto um campo que só apareceu no compartilhamento. Preservar os campos exclusivamente compartilhados ao longo de uma pesquisa que falhou requer um armazenamento temporário e protegido de contexto; o projeto ainda não fornece esse armazenamento.

## Cartão de resultados — Bot API 10.3

O bot agora apresenta as consultas em **Rich Messages** nativas do Telegram:

- `sendRichMessage`: cria um cartão de pesquisa com título, tabela compacta e o botão **Atualizar**.
- O TGCloud envia o `message_id` do cartão ao workflow `resolver.yml`. O resolver edita o mesmo cartão via `editMessageText` com `rich_message` quando a autenticação, a identificação da entidade e a coleta terminam.
- Resultado final: cabeçalho, tabela `<table bordered striped compact>`, dados verificados, seção expandível de detalhes e botões **Atualizar**, **Copiar ID** e **Abrir perfil** (somente com username).
- A imagem do perfil pode aparecer dentro do próprio cartão por `InputRichMessageMedia` e `tg://photo?id=...`, com upload multipart. Se o Telegram recusar a mídia embutida, a mensagem rica permanece e a foto é tentada como envio separado.
- O Telegram Serverless também implementa `handlers/callback_query.js` para atualizar o mesmo cartão, com limite de solicitações e verificação de chat privado.
- Falhas de rich message usam a mensagem HTML convencional como alternativa. Nunca são montadas tabelas HTML na propriedade `text` de `sendMessage`; tabelas são exclusivas de `rich_message`.

**Importante:** `sendRichMessageDraft` cria rascunhos temporários e não substitui uma mensagem persistente. Optamos por `sendRichMessage` e edições de uma mensagem real. O sucesso do CI não comprova que todos os clientes Telegram renderizam a ficha da mesma forma; requer teste real. O token do bot continua exclusivamente no GitHub Actions Secrets, não no código do TGCloud.

Referências: https://core.telegram.org/bots/api#sendrichmessage, https://core.telegram.org/bots/api#editmessagetext, https://core.telegram.org/bots/api#rich-messages e https://core.telegram.org/bots/api#inputrichmessage.

## Referência oficial de username e callbacks sem separador ambíguo

A partir de 2026-11-02, o código diferencia **ID esperado**, **username** e **ação do botão**. O texto que a pessoa envia pode ser `@username`, `ID` ou `ID @username` (esta última é uma convenção de entrada do Infocard, não sintaxe da API do Telegram).

- O Telegram Bot API define `callback_data` como **1–64 bytes opacos**; o Infocard usa o esquema interno validado `f:u:ID:username`, `f:n:username`, `f:i:ID` (também `r:` para atualizar). Ele nunca converte esses dados em texto da pesquisa. A ausência de padrão Telegram para os bytes de `callback_data` não autoriza aceitar sequências arbitrárias sem validação.
- O TGCloud valida o payload e envia `alvo` (username ou ID) e `expected_id` (opcional) como dois inputs distintos para `workflow_dispatch`; não há `ID|username` como referência de perfil.
- O resolver Python chama `contacts.resolveUsername(username)`, recebe `contacts.ResolvedPeer` e, quando `expected_id` está presente, compara o `Peer` retornado usando `utils.get_peer_id` antes de enriquecer o perfil. A pesquisa por ID sem username ainda pode falhar pelas regras de `access_hash` do Telegram.
- Botões produzidos pela versão anterior, com payload antigo, apresentam erro informativo e precisam de uma nova pesquisa. Isso evita reinterpretar indevidamente uma referência legada.

**Regras do repositório:** sem comentários e docstrings no código modificado; os testes Python anteriormente criados pelo mesmo autor da implementação foram retirados do repositório. O CI continua verificando sintaxe JS/Python, placeholders de segredos e deploy. Ele **não comprova resolução MTProto nem callback real**. Para validar o fluxo, use o botão e confira uma execução com `EXPECTED_ID` e `MODO=completo`, além da entrega do `.md` pelo Telegram.

Fontes normativas: https://core.telegram.org/bots/api#callbackquery, https://core.telegram.org/method/contacts.resolveUsername, https://core.telegram.org/type/contacts.ResolvedPeer, https://core.telegram.org/api/peers e https://core.telegram.org/bots/api#senddocument.

## Escolha sob demanda: relatório completo + arquivo Markdown

A primeira consulta de um ID ou username publica apenas um **resumo** com identificação confirmada, destaques e botões. O botão **📚 Completo + Markdown** (callback `f:`) abre **uma nova ficha de andamento**, sem apagar o resumo original, e solicita ao workflow MTProto uma nova coleta oficial da mesma referência.

Após a consulta, o bot envia:
- **Todas as categorias e todos os campos retornados** em uma ou mais mensagens ricas com tabelas e numeração `Parte N/M`, usando `rich_pages`. Se rich messages falharem, usa as páginas do fallback HTML.
- **Anexo `.md` em UTF-8**, enviado via Bot API `sendDocument`, com identificação, todos os campos e observações. Valores não são abreviados no arquivo. Para documentos maiores do que o limite seguro de 40 MiB, o relatório é repartido em arquivos `.md` individualmente válidos. Cada arquivo tem cabeçalho e blocos de texto completos; valores longos são divididos em trechos numerados, preservando os caracteres e a ordem do conteúdo original (não por concatenação literal dos arquivos).
- **Foto de perfil**, quando disponível, incorporada à Rich Message se a Bot API permitir, ou enviada separadamente.

O resumo original não é sobrescrito no modo completo. No modo rico, o botão fica dentro do cartão; se o servidor não aceitar o formato rico, existe também um botão inline convencional **Completo + Markdown** no resumo HTML. A ação é restrita ao chat privado do usuário que a acionou.

**Por segurança e para não reter perfis em bancos públicos**, o botão faz uma nova consulta MTProto. Os valores podem mudar entre a emissão do resumo e o relatório completo. Para permitir o resumo seguido do download sem esperar um minuto, o limite passa a 2 pesquisas por chat por 60 segundos, com total global de 6 por 60 segundos; pesquisas posteriores continuam sujeitas aos limites de Telegram e GitHub.

Apenas os campos oficialmente obtidos e disponíveis à sessão do bot aparecem. Não há consulta universal por ID desconhecido, nem exportação de `access_hash`, telefones privados ou tokens. O arquivo `.md` é um relatório legível, não uma exportação de dados internos/credenciais.

Referência para anexos Bot API: https://core.telegram.org/bots/api#senddocument e https://core.telegram.org/bots/faq.

## Relatório integral com paginação oficial — 2026-11-02

O Infocard reúne identificação confirmada, todos os campos úteis que o resolver MTProto efetivamente extraiu, detalhes da conta/bot/canal, foto e notas de acesso. **Nenhum campo coletado é descartado pelo layout só por exceder 13 linhas ou pelo comprimento de uma bio.** O próprio relatório é dividido em quantas páginas ricas forem necessárias quando atingir o limite oficial; as partes subsequentes aparecem como respostas ao cartão original, identificadas por `Parte X/Y`.

- O **primeiro cartão** é atualizado em seu `message_id` existente. As **continuidades** são enviadas por `sendRichMessage`, com tabelas compactas, títulos, botões e numeração.
- Cada página respeita margem para os limites documentados: até **32.768 caracteres UTF-8**, **500 blocos**, 16 níveis de aninhamento e 50 mídias por mensagem. Os cortes são exclusivamente técnicos e **não omitem valores**; uma descrição muito longa é enviada em partes numeradas.
- A primeira página tenta incluir a foto como mídia nativa da Rich Message. Se a API não aceitar a incorporação na edição, a foto pode ser enviada à parte. Não são inventadas imagens ou outras mídias ausentes.
- O modo de compatibilidade usa mensagens HTML convencionais **também paginadas**, de modo que um erro de Rich Messages não apague os dados.
- Campos adicionais de `userFull` e `channelFull` incluem Stars e suas pontuações, recursos comerciais, permissões disponíveis na sessão do bot, presença de recursos de canal e estatísticas apenas quando os valores são realmente retornados. Dados de sessão, telefone e `access_hash` não são expostos.
- A verificação atual executa checagem sintática JS/Python e dos placeholders de segredos, respeitando a regra do repositório que proíbe testes criados pelo autor da implementação. A prova funcional exige consulta real.

**Limitação de origem:** nem toda conta permite obter todos os campos; IDs numéricos sem referência continuam sujeitos ao acesso autorizado do Telegram. O formato integral evita perder dados **já obtidos**, mas não cria direitos de consulta nem contorna a privacidade.

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
