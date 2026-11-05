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

## Evidência observada antes desta retomada

A [execução real 42023095036](https://github.com/morfalespi/IC/actions/runs/42023095036), no commit 03baeed, confirmou getMe, getChat, autenticação Telethon, mesmo canal e perfil completo MTProto e redação dos campos de autenticação exportados. Aguardou FLOOD_WAIT de 64 e 141 segundos. Não enviou mensagens nem arquivos. É evidência histórica daquele commit, não validação automática das alterações atuais.

A [CI 42023853598](https://github.com/morfalespi/IC/actions/runs/42023853598), no commit cb7c480, verificou sintaxe e compatibilidade em Node 22/Python 3.12 e Node 24/Python 3.13. Inspeção de importações e assinaturas não comprova comportamento remoto.

As execuções do novo commit serão vinculadas no PR com seus resultados efetivos. Não foram criados testes com API substituída nesta retomada.

## Limites e decisões operacionais

- Entrega real de mensagens, Markdown, JSONL e ZIP ainda depende de um chat de teste explicitamente autorizado. A rota opt-in `validar_entrega` está preparada; sua existência não comprova entrega. Nenhum destinatário é inferido de logs ou execuções anteriores.
- Não foi executado o runtime Serverless publicado nem deploy real. O workflow de deploy ainda possui gatilho em push para main nos caminhos configurados; um merge pode acioná-lo.
- Timeouts HTTP, timeout do job, tamanhos de lote/arquivo e limites locais de consumo são decisões operacionais, não garantias do Telegram. Esperas de rate limit continuam sujeitas ao término/cancelamento do job.
- Máscaras protegem logs do Actions, não tornam workflow_dispatch ou o repositório públicos confidenciais.
- JSONL usa `infocard-telegram-jsonl-v3`; consumidores externos que exijam v2 podem precisar de adaptação.
- Sem resposta conclusiva a uma escrita, não há garantia de entrega exatamente uma vez. O cliente não repete a escrita cegamente e não afirma sucesso.
- Commits verificados comprovam assinatura, não correção funcional. Esta revisão não promete eliminar erros externos, indisponibilidade ou restrições de acesso das APIs.
