# Checklist operacional do Infocard

## Antes de publicar

- Confirmar a main e o diff previsto, sem segredos no Git.
- Consultar documentação oficial do método alterado e o SDK instalado.
- Validar contratos documentados e registrar o escopo efetivamente observado; SDK substituído não comprova integração real.
- Conferir que npm run check executa sintaxe JS/Python e verifica o placeholder de tgcloud/lib/segredos.js.
- Verificar configurações de deploy, migração e healthcheck separadamente.

## Após publicar

- CI verde prova somente verificações que ele executou.
- Deploy verde prova que sincronização/migração/publicação declaradas terminaram, não que a função corrigida funciona.
- Healthcheck do resolver prova aceitação do workflow_dispatch; Telethon é pulado.
- Verificar nos logs do worker qual input chegou, se o peer corresponde e quais operações Bot API retornaram ok. Não divulgar valores completos de IDs de terceiros em relatórios públicos.
- Verificar a mesma mensagem no aplicativo Telegram, incluindo o recebimento de mídia e anexo .md.

## Matriz de comportamento real

| Cenário | Resultado obrigatório | Prova |
|---|---|---|
| /start, /help | Ajuda e seletores | Mensagem recebida no privado |
| @username público | contacts.resolveUsername e relatório | Run não-healthcheck e mensagem |
| ID sem contexto | Resultado permitido ou erro explicativo | Run e feedback |
| ID @username com correspondência | Identidade coincidente antes dos dados | Log de resolução e relatório |
| ID @username divergente | Nenhum dado atribuído ao ID incorreto | Mensagem de recusa |
| Escolher usuário, grupo e canal | Mostrar referência recebida e iniciar automaticamente a coleta completa | Mensagem inicial e workflow `MODO=completo` |
| Atualizar | Callback validado e nova coleta completa editando o cartão | Callback, workflow e mesmo message_id |
| Consulta privada normal | Páginas ricas, Markdown, JSONL e ZIP com mídia acessível | Logs de envio, hashes e anexos recebidos/abertos no Telegram |
| Rich Message recusada ou pendente | Falha ou pendência explícita, sem HTML/foto alternativos nem início do worker com message_id=0 | Resposta oficial e interrupção do fluxo |
| Limite excedido | Explicação ao usuário | Mensagem e bloqueio de dispatch |

## Limites e riscos

- 2 consultas por chat e 6 no total em janela de 60 s (tgcloud/lib/limite.js).
- Telegram Bot API 10.3: limites oficiais de Rich Messages; paginar preservando conteúdo efetivamente coletado.
- Um botão criado por versão anterior pode ser inválido e deve solicitar nova busca.
- Identificador ID isolado desconhecido não é consulta universal.
- O repositório é público e os inputs do workflow podem expor ID/chat. Não tratar logs públicos como repositório de dados privados.
- Um arquivo Markdown válido e um CI verde **não** confirmam que o documento foi entregue: verificar sendDocument e recebimento.

## Entrega sem corte arbitrário

- Conferir que uma consulta normal inicia a coleta completa e entrega todos os campos das respostas efetivamente coletadas, não apenas os campos mapeados do cartão resumido.
- Para grupos básicos acessíveis, verificar se `messages.getFullChat` responde e fornece informações complementares.
- Observar retry_after/FLOOD_WAIT recebidos do servidor; não antecipar a repetição nem alternar o formato após recusa.
- Coleta ou entrega parcial deve impedir conclusão integral. O formato rich ou HTML deve ser escolhido antes da execução.
- Comprovar `RELATÓRIO ENTREGUE` somente quando as confirmações de todos os componentes obrigatórios estiverem presentes; não confundir com a aceitação do dispatch.
