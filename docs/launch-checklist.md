# Verificações de relatório integral

1. Confira que `npm run check` executou também `test_ficha_completa.py` e não só a sintaxe dos arquivos.
2. Faça uma consulta por `ID @username` cuja correspondência já foi verificada; compare cada campo retornado com a ficha final.
3. Use um usuário/bot com bio, dados adicionais e foto, observando cada campo dentro de seção apropriada.
4. Em caso de muitos campos, confirme `Parte 1/N`, `Parte 2/N` etc. **Nenhuma seção pode desaparecer ou ser truncada**.
5. Confirme a foto incorporada ou enviada separadamente e os botões de Atualizar, Copiar ID e Abrir perfil.
6. Em caso de erro do formato rico, confirme que o modo HTML clássico envia todas as partes.
7. Confira que o worker nunca transmite `access_hash`, telefone, `API_ID`, `API_HASH`, sessões ou tokens como conteúdo do relatório.
8. Registre sucesso apenas com uma execução real de `resolver.yml` que tenha enviado o relatório ao Telegram; deploy e healthcheck não são prova de sucesso em consulta.

## Limites oficiais

A Bot API 10.3 admite até 32.768 caracteres UTF-8, 500 blocos, 16 níveis, 50 mídias e 20 colunas por Rich Message. Ao exceder qualquer teto, o resultado deve continuar na próxima mensagem, sem descarte: https://core.telegram.org/bots/api#rich-message-formatting-options.

# Checklist — cartão rico Telegram Bot API 10.3

- Enviar `@BotFather` no privado: mensagem inicial precisa ser um cartão com título, tabela e botão **Atualizar**.
- Observar as edições de progresso: status de autenticação, entidade identificada e conclusão, sem mandar uma nova mensagem para cada etapa.
- Após o resultado, confirmar campos MTProto dentro da tabela, detalhes expansíveis e botões **Copiar ID** e **Abrir perfil** quando houver username.
- Se existir foto do perfil, verificar se a imagem aparece **na mesma mensagem rica**. Se não, conferir aviso nos logs e fallback de foto separada.
- Pressionar **Atualizar** e confirmar que o callback atualiza o mesmo cartão e respeita o limite de 1 busca por chat por 60 s.
- Conferir busca por ID desconhecido e falha do GitHub para assegurar que a mensagem seja editada com uma explicação, sem credenciais em logs.
- Validar que Rich Messages usam `rich_message` e não `parse_mode=HTML` convencional, que não aceita tabelas.
- Conferir CI, deploy e execução **real** de `resolver.yml`. Um healthcheck verde não executa Telethon.
- Observar diferenças entre versões de clientes Telegram; ter fallback em mensagens HTML convencionais.

Fonte oficial: https://core.telegram.org/bots/api (Bot API 10.3, 24 de agosto de 2026).

# Checklist do Infocard — pesquisa MTProto por ID ou referência

## Antes do deploy

- Use `main` e confirme CI verde; prefira repositório privado durante testes.
- Mantenha `.gitignore`, sem `.env`, sessões, tokens ou credenciais no Git.
- Confirme os cinco secrets no GitHub Actions: `API_ID`, `API_HASH`, `BOT_TOKEN`, `GH_DISPATCH_TOKEN`, `TGCLOUD_TOKEN`.
- O `GH_DISPATCH_TOKEN` precisa de Actions: Read and write; o repositório é obtido de `github.repository`, nunca fixado.
- No @BotFather, ative o Serverless; opcionalmente habilite inline mode.

## Deploy

- Execute `Deploy (Telegram Serverless)` na `main` ou faça push de mudanças do runtime.
- Confira: `npm ci`, `fetch`, `status`, migração, configuração privada no runner, `push`, webhook e dispatch.
- O healthcheck **não** prova a resolução real por MTProto.

## Smoke tests no privado

1. `/start` mostra as três formas: `@username`, `ID` e `ID @username` e o botão seletor.
2. `@BotFather` dispara um workflow MTProto real e retorna uma resposta.
3. Um ID numérico não é bloqueado localmente: inicia tentativa oficial por ID e apresenta o resultado ou causa de falha.
4. `ID @username` correspondente recebe resultado verificado; ID discordante deve dar erro sem associar pessoas erradas.
5. Teste o botão `Escolher usuário como referência`. O Telegram pode enviar apenas ID (sem username), sem garantir resolução.
6. Encaminhamento com remetente visível pode oferecer ID/username; remetente oculto deve ser informado como indisponível.
7. Confira que nenhuma consulta de perfil usa `api.getChat`.
8. Verifique execução e logs de `Resolver entidade (MTProto)`.

## Teste de retorno parcial verificável

- Escolha um usuário usando o botão oficial e confirme que a primeira resposta exibe **Informações fornecidas pelo Telegram**, ID e nome/username se presentes, independentemente de sucesso do resolver.
- Escolha um canal e um grupo. Verifique os dados `chat_shared` e a tentativa separada de enriquecimento por MTProto.
- Não confunda campos fornecidos em uma seleção com campos confirmados pelo MTProto.
- Confira erros de runtime do `request_chat` no SDK, pois CI e deploy validam publicação e sintaxe, não a compatibilidade de cada botão com o cliente Telegram.
- Na pesquisa por ID digitado, confirme que uma recusa do servidor gera explicação útil, sem dados inventados.

## Enriquecimento real — testes adicionais

- Execute uma pesquisa de usuário com `ID @username` já confirmado e confira que os campos extraídos do MTProto permanecem corretos.
- Se `stars_rating` vier presente, verifique se o relatório exibe o nível. Nunca interprete campo ausente como nível zero.
- Se `saved_music` vier presente, confira a música destacada e, quando autorizada, a contagem de músicas via método oficial.
- Se o Telegram fornecer fotos, confira se `photos.getUserPhotos` retornou total ou apenas amostra; ambos devem ser apresentados com rótulos diferentes.
- Teste um bot público e verifique os campos de `bot_info`, sem expor informações internas.
- Simule uma resposta sem dados adicionais para confirmar que o relatório básico continua disponível. A execução do CI garante sintaxe, mas **não substitui** os testes reais da API.
- A solução não utiliza scraping, gerações de dados por IA nem consultas não oficiais para inventar campos.

## Limites

Um `access_hash` é específico do contexto MTProto e não é fornecido universalmente a partir de IDs. O valor zero é uma forma documentada de referência para bots em certas condições, não um método para contornar restrições. Não prometa que qualquer ID terá resultado.
