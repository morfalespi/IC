# Integrações Telegram: contratos, evidências e limites

Revisão iniciada na `main` c9195d1, que incorporou o PR #32. Este documento substitui o relatório acumulado anterior: contagens de sondagens simuladas não constituem prova de integração real. README.md, AGENTS.md e SECURITY.md permanecem excluídos.

## Contratos usados na implementação

- [Bot API — Making requests](https://core.telegram.org/bots/api#making-requests): HTTPS e envelope `ok/result` ou erro com `description/error_code`. O cliente rejeita envelope incompleto e contradição entre sucesso e status HTTP de erro. Autenticação recusada é fatal.
- [ResponseParameters](https://core.telegram.org/bots/api#responseparameters): repetição por `retry_after` aguarda a duração fornecida; migração de grupo usa exclusivamente `migrate_to_chat_id` recebido. Erro de transporte ou 5xx sem instrução não dispara novo envio.
- [Message](https://core.telegram.org/bots/api#message): aceitação com `message_id=0` permanece pendente. Confirmação requer resposta coerente com o chat solicitado; não prova leitura humana. A regra conservadora local também mantém `date=0` pendente, sem reenvio automático.
- [Peer database e access hash](https://core.telegram.org/api/peers): peers são distinguidos pelo tipo e ID; hashes completos do cache da mesma sessão são preservados. Hash zero fica restrito ao contexto de bot previsto pelo protocolo. ChatEmpty e formatos numéricos não provam acesso.
- [Telethon — cliente](https://docs.telethon.dev/en/stable/modules/client.html): autenticação usa `start(bot_token=...)`; `raise_last_call_error=True` preserva a última recusa RPC após esgotar as tentativas nativas, evitando substituí-la por ValueError genérico. O restante das tentativas nativas permanece com os padrões do SDK.
- [Telethon — erros](https://docs.telethon.dev/en/stable/concepts/errors.html): FLOOD_WAIT propagado aguarda os segundos do servidor. Recusas esperadas de leituras opcionais são registradas como coleta parcial; autenticação e falhas de programação interrompem o fluxo. Coleta parcial não significa conclusão integral.
- [Telethon — sessões](https://docs.telethon.dev/en/stable/concepts/sessions.html): SQLite conserva a autorização e o cache. Sem diretório privado configurado, a sessão é temporária e não persiste entre runners. Sessões e credenciais não são publicadas nem armazenadas em artifacts/cache.

Formato rich ou HTML é escolhido antes de enviar. Não há fallback automático para outro formato, reenvio sem foto após recusa, nem criação de peer presumido após falha das APIs. A notificação de falha é um fluxo separado e registra recusa, pendência ou confirmação. Os relatórios preservam os dados de perfil da funcionalidade; a redação de credenciais não equivale a anonimização universal.

## Alterações desta retomada

1. Preservar o erro RPC original no cliente Telethon.
2. Rejeitar envelope de erro sem os campos documentados antes de interpretar instruções de repetição.
3. Na leitura real entre APIs, consultar MTProto pelo ID estável já confirmado por getChat, em vez de resolver novamente o username.
4. Substituir o relatório de sondagens por contratos e evidências com escopo explícito.
5. Antes da coleta, confirmar o bot por getMe e confrontá-lo com get_me do Telethon. start pode reutilizar uma sessão autorizada e apenas emitir aviso quando o token aponta para outra conta; o worker agora interrompe uma divergência antes de resolver o alvo. Não usa regex de credenciais, prazo de autenticação inventado nem identidade inferida de cache.
6. No JavaScript, mensagens pendentes/inacessíveis ou incompatíveis com o destino não iniciam o worker. Falhas de envio/edição atravessam consultar e os handlers sem nova edição ou mensagem HTML alternativa. Uma recusa explícita de edição inalterada permanece uma operação sem mudança, sem fabricar Message/data/chat de sucesso.
7. A rota validar_apis passa a executar também fontes locais no runtime Serverless por /run, sem publicar. Ela exige o mesmo bot/canal confirmado pelo Python, carrega os handlers reais, lê as colunas do schema sem alterá-lo, verifica uma recusa real de getChat(0) e lê o estado público do workflow pelo fetch do SDK. Não usa SDK substituído ou banco falso. As referências ao CLI interno estão vinculadas à versão do package-lock; mudança da interface deve falhar na validação.

8. Modo desconhecido, MESSAGE_ID inválido/sem chat e ORIGEM_ID inválido/sem chat falham antes de qualquer autenticação. Não são convertidos silenciosamente em consulta completa, novo envio ou ausência de referência.
9. O deploy deixa de confiar somente no código de saída de tgcloud webhook: o CLI pode imprimir OUT OF SYNC e terminar com zero. O novo verificador exige in_sync=true, URL e tipos de update correspondentes e contagem válida; não sincroniza o webhook automaticamente nem imprime sua URL.

A conferência do runtime não exercita entregas, callbacks reais ou disparo de pesquisa pelo bot. Esses cenários não serão apresentados como validados por uma leitura.

## Evidência observada antes desta retomada

A [execução real 42023095036](https://github.com/morfalespi/IC/actions/runs/42023095036), no commit 03baeed, confirmou getMe, getChat, autenticação Telethon, mesmo canal e perfil completo MTProto e redação dos campos de autenticação exportados. Aguardou FLOOD_WAIT de 64 e 141 segundos. Não enviou mensagens nem arquivos. É evidência histórica daquele commit, não validação automática das alterações atuais.

A [CI 42023853598](https://github.com/morfalespi/IC/actions/runs/42023853598), no commit cb7c480, verificou sintaxe e compatibilidade em Node 22/Python 3.12 e Node 24/Python 3.13. Inspeção de importações e assinaturas não comprova comportamento remoto.

A execução [42077826191](https://github.com/morfalespi/IC/actions/runs/42077826191), no commit fd0b167, confirmou a leitura Bot API/MTProto e a correspondência da conta autenticada. A etapa Serverless falhou antes da chamada remota porque o verificador tentou abrir schema.js fora de tgcloud/. O caminho foi corrigido usando readWd do próprio CLI; essa falha não é apresentada como validação Serverless. As execuções seguintes serão vinculadas no PR com seus resultados efetivos. Não foram criados testes com API substituída nesta retomada.

## Limites e decisões operacionais

- Entrega real de mensagens, Markdown, JSONL e ZIP ainda depende de um chat de teste explicitamente autorizado. A rota opt-in `validar_entrega` está preparada; sua existência não comprova entrega. Nenhum destinatário é inferido de logs ou execuções anteriores.
- Não foi executado o runtime Serverless publicado nem deploy real. O workflow de deploy ainda possui gatilho em push para main nos caminhos configurados; um merge pode acioná-lo.
- Timeouts HTTP, timeout do job, tamanhos de lote/arquivo e limites locais de consumo são decisões operacionais, não garantias do Telegram. Esperas de rate limit continuam sujeitas ao término/cancelamento do job.
- Máscaras protegem logs do Actions, não tornam workflow_dispatch ou o repositório públicos confidenciais.
- JSONL usa `infocard-telegram-jsonl-v3`; consumidores externos que exijam v2 podem precisar de adaptação.
- Sem resposta conclusiva a uma escrita, não há garantia de entrega exatamente uma vez. O cliente não repete a escrita cegamente e não afirma sucesso.
- Commits verificados comprovam assinatura, não correção funcional. Esta revisão não promete eliminar erros externos, indisponibilidade ou restrições de acesso das APIs.
